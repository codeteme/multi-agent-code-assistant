"""Cross-run memory for the agentic controller."""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

MEMORY_DIR = Path(".agentic_memory")


def _memory_path(file_path: str, agent_name: str) -> Path:
    safe_name = file_path.replace("/", "_").replace("\\", "_")
    return MEMORY_DIR / safe_name / f"{agent_name}.json"


def save_agentic_memory(
    file_path: str, agent_name: str, tool_calls: list[dict], outcome: str
) -> None:
    path = _memory_path(file_path, agent_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "tool_calls": tool_calls,
        "outcome": outcome,
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        logger.info("Saved agentic memory to %s", path)
    except OSError as e:
        logger.warning("Could not save agentic memory: %s", e)


def load_agentic_memory(file_path: str, agent_name: str) -> dict | None:
    path = _memory_path(file_path, agent_name)
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not load agentic memory: %s", e)
        return None


def format_for_prompt(record: dict) -> str:
    timestamp = record.get("timestamp", "unknown time")[:10]
    outcome = record.get("outcome", "unknown")
    tool_calls = record.get("tool_calls", [])

    tool_summary = ", ".join(
        f"{tc['tool']} (result: {tc['result']})" for tc in tool_calls
    )

    return (
        f"Previous attempt ({timestamp}): {tool_summary}. "
        f"Outcome: {outcome}. "
        "Adapt your strategy — avoid repeating approaches that did not converge."
    )
