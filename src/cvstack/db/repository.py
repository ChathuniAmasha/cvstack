from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Tuple
import psycopg
from pgvector.psycopg import register_vector
from psycopg.types.json import Json
from ..config import settings

log = logging.getLogger(__name__)

class Repository:
    def __init__(self) -> None:
        self.conn = psycopg.connect(
            host=settings.pg_host,
            port=settings.pg_port,
            dbname=settings.pg_db,
            user=settings.pg_user,
            password=settings.pg_password,
        )


    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    def insert_candidate(self, full_name: str | None, email: str | None, raw_text: str) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO candidates (full_name, email, raw_text) VALUES (%s, %s, %s) RETURNING id",
                (full_name, email, raw_text),
            )
            cid = cur.fetchone()[0]
            self.conn.commit()
            return cid

    def insert_sections(self, section_rows: List[Tuple[int, str, Dict[str, Any], str]]) -> List[int]:
        ids: List[int] = []
        with self.conn.cursor() as cur:
            for r in section_rows:
                cur.execute(
                    "INSERT INTO sections (candidate_id, topic, payload, text_for_embedding) VALUES (%s, %s, %s, %s) RETURNING id",
                    (r[0], r[1], Json(r[2]), r[3]),
                )
                ids.append(cur.fetchone()[0])
            self.conn.commit()
        return ids

    def insert_vectors(self, section_ids: List[int], vectors: List[List[float]]) -> None:
        if not vectors:
            print("No vectors to insert")
            return
        try:
            with self.conn.cursor() as cur:
                print(f"Inserting {len(vectors)} vectors...")
                cur.executemany(
                    "INSERT INTO section_vectors (section_id, embedding) VALUES (%s, %s)",
                    list(zip(section_ids, vectors)),
                )
                self.conn.commit()
                print("Vectors inserted successfully")
        except Exception as e:
            print(f"Error inserting vectors: {e}")
            raise