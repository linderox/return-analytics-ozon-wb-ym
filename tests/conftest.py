import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
import os

# --- Mocks for Supabase ---

class MockQueryChain:
    def __init__(self, data=None, error=None):
        self._data = data
        self._error = error
        self._inserted = None

    def select(self, *args, **kwargs): return self
    def eq(self, *args, **kwargs): return self
    def order(self, *args, **kwargs): return self
    def limit(self, *args, **kwargs): return self
    def maybe_single(self): return self
    def single(self): return self
    def insert(self, data):
        self._inserted = data if isinstance(data, list) else [data]
        return self
    def update(self, data):
        self._inserted = data if isinstance(data, list) else [data]
        return self
    def delete(self): return self
    def upsert(self, data, **kwargs):
        self._inserted = data if isinstance(data, list) else [data]
        return self

    async def execute(self):
        result = MagicMock()
        result.data = self._inserted if self._inserted is not None else self._data
        result.error = self._error
        return result

class MockSupabaseClient:
    def __init__(self):
        self._responses = {}

    def set_response(self, table, data):
        self._responses[table] = data

    def table(self, name):
        return MockQueryChain(self._responses.get(name))

# --- Fixtures ---

@pytest.fixture
def app():
    from webapp.backend.main import app as fastapi_app
    # Reset dependency overrides before each test
    fastapi_app.dependency_overrides = {}
    return fastapi_app

@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_supabase(monkeypatch):
    mock = MockSupabaseClient()
    import core.db.database
    # Patch the internal _supabase_client if it exists or get_supabase_client
    monkeypatch.setattr(core.db.database, "_supabase_client", mock)

    # Also patch the function to return the mock directly
    async def mock_get_client():
        return mock
    monkeypatch.setattr(core.db.database, "get_supabase_client", mock_get_client)

    return mock

@pytest.fixture
def authenticated_user(app):
    from webapp.backend.auth import get_current_user
    user_id = "test-user-id"
    app.dependency_overrides[get_current_user] = lambda: user_id
    return user_id

@pytest.fixture
def authenticated_admin(app, mock_supabase):
    from webapp.backend.auth import get_current_user
    from webapp.backend.routers.admin import check_admin

    admin_id = "test-admin-id"
    app.dependency_overrides[get_current_user] = lambda: admin_id
    app.dependency_overrides[check_admin] = lambda: admin_id

    # Ensure check_admin's internal DB check also passes
    mock_supabase.set_response('profiles', {'id': admin_id, 'is_admin': True})

    return admin_id
