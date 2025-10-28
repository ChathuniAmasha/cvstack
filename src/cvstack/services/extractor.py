from __future__ import annotations
import json
import re
from typing import Any, Dict
import google.generativeai as genai
from ..config import settings
from cvstack.prompts.extraction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, SCHEMA


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
        prompt = USER_PROMPT_TEMPLATE.format(
            schema=json.dumps(SCHEMA, ensure_ascii=False, indent=2),
            cv_text=cv_text[:200000]
        )
        combined = SYSTEM_PROMPT + "\n\n" + prompt
        resp = self.model.generate_content([{ "role": "user", "parts": [combined] }])
        raw = self._strip_fences((resp.text or "").strip())
        
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}\s*$", raw, flags=re.DOTALL)
            if not m:
                raise
            return json.loads(m.group(0))