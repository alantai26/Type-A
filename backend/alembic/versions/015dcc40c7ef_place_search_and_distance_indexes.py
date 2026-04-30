"""place search and distance indexes

Revision ID: 015dcc40c7ef
Revises: 9a5cecfca606
Create Date: 2026-04-29 23:36:52.414008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '015dcc40c7ef'
down_revision: Union[str, Sequence[str], None] = '9a5cecfca606'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:                                                                                                                 
    # Enable extensions. IF NOT EXISTS is idempotent — safe if someone re-runs.
    op.execute("CREATE EXTENSION IF NOT EXISTS cube")                                                                                  
    op.execute("CREATE EXTENSION IF NOT EXISTS earthdistance")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")                                                                               
                                                                                                                                         
    # GIST index over earth-points. Lets distance queries skip the full table scan.                                                    
    op.execute(                                                                                                                        
        "CREATE INDEX places_earth_idx ON places "                                                                                     
        "USING gist (ll_to_earth(latitude, longitude))"
    )                                                                                                                                  
  
    # GIN trigram index on name. Powers fuzzy + substring search via pg_trgm.                                                          
    op.execute( 
        "CREATE INDEX places_name_trgm_idx ON places "                                                                                 
        "USING gin (name gin_trgm_ops)"
    )                    

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS places_name_trgm_idx")
    op.execute("DROP INDEX IF EXISTS places_earth_idx")
    # Intentionally do NOT drop extensions — they're database-wide and other                                                           
    # migrations or future features may depend on them. Dropping is destructive.
