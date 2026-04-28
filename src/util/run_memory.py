import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

MEMORY_DIR = Path(".refactor_memory")


def _memory_path(file_path: str) -> Path:
    """Derive a stable memory file path from the source file path."""
    safe_name = file_path.replace("/", "_").replace("\\", "_")
    return MEMORY_DIR / f"{safe_name}.json"


def load_memory(file_path: str) -> dict:
    """Load the last run record for a file, or return empty state."""
    path = _memory_path(file_path)
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not load memory for %s: %s", file_path, e)
        return {}


def save_memory(file_path: str, results: dict) -> None:
    """Save the run record for a file."""
    MEMORY_DIR.mkdir(exist_ok=True)
    path = _memory_path(file_path)
    record = {
        "file": file_path,
        "last_run": datetime.now().isoformat(),
        "results": results,
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        logger.info("Saved run memory to %s", path)
    except OSError as e:
        logger.warning("Could not save memory: %s", e)