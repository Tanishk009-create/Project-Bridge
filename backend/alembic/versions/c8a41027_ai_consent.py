"""Explicit AI sharing consent and durable reply idempotency."""
from alembic import op
import sqlalchemy as sa

revision = "c8a41027"
down_revision = "b7d3e9a21026"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("ai_turns",
        sa.Column("message_id", sa.Uuid(), sa.ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assistant_id", sa.Uuid(), sa.ForeignKey("messages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("lease_id", sa.Uuid(), nullable=False),
        sa.Column("consent_version", sa.String(24), nullable=False),
        sa.Column("safety_routed", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_ai_turns_user_id", "ai_turns", ["user_id"])

def downgrade():
    op.drop_table("ai_turns")
