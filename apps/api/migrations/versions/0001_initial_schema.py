"""initial schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from app.db.base import Base

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _copy_table_constraints(table: sa.Table) -> list[sa.schema.Constraint]:
    constraints: list[sa.schema.Constraint] = []
    for constraint in table.constraints:
        if isinstance(constraint, (sa.UniqueConstraint, sa.CheckConstraint)):
            constraints.append(constraint.copy())
    return constraints


def upgrade() -> None:
    for table in Base.metadata.sorted_tables:
        copied_columns = [column.copy() for column in table.columns]
        copied_constraints = _copy_table_constraints(table)
        op.create_table(table.name, *copied_columns, *copied_constraints)

        for index in table.indexes:
            op.create_index(
                index.name,
                table.name,
                [column.name for column in index.columns],
                unique=index.unique,
            )


def downgrade() -> None:
    for table in reversed(Base.metadata.sorted_tables):
        op.drop_table(table.name)
