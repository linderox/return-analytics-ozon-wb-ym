from fastapi import APIRouter, Depends, HTTPException
from webapp.backend.auth import get_current_user
from core.db.database import get_supabase_client, get_sqlite_conn
from webapp.backend.services.sync_wb import sync_wb_returns
from webapp.backend.services.sync_ozon import sync_ozon_returns
from webapp.backend.services.sync_ym import sync_ym_returns
from uuid import UUID
from datetime import datetime, timezone

router = APIRouter()

@router.post("/sync/{shop_id}")
async def sync_shop(shop_id: UUID, user_id: str = Depends(get_current_user)):
    client = await get_supabase_client()
    shop_result = await client.table('shops').select('*').eq('id', str(shop_id)).eq('user_id', user_id).maybe_single().execute()
    if shop_result.data is None:
        raise HTTPException(status_code=404, detail="Shop not found")

    shop = shop_result.data
    marketplace = shop['marketplace']
    if marketplace == 'wb':
        result = await sync_wb_returns(shop, user_id)
    elif marketplace == 'ozon':
        result = await sync_ozon_returns(shop, user_id)
    elif marketplace == 'ym':
        result = await sync_ym_returns(shop, user_id)
    else:
        raise HTTPException(status_code=400, detail="Unsupported marketplace")

    await client.table('shops').update({'last_synced_at': datetime.now(timezone.utc).isoformat()}).eq('id', str(shop_id)).execute()
    return result

@router.get("/{marketplace}")
async def get_returns(marketplace: str, user_id: str = Depends(get_current_user)):
    if marketplace not in ("ozon", "wb", "ym"):
        raise HTTPException(status_code=400, detail="Unsupported marketplace")

    prefix = user_id.replace("-", "")[:12]
    table_name = f"{prefix}_returns_{marketplace}"

    try:
        db = get_sqlite_conn()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                return []
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY synced_at DESC LIMIT 100")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Storage unavailable: {str(e)}")
