"""
Alembic migration for api_keys table
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('identifier', sa.String, nullable=False),
        sa.Column('api_key_hash', sa.String, nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('expires_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.String, nullable=True),
        sa.Column('tenant_id', sa.String, nullable=True),
        sa.Column('scopes', sa.String, nullable=True),  # JSON or comma-separated
        sa.Column('rate_limit', sa.Integer, nullable=True),
    )

def downgrade():
    op.drop_table('api_keys')
