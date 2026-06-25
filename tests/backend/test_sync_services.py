import pytest
from unittest.mock import MagicMock, patch
from webapp.backend.services.sync_wb import sync_wb_returns
import asyncio
import sqlite3
import os

class MockConnWrapper:
    def __init__(self, conn):
        self.conn = conn
    def cursor(self):
        return self.conn.cursor()
    def commit(self):
        return self.conn.commit()
    def close(self):
        pass # Don't actually close

@pytest.mark.asyncio
async def test_sync_wb_mock():
    # Simulated data from WB API
    mock_data = [
        {
            "srid": "test_srid_1",
            "orderDt": "2026-06-20",
            "brand": "TestBrand",
            "status": "Выдано"
        }
    ]

    # Use a real in-memory SQLite for testing logic without disk IO
    test_db = sqlite3.connect(":memory:")
    test_db.row_factory = sqlite3.Row
    wrapper = MockConnWrapper(test_db)

    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response

        shop = {"wb_token": "fake_token"}
        user_id = "testuserid"

        from core.db.database import ensure_returns_table
        with patch("core.db.database.get_sqlite_conn", return_value=wrapper):
            await ensure_returns_table(user_id, "wb")

        with patch("webapp.backend.services.sync_wb.get_sqlite_conn", return_value=wrapper):
            result = await sync_wb_returns(shop, user_id)
            assert result["added"] == 1

            cursor = test_db.cursor()
            cursor.execute("SELECT * FROM testuserid_returns_wb")
            row = cursor.fetchone()
            assert row["srid"] == "test_srid_1"
            assert row["brand"] == "TestBrand"

    test_db.close()
