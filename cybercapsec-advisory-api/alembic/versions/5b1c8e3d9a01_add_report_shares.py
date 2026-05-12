"""add report_shares table

Revision ID: 5b1c8e3d9a01
Revises: 4332699ab7a3
Create Date: 2026-05-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5b1c8e3d9a01"
down_revision: Union[str, None] = "4332699ab7a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_shares",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(
        op.f("ix_report_shares_report_id"), "report_shares", ["report_id"]
    )
    op.create_index(
        op.f("ix_report_shares_company_id"), "report_shares", ["company_id"]
    )
    op.create_index(
        op.f("ix_report_shares_token"), "report_shares", ["token"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_report_shares_token"), table_name="report_shares")
    op.drop_index(op.f("ix_report_shares_company_id"), table_name="report_shares")
    op.drop_index(op.f("ix_report_shares_report_id"), table_name="report_shares")
    op.drop_table("report_shares")
