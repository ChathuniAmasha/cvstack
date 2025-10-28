from __future__ import annotations
import argparse
import json
import logging
import re
from typing import Any, Dict, List, Tuple
from pypdf import PdfReader

from ..logging_conf import configure_logging
from ..services.extractor import CVExtractor
from ..services.embedder import Embedder
from ..db.repository import Repository

# Note: The functions read_pdf_text, compact_text_for_embedding, 
# and build_sections (from your previous snippets) should be here.
# ...existing imports...
def read_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def main() -> None:
    configure_logging()
    log = logging.getLogger("cvstack.cli")


    #Command line parsing is the process a program uses to interpret and understand the input provided 
    # by a user (or another program) when it is run from a shell or terminal.

    parser = argparse.ArgumentParser()
    parser.add_argument("--cv", help="Path to CV PDF or TXT")
    parser.add_argument("--text", help="Raw CV text (overrides --cv)")
    parser.add_argument("--no-extract", action="store_true", help="Don't call LLM; use simple heuristics")
    args = parser.parse_args()  #reads the arguments passed by the user from the command line, processes them according to the
                                #definitions above, and stores them as attributes in the args object

    # Load CV text
    if args.text:
        cv_text = args.text
    elif args.cv:
        if args.cv.lower().endswith(".pdf"):
            cv_text = read_pdf_text(args.cv)
        else:
            with open(args.cv, "r", encoding="utf-8") as f:
                cv_text = f.read()
    else:
        raise SystemExit("Provide --cv /path/to/file or --text 'CV text'")

    # Parse
    if args.no_extract:
        parsed: Dict[str, Any] = {
            "candidate": {"full_name": cv_text.splitlines()[0] if cv_text else None},
            "education": [],
            "projects": [],
            "skills": [s.strip() for s in re.findall(r"Skills:\s*(.*)", cv_text, flags=re.IGNORECASE)] or [],
            "experience": [{"summary": cv_text}] if "Experience:" in cv_text else []
        }
    else:
        parsed = CVExtractor().extract(cv_text)

    repo = Repository()
    try:
        # Insert candidate first to get ID
        cand_name = parsed.get("candidate", {}).get("full_name")
        cand_email = parsed.get("candidate", {}).get("email")
        candidate_id = repo.insert_candidate(cand_name, cand_email, cv_text)

        # Build sections + embed
        section_rows, texts = build_sections(parsed, candidate_id)
        embeddings = Embedder().embed(texts)

        # Persist sections + vectors
        section_ids = repo.insert_sections(section_rows)
        repo.insert_vectors(section_ids, embeddings)

        print(json.dumps({"candidate_id": candidate_id, "parsed_sample": parsed}, ensure_ascii=False, indent=2))
    finally:
        repo.close()

# add at top with other imports
from typing import Any, Dict, List, Tuple
import json

def compact_text_for_embedding(section: Dict[str, Any], topic: str) -> str:
    if topic == "education":
        return ", ".join(filter(None, [
            section.get("degree"), section.get("field"),
            section.get("institution"),
            f"{section.get('start','')}–{section.get('end','')}",
            section.get("grade"),
        ]))
    if topic == "projects":
        skills = ", ".join(section.get("skills") or [])
        return " | ".join(filter(None, [
            section.get("title"), section.get("summary"),
            f"Skills: {skills}" if skills else "", section.get("impact"),
        ]))
    if topic == "experience":
        highlights = "; ".join(section.get("highlights") or [])
        return " | ".join(filter(None, [
            f"{section.get('role','')} @ {section.get('company','')}",
            f"{section.get('start','')}–{section.get('end','')}",
            section.get("summary"),
            f"Highlights: {highlights}" if highlights else "",
        ]))
    if topic == "skills":
        return section.get("skill", "")
    return json.dumps(section, ensure_ascii=False)

def build_sections(parsed: Dict[str, Any], candidate_id: int) -> Tuple[List[Tuple[int, str, Dict[str, Any], str]], List[str]]:
    section_rows: List[Tuple[int, str, Dict[str, Any], str]] = []
    texts: List[str] = []

    def add(topic: str, item: Dict[str, Any]):
        txt = compact_text_for_embedding(item, topic)
        section_rows.append((candidate_id, topic, item, txt))
        texts.append(txt)

    for edu in parsed.get("education", []) or []:
        add("education", edu)
    for proj in parsed.get("projects", []) or []:
        add("projects", proj)
    for exp in parsed.get("experience", []) or []:
        add("experience", exp)
    for sk in parsed.get("skills", []) or []:
        add("skills", {"skill": sk})

    return section_rows, texts


if __name__ == "__main__":
    main()
