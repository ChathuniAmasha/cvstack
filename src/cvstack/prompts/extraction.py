from __future__ import annotations

import json
from typing import Any, Dict

# -----------------------------
# 1) SYSTEM PROMPTS (SEPARATE)
# -----------------------------

CV_EXTRACTION_SYSTEM_PROMPT = """You are a precise CV parsing engine. Extract data from the provided CV text into VALID JSON strictly following the provided SCHEMA.

STRICT RULES (highest priority):
1) NO HALLUCINATION / NO INFERENCE
- Only extract what is explicitly present in the CV text.
- If a field is not found, return null (for strings/objects) or false (for booleans ONLY when applicable).
- Do NOT output "N/A", "Unknown", or invented values.

Address rule (critical):
- If no physical address is found, set address fields to null.
- CRITICAL: If address.address_line_1 is null, address.is_current_address MUST be null (not true/false).

Industry / Role & Domain (MANDATORY):
- You MUST infer the candidate’s primary professional domain and likely target role using resume evidence.
- Priority for inference:
  1) Explicit objective / headline / “Position applied for”
  2) Most recent job title + responsibilities
  3) Dominant toolchain + recurring keywords + projects
Store in:
- user_profile.industry (domain label like "Cybersecurity", "Data Science", "Data Engineering", "Software Engineering")
- user_profile.target_role (inferred target role)
- user_profile.role_confidence (0–1 float, based on strength of evidence)
- user_profile.about (1–3 sentences: inferred target role + seniority + strongest proof points)

Web links:
- Aggressively scan for URLs or patterns like "linkedin.com/in/...", "github.com/...", "portfolio..."
- Include incomplete URLs if clearly intended as links.
- user_web_links.website_type must be one of: ["LinkedIn","GitHub","Portfolio","Website","Blog","Other"]

Dates:
- Education/certification dates: keep as found; but if garbage characters exist (e.g., "2023 xyz"), strip garbage.
- If a valid date cannot be parsed, return null.
- Do not output random letters.

Schema compliance:
- Output ONLY JSON.
- Do NOT add extra keys beyond schema.
- Ensure types match schema exactly.
"""

SKILL_RATING_SYSTEM_PROMPT = """You are a strict skill evidence evaluator. Your task is to produce ONLY the user_skills array in VALID JSON matching the provided SKILL_SCHEMA.

CRITICAL SCORING RULES:
- Score system_rating (1–10) ONLY from explicit evidence in the resume.
- NEVER rate any skill > 3 unless there is explicit WORK EXPERIENCE or PROJECT evidence demonstrating that skill.
- Keywords alone, self-claimed skill lists, or coursework alone MUST be rated 1–3.

Evidence strength rubric:
- none: only keyword or not mentioned → 1
- weak: mentioned in skills list/course/generic summary without details → 2–3
- moderate: used in at least one work/project bullet with context → 4–6
- strong: repeated professional use, clear responsibility, scale or outcomes → 7–8
- distinguished: patents/books/major OSS/industry authority → 9–10 (rare)

Role-critical penalty:
- Use the inferred target role (provided as input) to identify role-critical skills.
- If a skill is critical but resume lacks WORK/PROJECT evidence, keep rating 1–3 and explicitly state what evidence would be expected.

FIELD MAPPING (must follow exactly):
For each item:
- skill: normalized skill name (e.g., "Python", "SQL", "SIEM", "AWS", "React")
- level_of_skill: derived from system_rating:
  1–2 beginner, 3–4 intermediate, 5–6 advanced, 7–10 expert
- system_rating: integer 1–10
- description: MUST include:
  (a) 1–2 short evidence snippets (work/project context) OR if none: "No work/project evidence found; mentioned only as keyword/self-claim/course."
  (b) If role-critical and missing evidence: state what evidence would be expected.

Output:
- Output ONLY valid JSON (the array).
- No markdown, no extra text.
- Do NOT include skills not present in the resume text.
"""

# -----------------------------
# 2) SCHEMAS
# -----------------------------

