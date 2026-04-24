import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.agents.registry import AGENT_REGISTRY
from src.util.input import ParsedInput, parse_input
from src.util.issue import Issue
from src.util.planner import plan
from src.util.suggestion import Suggestion

logger = logging.getLogger(__name__)


class Controller:
    MAX_RETRIES = 3

    def run(self, args=None):
        parsed_input = parse_input(args)
        self._log_parsed_input(parsed_input)

        agent_names, planned_input = plan(parsed_input)
        logger.info("Planner selected agents: %s", agent_names)

        # All agents run sequentially — they share a file
        for name in agent_names:
            if name not in AGENT_REGISTRY:
                raise ValueError(f"Unknown agent: {name}")
            agent = AGENT_REGISTRY[name]()
            try:
                self._run_agent(agent, planned_input)
            except Exception as e:
                logger.error("[%s] Agent failed: %s", name, e)

    def _run_parallel(self, agents, planned_input):
        if not agents:
            return
        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = {
                executor.submit(self._run_agent, agent, planned_input): agent.agent_name
                for agent in agents
            }
            for future in as_completed(futures):
                agent_name = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error("[%s] Agent failed: %s", agent_name, e)

    def _run_agent(self, agent, planned_input):
        logger.info("Running agent: %s", agent.agent_name)

        issues = agent.scan(planned_input.file_path)
        logger.info("[%s] Found %d issue(s).", agent.agent_name, len(issues))

        if not issues:
            logger.info("[%s] No issues found, skipping.", agent.agent_name)
            return

        # Re-read file — a previous agent may have modified it
        with open(planned_input.file_path, encoding="utf-8") as f:
            current_content = f.read()

        suggestions = agent.get_suggestions(issues, current_content)
        logger.info("[%s] Generated %d suggestion(s).", agent.agent_name, len(suggestions))

        if not planned_input.apply:
            return

        for attempt in range(1, self.MAX_RETRIES + 1):
            agent.apply(suggestions, planned_input.file_path)

            with open(planned_input.file_path, encoding="utf-8") as f:
                current_content = f.read()

            issues = agent.scan(planned_input.file_path)

            if agent.validate(issues):
                logger.info("[%s] Validated on attempt %d.", agent.agent_name, attempt)
                return

            logger.warning("[%s] Attempt %d failed, %d issue(s) remain.",
                        agent.agent_name, attempt, len(issues))
            suggestions = agent.get_suggestions(issues, current_content)

        logger.error("[%s] Did not converge after %d attempts.", agent.agent_name, self.MAX_RETRIES)
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