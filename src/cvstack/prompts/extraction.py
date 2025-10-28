# src/cvstack/prompts/extraction.py

SYSTEM_PROMPT = (
    "You are an expert CV parser. Extract clean, schema-compliant JSON. "
    "Return ONLY JSON, no explanations."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "candidate": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string"},
                "email": {"type": "string"}
            }
        },
        "education": {"type": "array", "items": {"type": "object", "properties": {
            "degree": {"type": "string"},
            "field": {"type": "string"},
            "institution": {"type": "string"},
            "start": {"type": "string"},
            "end": {"type": "string"},
            "grade": {"type": "string"}
        } }},
        "projects": {"type": "array", "items": {"type": "object", "properties": {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "skills": {"type": "array", "items": {"type": "string"}},
            "impact": {"type": "string"}
        } }},
        "skills": {"type": "array", "items": {"type": "string"}},
        "experience": {"type": "array", "items": {"type": "object", "properties": {
            "company": {"type": "string"},
            "role": {"type": "string"},
            "start": {"type": "string"},
            "end": {"type": "string"},
            "summary": {"type": "string"},
            "highlights": {"type": "array", "items": {"type": "string"}}
        } }}
    },
    "required": ["education", "projects", "skills", "experience"]
}

USER_PROMPT_TEMPLATE = """Extract the following CV into JSON using this schema:
{schema}

CV:
{cv_text}
"""
