"""One optional photo on each capture or conversation message."""
from alembic import op
import sqlalchemy as sa

revision = "e1a51116"
down_revision = "d9b41027"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("captures", sa.Column("photo_data", sa.Text(), nullable=True))
    op.add_column("messages", sa.Column("photo_data", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("messages", "photo_data")
    op.drop_column("captures", "photo_data")
