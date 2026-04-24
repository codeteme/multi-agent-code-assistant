import logging
from pathlib import Path

from src.agents.registry import AGENT_REGISTRY
from src.util.input import ParsedInput, parse_input
from src.util.issue import Issue
from src.util.planner import plan
from src.util.run_memory import load_memory, save_memory
from src.util.suggestion import Suggestion

logger = logging.getLogger(__name__)


class Controller:
    MAX_RETRIES = 3

    def run(self, args=None):
        parsed_input = parse_input(args)
        self._log_parsed_input(parsed_input)

        agent_names, planned_input = plan(parsed_input)
        logger.info("Planner selected agents: %s", agent_names)

        # Load memory from previous run
        memory = load_memory(planned_input.file_path)
        if memory:
            logger.info("Found memory from previous run: %s", memory.get("last_run"))

        # Run agents and collect results
        run_results = {}
        for name in agent_names:
            if name not in AGENT_REGISTRY:
                raise ValueError(f"Unknown agent: {name}")
            agent = AGENT_REGISTRY[name]()
            result = self._run_agent(agent, planned_input)
            run_results[name] = result

        # Save memory and print summary
        save_memory(planned_input.file_path, run_results)
        self._print_summary(planned_input.file_path, run_results)

    def _run_agent(self, agent, planned_input) -> dict:
        """Run a single agent and return a result record."""
        logger.info("Running agent: %s", agent.agent_name)

        issues = agent.scan(planned_input.file_path)
        logger.info("[%s] Found %d issue(s).", agent.agent_name, len(issues))

        if not issues:
            logger.info("[%s] No issues found, skipping.", agent.agent_name)
            return {"status": "skipped", "issues_found": 0, "changes": []}

        with open(planned_input.file_path, encoding="utf-8") as f:
            current_content = f.read()

        suggestions = agent.get_suggestions(issues, current_content)
        logger.info("[%s] Generated %d suggestion(s).", agent.agent_name, len(suggestions))

        if not planned_input.apply:
            return {
                "status": "scanned",
                "issues_found": len(issues),
                "changes": [s.issue.message for s in suggestions],
            }

        for attempt in range(1, self.MAX_RETRIES + 1):
            agent.apply(suggestions, planned_input.file_path)

            with open(planned_input.file_path, encoding="utf-8") as f:
                current_content = f.read()

            issues = agent.scan(planned_input.file_path)

            if agent.validate(issues):
                logger.info("[%s] Validated on attempt %d.", agent.agent_name, attempt)
                return {
                    "status": "fixed",
                    "attempts": attempt,
                    "issues_found": len(issues),
                    "changes": [s.rationale for s in suggestions],
                }

            logger.warning("[%s] Attempt %d failed, %d issue(s) remain.",
                           agent.agent_name, attempt, len(issues))
            suggestions = agent.get_suggestions(issues, current_content)

        logger.error("[%s] Did not converge after %d attempts.", agent.agent_name, self.MAX_RETRIES)
        return {
            "status": "failed",
            "attempts": self.MAX_RETRIES,
            "issues_remaining": len(issues),
            "changes": [],
        }

    def _print_summary(self, file_path: str, results: dict) -> None:
        """Print a human-readable summary of what was done."""
        print("\n" + "=" * 60)
        print(f"  Refactor Summary — {Path(file_path).name}")
        print("=" * 60)

        for agent_name, result in results.items():
            status = result["status"]

            if status == "skipped":
                icon = ""
                detail = "no issues found"
            elif status == "scanned":
                icon = ""
                detail = f"{result['issues_found']} issue(s) found (--apply not set)"
            elif status == "fixed":
                icon = ""
                detail = f"fixed in {result['attempts']} attempt(s)"
            elif status == "failed":
                icon = ""
                detail = f"{result['issues_remaining']} issue(s) remain after {result['attempts']} attempt(s)"
            else:
                icon = ""
                detail = status

            print(f"  {icon}  {agent_name:<15} {detail}")

            if status == "fixed" and result.get("changes"):
                for change in result["changes"]:
                    print(f"       └─ {change}")

        print("=" * 60 + "\n")

    def _log_parsed_input(self, parsed_input: ParsedInput):
        logger.info(
            "Parsed input: agent=%s, file=%s, apply=%s",
            parsed_input.agent,
            parsed_input.file_path,
            parsed_input.apply,
        )

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