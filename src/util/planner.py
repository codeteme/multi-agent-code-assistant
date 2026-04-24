import logging

from src.util.input import AGENTS, ParsedInput

logger = logging.getLogger(__name__)

def plan(parsed_input: ParsedInput) -> tuple[list[str], ParsedInput]:
    if parsed_input.agent:
        logger.info("User selected agent: %s", parsed_input.agent)
        return [parsed_input.agent], parsed_input
    logger.info("No agent specified, running all agents: %s", list(AGENTS))
    return list(AGENTS), parsed_input
