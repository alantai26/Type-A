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
      op.execute("UPDATE outings SET status = 'planning_in_progress' WHERE status = 'draft'")
      op.execute("UPDATE events  SET status = 'planning_in_progress' WHERE status = 'draft'")                                             
                                                                                                                                          
      op.drop_constraint('check_outing_status', 'outings', type_='check')                                                                 
      op.create_check_constraint(                                                                                                         
          'check_outing_status', 'outings',                                                                                               
          "status IN ('planning_in_progress', 'confirmed', 'completed', 'cancelled')"
      )                                                                                                                                   
                  
      op.drop_constraint('check_event_status', 'events', type_='check')                                                                   
      op.create_check_constraint(
          'check_event_status', 'events',                                                                                                 
          "status IN ('planning_in_progress', 'confirmed', 'completed', 'cancelled')"
      )           


def downgrade() -> None:
      """Downgrade schema."""
      op.drop_constraint('check_outing_status', 'outings', type_='check')
      op.create_check_constraint(                                                                                                         
          'check_outing_status', 'outings',
          "status IN ('draft', 'confirmed', 'completed', 'cancelled')"                                                                    
      )                                                                                                                                   
      op.drop_constraint('check_event_status', 'events', type_='check')
      op.create_check_constraint(                                                                                                         
          'check_event_status', 'events',                                                                                                 
          "status IN ('draft', 'confirmed', 'completed', 'cancelled')"
      )                                                                                                                                   
      op.execute("UPDATE outings SET status = 'draft' WHERE status = 'planning_in_progress'")
      op.execute("UPDATE events  SET status = 'draft' WHERE status = 'planning_in_progress'")   