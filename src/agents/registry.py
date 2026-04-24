from src.agents.code_style_agent import StyleAgent
from src.agents.idioms_agent import IdiomsAgent
from src.agents.testing_agent import TestingAgent
from src.agents.clean_code_agent import CleanCodeAgent

AGENT_REGISTRY = {
    "CODE_STYLE": StyleAgent,
    "IDIOMS": IdiomsAgent,
    "TESTS": TestingAgent,
    "CLEAN_CODE": CleanCodeAgent,
}