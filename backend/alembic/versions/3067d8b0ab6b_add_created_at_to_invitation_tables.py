"""add created_at to invitation tables

Revision ID: 3067d8b0ab6b
Revises: fe0d54be86d0
Create Date: 2026-05-03 20:47:32.678321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3067d8b0ab6b'
down_revision: Union[str, Sequence[str], None] = 'fe0d54be86d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:                                      
    """Upgrade schema."""                                   
    op.add_column(                                          
        "event_invitations",                              
        sa.Column(                                          
            "created_at",              
            sa.DateTime(timezone=True),                   
            nullable=False,            
            server_default=sa.text("now()"),                
        ),                     
    )                                                       
    op.add_column(                     
        "outing_invitations",                             
        sa.Column(                                          
            "created_at",              
            sa.DateTime(timezone=True),                     
            nullable=False,            
            server_default=sa.text("now()"),              
        ),   
    )
                                                              
                            
def downgrade() -> None:                                    
    """Downgrade schema."""            
    op.drop_column("outing_invitations", "created_at")    
    op.drop_column("event_invitations", "created_at")