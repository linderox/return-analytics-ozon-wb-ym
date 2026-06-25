import pytest
import os
from core.db.database import get_supabase_client

@pytest.mark.integration
@pytest.mark.asyncio
async def test_profiles_table_structure():
    """Verify profiles table exists and has expected columns."""
    client = await get_supabase_client()
    # We use a limit 0 just to check the table presence and columns
    result = await client.table('profiles').select('*').limit(1).execute()
    # In newer supabase-py versions, result is the data itself or an object without .error
    if result.data:
        row = result.data[0]
        assert 'id' in row
        assert 'plan' in row
        assert 'is_admin' in row

@pytest.mark.integration
@pytest.mark.asyncio
async def test_shops_table_structure():
    """Verify shops table exists and has expected columns."""
    client = await get_supabase_client()
    result = await client.table('shops').select('*').limit(1).execute()
    if result.data:
        row = result.data[0]
        assert 'id' in row
        assert 'user_id' in row
        assert 'marketplace' in row
        assert 'name' in row
        # Note: Some columns might be missing if the user hasn't run the fix_schema.sql
        # This test will help identify what's missing.

@pytest.mark.integration
@pytest.mark.asyncio
async def test_subscriptions_table_structure():
    """Verify subscriptions table exists."""
    client = await get_supabase_client()
    result = await client.table('subscriptions').select('*').limit(1).execute()
    assert result.data is not None
