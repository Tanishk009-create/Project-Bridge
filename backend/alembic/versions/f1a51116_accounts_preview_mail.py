"""Email lifecycle, scheduled previews and generic reminder delivery."""
from alembic import op
import sqlalchemy as sa

revision = "f1a51116"
down_revision = "e1a51116"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE users SET email_verified_at = CURRENT_TIMESTAMP")
    op.add_column("user_preferences", sa.Column("notification_email_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("reminders", sa.Column("delivery_status", sa.String(24), nullable=False, server_default="pending"))
    op.add_column("reminders", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table("account_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(24), nullable=False),
        sa.Column("token_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_account_tokens_user_id", "account_tokens", ["user_id"])
    op.create_table("preview_schedules",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("cadence_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(24), nullable=False, server_default="scheduled"),
        sa.Column("last_reflection_id", sa.Uuid(), sa.ForeignKey("reflections.id", ondelete="SET NULL"), nullable=True))

def downgrade():
    op.drop_table("preview_schedules")
    op.drop_index("ix_account_tokens_user_id", table_name="account_tokens")
    op.drop_table("account_tokens")
    op.drop_column("reminders", "delivered_at")
    op.drop_column("reminders", "delivery_status")
    op.drop_column("user_preferences", "notification_email_enabled")
    op.drop_column("users", "email_verified_at")
