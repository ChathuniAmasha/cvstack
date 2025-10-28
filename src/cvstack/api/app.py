from __future__ import annotations
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import Any, Dict
from pypdf import PdfReader
import io
import traceback 

from ..services.extractor import CVExtractor
from ..services.embedder import Embedder
from ..db.repository import Repository
from ..cli.app import build_sections

app = FastAPI(title="CVStack API", version="0.1.0")

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        print(f"[INGEST] filename={file.filename}, content_type={file.content_type}")

        # 1) Read file content
        content = await file.read()
        if not content:
            raise ValueError("Uploaded file is empty")

        # 2) Extract text (PDF vs TXT)
        if file.filename.lower().endswith(".pdf"):
            try:
                reader = PdfReader(io.BytesIO(content))
                text = "\n".join([(p.extract_text() or "") for p in reader.pages]).strip()
            except Exception as e:
                raise ValueError(f"PDF parse failed: {e}")
        else:
            text = content.decode("utf-8", errors="ignore").strip()

        if not text:
            raise ValueError("No text extracted from the file")

        print(f"[INGEST] text_len={len(text)}")

        # 3) LLM extraction
        extractor = CVExtractor()
        print(f"[INGEST] using extraction model: {extractor.model.model_name}")
        parsed = extractor.extract(text)
        if not isinstance(parsed, dict):
            raise ValueError("Extractor returned non-dict payload")
        print(f"[INGEST] parsed keys={list(parsed.keys())}")

        # 4) DB + embeddings
        repo = Repository()
        try:
            cand_name = (parsed.get("candidate") or {}).get("full_name")
            cand_email = (parsed.get("candidate") or {}).get("email")
            candidate_id = repo.insert_candidate(cand_name, cand_email, text)

            section_rows, texts = build_sections(parsed, candidate_id)
            print(f"[INGEST] sections={len(section_rows)}")

            emb = Embedder()
            print(f"[INGEST] using embedding model: {emb.model_name}, skip={emb.skip}")
            vectors = emb.embed(texts)

            section_ids = repo.insert_sections(section_rows)
            repo.insert_vectors(section_ids, vectors)
        finally:
            repo.close()

        return {"candidate_id": candidate_id, "parsed": parsed}

    except Exception as e:
        traceback.print_exc()
        # Surface a readable error instead of a blank 500
        raise HTTPException(status_code=500, detail=str(e))