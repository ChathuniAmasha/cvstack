-- Enable pgvector once per database
CREATE EXTENSION IF NOT EXISTS vector;


-- Main tables
CREATE TABLE IF NOT EXISTS candidates (
id BIGSERIAL PRIMARY KEY,
full_name TEXT,
email TEXT,
raw_text TEXT,
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


CREATE TABLE IF NOT EXISTS sections (
id BIGSERIAL PRIMARY KEY,
candidate_id BIGINT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
topic TEXT NOT NULL,
payload JSONB NOT NULL,
text_for_embedding TEXT,
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


CREATE TABLE IF NOT EXISTS section_vectors (
section_id BIGINT PRIMARY KEY REFERENCES sections(id) ON DELETE CASCADE,
embedding VECTOR(768) NOT NULL
);


-- Indexes
CREATE INDEX IF NOT EXISTS sections_topic_idx ON sections(topic);
CREATE INDEX IF NOT EXISTS sections_cand_idx ON sections(candidate_id);
CREATE INDEX IF NOT EXISTS sections_payload_gin ON sections USING GIN (payload);


CREATE INDEX IF NOT EXISTS section_vectors_embed_idx
ON section_vectors USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);