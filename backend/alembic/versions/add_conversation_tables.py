"""add conversation tables

Revision ID: b9c4e7f3a2d6
Revises: a8f9e3d2b1c5
Create Date: 2025-10-17 20:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b9c4e7f3a2d6'
down_revision = 'a8f9e3d2b1c5'  # Latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('project_id', sa.String(length=255), nullable=True),
        sa.Column('phase', sa.Enum(
            'IDEA_SATURATION',
            'NAME_DISCUSSION',
            'TEMPLATE_SELECTION',
            'DATA_GATHERING',
            'GENERATION',
            name='conversationphase'
        ), nullable=False),
        sa.Column('extracted_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('selected_template_id', sa.String(length=255), nullable=True),
        sa.Column('template_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('user_engagement_level', sa.Enum(
            'LOW',
            'MEDIUM',
            'HIGH',
            name='engagementlevel'
        ), nullable=False),
        sa.Column('message_count', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for conversations
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)
    op.create_index(op.f('ix_conversations_project_id'), 'conversations', ['project_id'], unique=False)
    
    # Create foreign keys
    op.create_foreign_key(
        'fk_conversations_user_id',
        'conversations', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_conversations_project_id',
        'conversations', 'projects',
        ['project_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create conversation_messages table
    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('conversation_id', sa.String(length=255), nullable=False),
        sa.Column('sender', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.Enum(
            'TEXT',
            'QUICK_REPLIES',
            'TEMPLATE_SELECTION',
            'THINKING',
            'GENERATION_PROGRESS',
            name='messagetype'
        ), nullable=False),
        sa.Column('quick_replies', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('templates', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('thinking_status', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for messages
    op.create_index(op.f('ix_conversation_messages_conversation_id'), 'conversation_messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_conversation_messages_created_at'), 'conversation_messages', ['created_at'], unique=False)
    
    # Create foreign key
    op.create_foreign_key(
        'fk_conversation_messages_conversation_id',
        'conversation_messages', 'conversations',
        ['conversation_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Drop conversation_messages table
    op.drop_index(op.f('ix_conversation_messages_created_at'), table_name='conversation_messages')
    op.drop_index(op.f('ix_conversation_messages_conversation_id'), table_name='conversation_messages')
    op.drop_table('conversation_messages')
    
    # Drop conversations table
    op.drop_index(op.f('ix_conversations_project_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
    op.drop_table('conversations')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS conversationphase')
    op.execute('DROP TYPE IF EXISTS engagementlevel')
    op.execute('DROP TYPE IF EXISTS messagetype')
