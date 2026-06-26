import requests
from datetime import datetime, timedelta, timezone
from core.db.database import get_supabase_client


async def sync_ym_returns(shop: dict):
    api_key = shop.get("ym_token")
    campaign_id = shop.get("ym_campaign_id")
    shop_id = shop["id"]
    days = 60

    today = datetime.now(tz=timezone.utc)
    past = today - timedelta(days=days)
    to_date = today.strftime("%Y-%m-%d")
    from_date = past.strftime("%Y-%m-%d")

    all_returns = []
    page_token = ""

    while True:
        url = (
            f"https://api.partner.market.yandex.ru/v2/campaigns/{campaign_id}/returns"
            f"?fromDate={from_date}&toDate={to_date}&limit=100"
        )
        if page_token:
            url += f"&pageToken={page_token}"

        resp = requests.get(url, headers={"Api-Key": api_key}, timeout=30)
        if resp.status_code != 200:
            return {"error": resp.text, "status_code": resp.status_code, "added": 0}

        data = resp.json()
        result = data.get("result") or {}
        page_returns = result.get("returns") or []
        all_returns.extend(page_returns)

        paging = result.get("paging") or {}
        page_token = paging.get("nextPageToken", "")
        if not page_token:
            break

    rows = [
        {
            "shop_id":                  shop_id,
            "ym_return_id":             item.get("id"),
            "order_id":                 item.get("orderId"),
            "return_type":              item.get("returnType"),
            "shipment_status":          item.get("shipmentStatus"),
            "refund_status":            item.get("refundStatus"),
            "creation_date":            item.get("creationDate"),
            "update_date":              item.get("updateDate"),
            "pickup_till_date":         item.get("pickupTillDate"),
            "amount":                   (item.get("amount") or {}).get("value"),
            "currency":                 (item.get("amount") or {}).get("currencyId"),
            "shipment_recipient_type":  item.get("shipmentRecipientType"),
            "logistic_point":           (item.get("logisticPickupPoint") or {}).get("name"),
            "items":                    item.get("items"),
            "synced_at":                datetime.now(tz=timezone.utc).isoformat(),
        }
        for item in all_returns
        if item.get("id")
    ]

    client = await get_supabase_client()

    count_res = await client.table("returns_ym").select("id", count="exact").eq("shop_id", shop_id).execute()
    db_before = count_res.count or 0

    if not rows:
        return {"db_before": db_before, "api_fetched": len(all_returns), "added": 0, "updated": 0}

    incoming_ids = [r["ym_return_id"] for r in rows]
    existing_res = await client.table("returns_ym").select("ym_return_id").eq("shop_id", shop_id).in_("ym_return_id", incoming_ids).execute()
    existing_ids = {r["ym_return_id"] for r in (existing_res.data or [])}

    added_count   = sum(1 for r in rows if r["ym_return_id"] not in existing_ids)
    updated_count = sum(1 for r in rows if r["ym_return_id"] in existing_ids)

    await client.table("returns_ym").upsert(rows, on_conflict="ym_return_id,shop_id").execute()

    return {
        "db_before":   db_before,
        "api_fetched": len(all_returns),
        "added":       added_count,
        "updated":     updated_count,
    }
