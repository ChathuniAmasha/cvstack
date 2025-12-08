from __future__ import annotations
import json
from pathlib import Path

from cvstack.db.repository import Repository
from cvstack.services.embedder import Embedder

DATA_FILE = Path(__file__).resolve().parents[2] / "cvstack"/ "data" / "skill_catalog.json"

def main() -> None:
    skills = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    texts = [f"{item['name']}: {item.get('description', '')}" for item in skills]

    embedder = Embedder()
    vectors = embedder.embed(texts)
    if not vectors:
        raise RuntimeError("No vectors generated")

    repo = Repository()
    try:
        repo.upsert_skill_vectors(skills, vectors)
    finally:
        repo.close()

if __name__ == "__main__":
    main()