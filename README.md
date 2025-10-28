# CVStack (No pyproject.toml)


Production-style CV extraction + pgvector embeddings using plain `requirements.txt`.


## Setup
```bash
cp .env.example .env
pip install -r requirements.txt
# create tables
psql "$PGDATABASE" -h "$PGHOST" -U "$PGUSER" -f migrations/0001_init.sql