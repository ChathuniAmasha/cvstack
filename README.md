CVStack – AI-Powered CV Extraction & Vector Embedding System

This project extracts structured information from CVs/Resumes and converts them into vector embeddings for semantic search and candidate matching.

It uses Google Gemini to identify key fields such as:

Candidate Name & Contact Details

Education History

Work Experience

Skills

Projects and Achievements

The extracted text segments are then embedded using a text-embedding model and stored in PostgreSQL with pgvector, enabling similarity search and candidate ranking by skill relevance.

Key Capabilities:

Upload CVs (PDF or Text)

Automatic structured CV parsing using LLMs

Vector embeddings for semantic comparison

Storage in a relational database for reuse and analytics

Modular, maintainable architecture (API layer → service layer → database layer)

This system can be extended for:

HR automation

Recruitment workflows

Skill-based candidate matching

Resume database search and filtering
