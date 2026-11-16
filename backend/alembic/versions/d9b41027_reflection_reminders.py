"""Exact reflection citations and opt-in in-app reminders."""
from alembic import op
import sqlalchemy as sa
revision="d9b41027"
down_revision="c8a41027"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("reflection_sources",
        sa.Column("reflection_id",sa.Uuid(),sa.ForeignKey("reflections.id",ondelete="CASCADE"),primary_key=True),
        sa.Column("message_id",sa.Uuid(),sa.ForeignKey("messages.id",ondelete="CASCADE"),primary_key=True),
        sa.Column("quote",sa.Text(),nullable=False),sa.Column("explanation",sa.Text(),nullable=False))
    op.create_table("reminders",
        sa.Column("id",sa.Uuid(),primary_key=True),
        sa.Column("user_id",sa.Uuid(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),
        sa.Column("reflection_id",sa.Uuid(),sa.ForeignKey("reflections.id",ondelete="CASCADE"),nullable=True),
        sa.Column("destination",sa.String(32),nullable=False),
        sa.Column("scheduled_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("status",sa.String(24),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index("ix_reminders_user_id","reminders",["user_id"])
def downgrade():
    op.drop_table("reminders");op.drop_table("reflection_sources")
