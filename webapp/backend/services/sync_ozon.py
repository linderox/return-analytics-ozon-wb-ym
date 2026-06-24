import requests
from datetime import datetime, timedelta, timezone
from core.db.database import ensure_returns_table, get_sqlite_conn

async def sync_ozon_returns(shop: dict, user_id: str, conn_supabase):
    client_id = shop.get("ozon_client_id")
    api_key = shop.get("ozon_client_secret")
    days = 60

    now = datetime.now(tz=timezone.utc)
    time_from = (now - timedelta(days=days)).isoformat()
    time_to = now.isoformat()

    all_returns = []
    last_id = 0
    has_next = True

    while has_next:
        body = {
            "filter": {"logistic_return_date": {"time_from": time_from, "time_to": time_to}},
            "limit": 500,
            "last_id": last_id,
        }
        resp = requests.post(
            "https://api-seller.ozon.ru/v1/returns/list",
            json=body,
            headers={"Client-Id": str(client_id), "Api-Key": api_key},
            timeout=30,
        )
        if resp.status_code != 200:
            break

        data = resp.json()
        returns = data.get("returns") or []
        if not returns:
            break

        all_returns.extend(returns)
        has_next = bool(data.get("has_next"))
        last_id = data.get("last_id") or (returns[-1].get("id", 0) if returns else 0)

    table_name = await ensure_returns_table(user_id, "ozon")
    db = get_sqlite_conn()
    cursor = db.cursor()

    for item in all_returns:
        row = {
            "posting_number": item.get("posting_number"),
            "added_at": item.get("added_at"),
            "barcode": item.get("barcode"),
            "clearing_id": item.get("clearing_id"),
            "offer_id": item.get("offer_id"),
            "status": item.get("status"),
            "return_reason": item.get("return_reason"),
            "return_date": item.get("return_date"),
            "received_at": item.get("received_at"),
            "quantity": item.get("quantity"),
            "price": item.get("price"),
            "is_opened": item.get("is_opened")
        }
        keys = list(row.keys())
        values = list(row.values())
        placeholders = ", ".join(["?" for _ in keys])
        cols = ", ".join(keys)
        updates = ", ".join([f"{k} = excluded.{k}" for k in keys if k != 'posting_number'])
        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders}) ON CONFLICT (posting_number) DO UPDATE SET {updates}"
        cursor.execute(query, values)

    db.commit()
    db.close()
    return {"added": len(all_returns)}
