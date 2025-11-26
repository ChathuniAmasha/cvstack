from __future__ import annotations
import json
import re
from typing import Any, Dict, List
import google.generativeai as genai
from ..config import settings
from ..prompts.extraction import SYSTEM_PROMPT, build_user_prompt
from datetime import datetime


class CVExtractor:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.extraction_model)
        print("Using extraction model:", settings.extraction_model)

    @staticmethod
    def _strip_fences(s: str) -> str:
        return re.sub(r"^```(?:json)?\s*|\s*```$", "", s.strip(), flags=re.IGNORECASE | re.DOTALL)

    def extract(self, cv_text: str) -> Dict[str, Any]:
        if not cv_text or not cv_text.strip():
            raise ValueError("CV text is empty, cannot extract")

        print("[EXTRACTOR] ---- CV TEXT START ----")
        print(cv_text[:500])  # Print first 500 chars
        print("[EXTRACTOR] ---- CV TEXT END ----")

        user_prompt = build_user_prompt(cv_text[:200000])
        if not user_prompt or not user_prompt.strip():
            raise ValueError("build_user_prompt returned empty string")


        print(f"[EXTRACTOR] Prompt length: {len(user_prompt)}")

        # Correct format for Gemini API
        resp = self.model.generate_content(user_prompt)

        raw_text = (resp.text or "").strip()
        if not raw_text:
            raise ValueError("Model returned empty response")

        print("[EXTRACTOR] ---- RAW RESPONSE ----")
        print(raw_text[:1000])
        print("[EXTRACTOR] ---- END RAW RESPONSE ----")

        raw = self._strip_fences(raw_text)

        try:
            parsed = json.loads(raw)
            print("Extracted JSON:", json.dumps(parsed, indent=2)[:2000])
            excel_file = self.save_to_csv(parsed)
            print(f"Saved extracted data to: {excel_file}")
            return parsed

        except json.JSONDecodeError:
            print("[EXTRACTOR] JSONDecodeError, trying fallback...")
            m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if not m:
                print("Failed to parse JSON response")
                raise

            parsed = json.loads(m.group(0))
            print("Extracted JSON (after cleanup):", json.dumps(parsed, indent=2)[:2000])

            excel_file = self.save_to_csv(parsed)
            print(f"Saved extracted data to: {excel_file}")

            return parsed

        except Exception as e:
            print(f"Error during extraction: {str(e)}")
            raise

    def save_to_csv(self, parsed: Dict[str, Any]) -> str:
        from pathlib import Path
        import pandas as pd

        project_root = Path(__file__).resolve().parents[3]
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_path = output_dir / f"extracted_cv_{timestamp}.xlsx"
        print(f"Saving Excel to absolute path: {excel_path}")

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

        profile = parsed.get("user_profile") or {}
        if profile:
            sheets["user_profile"].append(profile)

        for link in parsed.get("user_web_links", []):
            sheets["user_web_links"].append(link)

        address = parsed.get("address") or {}
        if address:
            sheets["address"].append(address)

        for edu in parsed.get("education", []):
            sheets["education"].append(edu)

        for exp in parsed.get("experience", []):
            rec = exp.copy()
            rec["highlights"] = "; ".join(rec.get("highlights", []))
            sheets["experience"].append(rec)

        for proj in parsed.get("projects", []):
            rec = proj.copy()
            rec["skills"] = "; ".join(rec.get("skills", []))
            sheets["projects"].append(rec)

        for cert in parsed.get("certifications", []):
            sheets["certifications"].append(cert)

        for skill in parsed.get("user_skills", []):
            sheets["user_skills"].append(skill)

        wrote_any = False
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="w") as writer:
            for sheet, rows in sheets.items():
                df = pd.DataFrame(rows)
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet, index=False)
                    wrote_any = True

            if not wrote_any:
                pd.DataFrame(
                    [{"note": "no sections extracted", "timestamp": timestamp}]
                ).to_excel(writer, sheet_name="meta", index=False)

        print(f"Saved Excel to: {excel_path}")
        return str(excel_path)