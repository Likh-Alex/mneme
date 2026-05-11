"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-05

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    source_kind = sa.Enum("url", "pdf", "markdown", name="source_kind")
    source_status = sa.Enum("pending", "processing", "ready", "failed", name="source_status")
    op.create_table(
        "sources",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", source_kind, nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", source_status, nullable=False, server_default="pending"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("original_s3_key", sa.Text(), nullable=True),
        sa.Column("parsed_s3_key", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_sources_user_id", "sources", ["user_id"])
    op.create_index("ix_sources_status", "sources", ["status"])

    op.create_table(
        "chunks",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "source_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ord", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.UniqueConstraint("source_id", "ord", name="uq_chunks_source_ord"),
    )
    op.create_index("ix_chunks_source_id", "chunks", ["source_id"])

    op.create_table(
        "embeddings",
        sa.Column(
            "chunk_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("chunks.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("vector", Vector(1536), nullable=False),
    )
    op.create_index(
        "ix_embeddings_vector_hnsw",
        "embeddings",
        ["vector"],
        postgresql_using="hnsw",
        postgresql_ops={"vector": "vector_cosine_ops"},
    )

    concept_kind = sa.Enum("concept", "term", "person", "other", name="concept_kind")
    op.create_table(
        "concepts",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "source_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("kind", concept_kind, nullable=False),
    )
    op.create_index("ix_concepts_source_id", "concepts", ["source_id"])

    op.create_table(
        "flashcards",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "source_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column(
            "ease",
            sa.Float(),
            nullable=False,
            server_default=sa.text("2.5"),
        ),
        sa.Column(
            "interval_days",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "next_due_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_flashcards_source_id", "flashcards", ["source_id"])
    op.create_index("ix_flashcards_next_due_at", "flashcards", ["next_due_at"])

    op.create_table(
        "reviews",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "flashcard_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("flashcards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "graded_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("grade", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("grade BETWEEN 0 AND 5", name="ck_reviews_grade_range"),
    )
    op.create_index("ix_reviews_flashcard_id", "reviews", ["flashcard_id"])
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"])

    op.create_table(
        "conversations",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    message_role = sa.Enum("user", "assistant", "system", name="message_role")
    op.create_table(
        "messages",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "citations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.execute("DROP TYPE IF EXISTS message_role")

    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_table("conversations")

    op.drop_index("ix_reviews_user_id", table_name="reviews")
    op.drop_index("ix_reviews_flashcard_id", table_name="reviews")
    op.drop_table("reviews")

    op.drop_index("ix_flashcards_next_due_at", table_name="flashcards")
    op.drop_index("ix_flashcards_source_id", table_name="flashcards")
    op.drop_table("flashcards")

    op.drop_index("ix_concepts_source_id", table_name="concepts")
    op.drop_table("concepts")
    op.execute("DROP TYPE IF EXISTS concept_kind")

    op.drop_index("ix_embeddings_vector_hnsw", table_name="embeddings")
    op.drop_table("embeddings")

    op.drop_index("ix_chunks_source_id", table_name="chunks")
    op.drop_table("chunks")

    op.drop_index("ix_sources_status", table_name="sources")
    op.drop_index("ix_sources_user_id", table_name="sources")
    op.drop_table("sources")
    op.execute("DROP TYPE IF EXISTS source_status")
    op.execute("DROP TYPE IF EXISTS source_kind")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.execute("DROP EXTENSION IF EXISTS vector")
