"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('USER', 'ADMIN', name='role'), nullable=False),
        sa.Column('tier', sa.Enum('FREE', 'PRO', 'ULTIMATE', name='tier'), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255)),
        sa.Column('stripe_subscription_id', sa.String(length=255)),
        sa.Column('subscription_status', sa.Enum('ACTIVE', 'PAST_DUE', 'CANCELED', 'INCOMPLETE', name='subscriptionstatus')),
        sa.Column('payment_status', sa.Enum('ACTIVE', 'FAILED', 'GRACE_PERIOD', 'SUSPENDED', name='paymentstatus'), nullable=False),
        sa.Column('generations_used_this_month', sa.Integer(), nullable=False),
        sa.Column('revisions_used_this_month', sa.Integer(), nullable=False),
        sa.Column('usage_reset_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_active_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('stripe_customer_id'),
        sa.UniqueConstraint('stripe_subscription_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'])
    op.create_index(op.f('ix_users_stripe_customer_id'), 'users', ['stripe_customer_id'])
    
    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'ANALYZING', 'GENERATING', 'GENERATED', 'PUBLISHED', 'ARCHIVED', name='projectstatus'), nullable=False),
        sa.Column('subdomain', sa.String(length=255)),
        sa.Column('subdomain_reserved_at', sa.DateTime()),
        sa.Column('subdomain_released_at', sa.DateTime()),
        sa.Column('custom_domain', sa.String(length=255)),
        sa.Column('custom_domain_verified', sa.Boolean(), nullable=False),
        sa.Column('template_id', sa.String(length=255)),
        sa.Column('template_version', sa.String(length=50)),
        sa.Column('generated_data', sa.JSON()),
        sa.Column('html_content', sa.Text()),
        sa.Column('signups_count', sa.Integer(), nullable=False),
        sa.Column('last_signup_at', sa.DateTime()),
        sa.Column('last_exported_at', sa.DateTime()),
        sa.Column('export_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('subdomain'),
        sa.UniqueConstraint('custom_domain')
    )
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'])
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'])
    op.create_index(op.f('ix_projects_subdomain'), 'projects', ['subdomain'])
    op.create_index(op.f('ix_projects_custom_domain'), 'projects', ['custom_domain'])
    
    # Create generations table
    op.create_table('generations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('generation_number', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('NEW', 'REVISION', name='generationtype'), nullable=False),
        sa.Column('template_id', sa.String(length=255), nullable=False),
        sa.Column('template_version', sa.String(length=50), nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=False),
        sa.Column('generated_copy', sa.JSON()),
        sa.Column('images', sa.JSON()),
        sa.Column('status', sa.Enum('PENDING', 'ANALYZING', 'GENERATING_COPY', 'GENERATING_IMAGES', 'ASSEMBLING', 'COMPLETE', 'FAILED', name='generationstatus'), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('llm_cost', sa.Float()),
        sa.Column('image_cost', sa.Float()),
        sa.Column('total_cost', sa.Float()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generations_project_id'), 'generations', ['project_id'])
    op.create_index(op.f('ix_generations_status'), 'generations', ['status'])
    
    # Create signups table
    op.create_table('signups',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signups_project_id'), 'signups', ['project_id'])
    op.create_index(op.f('ix_signups_email'), 'signups', ['email'])
    op.create_index(op.f('ix_signups_created_at'), 'signups', ['created_at'])
    
    # Create exports table
    op.create_table('exports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETE', 'FAILED', 'EXPIRED', name='exportstatus'), nullable=False),
        sa.Column('download_url', sa.String(length=512)),
        sa.Column('file_size_bytes', sa.Integer()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exports_user_id'), 'exports', ['user_id'])
    op.create_index(op.f('ix_exports_status'), 'exports', ['status'])
    
    # Create admin_actions table
    op.create_table('admin_actions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('admin_user_id', sa.String(length=36), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('affected_user_id', sa.String(length=36)),
        sa.Column('affected_project_id', sa.String(length=36)),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('reason', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['admin_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_actions_admin_user_id'), 'admin_actions', ['admin_user_id'])
    op.create_index(op.f('ix_admin_actions_action_type'), 'admin_actions', ['action_type'])
    op.create_index(op.f('ix_admin_actions_created_at'), 'admin_actions', ['created_at'])
    
    # Create moderation_items table
    op.create_table('moderation_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('flagged_reason', sa.String(length=255), nullable=False),
        sa.Column('flagged_content', sa.JSON(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='moderationstatus'), nullable=False),
        sa.Column('reviewed_by', sa.String(length=36)),
        sa.Column('reviewed_at', sa.DateTime()),
        sa.Column('decision', sa.String(length=50)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_moderation_items_status'), 'moderation_items', ['status'])
    op.create_index(op.f('ix_moderation_items_created_at'), 'moderation_items', ['created_at'])
    
    # Create rate_limits table
    op.create_table('rate_limits',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('identifier', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('reset_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rate_limits_identifier'), 'rate_limits', ['identifier'])
    op.create_index(op.f('ix_rate_limits_reset_at'), 'rate_limits', ['reset_at'])


def downgrade() -> None:
    op.drop_table('rate_limits')
    op.drop_table('moderation_items')
    op.drop_table('admin_actions')
    op.drop_table('exports')
    op.drop_table('signups')
    op.drop_table('generations')
    op.drop_table('projects')
    op.drop_table('users')
