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
from ..prompts.extraction import (
    CV_EXTRACTION_SYSTEM_PROMPT,
    SKILL_RATING_SYSTEM_PROMPT,
    build_cv_extraction_prompt,
    build_skill_rating_prompt,
)

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
        cv_text_trimmed = cv_text[:200000]

        try:
            # ===== STEP 1: CV Extraction =====
            log.info("[EXTRACTOR] Step 1: Extracting CV data...")
            extraction_prompt = build_cv_extraction_prompt(cv_text_trimmed)
            if not extraction_prompt or not extraction_prompt.strip():
                raise ValueError("Prompt generation failed (empty prompt)")

            # Use chat for system prompt support
            chat = self.model.start_chat(history=[])
            
            # Send system prompt as first message context, then user prompt
            step1_full_prompt = f"{CV_EXTRACTION_SYSTEM_PROMPT}\n\n{extraction_prompt}"
            resp1 = chat.send_message(step1_full_prompt)
            
            raw_text1 = (resp1.text or "").strip()
            if not raw_text1:
                raise ValueError("Gemini returned empty response for CV extraction")

            # Parse Step 1 result
            parsed = self._parse_json_response(raw_text1, "CV extraction")
            
            # ===== STEP 2: Skill Rating =====
            log.info("[EXTRACTOR] Step 2: Rating skills with evidence...")
            skill_prompt = build_skill_rating_prompt(cv_text_trimmed, parsed)
            
            # New chat for skill rating
            chat2 = self.model.start_chat(history=[])
            step2_full_prompt = f"{SKILL_RATING_SYSTEM_PROMPT}\n\n{skill_prompt}"
            resp2 = chat2.send_message(step2_full_prompt)
            
            raw_text2 = (resp2.text or "").strip()
            if not raw_text2:
                log.warning("Gemini returned empty response for skill rating, keeping original skills")
            else:
                # Parse Step 2 result (should be JSON array)
                skill_array = self._parse_json_response(raw_text2, "skill rating", expect_array=True)
                if skill_array:
                    parsed["user_skills"] = skill_array
                    log.info(f"[EXTRACTOR] Rated {len(skill_array)} skills with evidence")

            # Save Debug Excel (Safe Path) - Always try to save if we have parsed data
            if parsed:
                try:
                    saved_path = self.save_to_csv(parsed)
                    log.info(f"Successfully saved Excel to: {saved_path}")
                except Exception as e:
                    log.error(f"Failed to save debug Excel (skipping): {e}")
                    import traceback
                    log.error(traceback.format_exc())

            return parsed

        except Exception as e:
            log.error(f"Error during extraction: {str(e)}")
            raise e

    def _parse_json_response(self, raw_text: str, step_name: str, expect_array: bool = False) -> Any:
        """Parse JSON from LLM response with fallback extraction."""
        raw = self._strip_fences(raw_text)
        
        try:
            parsed = json.loads(raw)
            return parsed
        except json.JSONDecodeError as json_err:
            log.warning(f"[{step_name}] JSON decode failed at line {json_err.lineno} col {json_err.colno}: {json_err.msg}")
            log.warning(f"[{step_name}] Attempting fallback extraction...")
            
            # Try to extract JSON object or array
            pattern = r"\[.*\]" if expect_array else r"\{.*\}"
            m = re.search(pattern, raw, flags=re.DOTALL)
            if not m:
                log.error(f"[{step_name}] Raw response (first 500 chars): {raw[:500]}")
                self._save_failed_response(raw)
                raise ValueError(f"Could not parse JSON from {step_name} response. Error: {json_err.msg} at line {json_err.lineno}")
            
            try:
                parsed = json.loads(m.group(0))
                return parsed
            except json.JSONDecodeError as json_err2:
                log.error(f"[{step_name}] Fallback also failed: {json_err2.msg} at line {json_err2.lineno}")
                log.error(f"[{step_name}] Extracted JSON (first 1000 chars): {m.group(0)[:1000]}")
                self._save_failed_response(m.group(0))
                raise ValueError(f"JSON parsing failed for {step_name}: {json_err2.msg} at line {json_err2.lineno}")
    
    def _save_failed_response(self, content: str) -> None:
        """Save failed JSON responses for debugging"""
        try:
            output_dir = Path(__file__).parent.parent.parent.parent / "output"
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            failed_path = output_dir / f"failed_response_{timestamp}.txt"
            failed_path.write_text(content, encoding='utf-8')
            log.info(f"Saved failed response to: {failed_path}")
        except Exception as e:
            log.error(f"Could not save failed response: {e}")

    def save_to_csv(self, parsed: Dict[str, Any]) -> str:
        # Save to output folder - use /app/output in Docker, or local output folder
        if Path("/app/output").exists() or Path("/app").exists():
            output_dir = Path("/app/output")
        else:
            output_dir = Path(__file__).parent.parent.parent.parent / "output"
        log.info(f"Output directory path: {output_dir.resolve()}")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_path = output_dir / f"extracted_cv_{timestamp}.xlsx"
        
        log.info(f"Attempting to save Excel to: {excel_path}")

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

        log.info(f"Excel file successfully written to: {excel_path}")
        return str(excel_path)