"""
One-time script: insert WB and YM shop credentials from .env into Supabase public.shops.

Usage:
    Fill in the GOOGLE_SHEET_* constants below, then run:
    python insert_shops.py
"""
import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]

WB_TOKEN = os.environ["WB_TOKEN"]
YM_TOKEN = os.environ["YM_TOKEN"]
YM_CAMPAIGN_ID = os.environ["YM_CAMPAIGN_ID"]

# ── Fill in your Google Sheet IDs ─────────────────────────────────────────────
GOOGLE_SHEET_WB   = None   # e.g. "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
GOOGLE_SHEET_YM   = None
GOOGLE_SHEET_OZON = None   # for future use when OZON_CLIENT_ID is added
# ──────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


async def get_admin_user_id(http: httpx.AsyncClient) -> str:
    resp = await http.get(
        f"{SUPABASE_URL}/auth/v1/admin/users",
        headers=HEADERS,
        params={"page": 1, "per_page": 200},
    )
    resp.raise_for_status()
    users = resp.json().get("users", [])
    for u in users:
        if u.get("email") == ADMIN_EMAIL:
            return u["id"]
    raise ValueError(f"User {ADMIN_EMAIL!r} not found in Supabase Auth")


async def insert_shop(http: httpx.AsyncClient, shop: dict):
    # Remove None values — don't send nulls for optional fields
    payload = {k: v for k, v in shop.items() if v is not None}
    resp = await http.post(
        f"{SUPABASE_URL}/rest/v1/shops",
        headers=HEADERS,
        json=payload,
    )
    if resp.status_code not in (200, 201):
        print(f"  ERROR {resp.status_code}: {resp.text}")
        return None
    data = resp.json()
    row = data[0] if data else {}
    print(f"  OK — id={row.get('id')!r}  name={row.get('name')!r}  marketplace={row.get('marketplace')!r}")
    return row


async def main():
    async with httpx.AsyncClient(timeout=15) as http:
        print(f"Looking up admin user: {ADMIN_EMAIL!r} ...")
        user_id = await get_admin_user_id(http)
        print(f"  Found user_id: {user_id}\n")

        shops = [
            {
                "user_id": user_id,
                "marketplace": "wb",
                "name": "Wildberries",
                "wb_token": WB_TOKEN,
                "fulfillment_models": ["FBS", "FBW"],
                "google_sheet_id": GOOGLE_SHEET_WB,
            },
            {
                "user_id": user_id,
                "marketplace": "ym",
                "name": "Яндекс Маркет",
                "ym_token": YM_TOKEN,
                "ym_campaign_id": YM_CAMPAIGN_ID,
                "fulfillment_models": ["FBS", "FBY"],
                "google_sheet_id": GOOGLE_SHEET_YM,
            },
            # Ozon: OZON_CLIENT_ID and OZON_CLIENT_SECRET are empty in .env — add creds and uncomment when ready
            # {
            #     "user_id": user_id,
            #     "marketplace": "ozon",
            #     "name": "Ozon",
            #     "ozon_client_id": os.environ.get("OZON_CLIENT_ID"),
            #     "ozon_client_secret": os.environ.get("OZON_CLIENT_SECRET"),
            #     "fulfillment_models": ["FBS", "FBO"],
            #     "google_sheet_id": GOOGLE_SHEET_OZON,
            # },
        ]

        for shop in shops:
            print(f"Inserting {shop['name']!r} ({shop['marketplace']}) ...")
            await insert_shop(http, shop)

        print("\nDone.")


asyncio.run(main())
