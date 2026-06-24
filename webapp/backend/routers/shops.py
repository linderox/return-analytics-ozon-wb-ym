from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from webapp.backend.auth import get_current_user
from core.db.database import get_db_connection

router = APIRouter()

@router.get("/")
async def list_shops(user_id: str = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        shops = await conn.fetch("SELECT * FROM public.shops WHERE user_id = $1", user_id)
        return [dict(s) for s in shops]
    finally:
        await conn.close()

@router.post("/")
async def add_shop(shop_data: dict, user_id: str = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        keys = list(shop_data.keys())
        placeholders = ", ".join([f"${i+2}" for i in range(len(keys))])
        cols = ", ".join(keys)
        query = f"INSERT INTO public.shops (user_id, {cols}) VALUES ($1, {placeholders}) RETURNING *"
        shop = await conn.fetchrow(query, user_id, *shop_data.values())
        return dict(shop)
    finally:
        await conn.close()
