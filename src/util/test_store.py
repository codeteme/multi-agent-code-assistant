"""
RAG layer for the TESTS agent.

seed()     — one-time setup: indexes all existing test files into ChromaDB
retrieve() — at scan time: finds the most similar test files to the source
             being analyzed and returns them as a string for prompt injection
"""

import logging
from pathlib import Path

import chromadb

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).resolve().parents[2] / ".chromadb"
_COLLECTION = "test_examples"


def _get_collection():
    client = chromadb.PersistentClient(path=str(_DB_PATH))
    return client.get_or_create_collection(_COLLECTION)


def seed(tests_dir: str = "tests/") -> int:
    """Index all existing test files. Re-run whenever tests change."""
    collection = _get_collection()
    indexed = 0
    for path in Path(tests_dir).rglob("test_*.py"):
        content = path.read_text(encoding="utf-8").strip()
        if content:
            collection.upsert(documents=[content], ids=[str(path)])
            indexed += 1
            logger.info("Indexed %s", path)
    logger.info("Seeded %d test files into ChromaDB", indexed)
    return indexed


def retrieve(source_code: str, top_k: int = 2) -> str:
    """
    Find the top_k most similar existing test files to the given source code.
    Returns them as a single string ready for prompt injection.
    Returns empty string if the store is empty.
    """
    collection = _get_collection()
    if collection.count() == 0:
        logger.warning("ChromaDB is empty — run seed() first")
        return ""

    results = collection.query(query_texts=[source_code], n_results=min(top_k, collection.count()))
    examples = results["documents"][0]
    logger.info("Retrieved %d test example(s) from ChromaDB", len(examples))
    return "\n\n---\n\n".join(examples)
