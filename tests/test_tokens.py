import pytest
import httpx
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# Standardized Marketplace Credentials
WB_TOKEN = os.getenv("WB_TOKEN")
YM_API_KEY = os.getenv("YM_TOKEN")
YM_CAMPAIGN_ID = os.getenv("YM_CLIENT_ID")
OZON_CLIENT_ID = os.getenv("OZON_CLIENT_ID")
OZON_API_KEY = os.getenv("OZON_CLIENT_SECRET")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_wb_token_validation():
    """Test actual WB token."""
    if not WB_TOKEN:
        pytest.skip("WB_TOKEN not provided")

    today = datetime.now(timezone.utc)
    past = today - timedelta(days=2)
    url = f"https://seller-analytics-api.wildberries.ru/api/v1/analytics/goods-return?dateFrom={past.strftime('%Y-%m-%d')}&dateTo={today.strftime('%Y-%m-%d')}"

    async with httpx.AsyncClient() as http:
        resp = await http.get(url, headers={"Authorization": WB_TOKEN})
        assert resp.status_code in (200, 400)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_ym_token_validation():
    """Test actual YM token."""
    if not YM_API_KEY or not YM_CAMPAIGN_ID:
        pytest.skip("YM_TOKEN or YM_CLIENT_ID not provided")

    url = f"https://api.partner.market.yandex.ru/v2/campaigns/{YM_CAMPAIGN_ID}/returns?limit=1"
    async with httpx.AsyncClient() as http:
        resp = await http.get(url, headers={"Api-Key": YM_API_KEY})
        assert resp.status_code == 200

@pytest.mark.integration
@pytest.mark.asyncio
async def test_ozon_token_validation():
    """Test Ozon token."""
    if not OZON_CLIENT_ID or not OZON_API_KEY:
        pytest.skip("OZON_CLIENT_ID or OZON_CLIENT_SECRET not provided")

    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    past_21 = yesterday - timedelta(days=21)

    url = "https://api-seller.ozon.ru/v1/returns/list"
    payload = {
        "filter": {
            "logistic_return_date": {
                "time_from": past_21.strftime("%Y-%m-%dT00:00:00Z"),
                "time_to": yesterday.strftime("%Y-%m-%dT23:59:59Z")
            }
        },
        "limit": 1
    }
    headers = {
        "Client-Id": str(OZON_CLIENT_ID),
        "Api-Key": str(OZON_API_KEY),
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as http:
        resp = await http.post(url, json=payload, headers=headers)
        assert resp.status_code not in (401, 403)
