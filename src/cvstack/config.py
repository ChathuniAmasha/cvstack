from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    # DB
    pg_host: str = os.getenv("PGHOST", "localhost")
    pg_port: int = int(os.getenv("PGPORT", "5432"))
    pg_db: str = os.getenv("PGDATABASE", "cvdb")
    pg_user: str = os.getenv("PGUSER", "postgres")
    pg_password: str = os.getenv("PGPASSWORD", "postgres")

    # AI
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    extraction_model: str = os.getenv("EXTRACTION_MODEL", "models/gemini-2.5-flash")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "768"))
    skip_embedding: bool = os.getenv("SKIP_EMBEDDING", "0") == "1"

    # App
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
