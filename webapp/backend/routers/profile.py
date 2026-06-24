from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from webapp.backend.auth import get_current_user
from core.db.database import get_supabase_client

router = APIRouter()


@router.get("/")
async def get_profile(user_id: str = Depends(get_current_user)):
    client = await get_supabase_client()
    result = await client.table('profiles').select('*').eq('id', user_id).maybe_single().execute()
    if result.data is None:
        ins = await client.table('profiles').insert({'id': user_id, 'plan': 'free'}).execute()
        return ins.data[0] if ins.data else {}
    return result.data


class UpdateProfileRequest(BaseModel):
    fio: Optional[str] = None
    phone: Optional[str] = None


@router.patch("/")
async def update_profile(body: UpdateProfileRequest, user_id: str = Depends(get_current_user)):
    client = await get_supabase_client()
    await client.table('profiles').update({
        'fio': body.fio,
        'phone': body.phone,
    }).eq('id', user_id).execute()
    result = await client.table('profiles').select('*').eq('id', user_id).maybe_single().execute()
    return result.data
