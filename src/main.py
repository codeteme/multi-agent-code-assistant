import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"


def main():
    load_dotenv(dotenv_path=ENV_PATH)
    logger.info("Loaded environment variables from %s", ENV_PATH)

    from src.util.input import parse_input

    parsed_input = parse_input()

    if not parsed_input.file_path.endswith(".py"):
        logger.error("Unsupported file type: %s. Only Python files are supported.", parsed_input.file_path)
        sys.exit(1)

    if parsed_input.agentic:
        from src.agentic_controller import AgenticController
        AgenticController().run(
            file_path=parsed_input.file_path,
            agent_name=parsed_input.agent or "CLEAN_CODE",
            apply_fixes=parsed_input.apply,
        )
    else:
        from src.controller import Controller
        Controller().run()


if __name__ == "__main__":
    main()