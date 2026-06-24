from fastapi import APIRouter, Depends, HTTPException
from webapp.backend.auth import get_current_user
from core.db.database import get_db_connection, get_sqlite_conn
import re

router = APIRouter()

async def check_admin(user_id: str = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        profile = await conn.fetchrow("SELECT is_admin FROM public.profiles WHERE id = $1", user_id)
        if not profile or not profile['is_admin']:
            raise HTTPException(status_code=403, detail="Admin access required")
        return user_id
    finally:
        await conn.close()

@router.get("/users")
async def list_users(admin_id: str = Depends(check_admin)):
    conn = await get_db_connection()
    try:
        users = await conn.fetch("""
            SELECT p.*, (SELECT COUNT(*) FROM public.shops WHERE user_id = p.id) as shop_count
            FROM public.profiles p
        """)
        return [dict(u) for u in users]
    finally:
        await conn.close()

@router.get("/user/{user_id}/shops")
async def get_user_shops(user_id: str, admin_id: str = Depends(check_admin)):
    # Validate user_id to prevent injection in constructed table names
    if not re.match(r'^[a-f0-9\-]{36}$', user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    conn = await get_db_connection()
    try:
        shops = await conn.fetch("SELECT * FROM public.shops WHERE user_id = $1", user_id)

        results = []
        db_sqlite = get_sqlite_conn()
        cursor = db_sqlite.cursor()

        for shop in shops:
            shop_dict = dict(shop)
            prefix = user_id.replace("-", "")[:12]
            marketplace = shop['marketplace']
            # Whitelist marketplaces
            if marketplace not in ['wb', 'ozon', 'ym']:
                continue

            table_name = f"{prefix}_returns_{marketplace}"

            row_count = 0
            try:
                # Still dynamic but heavily constrained by regex and whitelist
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
            except:
                pass

            shop_dict['row_count'] = row_count
            results.append(shop_dict)

        db_sqlite.close()
        return results
    finally:
        await conn.close()
