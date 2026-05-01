"""loosen_planning_fields_add_outing_title

Revision ID: 0fca5c07c957
Revises: 015dcc40c7ef
Create Date: 2026-04-30 16:55:00.355329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fca5c07c957'
down_revision: Union[str, Sequence[str], None] = '015dcc40c7ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:                                                                                   
      # Loosen create-time validation: scheduled_for is set during planning,                               
      # not at creation. Confirm-time validators will enforce non-null.                                    
      op.alter_column("outings", "scheduled_for", nullable=True)                                           
      op.alter_column("events", "scheduled_for", nullable=True)                                            
                                                                                                           
      # Outings get a user-facing title. NOT NULL — every outing has one                                   
      # from creation. server_default="" backfills any existing rows so the                                
      # NOT NULL add doesn't fail; we then drop the default so future inserts                              
      # must provide a real title (enforced at the API layer).                                             
      op.add_column(                                                                                       
          "outings",                                                                                       
          sa.Column("title", sa.String(length=255), nullable=False, server_default=""),                    
      )                                                                                                  
      op.alter_column("outings", "title", server_default=None)


def downgrade() -> None:                                                                                 
    op.drop_column("outings", "title")                                                                 
    op.alter_column("events", "scheduled_for", nullable=False)
    op.alter_column("outings", "scheduled_for", nullable=False)     
