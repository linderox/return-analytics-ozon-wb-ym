import argparse
import asyncio

async def run_ym_returns(api_key, campaign_id, shop_id):
    from webapp.backend.services.sync_ym import sync_ym_returns
    shop = {"ym_token": api_key, "ym_campaign_id": campaign_id, "id": shop_id}
    result = await sync_ym_returns(shop)
    print(f"YM sync complete: {result}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--shop-id", required=True)
    args = parser.parse_args()

    asyncio.run(run_ym_returns(args.api_key, args.campaign_id, args.shop_id))
