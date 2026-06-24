import argparse
import asyncio
import os
import requests
from core.db.database import ensure_returns_table, get_sqlite_conn, get_db_connection

# Shared fetch logic
async def run_ozon_returns(client_id, api_key, user_id):
    from webapp.backend.services.sync_ozon import sync_ozon_returns
    shop = {"ozon_client_id": client_id, "ozon_client_secret": api_key}
    # For CLI tools we might not have a Supabase connection or we mock it
    result = await sync_ozon_returns(shop, user_id, None)
    print(f"Ozon sync complete: {result}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--user-id", default="admin-cli-user")
    args = parser.parse_args()

    asyncio.run(run_ozon_returns(args.client_id, args.api_key, args.user_id))
