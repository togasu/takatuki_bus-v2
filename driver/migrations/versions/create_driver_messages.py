"""Create driver_messages table for driver-admin communication

Revision ID: create_driver_messages
Revises: 
Create Date: 2026-01-13
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_driver_messages'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create driver_messages table"""
    op.create_table('driver_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('driver_username', sa.String(length=100), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('replied', sa.Boolean(), nullable=True),
        sa.Column('reply_message', sa.Text(), nullable=True),
        sa.Column('replied_at', sa.DateTime(), nullable=True),
        sa.Column('replied_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Set default values
    op.execute("UPDATE driver_messages SET priority = 'normal' WHERE priority IS NULL")
    op.execute("UPDATE driver_messages SET is_read = false WHERE is_read IS NULL")
    op.execute("UPDATE driver_messages SET replied = false WHERE replied IS NULL")


def downgrade():
    """Drop driver_messages table"""
    op.drop_table('driver_messages')
