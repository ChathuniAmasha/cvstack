from __future__ import annotations
import logging
from typing import Any, Dict, List

from ..db.repository import Repository
from ..services.embedder import Embedder

log = logging.getLogger(__name__)


class SearchService:
    def __init__(self) -> None:
        self.repo = Repository()
        self.embedder = Embedder()

    def index_catalog(self, skills: List[Dict[str, str]]) -> None:
        """
        1. Receives raw JSON list: [{'name': 'Python', 'description': '...'}]
        2. Creates text for embedding: "Python: ..."
        3. Generates vectors
        4. Saves to DB
        """
        if not skills:
            return

        # Prepare text for embedding (Name + Description gives better context)
        texts_to_embed = [
            f"{s['name']}: {s.get('description', '')}" 
            for s in skills
        ]
        
        log.info(f"Generating embeddings for {len(texts_to_embed)} skills...")
        vectors = self.embedder.embed(texts_to_embed)
        
        log.info("Saving skill vectors to database...")
        self.repo.upsert_skill_vectors(skills, vectors)

    def search(self, skill_text: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """Search using free-text skill query (embeds the query first)."""
        if not skill_text.strip():
            return []
        query_vector = self.embedder.embed([skill_text])[0]
        return self.repo.search_by_skill(query_vector, top_k)

    def search_by_catalog(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Search candidates matching ALL skills in the uploaded catalog."""
        return self.repo.search_candidates_by_skill_catalog(limit)

    def search_by_catalog_skill(self, skill_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search candidates matching a SPECIFIC skill from the catalog."""
        return self.repo.search_candidates_by_single_skill(skill_name, limit)