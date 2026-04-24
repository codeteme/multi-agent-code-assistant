import logging
import subprocess
from src.util.input import ParsedInput
from src.util.run_memory import load_memory

logger = logging.getLogger(__name__)

AGENT_ORDER = ["CODE_STYLE", "IDIOMS", "CLEAN_CODE", "TESTS"]


def plan(parsed_input: ParsedInput) -> tuple[list[str], ParsedInput]:
    if parsed_input.agent:
        logger.info("User selected agent: %s", parsed_input.agent)
        return [parsed_input.agent], parsed_input

    file_path = parsed_input.file_path
    selected = []

    if not file_path.endswith(".py"):
        logger.warning("File is not a Python file. No agents selected.")
        return [], parsed_input

    # Load memory — skip agents that already passed last time
    memory = load_memory(file_path)
    previously_fixed = {
        name for name, result in memory.get("results", {}).items()
        if result.get("status") == "fixed"
    }
    if previously_fixed:
        logger.info("Planner: skipping previously fixed agents: %s", previously_fixed)

    # Style agent — only if ruff finds issues
    if "CODE_STYLE" not in previously_fixed:
        ruff_result = subprocess.run(
            ["ruff", "check", file_path, "--output-format", "json"],
            capture_output=True, text=True, check=False
        )
        if ruff_result.stdout.strip() not in ("", "[]"):
            selected.append("CODE_STYLE")
            logger.info("Planner: style issues found, dispatching CODE_STYLE")
        else:
            logger.info("Planner: no style issues, skipping CODE_STYLE")
    else:
        logger.info("Planner: CODE_STYLE passed last run, skipping")

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        line_count = content.count("\n")

        if line_count >= 5:
            for agent in ["IDIOMS", "CLEAN_CODE"]:
                if agent not in previously_fixed:
                    selected.append(agent)
                    logger.info("Planner: dispatching %s", agent)
                else:
                    logger.info("Planner: %s passed last run, skipping", agent)
        else:
            logger.info("Planner: file too short, skipping IDIOMS and CLEAN_CODE")

    except OSError:
        logger.warning("Planner: could not read file")
        content = ""

    if "TESTS" not in previously_fixed:
        if "def " in content or "class " in content:
            selected.append("TESTS")
            logger.info("Planner: testable code found, dispatching TESTS")
    else:
        logger.info("Planner: TESTS passed last run, skipping")

    logger.info("Planner selected agents: %s", selected)
    return selected, parsed_input