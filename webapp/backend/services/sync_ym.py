import requests
from datetime import datetime, timedelta, timezone
from core.db.database import ensure_returns_table, get_sqlite_conn
import json

async def sync_ym_returns(shop: dict, user_id: str):
    api_key = shop.get("ym_client_id")
    campaign_id = shop.get("ym_campaign_id")
    days = 60

    today = datetime.now(tz=timezone.utc)
    past = today - timedelta(days=days)
    to_date = today.strftime("%Y-%m-%d")
    from_date = past.strftime("%Y-%m-%d")

    all_returns = []
    page_token = ""

    while True:
        url = f"https://api.partner.market.yandex.ru/v2/campaigns/{campaign_id}/returns?fromDate={from_date}&toDate={to_date}&limit=100"
        if page_token:
            url += f"&pageToken={page_token}"

        resp = requests.get(url, headers={"Api-Key": api_key}, timeout=30)
        if resp.status_code != 200:
            break

        data = resp.json()
        result = data.get("result") or {}
        page_returns = result.get("returns") or []
        all_returns.extend(page_returns)

        paging = result.get("paging") or {}
        page_token = paging.get("nextPageToken", "")
        if not page_token:
            break

    table_name = await ensure_returns_table(user_id, "ym")
    db = get_sqlite_conn()
    cursor = db.cursor()

    for item in all_returns:
        row = {
            "id": item.get("id"),
            "orderId": item.get("orderId"),
            "returnType": item.get("returnType"),
            "shipmentStatus": item.get("shipmentStatus"),
            "refundStatus": item.get("refundStatus"),
            "creationDate": item.get("creationDate"),
            "updateDate": item.get("updateDate"),
            "pickupTillDate": item.get("pickupTillDate"),
            "amount": item.get("amount"),
            "currency": item.get("currency"),
            "shipmentRecipientType": item.get("shipmentRecipientType"),
            "logisticPoint": item.get("logisticPoint"),
            "items": json.dumps(item.get("items"))
        }
        keys = list(row.keys())
        values = list(row.values())
        placeholders = ", ".join(["?" for _ in keys])
        cols = ", ".join([f'"{k}"' for k in keys])
        updates = ", ".join([f'"{k}" = excluded."{k}"' for k in keys if k != 'id'])
        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders}) ON CONFLICT (id) DO UPDATE SET {updates}"
        cursor.execute(query, values)

    db.commit()
    db.close()
    return {"added": len(all_returns)}
