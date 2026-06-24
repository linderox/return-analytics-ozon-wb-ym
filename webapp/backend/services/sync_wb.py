import requests
from datetime import datetime, timedelta, timezone
from core.db.database import ensure_returns_table, get_sqlite_conn

async def sync_wb_returns(shop: dict, user_id: str, conn_supabase):
    token = shop.get("wb_token")
    days = 60 # Extended window for history
    today = datetime.now(tz=timezone.utc)
    past = today - timedelta(days=days)

    url = f"https://seller-analytics-api.wildberries.ru/api/v1/analytics/goods-return?dateFrom={past.strftime('%Y-%m-%d')}&dateTo={today.strftime('%Y-%m-%d')}"

    resp = requests.get(url, headers={"Authorization": token}, timeout=30)
    if resp.status_code != 200:
        return {"error": resp.text, "status_code": resp.status_code}

    data = resp.json()
    items = data if isinstance(data, list) else data.get("data", [])

    table_name = await ensure_returns_table(user_id, "wb")

    db = get_sqlite_conn()
    cursor = db.cursor()

    added = 0
    for item in items:
        keys = list(item.keys())
        values = list(item.values())
        placeholders = ", ".join(["?" for _ in keys])
        cols = ", ".join(keys)
        updates = ", ".join([f"{k} = excluded.{k}" for k in keys if k != 'srid'])

        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders}) ON CONFLICT (srid) DO UPDATE SET {updates}"
        cursor.execute(query, values)
        added += 1

    db.commit()
    db.close()
    return {"added": added}
