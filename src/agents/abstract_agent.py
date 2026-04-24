from abc import ABC, abstractmethod

from src.util.issue import Issue
from src.util.suggestion import Suggestion


class BaseAgent(ABC):
    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name

    @abstractmethod
    def scan(self, file_path: str) -> list[Issue]:
        """Scan code file and return list of issues found"""
        pass

    @abstractmethod
    def get_suggestions(self, issues: list[Issue], code: str) -> list[Suggestion]:
        """Generate fix suggestions for given issues"""
        pass

    @abstractmethod
    def validate(self, issues: list[Issue]) -> bool:
        """Return True if no blocking issues remain."""
        pass

    @abstractmethod
    def apply(self, suggestions: list[Suggestion], file_path: str) -> None:
        """Apply suggestions to the file."""
        pass
