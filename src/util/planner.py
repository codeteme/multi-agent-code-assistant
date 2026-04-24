import logging

from src.util.input import AGENTS, ParsedInput

logger = logging.getLogger(__name__)

def plan(parsed_input: ParsedInput) -> tuple[list[str], ParsedInput]:
    if parsed_input.agent:
        logger.info("User selected agent: %s", parsed_input.agent)
        return [parsed_input.agent], parsed_input
    
    logger.info("No agent specified, defaulting to: %s", parsed_input.agent)
    return list(AGENTS), parsed_input  # all agents by default