CV_SCHEMA: Dict[str, Any] = {
    "user_profile": {
        "first_name": "text",
        "middle_name": "text",
        "last_name": "text",
        "about": "text",
        "email": "text",
        "phone": "text",
        "dob": "text",
        "target_role": "text",
        "role_confidence": "number",
        "marital_status": "text",
        "gender": "text",
        "industry": "text",
        "is_valid_resume": "boolean",
    },
    "user_web_links": [{"web_link": "text", "website_type": "text"}],
    "address": {
        "address_line_1": "text",
        "address_line_2": "text",
        "city": "text",
        "postal_code": "text",
        "province": "text",
        "country": "text",
        "is_current_address": "boolean",
    },
    "education": [
        {
            "degree": "text",
            "field": "text",
            "institution": "text",
            "start": "text",
            "end": "text",
            "grade": "text",
        }
    ],
    "experience": [
        {
            "company": "text",
            "role": "text",
            "start": "text",
            "end": "text",
            "summary": "text",
            "currently_working": "boolean",
            "highlights": ["text"],
        }
    ],
    "projects": [
        {
            "title": "text",
            "summary": "text",
            "skills": ["text"],
            "domain": "text",
            "responsibilities": ["text"],
        }
    ],
    "certifications": [{"name": "text", "issuer": "text", "issue_date": "text"}],
    "user_skills": [
        {"skill": "text", "level_of_skill": "text", "system_rating": "integer", "description": "text"}
    ],
}

SKILL_SCHEMA: Dict[str, Any] = {
    "user_skills": [
        {
            "skill": "text",
            "level_of_skill": "text",
            "system_rating": "integer",
            "description": "text",
        }
    ]
}

# -----------------------------
# 3) USER PROMPT TEMPLATES
# -----------------------------

CV_EXTRACTION_USER_PROMPT_TEMPLATE = """
Extract data from the following CV text using the SCHEMA below.

Rules:
- Respect field types exactly.
- If not found: use null for strings/objects; for booleans use false only when applicable.
- Address rule: if address_line_1 is null, is_current_address must be null.
- Infer and fill: user_profile.industry, user_profile.target_role, user_profile.role_confidence, user_profile.about (evidence-based).
- Return ONLY the JSON object (no markdown).

SCHEMA:
{schema}

CV TEXT:
\"\"\"
{cv_text}
\"\"\"
"""

SKILL_RATING_USER_PROMPT_TEMPLATE = """
You will be given:
1) Inferred target role and domain (from extraction step)
2) CV text (source of truth)
3) A SKILL_SCHEMA

Task:
- Produce ONLY a JSON array for user_skills (NOT the full CV JSON).
- Only include skills explicitly present in the CV text.
- Apply the strict rating rubric: never >3 without work/project evidence.

Inferred role context:
- target_role: {target_role}
- domain/industry: {industry}
- role_confidence: {role_confidence}

SKILL_SCHEMA:
{skill_schema}

CV TEXT:
\"\"\"
{cv_text}
\"\"\"
"""

# -----------------------------
# 4) BUILDERS
# -----------------------------

def build_cv_extraction_prompt(cv_text: str) -> str:
    if not cv_text or not cv_text.strip():
        raise ValueError("cv_text cannot be empty")

    return CV_EXTRACTION_USER_PROMPT_TEMPLATE.format(
        schema=json.dumps(CV_SCHEMA, indent=2),
        cv_text=cv_text.strip(),
    ).strip()


def build_skill_rating_prompt(cv_text: str, extracted_cv_json: Dict[str, Any]) -> str:
    if not cv_text or not cv_text.strip():
        raise ValueError("cv_text cannot be empty")
    if not isinstance(extracted_cv_json, dict):
        raise ValueError("extracted_cv_json must be a dict")

    user_profile = extracted_cv_json.get("user_profile") or {}
    target_role = user_profile.get("target_role") or "null"
    industry = user_profile.get("industry") or "null"
    role_confidence = user_profile.get("role_confidence")
    role_confidence = role_confidence if isinstance(role_confidence, (int, float)) else "null"

    return SKILL_RATING_USER_PROMPT_TEMPLATE.format(
        target_role=target_role,
        industry=industry,
        role_confidence=role_confidence,
        skill_schema=json.dumps(SKILL_SCHEMA["user_skills"], indent=2),
        cv_text=cv_text.strip(),
    ).strip()


# -----------------------------
# 5) EXAMPLE USAGE (LLM CALL PSEUDO)
# -----------------------------
"""
# Step 1: Extraction
extraction_user_prompt = build_cv_extraction_prompt(cv_text)

messages_step1 = [
  {"role": "system", "content": CV_EXTRACTION_SYSTEM_PROMPT},
  {"role": "user", "content": extraction_user_prompt},
]
# extracted_cv_json = llm(messages_step1)  # must return JSON object
# extracted_cv_json = json.loads(extracted_cv_json_str)

# Step 2: Skill rating
skill_user_prompt = build_skill_rating_prompt(cv_text, extracted_cv_json)

messages_step2 = [
  {"role": "system", "content": SKILL_RATING_SYSTEM_PROMPT},
  {"role": "user", "content": skill_user_prompt},
]
# user_skills_array = llm(messages_step2)  # must return JSON array
# user_skills_array = json.loads(user_skills_array_str)

# Merge if you want:
# extracted_cv_json["user_skills"] = user_skills_array
"""
