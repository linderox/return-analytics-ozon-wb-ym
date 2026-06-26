import requests
from datetime import datetime, timedelta, timezone
from core.db.database import get_supabase_client


async def sync_wb_returns(shop: dict):
    token = shop.get("wb_token")
    shop_id = shop["id"]
    days = 30
    today = datetime.now(tz=timezone.utc)
    past = today - timedelta(days=days)

    url = (
        f"https://seller-analytics-api.wildberries.ru/api/v1/analytics/goods-return"
        f"?dateFrom={past.strftime('%Y-%m-%d')}&dateTo={today.strftime('%Y-%m-%d')}"
    )
    resp = requests.get(url, headers={"Authorization": token}, timeout=30)
    if resp.status_code != 200:
        return {"error": resp.text, "status_code": resp.status_code}

    data = resp.json()
    items = data if isinstance(data, list) else data.get("report") or data.get("data") or []

    rows = [
        {
            "shop_id":             shop_id,
            "srid":                item.get("srid"),
            "order_dt":            item.get("orderDt"),
            "nm_id":               item.get("nmId"),
            "brand":               item.get("brand"),
            "subject_name":        item.get("subjectName"),
            "tech_size":           item.get("techSize"),
            "barcode":             item.get("barcode"),
            "shk_id":              item.get("shkId"),
            "return_type":         item.get("returnType"),
            "reason":              item.get("reason"),
            "status":              item.get("status"),
            "is_status_active":    bool(item.get("isStatusActive")),
            "ready_to_return_dt":  item.get("readyToReturnDt"),
            "completed_dt":        item.get("completedDt"),
            "expired_dt":          item.get("expiredDt"),
            "dst_office_id":       item.get("dstOfficeId"),
            "dst_office_address":  item.get("dstOfficeAddress"),
            "order_id":            item.get("orderId"),
            "sticker_id":          item.get("stickerId"),
            "synced_at":           datetime.now(tz=timezone.utc).isoformat(),
        }
        for item in items
        if item.get("srid")
    ]

    client = await get_supabase_client()

    # Count existing rows in DB for this shop
    count_res = await client.table("returns_wb").select("id", count="exact").eq("shop_id", shop_id).execute()
    db_before = count_res.count or 0

    if not rows:
        return {"db_before": db_before, "api_fetched": len(items), "added": 0, "updated": 0}

    # Check which incoming srids already exist (to split new vs updated)
    incoming_srids = [r["srid"] for r in rows]
    existing_res = await client.table("returns_wb").select("srid").eq("shop_id", shop_id).in_("srid", incoming_srids).execute()
    existing_srids = {r["srid"] for r in (existing_res.data or [])}

    added_count   = sum(1 for r in rows if r["srid"] not in existing_srids)
    updated_count = sum(1 for r in rows if r["srid"] in existing_srids)

    await client.table("returns_wb").upsert(rows, on_conflict="srid,shop_id").execute()

    return {
        "db_before":   db_before,
        "api_fetched": len(items),
        "added":       added_count,
        "updated":     updated_count,
    }
