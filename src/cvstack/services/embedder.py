from __future__ import annotations
from typing import List
import google.generativeai as genai
from ..config import settings


class Embedder:
    def __init__(self) -> None:                                                   #initialize the new object by setting up its initial 
                                                                                #properties based on values from a settings object
        if settings.gemini_api_key and not settings.skip_embedding:
            genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.embedding_model
        self.dim = settings.embedding_dim
        self.skip = settings.skip_embedding or not settings.gemini_api_key
        print("Using embedding model:", settings.embedding_model)



    def embed(self, texts: List[str]) -> List[List[float]]:
        if self.skip:
            return [[0.0] * self.dim for _ in texts]
        
        print(f"Embedding {len(texts)} texts...")
        vectors: List[List[float]] = []
        for t in texts:
            r = genai.embed_content(model=self.model_name, content=t) #Call the Google AI (genai) library's embed_content function
            print(f"Got embedding response type: {type(r)}")          #store the given output r as response.

        vectors: List[List[float]] = []
        for t in texts:
            r = genai.embed_content(model=self.model_name, content=t)
            emb = None
            
            if isinstance(r, dict):
                e = r.get("embedding")
                if isinstance(e, dict):                               #checks whether the response is a dictionary
                    emb = e.get("values") or e.get("vector") or e.get("data")  #Look for the actual numbers inside that dictionary with keys like 'values', 'vector', or 'data'
                elif isinstance(e, list):                                      #Or, is the value of 'embedding' just a list?"
                    emb = e
                
                if emb is None and isinstance(r.get("data"), list) and r["data"]:
                    first = r["data"][0]
                    if isinstance(first, dict) and "embedding" in first:
                        emb = first.get("embedding")
                    elif isinstance(first, list):
                        emb = first
            
            elif isinstance(r, list):
                emb = r

            if emb is None:
                raise RuntimeError(f"Unexpected embedding response: {type(r)} {str(r)[:200]}")
            
            vectors.append(emb)
            
        return vectors