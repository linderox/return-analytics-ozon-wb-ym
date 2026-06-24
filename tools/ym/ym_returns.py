import argparse
import asyncio
from core.db.database import ensure_returns_table, get_sqlite_conn

async def run_ym_returns(api_key, campaign_id, user_id):
    from webapp.backend.services.sync_ym import sync_ym_returns
    shop = {"ym_client_id": api_key, "ym_campaign_id": campaign_id}
    result = await sync_ym_returns(shop, user_id, None)
    print(f"YM sync complete: {result}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--user-id", default="admin-cli-user")
    args = parser.parse_args()

    asyncio.run(run_ym_returns(args.api_key, args.campaign_id, args.user_id))
