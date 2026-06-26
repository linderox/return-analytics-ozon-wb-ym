import requests
from datetime import datetime, timedelta, timezone
from core.db.database import get_supabase_client


async def sync_ozon_returns(shop: dict):
    client_id = shop.get("ozon_client_id")
    api_key = shop.get("ozon_client_secret")
    shop_id = shop["id"]
    days = 60

    now = datetime.now(tz=timezone.utc)
    time_from = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    time_to = now.strftime("%Y-%m-%dT%H:%M:%SZ")

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
            return {"error": resp.text, "status_code": resp.status_code, "added": 0}

        data = resp.json()
        returns = data.get("returns") or []
        if not returns:
            break

        all_returns.extend(returns)
        has_next = bool(data.get("has_next"))
        last_id = data.get("last_id") or (returns[-1].get("id", 0) if returns else 0)

    now_iso = datetime.now(tz=timezone.utc).isoformat()
    seen = set()
    rows = []
    for item in all_returns:
        pn = item.get("posting_number")
        if not pn or pn in seen:
            continue
        seen.add(pn)

        schema = item.get("schema", "")
        status_name = (item.get("visual") or {}).get("status_name", "")
        status = f"[{schema}] {status_name}" if schema else status_name

        logistic = item.get("logistic") or {}
        product  = item.get("product")  or {}
        price_obj = product.get("price") or {}

        rows.append({
            "shop_id":        shop_id,
            "posting_number": pn,
            "added_at":       now_iso,
            "barcode":        logistic.get("barcode"),
            "clearing_id":    item.get("clearing_id"),
            "offer_id":       product.get("offer_id"),
            "status":         status,
            "return_reason":  item.get("return_reason_name"),
            "return_date":    logistic.get("return_date"),
            "received_at":    item.get("received_at"),
            "quantity":       product.get("quantity"),
            "price":          price_obj.get("price"),
            "is_opened":      bool((item.get("additional_info") or {}).get("is_opened")),
            "synced_at":      now_iso,
        })

    client = await get_supabase_client()

    count_res = await client.table("returns_ozon").select("id", count="exact").eq("shop_id", shop_id).execute()
    db_before = count_res.count or 0

    if not rows:
        return {"db_before": db_before, "api_fetched": len(all_returns), "added": 0, "updated": 0}

    incoming_pns = [r["posting_number"] for r in rows]
    existing_res = await client.table("returns_ozon").select("posting_number").eq("shop_id", shop_id).in_("posting_number", incoming_pns).execute()
    existing_pns = {r["posting_number"] for r in (existing_res.data or [])}

    added_count   = sum(1 for r in rows if r["posting_number"] not in existing_pns)
    updated_count = sum(1 for r in rows if r["posting_number"] in existing_pns)

    await client.table("returns_ozon").upsert(rows, on_conflict="posting_number,shop_id").execute()

    return {
        "db_before":   db_before,
        "api_fetched": len(all_returns),
        "added":       added_count,
        "updated":     updated_count,
    }
