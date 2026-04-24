import logging

from src.util.suggestion import Suggestion

logger = logging.getLogger(__name__)


class TextApplier:
    def apply(self, suggestions: list[Suggestion], file_path: str) -> None:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        for suggestion in suggestions:
            original = suggestion.original_code
            fixed = suggestion.fixed_code

            if not original or not fixed:
                logger.warning("Skipping suggestion with missing code.")
                continue

            if original in content:
                content = content.replace(original, fixed, 1)
                logger.info("Applied fix for rule: %s", suggestion.issue.rule_id)
            else:
                logger.warning(
                    "Could not find original code for rule %s — skipping.",
                    suggestion.issue.rule_id,
                )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)