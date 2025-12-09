import logging
import google.generativeai as genai
from typing import List
from ..config import settings

log = logging.getLogger(__name__)

class Embedder:
    def __init__(self):
        # Ensure API Key is present
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        
        genai.configure(api_key=settings.gemini_api_key)
        self.model = "models/text-embedding-004" 

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of texts using Gemini.
        CRITICAL: Filters out empty strings to prevent API errors.
        """
        # 1. Clean inputs: Remove newlines, strip whitespace, remove empty strings
        clean_texts = [
            t.replace("\n", " ").strip() 
            for t in texts 
            if t and t.strip() # <--- This check prevents the error
        ]
        
        # 2. Safety Valve: If nothing is left, return empty list immediately
        if not clean_texts:
            log.warning("Embedder received empty or whitespace-only text list. Skipping API call.")
            return []

        try:
            log.info(f"Generating Gemini embeddings for {len(clean_texts)} texts...")
            
            # 3. Call Gemini API
            result = genai.embed_content(
                model=self.model,
                content=clean_texts,
                task_type="retrieval_document"
            )

            # 4. Return results
            if 'embedding' in result:
                return result['embedding']
            else:
                log.error("Gemini response missing 'embedding' key")
                return []

        except Exception as e:
            log.error(f"Gemini embedding failed: {e}")
            # Do not crash the app, just return empty so the process can continue
            return []