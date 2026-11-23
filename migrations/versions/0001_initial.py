"""Create designers, categories, materials, print models and material associations."""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "designers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.UniqueConstraint("email", name="uq_designers_email"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_designers_name"),
    )
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("name_key", sa.String(), nullable=False),
        sa.UniqueConstraint("name_key", name="uq_categories_name_key"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_categories_name"),
    )
    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("name_key", sa.String(), nullable=False),
        sa.UniqueConstraint("name_key", name="uq_materials_name_key"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_materials_name"),
    )
    op.create_table(
        "print_models",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("name_key", sa.String(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("print_time_minutes", sa.Integer(), nullable=False),
        sa.Column("copies", sa.Integer(), nullable=False),
        sa.Column("designer_id", sa.Integer(), sa.ForeignKey("designers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.UniqueConstraint("designer_id", "name_key", name="uq_print_models_designer_name"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_print_models_name"),
        sa.CheckConstraint("length(trim(instructions)) > 0", name="ck_print_models_instructions"),
        sa.CheckConstraint("print_time_minutes > 0", name="ck_print_models_print_time"),
        sa.CheckConstraint("copies > 0", name="ck_print_models_copies"),
    )
    op.create_index("ix_print_models_designer_id", "print_models", ["designer_id"])
    op.create_index("ix_print_models_category_id", "print_models", ["category_id"])
    op.create_table(
        "print_model_materials",
        sa.Column("print_model_id", sa.Integer(), sa.ForeignKey("print_models.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_print_model_materials_quantity"),
        sa.CheckConstraint("unit IN ('g', 'm', 'ml')", name="ck_print_model_materials_unit"),
    )


def downgrade() -> None:
    op.drop_table("print_model_materials")
    op.drop_index("ix_print_models_category_id", table_name="print_models")
    op.drop_index("ix_print_models_designer_id", table_name="print_models")
    op.drop_table("print_models")
    op.drop_table("materials")
    op.drop_table("categories")
    op.drop_table("designers")
