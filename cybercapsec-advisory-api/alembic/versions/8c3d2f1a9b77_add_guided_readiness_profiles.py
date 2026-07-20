"""add guided_readiness_profiles table

Revision ID: 8c3d2f1a9b77
Revises: 5b1c8e3d9a01
Create Date: 2026-07-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8c3d2f1a9b77"
down_revision: Union[str, None] = "5b1c8e3d9a01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guided_readiness_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("updated_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("selected_goal", sa.String(length=80), nullable=True),
        sa.Column("target_framework", sa.String(length=80), nullable=True),
        sa.Column("program_profile", sa.JSON(), nullable=False),
        sa.Column("scope_answers", sa.JSON(), nullable=False),
        sa.Column("baseline_answers", sa.JSON(), nullable=False),
        sa.Column("questionnaire_drafts", sa.JSON(), nullable=False),
        sa.Column("readiness_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id"),
    )
    op.create_index(
        op.f("ix_guided_readiness_profiles_company_id"),
        "guided_readiness_profiles",
        ["company_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_guided_readiness_profiles_company_id"),
        table_name="guided_readiness_profiles",
    )
    op.drop_table("guided_readiness_profiles")
