import pytest
from fastapi.testclient import TestClient
from webapp.backend.main import app
from webapp.backend.auth import get_current_user
import sqlite3
import os
from unittest.mock import MagicMock, patch, AsyncMock

client = TestClient(app)

# Mock user for authentication
async def mock_get_current_user():
    return "test-user-uuid"

app.dependency_overrides[get_current_user] = mock_get_current_user

# Mock database connection to avoid Supabase dependency during tests
async def mock_get_db_connection():
    mock_conn = AsyncMock()
    # Mock close to be an awaitable
    mock_conn.close = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.fetchrow = AsyncMock(return_value=None)
    return mock_conn

@pytest.fixture(autouse=True)
def mock_db_patch():
    # Patch get_db_connection in all routers
    routers = ["billing", "shops", "profile", "returns", "admin"]
    patches = []
    for r in routers:
        p = patch(f"webapp.backend.routers.{r}.get_db_connection", side_effect=mock_get_db_connection)
        p.start()
        patches.append(p)
    yield
    for p in patches:
        p.stop()

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Marketplace Returns API is running"}

def test_sqlite_integration():
    test_user_id = "test-user-uuid"
    from core.db.database import ensure_returns_table, get_sqlite_conn

    import asyncio
    with patch("core.db.database.SQLITE_DB_PATH", "test_returns.db"):
        table_name = asyncio.run(ensure_returns_table(test_user_id, "wb"))

        db = get_sqlite_conn()
        cursor = db.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        assert cursor.fetchone() is not None
        db.close()
        if os.path.exists("test_returns.db"):
            os.remove("test_returns.db")

def test_billing_create_mock():
    response = client.post("/api/billing/create?plan=basic")
    assert response.status_code == 200
    data = response.json()
    assert "payment_id" in data
    assert "sbp_qr_code" in data
