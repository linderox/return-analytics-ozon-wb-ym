from fastapi import APIRouter, Depends
from webapp.backend.auth import get_current_user
from core.db.database import get_db_connection

router = APIRouter()

@router.get("/")
async def get_profile(user_id: str = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        profile = await conn.fetchrow("SELECT * FROM public.profiles WHERE id = $1", user_id)
        if not profile:
            await conn.execute("INSERT INTO public.profiles (id, plan) VALUES ($1, 'free') ON CONFLICT DO NOTHING", user_id)
            profile = await conn.fetchrow("SELECT * FROM public.profiles WHERE id = $1", user_id)
        return dict(profile)
    finally:
        await conn.close()
