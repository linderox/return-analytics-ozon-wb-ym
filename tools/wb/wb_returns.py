import argparse
import asyncio
from core.db.database import ensure_returns_table, get_sqlite_conn

async def run_wb_returns(token, user_id):
    from webapp.backend.services.sync_wb import sync_wb_returns
    shop = {"wb_token": token}
    result = await sync_wb_returns(shop, user_id, None)
    print(f"WB sync complete: {result}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--user-id", default="admin-cli-user")
    args = parser.parse_args()

    asyncio.run(run_wb_returns(args.token, args.user_id))
