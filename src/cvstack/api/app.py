from __future__ import annotations
import io
import json
import logging
import traceback
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pypdf import PdfReader

# --- Imports from your project ---
from ..cli.app import build_sections
from ..db.repository import Repository
from ..services.embedder import Embedder
from ..services.extractor import CVExtractor
from ..services.candidate_search import SearchService

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- App Setup ---
app = FastAPI(title="CVStack API", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class SearchRequest(BaseModel):
    query: str
    limit: int = 50

# --- Helper Functions ---
def sanitize_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.replace("\x00", "")
    cleaned = "".join(char if ord(char) >= 32 else " " for char in cleaned)
    return cleaned.strip()

# ===========================
#        ENDPOINTS
# ===========================

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

# 1. TEXT SEARCH
@app.post("/search")
def search_candidates(request: SearchRequest) -> Dict[str, Any]:
    try:
        service = SearchService()
        results = service.search(request.query, request.limit)
        return {"count": len(results), "results": results}
    except Exception as e:
        logger.error(f"[SEARCH ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 2. UPLOAD SKILL CATALOG (Fixes your 404 error)
@app.post("/skills/catalog")
async def upload_skill_catalog(file: UploadFile = File(...)):
    try:
        content = await file.read()
        skills_data = json.loads(content)
        
        if not isinstance(skills_data, list):
            raise ValueError("File must be a JSON array")

        service = SearchService()
        service.index_catalog(skills_data)
        
        return {
            "status": "success",
            "message": f"Successfully indexed {len(skills_data)} skills",
            "count": len(skills_data)
        }
    except Exception as e:
        logger.error(f"Skill upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 3. LIST SKILLS (For the blue tags)
@app.get("/skills/catalog/list")
def list_skills():
    repo = Repository()
    try:
        with repo.conn.cursor() as cur:
            cur.execute("SELECT skill_name FROM skill_vectors ORDER BY skill_name ASC")
            rows = cur.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"List skills failed: {e}")
        return []
    finally:
        repo.close()

# 4. SEARCH BY CATALOG (For "Find Matching CVs" button)
# This endpoint handles the "Find Matching CVs" button
@app.post("/search/catalog")
def search_by_catalog_stored(limit: int = 50) -> Dict[str, Any]:
    try:
        service = SearchService()
        
        # This calls the method we just updated in Step 1
        results = service.search_by_catalog(limit=limit)
        
        return {
            "status": "success", 
            "candidates_found": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Catalog search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
class SingleSkillRequest(BaseModel):
    skill: str
    limit: int = 50

@app.post("/search/catalog/skill")
def search_by_single_skill_endpoint(request: SingleSkillRequest) -> Dict[str, Any]:
    try:
        service = SearchService()
        # This calls the method to match ONE specific skill
        results = service.search_by_catalog_skill(request.skill, request.limit)
        return {
            "status": "success", 
            "candidates_found": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Single skill search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# 5. INGEST CV (PDF Upload)
@app.post("/ingest")
async def ingest(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        logger.info("[INGEST] filename=%s", file.filename)
        content = await file.read()
        
        # PDF Parsing
        if file.filename and file.filename.lower().endswith(".pdf"):
            try:
                reader = PdfReader(io.BytesIO(content))
                text = "\n".join([sanitize_text(p.extract_text() or "") for p in reader.pages])
            except Exception as e:
                raise ValueError(f"PDF parse failed: {e}")
        else:
            text = sanitize_text(content.decode("utf-8", errors="ignore"))

        if not text:
            raise ValueError("No text extracted")

        # Extraction
        extractor = CVExtractor()
        parsed = extractor.extract(text)
        
        # Sanitization
        profile = parsed.get("user_profile") or {}
        # ... (Simplified sanitization for brevity, your original logic fits here) ...
        
        # Database Save
        repo = Repository()
        try:
            full_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip() or None
            candidate_id = repo.insert_candidate(full_name, profile.get("email"), text)
            
            section_rows, texts = build_sections(parsed, candidate_id)
            texts = [sanitize_text(t) for t in texts]
            
            emb = Embedder()
            vectors = emb.embed(texts) if texts else []
            
            if section_rows:
                s_ids = repo.insert_sections(section_rows)
                if s_ids and vectors:
                    repo.insert_vectors(s_ids, vectors)
        finally:
            repo.close()

        return {"candidate_id": candidate_id, "parsed": parsed}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))