import logging

from src.util.input import ParsedInput

logger = logging.getLogger(__name__)

AGENT_ORDER = ["CODE_STYLE", "IDIOMS", "CLEAN_CODE", "TESTS"]


def plan(parsed_input: ParsedInput) -> tuple[list[str], ParsedInput]:
    if parsed_input.agent:
        logger.info("User selected agent: %s", parsed_input.agent)
        return [parsed_input.agent], parsed_input

    logger.info("No agent specified, running all agents in order: %s", AGENT_ORDER)
    return AGENT_ORDER, parsed_input