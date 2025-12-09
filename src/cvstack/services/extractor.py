from __future__ import annotations
import json
import re
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

import google.generativeai as genai
import pandas as pd

from ..config import settings
from ..prompts.extraction import SYSTEM_PROMPT, build_user_prompt

log = logging.getLogger(__name__)

class CVExtractor:
    def __init__(self) -> None:
        # Safety Check for API Key
        if not settings.gemini_api_key:
            import os
            key = os.getenv("GEMINI_API_KEY")
            if not key:
                raise RuntimeError("GEMINI_API_KEY not set in settings or environment")
            genai.configure(api_key=key)
        else:
            genai.configure(api_key=settings.gemini_api_key)

        model_name = getattr(settings, "extraction_model", "gemini-1.5-flash")
        self.model = genai.GenerativeModel(model_name)
        log.info(f"Using extraction model: {model_name}")

    @staticmethod
    def _strip_fences(s: str) -> str:
        return re.sub(r"^```(?:json)?\s*|\s*```$", "", s.strip(), flags=re.IGNORECASE | re.DOTALL)

    def extract(self, cv_text: str) -> Dict[str, Any]:
        if not cv_text or not cv_text.strip():
            raise ValueError("CV text is empty, cannot extract")

        log.info(f"[EXTRACTOR] Processing text length: {len(cv_text)}")

        # Build Prompt
        user_prompt = build_user_prompt(cv_text[:200000])
        if not user_prompt or not user_prompt.strip():
            raise ValueError("Prompt generation failed (empty prompt)")

        try:
            # Generate Content (Gemini)
            resp = self.model.generate_content(user_prompt)
            
            raw_text = (resp.text or "").strip()
            if not raw_text:
                raise ValueError("Gemini returned empty response")

            # Clean and Parse
            raw = self._strip_fences(raw_text)
            
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                log.warning("JSON decode failed, attempting fallback extraction...")
                m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
                if not m:
                    raise ValueError("Could not parse JSON from model response")
                parsed = json.loads(m.group(0))

            # Save Debug Excel (Safe Path)
            try:
                self.save_to_csv(parsed)
            except Exception as e:
                log.error(f"Failed to save debug Excel (skipping): {e}")

            return parsed

        except Exception as e:
            log.error(f"Error during extraction: {str(e)}")
            raise e

    def save_to_csv(self, parsed: Dict[str, Any]) -> str:
        # --- PERMANENT FIX: Use System Temp Directory (Always Writable) ---
        output_dir = Path(tempfile.gettempdir())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_path = output_dir / f"extracted_cv_{timestamp}.xlsx"
        
        log.info(f"Saving debug Excel to: {excel_path}")

        sheets: Dict[str, List[Dict[str, Any]]] = {
            "user_profile": [],
            "user_web_links": [],
            "address": [],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "user_skills": []
        }

        # Populate sheets safely
        profile = parsed.get("user_profile") or {}
        if profile: sheets["user_profile"].append(profile)

        for link in parsed.get("user_web_links", []):
            sheets["user_web_links"].append(link)

        address = parsed.get("address") or {}
        if address: sheets["address"].append(address)

        for edu in parsed.get("education", []):
            sheets["education"].append(edu)

        for exp in parsed.get("experience", []):
            rec = exp.copy()
            rec["highlights"] = "; ".join(rec.get("highlights", []) or [])
            sheets["experience"].append(rec)

        for proj in parsed.get("projects", []):
            rec = proj.copy()
            rec["skills"] = "; ".join(rec.get("skills", []) or [])
            sheets["projects"].append(rec)

        for cert in parsed.get("certifications", []):
            sheets["certifications"].append(cert)

        for skill in parsed.get("user_skills", []):
            sheets["user_skills"].append(skill)

        # Write to Excel
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="w") as writer:
            wrote_any = False
            for sheet, rows in sheets.items():
                df = pd.DataFrame(rows)
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet, index=False)
                    wrote_any = True
            
            if not wrote_any:
                 pd.DataFrame([{"info": "empty"}]).to_excel(writer, sheet_name="empty")

        return str(excel_path)