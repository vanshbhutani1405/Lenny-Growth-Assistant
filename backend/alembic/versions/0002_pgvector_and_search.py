"""Enable pgvector and add transcript keyword-search support."""
from alembic import op

revision = "0002_pgvector_and_search"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # Milestone 1 had no ingestion path, so its nullable JSON placeholder is empty.
    op.execute(
        "ALTER TABLE transcript_chunks "
        "ALTER COLUMN embedding TYPE vector(384) USING NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_transcript_chunks_search_vector "
        "ON transcript_chunks USING gin "
        "(to_tsvector('english', coalesce(chunk_text, '')))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_transcript_chunks_search_vector")
    op.execute(
        "ALTER TABLE transcript_chunks ALTER COLUMN embedding TYPE json "
        "USING NULL"
    )
