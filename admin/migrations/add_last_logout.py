"""Add last_logout column to users table

Revision ID: add_last_logout
Revises: 
Create Date: 2025-09-17

"""

# revision identifiers
revision = 'add_last_logout'
down_revision = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from datetime import datetime

def upgrade():
    """Add last_logout column to users table"""
    try:
        # last_logout カラムを追加
        op.add_column('users', sa.Column('last_logout', sa.DateTime(), nullable=True))
        print("Successfully added last_logout column to users table")
    except Exception as e:
        print(f"Error adding last_logout column: {e}")
        pass

def downgrade():
    """Remove last_logout column from users table"""
    try:
        op.drop_column('users', 'last_logout')
        print("Successfully removed last_logout column from users table")
    except Exception as e:
        print(f"Error removing last_logout column: {e}")
        pass