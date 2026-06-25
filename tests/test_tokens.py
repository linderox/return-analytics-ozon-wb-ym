import pytest
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# Sourced from env or *.gs files
WB_TOKEN = os.getenv("WB_TOKEN")
YM_TOKEN = os.getenv("YM_CLIENT_ID") # YM_CLIENT_ID is used as the Api-Key in some scripts
YM_CAMPAIGN_ID = os.getenv("YM_CAMPAIGN_ID")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_wb_token_validation():
    """Test actual WB token."""
    if not WB_TOKEN:
        pytest.skip("WB_TOKEN not provided")
    url = "https://seller-analytics-api.wildberries.ru/api/v1/analytics/goods-return?dateFrom=2024-01-01&dateTo=2024-01-02"
    async with httpx.AsyncClient() as http:
        resp = await http.get(url, headers={"Authorization": WB_TOKEN})
        assert resp.status_code in (200, 400)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_ym_token_validation():
    """Test actual YM token."""
    if not YM_TOKEN or not YM_CAMPAIGN_ID:
        pytest.skip("YM_CLIENT_ID or YM_CAMPAIGN_ID not provided")
    url = f"https://api.partner.market.yandex.ru/v2/campaigns/{YM_CAMPAIGN_ID}/returns?limit=1"
    async with httpx.AsyncClient() as http:
        resp = await http.get(url, headers={"Api-Key": YM_TOKEN})
        assert resp.status_code == 200

@pytest.mark.integration
@pytest.mark.asyncio
async def test_ozon_token_validation():
    """Test Ozon token."""
    client_id = os.getenv("OZON_CLIENT_ID")
    api_key = os.getenv("OZON_CLIENT_SECRET") # Client secret is used as Api-Key in Ozon
    if not client_id or not api_key:
        pytest.skip("OZON_CLIENT_ID or OZON_CLIENT_SECRET not provided")

    url = "https://api-seller.ozon.ru/v1/returns/list"
    payload = {
        "filter": {
            "logistic_return_date": {
                "time_from": "2024-01-01T00:00:00Z",
                "time_to": "2024-01-02T00:00:00Z"
            }
        },
        "limit": 1
    }
    headers = {
        "Client-Id": str(client_id),
        "Api-Key": str(api_key),
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as http:
        resp = await http.post(url, json=payload, headers=headers)
        assert resp.status_code not in (401, 403)
