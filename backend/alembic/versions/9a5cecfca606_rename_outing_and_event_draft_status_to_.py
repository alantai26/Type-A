"""rename outing and event draft status to planning_in_progress

Revision ID: 9a5cecfca606
Revises: 40546b016600
Create Date: 2026-04-29 17:17:06.173507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a5cecfca606'
down_revision: Union[str, Sequence[str], None] = '40546b016600'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
