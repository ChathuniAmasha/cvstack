from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Tuple

from ..db.repository import Repository


log = logging.getLogger(__name__)


def sanitize_text(text: str) -> str:
    """Remove null bytes and other problematic characters from text"""
    if not text:
        return ""
    cleaned = text.replace("\x00", "")
    cleaned = "".join(char if ord(char) >= 32 else " " for char in cleaned)
    return cleaned.strip()


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize all text in a dictionary"""
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = sanitize_text(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value)
        elif isinstance(value, list):
            result[key] = [
                sanitize_dict(item) if isinstance(item, dict)
                else sanitize_text(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def build_sections(parsed: Dict[str, Any], candidate_id: int) -> Tuple[List[Tuple[int, str, Dict[str, Any], str]], List[str]]:
    """
    Convert parsed CV data into database rows for the sections table.
    Returns:
        - section_rows: List of tuples (candidate_id, topic, payload, text_for_embedding)
        - texts: List of text strings for embedding
    """
    rows = []
    texts = []

    # Sanitize all text in parsed data
    parsed = sanitize_dict(parsed)

    # 1. User Profile
    profile = parsed.get("user_profile", {})
    if profile:
        text = " ".join(str(v) for v in profile.values() if v)
        rows.append((candidate_id, "user_profile", profile, text))
        texts.append(text)

    # 2. User Web Links
    for link in parsed.get("user_web_links", []):
        text = f"{link.get('website_type', '')} {link.get('web_link', '')}"
        rows.append((candidate_id, "user_web_links", link, text))
        texts.append(text)

    # 3. Address
    address = parsed.get("address", {})
    if address:
        text = " ".join(str(v) for v in address.values() if v)
        rows.append((candidate_id, "address", address, text))
        texts.append(text)

    # 4. Education
    for edu in parsed.get("education", []):
        text = f"{edu.get('degree', '')} {edu.get('institution', '')} {edu.get('field', '')}"
        rows.append((candidate_id, "education", edu, text))
        texts.append(text)

    # 5. Certifications
    for cert in parsed.get("certifications", []):
        text = f"{cert.get('name', '')} {cert.get('issuer', '')}"
        rows.append((candidate_id, "certifications", cert, text))
        texts.append(text)

    # 6. Experience
    for exp in parsed.get("experience", []):
        text = f"{exp.get('role', '')} {exp.get('company', '')} {exp.get('summary', '')}"
        rows.append((candidate_id, "experience", exp, text))
        texts.append(text)

    # 7. Projects
    for proj in parsed.get("projects", []):
        text = f"{proj.get('title', '')} {proj.get('summary', '')}"
        rows.append((candidate_id, "projects", proj, text))
        texts.append(text)

    # 8. User Skills
    for skill in parsed.get("user_skills", []):
        text = f"{skill.get('skill', '')} {skill.get('level_of_skill', '')} rating:{skill.get('system_rating', '')}"
        rows.append((candidate_id, "user_skills", skill, text))
        texts.append(text)

    return rows, texts

