"""Persistent workspace and unified identity.
Revision ID: b7d3e9a21026
Revises: d5150e6c6eb3
"""
from alembic import op
import sqlalchemy as sa

revision = "b7d3e9a21026"
down_revision = "d5150e6c6eb3"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("google_subject", sa.String(255), nullable=True))
    op.create_unique_constraint("uq_users_google_subject", "users", ["google_subject"])
    for name, default in [("save_history", "true"), ("save_context_allowed", "false"), ("dark_mode", "false"), ("reduced_motion", "false"), ("onboarding_complete", "false")]:
        op.add_column("user_preferences", sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.text(default)))
    op.add_column("user_preferences", sa.Column("text_size", sa.String(32), nullable=False, server_default="comfortable"))
    op.add_column("hypotheses", sa.Column("user_correction", sa.Text(), nullable=True))
    op.alter_column("reflections", "hypothesis_id", existing_type=sa.Uuid(), nullable=True)
    op.add_column("reflections", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_table("captures",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False), sa.Column("category", sa.String(32), nullable=False),
        sa.Column("analysis_allowed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_captures_user_id", "captures", ["user_id"])
    op.create_table("passport_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section", sa.String(32), nullable=False), sa.Column("title", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("use_in_conversations", sa.Boolean(), nullable=False),
        sa.Column("use_for_patterns", sa.Boolean(), nullable=False),
        sa.Column("allow_reflections", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_passport_items_user_id", "passport_items", ["user_id"])

def downgrade():
    raise RuntimeError("Forward-only: restore a pre-migration backup to revert without losing free-form reflections.")
