"""Agentic controller: the LLM decides which tools to call and when to stop."""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

from src.agents.abstract_agent import BaseAgent
from src.agents.registry import AGENT_REGISTRY
from src.util.agentic_memory import format_for_prompt, load_agentic_memory, save_agentic_memory
from src.util.issue import Issue
from src.util.suggestion import Suggestion

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 3

SYSTEM_PROMPT = """You are an autonomous code quality agent. You have four tools:
- scan: find issues in the file
- get_suggestions: generate fixes for the issues found
- apply: apply the fixes to the file
- validate: re-scan to check whether issues remain

Your job is to iterate until the file is clean or you have validated {max_iterations} times.
Always call scan first. If issues are found and apply_fixes is true, call get_suggestions,
then apply, then validate. If validate shows remaining issues, repeat the cycle.
Never ask the user whether to continue — keep going autonomously until done or until
you have reached the iteration limit. When finished, summarize what was done.""".format(
    max_iterations=MAX_ITERATIONS
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "scan",
            "description": "Scan the file for code quality issues using the selected agent.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_suggestions",
            "description": "Generate fix suggestions for the issues found by scan.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply",
            "description": "Apply the suggestions to the file.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate",
            "description": "Re-scan the file to check whether all issues have been resolved.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


@dataclass
class AgentState:
    file_path: str
    agent: BaseAgent
    apply_fixes: bool
    issues: list[Issue] = field(default_factory=list)
    suggestions: list[Suggestion] = field(default_factory=list)


def execute_tool(tool_name: str, state: AgentState) -> dict:
    if tool_name == "scan":
        state.issues = state.agent.scan(state.file_path)
        return {
            "issues_found": len(state.issues),
            "issues": [
                {"line": i.line, "message": i.message, "severity": i.severity}
                for i in state.issues
            ],
        }

    if tool_name == "get_suggestions":
        if not state.issues:
            return {"error": "No issues to suggest fixes for. Call scan first."}
        with open(state.file_path, encoding="utf-8") as f:
            content = f.read()
        state.suggestions = state.agent.get_suggestions(state.issues, content)
        return {"suggestions_generated": len(state.suggestions)}

    if tool_name == "apply":
        if not state.suggestions:
            return {"error": "No suggestions to apply. Call get_suggestions first."}
        if not state.apply_fixes:
            return {"skipped": True, "reason": "--apply flag not set"}
        state.agent.apply(state.suggestions, state.file_path)
        return {"applied": len(state.suggestions)}

    if tool_name == "validate":
        state.issues = state.agent.scan(state.file_path)
        is_valid = state.agent.validate(state.issues)
        return {
            "is_valid": is_valid,
            "remaining_issues": len(state.issues),
        }

    return {"error": f"Unknown tool: {tool_name}"}


class AgenticController:
    def __init__(self) -> None:
        token = os.getenv("LITELLM_TOKEN")
        if not token:
            raise RuntimeError("Missing LITELLM_TOKEN.")
        base_url = os.getenv("LLM_API_URL", "https://litellm.oit.duke.edu/v1")
        self.client = OpenAI(api_key=token, base_url=base_url)
        self.model = os.getenv("MODEL_ID", "GPT 4.1")

    def run(self, file_path: str, agent_name: str, apply_fixes: bool) -> None:
        if agent_name not in AGENT_REGISTRY:
            raise ValueError(f"Unknown agent: {agent_name}")

        agent = AGENT_REGISTRY[agent_name]()
        state = AgentState(file_path=file_path, agent=agent, apply_fixes=apply_fixes)

        system_prompt = SYSTEM_PROMPT
        prior = load_agentic_memory(file_path, agent_name)
        if prior:
            system_prompt += "\n\n" + format_for_prompt(prior)
            logger.info("[Agentic] Loaded memory from previous run: %s", prior["timestamp"])

        messages: list[Any] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"File: {file_path}\n"
                    f"Agent: {agent_name}\n"
                    f"Apply fixes: {apply_fixes}\n\n"
                    "Please scan the file, fix any issues you find, and validate the result."
                ),
            },
        ]

        validate_count = 0
        collected_tool_calls: list[dict] = []
        outcome = "did not converge"

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            message = response.choices[0].message

            if not message.tool_calls:
                print(message.content)
                outcome = "converged"
                break

            messages.append(message)

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                logger.info("[Agentic] LLM called tool: %s", name)
                result = execute_tool(name, state)
                logger.info("[Agentic] Tool result: %s", result)

                collected_tool_calls.append({"tool": name, "result": result})

                if name == "validate":
                    validate_count += 1
                    if result.get("is_valid"):
                        outcome = "converged"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })

            if validate_count >= MAX_ITERATIONS:
                logger.info("[Agentic] Reached max iterations (%d), stopping.", MAX_ITERATIONS)
                break

        save_agentic_memory(file_path, agent_name, collected_tool_calls, outcome)
        logger.info("[Agentic] Run complete. Outcome: %s", outcome)
