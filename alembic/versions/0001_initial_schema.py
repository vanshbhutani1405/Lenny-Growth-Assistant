"""Create initial application schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("sessions", sa.Column("id", sa.String(36), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("metadata", sa.JSON(), nullable=True))
    op.create_table("messages", sa.Column("id", sa.String(36), primary_key=True), sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(32), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("metadata", sa.JSON(), nullable=True))
    op.create_index("ix_messages_session_id", "messages", ["session_id"])
    op.create_index("ix_messages_session_created_at", "messages", ["session_id", "created_at"])
    op.create_table("transcript_chunks", sa.Column("id", sa.String(64), primary_key=True), sa.Column("episode_slug", sa.String(255), nullable=False), sa.Column("guest", sa.String(255), nullable=True), sa.Column("title", sa.String(500), nullable=True), sa.Column("youtube_url", sa.String(2048), nullable=True), sa.Column("publish_date", sa.Date(), nullable=True), sa.Column("chunk_index", sa.Integer(), nullable=False), sa.Column("chunk_text", sa.Text(), nullable=False), sa.Column("embedding", sa.JSON(), nullable=True))
    op.create_index("ix_transcript_chunks_episode_slug", "transcript_chunks", ["episode_slug"])
    op.create_index("ix_transcript_chunks_episode_chunk_index", "transcript_chunks", ["episode_slug", "chunk_index"], unique=True)


def downgrade() -> None:
    op.drop_table("transcript_chunks")
    op.drop_index("ix_messages_session_created_at", table_name="messages")
    op.drop_index("ix_messages_session_id", table_name="messages")
    op.drop_table("messages")
    op.drop_table("sessions")
