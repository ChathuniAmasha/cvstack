from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
import psycopg   #psycopg allows your Python application to connect to a PostgreSQL database, send SQL queries, and get results back
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

    
    def insert_candidate(self, full_name: Optional[str], email: Optional[str], raw_text: str) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO candidates (full_name, email, raw_text)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (full_name, email, raw_text),
            )
            candidate_id = cur.fetchone()[0]
            self.conn.commit()
            return candidate_id


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

    def search_candidates_by_skill_catalog(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Ranks candidates by TOTAL 'Skill Points' against the uploaded catalog.
        
        Logic:
          - We check every candidate against ALL 30+ skills in your 'skill_vectors' table.
          - Each match adds points to their score.
          - Candidates with MORE matches appear at the top.
        """
        sql = """
        WITH skill_matches AS (
            -- 1. Compare Every Candidate Section vs Every Catalog Skill
            SELECT 
                c.id AS candidate_id,
                c.full_name,
                c.email,
                sk.skill_name,
                (sv.embedding <=> sk.embedding) AS distance
            FROM section_vectors sv
            JOIN sections s ON s.id = sv.section_id
            JOIN candidates c ON c.id = s.candidate_id
            CROSS JOIN skill_vectors sk
        ),
        best_matches AS (
            -- 2. Find the single best match for each skill per candidate.
            -- We use a threshold of 0.65 to allow 'Good' matches (not just 'Perfect' ones).
            SELECT 
                candidate_id,
                full_name,
                email,
                skill_name,
                MIN(distance) as best_distance
            FROM skill_matches
            WHERE distance < 0.65
            GROUP BY candidate_id, full_name, email, skill_name
        ),
        candidate_scores AS (
            -- 3. Calculate Score based on SUM (Quantity + Quality)
            SELECT 
                candidate_id,
                full_name,
                email,
                ARRAY_AGG(skill_name) AS matched_skills,
                -- FORMULA: 10 points for having the skill + bonus for match quality
                SUM(10 + (1 - best_distance)) AS total_score
            FROM best_matches
            GROUP BY candidate_id, full_name, email
        )
        SELECT 
            candidate_id,
            full_name,
            email,
            matched_skills,
            ROUND(total_score::numeric, 1) AS match_score
        FROM candidate_scores
        ORDER BY total_score DESC
        LIMIT %s;
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (limit,))
                rows = cur.fetchall()

            return [
                {
                    "candidate_id": row[0],
                    "name": row[1],           
                    "full_name": row[1],      
                    "email": row[2],
                    "matched_skills": row[3], # This list populates the blue tags
                    "match_score": row[4]     # This score determines the ranking
                }
                for row in rows
            ]
            
        except Exception as e:
            print(f"Error in catalog search: {e}")
            return []
        
    def upsert_skill_vectors(self, skills: List[Dict[str, str]], vectors: List[List[float]]) -> None:
        """
        Inserts or updates skills in the skill_vectors table.
        """
        sql = """
            INSERT INTO skill_vectors (skill_name, skill_description, embedding)
            VALUES (%s, %s, %s)
            ON CONFLICT (skill_name)
            DO UPDATE SET 
                skill_description = EXCLUDED.skill_description,
                embedding = EXCLUDED.embedding;
        """
        
        # Prepare data: (name, description, vector)
        payload = []
        for s, vector in zip(skills, vectors):
            payload.append((s["name"], s.get("description", ""), vector))

        with self.conn.cursor() as cur:
            cur.executemany(sql, payload)
            self.conn.commit()