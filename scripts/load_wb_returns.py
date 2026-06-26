"""
Standalone script: fetch WB returns and load to Supabase.
Usage:
    python scripts/load_wb_returns.py [--days 30] [--dry-run]

Reads WB_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY from .env
Prints raw WB API response structure so you can see exactly what the API returns.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

WB_TOKEN = os.getenv("WB_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# The shop_id to assign rows to (copy from the admin UI URL or Supabase shops table)
SHOP_ID = os.getenv("WB_SHOP_ID", "6fa0f63d-d091-4821-a986-4001e8b3f9f8")


def get_token_from_supabase(shop_id: str) -> str:
    """Pull wb_token directly from the shops table — more reliable than .env."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = client.table("shops").select("wb_token").eq("id", shop_id).maybe_single().execute()
    if result.data and result.data.get("wb_token"):
        token = result.data["wb_token"]
        print(f"[token] loaded from Supabase shops table (len={len(token)})")
        return token
    return ""


def fetch_wb_returns(token: str, days: int) -> tuple[list, dict]:
    today = datetime.now(tz=timezone.utc)
    past = today - timedelta(days=days)
    url = (
        "https://seller-analytics-api.wildberries.ru/api/v1/analytics/goods-return"
        f"?dateFrom={past.strftime('%Y-%m-%d')}&dateTo={today.strftime('%Y-%m-%d')}"
    )
    print(f"[WB] GET {url}")
    resp = requests.get(url, headers={"Authorization": token}, timeout=30)
    print(f"[WB] status={resp.status_code}")

    raw = resp.json()

    # Print top-level keys so we can see the real structure
    if isinstance(raw, dict):
        print(f"[WB] response keys: {list(raw.keys())}")
        for key, val in raw.items():
            if isinstance(val, list):
                print(f"[WB]   [{key}] = list of {len(val)} items")
                if val:
                    print(f"[WB]   [{key}][0] keys: {list(val[0].keys()) if isinstance(val[0], dict) else type(val[0])}")
            else:
                print(f"[WB]   [{key}] = {repr(val)[:120]}")
    elif isinstance(raw, list):
        print(f"[WB] response is a list of {len(raw)} items")
        if raw:
            print(f"[WB] [0] keys: {list(raw[0].keys()) if isinstance(raw[0], dict) else type(raw[0])}")
    else:
        print(f"[WB] unexpected response type: {type(raw)}")

    if resp.status_code != 200:
        return [], raw

    # Try to extract the list — WB nests differently depending on the endpoint
    items: list = []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        # Try common nesting patterns
        for key in ("report", "data", "result", "returns", "items", "rows"):
            candidate = raw.get(key)
            if isinstance(candidate, list):
                print(f"[WB] found items under key '{key}': {len(candidate)} records")
                items = candidate
                break
            elif isinstance(candidate, dict):
                # one more level deep, e.g. data.returns
                for subkey in ("returns", "items", "rows", "data"):
                    sub = candidate.get(subkey)
                    if isinstance(sub, list):
                        print(f"[WB] found items under '{key}.{subkey}': {len(sub)} records")
                        items = sub
                        break
                if items:
                    break
        if not items:
            print("[WB] WARNING: could not locate items list in response — printing full response:")
            print(json.dumps(raw, ensure_ascii=False, indent=2)[:3000])

    return items, raw


def build_rows(items: list, shop_id: str) -> list[dict]:
    rows = []
    skipped = 0
    for item in items:
        srid = item.get("srid") or item.get("Srid") or item.get("SRID")
        if not srid:
            skipped += 1
            continue
        rows.append({
            "shop_id":            shop_id,
            "srid":               srid,
            "order_dt":           item.get("orderDt") or item.get("order_dt"),
            "nm_id":              item.get("nmId") or item.get("nm_id"),
            "brand":              item.get("brand"),
            "subject_name":       item.get("subjectName") or item.get("subject_name"),
            "tech_size":          item.get("techSize") or item.get("tech_size"),
            "barcode":            item.get("barcode"),
            "shk_id":             item.get("shkId") or item.get("shk_id"),
            "return_type":        item.get("returnType") or item.get("return_type"),
            "reason":             item.get("reason"),
            "status":             item.get("status"),
            "is_status_active":   bool(item.get("isStatusActive") or item.get("is_status_active")),
            "ready_to_return_dt": item.get("readyToReturnDt") or item.get("ready_to_return_dt"),
            "completed_dt":       item.get("completedDt") or item.get("completed_dt"),
            "expired_dt":         item.get("expiredDt") or item.get("expired_dt"),
            "dst_office_id":      item.get("dstOfficeId") or item.get("dst_office_id"),
            "dst_office_address": item.get("dstOfficeAddress") or item.get("dst_office_address"),
            "order_id":           item.get("orderId") or item.get("order_id"),
            "sticker_id":         item.get("stickerId") or item.get("sticker_id"),
            "synced_at":          datetime.now(tz=timezone.utc).isoformat(),
        })
    if skipped:
        print(f"[build] skipped {skipped} items without srid")
    return rows


def upsert_to_supabase(rows: list[dict]) -> int:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    batch = 500
    total = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        result = client.table("returns_wb").upsert(
            chunk, on_conflict="srid,shop_id"
        ).execute()
        total += len(result.data or chunk)
        print(f"[supabase] upserted batch {i//batch + 1}: {len(chunk)} rows")
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=90, help="How many days back to fetch (default: 90)")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and parse but do not write to Supabase")
    parser.add_argument("--shop-id", default=SHOP_ID, help="Supabase shop UUID to assign rows to")
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set in .env")
        sys.exit(1)

    # Prefer token from Supabase shops table; fall back to .env WB_TOKEN
    token = get_token_from_supabase(args.shop_id) or WB_TOKEN
    if not token:
        print("ERROR: no wb_token found in Supabase shops table and WB_TOKEN not set in .env")
        sys.exit(1)

    # Warn if the .env token is being used and looks malformed (missing dot before signature)
    if token == WB_TOKEN:
        parts = token.split(".")
        if len(parts) != 3:
            print(f"WARNING: WB_TOKEN looks malformed — expected 3 JWT segments, got {len(parts)}")

    print(f"Shop ID : {args.shop_id}")
    print(f"Days    : {args.days}")
    print(f"Dry run : {args.dry_run}")
    print()

    items, _raw = fetch_wb_returns(token, args.days)
    print(f"\n[parse] total items extracted: {len(items)}")

    if not items:
        print("\nNo items returned. The WB account may have no returns in this period,")
        print("or the API key lacks the 'Analytics' permission scope.")
        sys.exit(0)

    # Show first item for inspection
    if items:
        print(f"\n[parse] first item sample:\n{json.dumps(items[0], ensure_ascii=False, indent=2)}")

    rows = build_rows(items, args.shop_id)
    print(f"\n[build] rows ready to upsert: {len(rows)}")

    if args.dry_run:
        print("\n[dry-run] skipping Supabase write.")
        sys.exit(0)

    inserted = upsert_to_supabase(rows)
    print(f"\n[done] {inserted} rows written to returns_wb in Supabase.")


if __name__ == "__main__":
    main()
