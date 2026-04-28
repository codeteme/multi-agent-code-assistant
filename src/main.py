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

    from src.controller import Controller
    from src.util.input import parse_input

    parsed_input = parse_input()

    if not parsed_input.file_path.endswith(".py"):
        logger.error("Unsupported file type: %s. Only Python files are supported.", parsed_input.file_path)
        sys.exit(1)

    controller = Controller()
    controller.run()


if __name__ == "__main__":
    main()