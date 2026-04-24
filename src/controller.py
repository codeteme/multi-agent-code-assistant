import logging

from src.util.input import ParsedInput, parse_input
from src.util.issue import Issue
from src.util.planner import plan
from src.util.suggestion import Suggestion
from src.agents.registry import AGENT_REGISTRY

logger = logging.getLogger(__name__)


class Controller:
    def run(self, args=None):
        parsed_input = parse_input(args)
        self._log_parsed_input(parsed_input)

        agent_names, planned_input = plan(parsed_input)
        logger.info("Planner selected agents: %s", agent_names)

        for agent_name in agent_names:
            if agent_name not in AGENT_REGISTRY:
                raise ValueError(f"Unknown agent: {agent_name}")
            agent = AGENT_REGISTRY[agent_name]()
            self._run_agent(agent, planned_input)

    def _run_agent(self, agent, planned_input):
        logger.info("Running agent: %s", agent.agent_name)

        issues = agent.scan(planned_input.file_path)
        logger.info("[%s] Found %d issue(s).", agent.agent_name, len(issues))
        self._log_issues(issues)

        if not issues:
            return

        suggestions = agent.get_suggestions(issues, planned_input.file_content)
        logger.info("[%s] Generated %d suggestion(s).", agent.agent_name, len(suggestions))
        self._log_suggestions(suggestions)

        if planned_input.apply:
            logger.info("[%s] Applying auto-fixes", agent.agent_name)
            agent.apply(suggestions, planned_input.file_path)
            issues = agent.scan(planned_input.file_path)

        is_valid = agent.validate(issues)
        logger.info(
            "[%s] Validation result: valid=%s remaining_issues=%d",
            agent.agent_name, is_valid, len(issues),
        )
        self._log_issues(issues)

    def _log_issues(self, issues: list[Issue]):
        if issues:
            for issue in issues:
                logger.info(
                    "- line %s:%s [%s] %s - %s",
                    issue.line,
                    issue.column,
                    issue.severity,
                    issue.rule_id,
                    issue.message,
                )

    def _log_suggestions(self, suggestions: list[Suggestion]):
        if suggestions:
            for suggestion in suggestions:
                logger.info(
                    "- line %s:%s [%s] %s - %s",
                    suggestion.issue.line,
                    suggestion.issue.column,
                    suggestion.issue.severity,
                    suggestion.issue.rule_id,
                    suggestion.issue.message,
                )

    def _log_parsed_input(self, parsed_input: ParsedInput):
        logger.info(
            "Parsed input: agent=%s, file=%s, apply=%s",
            parsed_input.agent,
            parsed_input.file_path,
            parsed_input.apply,
        )