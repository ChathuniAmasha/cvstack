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

    def index_catalog(self, catalog_data: Any) -> None:
        """
        Handles both:
        1. OLD Format: [{"name": "Python"}, ...]
        2. NEW Format: [{"category": "Essential", "skills": [...]}, ...]
        """
        if not catalog_data:
            return

        flat_skills = []
        texts_to_embed = []

        # --- DETECT FORMAT ---
        # Check if it's the new nested format (List of Categories)
        is_nested = isinstance(catalog_data, list) and len(catalog_data) > 0 and "category" in catalog_data[0]

        if is_nested:
            log.info("Detected NESTED catalog format (Categories).")
            for group in catalog_data:
                category = group.get("category", "General")
                
                # Assign weights based on category name
                if "Essential" in category:
                    weight = 10
                elif "Nice-to-Have" in category:
                    weight = 5
                else:
                    weight = 2

                # Extract skills from this group
                for skill in group.get("skills", []):
                    # Safety check: ensure skill has a name
                    if "name" not in skill:
                        continue
                        
                    # Embed text: "Python (Essential): Description..."
                    embed_text = f"{skill['name']} ({category}): {skill.get('description', '')}"
                    
                    flat_skills.append({
                        "name": skill["name"],
                        "description": skill.get("description", ""),
                        "weight": weight,
                        "embed_text": embed_text
                    })
                    texts_to_embed.append(embed_text)

        else:
            log.info("Detected FLAT catalog format (Simple List).")
            for skill in catalog_data:
                # Safety check
                if "name" not in skill:
                    continue

                embed_text = f"{skill['name']}: {skill.get('description', '')}"
                flat_skills.append({
                    "name": skill["name"],
                    "description": skill.get("description", ""),
                    "weight": 5, # Default weight for flat lists
                    "embed_text": embed_text
                })
                texts_to_embed.append(embed_text)

        # --- EMBED & SAVE ---
        if not flat_skills:
            log.warning("No valid skills found to index.")
            return

        log.info(f"Generating embeddings for {len(flat_skills)} skills...")
        vectors = self.embedder.embed(texts_to_embed)

        if not vectors:
            log.warning("No vectors generated. Skipping DB save.")
            return

        log.info(f"Saving {len(flat_skills)} skill vectors to database...")
        self.repo.upsert_skill_vectors(flat_skills, vectors)

    def search(self, skill_text: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """Search using free-text skill query (embeds the query first)."""
        if not skill_text or not skill_text.strip():
            return []
        
        # Embed the single query string
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