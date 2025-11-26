# api/app.py
from __future__ import annotations
import io
import logging
import traceback
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader

from ..cli.app import build_sections
from ..db.repository import Repository
from ..services.embedder import Embedder
from ..services.extractor import CVExtractor

# Use standard logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CVStack API", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if not STATIC_DIR.exists():
    raise RuntimeError(f"Expected static folder at: {STATIC_DIR}")

app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def sanitize_text(text: str) -> str:
    """Remove null bytes and other problematic characters from text"""
    if not text:
        return ""
    cleaned = text.replace("\x00", "")
    cleaned = "".join(char if ord(char) >= 32 else " " for char in cleaned)
    return cleaned.strip()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        logger.info("[INGEST] filename=%s content_type=%s", file.filename, file.content_type)

        # 1) Read file content
        content = await file.read()
        if not content:
            raise ValueError("Uploaded file is empty")

        # 2) Extract and sanitize text (PDF vs TXT)
        if file.filename and file.filename.lower().endswith(".pdf"):
            try:
                reader = PdfReader(io.BytesIO(content))
                pages = []
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    pages.append(sanitize_text(page_text))
                text = "\n".join(pages)
            except Exception as e:
                raise ValueError(f"PDF parse failed: {e}")
        else:
            text = content.decode("utf-8", errors="ignore")
            text = sanitize_text(text)

        if not text:
            raise ValueError("No text extracted from the file")

        logger.info("[INGEST] text_len=%d", len(text))

        # 3) LLM extraction
        extractor = CVExtractor()
        logger.info("[INGEST] using extraction model: %s", getattr(extractor.model, "model_name", "unknown"))
        parsed = extractor.extract(text)
        if not isinstance(parsed, dict):
            raise ValueError("Extractor returned non-dict payload")

        profile = parsed.get("user_profile") or {}
        parsed["user_profile"] = {
            key: sanitize_text(str(value)) if value is not None else ""
            for key, value in profile.items()
        }

        parsed["user_web_links"] = [
            {k: sanitize_text(str(v)) if v is not None else "" for k, v in link.items()}
            for link in parsed.get("user_web_links", [])
        ]

        address = parsed.get("address") or {}
        parsed["address"] = {
            key: sanitize_text(str(value)) if value is not None else ""
            for key, value in address.items()
        }

        parsed["education"] = [
            {k: sanitize_text(str(v)) if v is not None else "" for k, v in edu.items()}
            for edu in parsed.get("education", [])
        ]

        parsed["certifications"] = [
            {k: sanitize_text(str(v)) if v is not None else "" for k, v in cert.items()}
            for cert in parsed.get("certifications", [])
        ]

        parsed["experience"] = [
            {k: sanitize_text(str(v)) if v is not None else "" for k, v in exp.items()}
            for exp in parsed.get("experience", [])
        ]

        parsed["projects"] = [
            {k: sanitize_text(str(v)) if v is not None else "" for k, v in proj.items()}
            for proj in parsed.get("projects", [])
        ]

        parsed["user_skills"] = [
            {k: sanitize_text(str(v)) if v is not None else "" for k, v in skill.items()}
            for skill in parsed.get("user_skills", [])
        ]

        # 4) DB + embeddings
        repo = Repository()
        try:
            full_name = " ".join(
                filter(
                    None,
                    [
                        profile.get("first_name"),
                        profile.get("middle_name"),
                        profile.get("last_name"),
                    ],
                )
            ).strip() or None
            email = profile.get("email")
            candidate_id = repo.insert_candidate(full_name, email, text)

            section_rows, texts = build_sections(parsed, candidate_id)
            texts = [sanitize_text(t) for t in texts]
            logger.info("[INGEST] sections=%d", len(section_rows))

            emb = Embedder()
            logger.info(
                "[INGEST] using embedding model: %s, skip=%s",
                getattr(emb, "model_name", "unknown"),
                getattr(emb, "skip", False),
            )
            vectors = emb.embed(texts) if texts else []

            section_ids = repo.insert_sections(section_rows) if section_rows else []
            if section_ids and vectors:
                repo.insert_vectors(section_ids, vectors)
        finally:
            repo.close()

        return {
            "candidate_id": candidate_id,
            "parsed": parsed,
            "stats": {
                "text_len": len(text),
                "sections": len(section_rows),
                "vectors": len(vectors),
                "filename": file.filename,
                "content_type": file.content_type,
            },
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))