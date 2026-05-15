"""add bio to users

Revision ID: b416388ba296
Revises: 3067d8b0ab6b
Create Date: 2026-05-15 09:35:44.932690

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b416388ba296'
down_revision: Union[str, Sequence[str], None] = '3067d8b0ab6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:                                                                 
    """Upgrade schema."""
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))                 
                                                                                         
  
def downgrade() -> None:                                                               
    """Downgrade schema."""                                                          
    op.drop_column("users", "bio")
