"""Add required print model difficulty, preserving existing rows and material links."""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_difficulty"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "print_models",
        sa.Column(
            "difficulty", sa.String(),
            sa.CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name="ck_print_models_difficulty"),
            nullable=False, server_default="easy",
        ),
    )


def downgrade() -> None:
    op.drop_column("print_models", "difficulty")
