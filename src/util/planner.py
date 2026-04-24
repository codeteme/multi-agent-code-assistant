import logging
import subprocess
from src.util.input import ParsedInput

logger = logging.getLogger(__name__)

AGENT_ORDER = ["CODE_STYLE", "IDIOMS", "CLEAN_CODE", "TESTS"]


def plan(parsed_input: ParsedInput) -> tuple[list[str], ParsedInput]:
    # User explicitly picked an agent — respect that, no planning needed
    if parsed_input.agent:
        logger.info("User selected agent: %s", parsed_input.agent)
        return [parsed_input.agent], parsed_input

    file_path = parsed_input.file_path
    selected = []

    # Rule 1: Only process Python files
    if not file_path.endswith(".py"):
        logger.warning("File is not a Python file. No agents selected.")
        return [], parsed_input

    # Rule 2: Style agent — only if ruff finds issues
    ruff_result = subprocess.run(
        ["ruff", "check", file_path, "--output-format", "json"],
        capture_output=True, text=True, check=False
    )
    if ruff_result.stdout.strip() not in ("", "[]"):
        selected.append("CODE_STYLE")
        logger.info("Planner: style issues found, dispatching CODE_STYLE")
    else:
        logger.info("Planner: no style issues, skipping CODE_STYLE")

    # Rule 3: Idioms and Clean Code — read file and check size
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        line_count = content.count("\n")

        # Only worth running on files with actual logic
        if line_count >= 5:
            selected.append("IDIOMS")
            selected.append("CLEAN_CODE")
            logger.info("Planner: file has %d lines, dispatching IDIOMS and CLEAN_CODE", line_count)
        else:
            logger.info("Planner: file too short, skipping IDIOMS and CLEAN_CODE")

    except OSError:
        logger.warning("Planner: could not read file, skipping IDIOMS and CLEAN_CODE")

    # Rule 4: Testing agent — always last, only if file has functions or classes
    if "def " in content or "class " in content:
        selected.append("TESTS")
        logger.info("Planner: testable code found, dispatching TESTS")
    else:
        logger.info("Planner: no testable code, skipping TESTS")

    logger.info("Planner selected agents: %s", selected)
    return selected, parsed_input