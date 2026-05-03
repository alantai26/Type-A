"""feed_indexes

Revision ID: fe0d54be86d0
Revises: 0fca5c07c957
Create Date: 2026-05-01 23:25:20.099054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe0d54be86d0'
down_revision: Union[str, Sequence[str], None] = '0fca5c07c957'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:                                                                                
    # Composite index powering the friend-feed rating query:
    # WHERE user_id IN (:friend_ids) AND created_at < :before ORDER BY created_at DESC.               
    # Second column gives sorted output for free — no in-memory sort.                                 
    op.execute(
        "CREATE INDEX place_ratings_user_created_idx "                                                
        "ON place_ratings (user_id, created_at DESC)"                                                 
    )
                                                                                                        
    # Same shape for saves.                                                                         
    op.execute(
        "CREATE INDEX saved_places_user_created_idx "
        "ON saved_places (user_id, created_at DESC)"                                                  
    )
                                                                                                        
    # Partial index — only rows the feed reads (rated + completed). Skips                             
    # in-progress/cancelled outings, keeps the index small.
    op.execute(                                                                                       
        "CREATE INDEX outings_creator_completed_idx "                                               
        "ON outings (creator_id, completed_at DESC) "
        "WHERE status = 'completed' AND final_rating IS NOT NULL"                                     
)
                                                                                                        
                                                                                                      
def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS outings_creator_completed_idx")
    op.execute("DROP INDEX IF EXISTS saved_places_user_created_idx")                                  
    op.execute("DROP INDEX IF EXISTS place_ratings_user_created_idx")
