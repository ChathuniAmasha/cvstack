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
        3. Generates vectors (using Gemini or OpenAI)
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
        
        # Embedder returns a list of vectors (List[List[float]])
        vectors = self.embedder.embed(texts_to_embed)
        
        if not vectors:
            log.warning("No vectors generated. Skipping DB save.")
            return

        log.info("Saving skill vectors to database...")
        self.repo.upsert_skill_vectors(skills, vectors)

    def search(self, skill_text: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """Search using free-text skill query (embeds the query first)."""
        if not skill_text or not skill_text.strip():
            return []
        
        # Embed the single query string
        # embed() returns a list of vectors, so we take the first one [0]
        vectors = self.embedder.embed([skill_text])
        if not vectors:
            return []
            
        query_vector = vectors[0]
        return self.repo.search_by_skill(query_vector, limit=top_k)

    def search_by_catalog(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Uses the skills ALREADY saved in the DB to find matching candidates.
        Matches against the FULL catalog using your "Total Points" logic.
        """
        return self.repo.search_candidates_by_skill_catalog(limit)

    def search_by_catalog_skill(self, skill_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search candidates matching a SPECIFIC skill from the catalog."""
        return self.repo.search_candidates_by_single_skill(skill_name, limit)