import logging
import os

from src.util.suggestion import Suggestion

logger = logging.getLogger(__name__)


class Applier:
    def __init__(self):
        pass

    def apply(self, suggestions: list[Suggestion], test_file_path: str, source_file_path: str = "") -> None:
        """Write suggested tests to the corresponding test file."""
        valid_suggestions = [
            s for s in suggestions
            if s.fixed_code and "def test_" in s.fixed_code
        ]

        if not valid_suggestions:
            logger.warning("No valid suggestions to apply.")
            return

        fixed_code_all = "\n\n".join(s.fixed_code for s in valid_suggestions)
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)

        # Derive relative module path from source file path
        header = ""
        if source_file_path:
            path = source_file_path
            for marker in ("src/", "data/"):
                if marker in path:
                    path = path[path.index(marker):]
                    break
            module_path = path.replace("/", ".").removesuffix(".py")
            header = f"from {module_path} import *\n\n"

        # Always overwrite — never accumulate broken tests across retries
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(header + fixed_code_all)

        logger.info("Wrote %d suggestions to %s", len(valid_suggestions), test_file_path)