from fastapi import APIRouter, Depends, HTTPException
from webapp.backend.auth import get_current_user
from core.db.database import get_db_connection, get_sqlite_conn
from webapp.backend.services.sync_wb import sync_wb_returns
from webapp.backend.services.sync_ozon import sync_ozon_returns
from webapp.backend.services.sync_ym import sync_ym_returns
from uuid import UUID

router = APIRouter()

@router.post("/sync/{shop_id}")
async def sync_shop(shop_id: UUID, user_id: str = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        shop = await conn.fetchrow("SELECT * FROM public.shops WHERE id = $1 AND user_id = $2", shop_id, user_id)
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")

        marketplace = shop['marketplace']
        if marketplace == 'wb':
            result = await sync_wb_returns(dict(shop), user_id, conn)
        elif marketplace == 'ozon':
            result = await sync_ozon_returns(dict(shop), user_id, conn)
        elif marketplace == 'ym':
            result = await sync_ym_returns(dict(shop), user_id, conn)
        else:
            raise HTTPException(status_code=400, detail="Unsupported marketplace")

        await conn.execute("UPDATE public.shops SET last_synced_at = NOW() WHERE id = $1", shop_id)
        return result
    finally:
        await conn.close()

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
