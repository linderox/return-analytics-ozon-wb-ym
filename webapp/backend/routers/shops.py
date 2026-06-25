from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import re
from webapp.backend.auth import get_current_user
from core.db.database import get_supabase_client

router = APIRouter()

VALID_MARKETPLACES = {"wb", "ozon", "ym"}

MARKETPLACE_FULFILLMENT = {
    "wb": {"FBS", "FBW"},
    "ozon": {"FBS", "FBO"},
    "ym": {"FBS", "FBY"},
}

CREDENTIAL_FIELDS = {
    "wb": {"wb_token"},
    "ozon": {
        "ozon_client_id",
        "ozon_client_secret",
        "ozon_performance_client_id",
        "ozon_performance_client_secret",
    },
    "ym": {"ym_client_id", "ym_client_secret", "ym_campaign_id"},
}

REQUIRED_CREDENTIALS = {
    "wb": {"wb_token"},
    "ozon": {"ozon_client_id", "ozon_client_secret"},
    "ym": {"ym_client_id", "ym_campaign_id"},
}


class CreateShopRequest(BaseModel):
    name: str
    marketplace: str
    fulfillment_models: Optional[List[str]] = None
    wb_token: Optional[str] = None
    ozon_client_id: Optional[str] = None
    ozon_client_secret: Optional[str] = None
    ozon_performance_client_id: Optional[str] = None
    ozon_performance_client_secret: Optional[str] = None
    ym_client_id: Optional[str] = None
    ym_client_secret: Optional[str] = None
    ym_campaign_id: Optional[str] = None
    status_filter: Optional[List[str]] = None
    schema_filter: Optional[List[str]] = None


class UpdateShopRequest(BaseModel):
    wb_token: Optional[str] = None
    ozon_client_id: Optional[str] = None
    ozon_client_secret: Optional[str] = None
    ozon_performance_client_id: Optional[str] = None
    ozon_performance_client_secret: Optional[str] = None
    ym_client_id: Optional[str] = None
    ym_client_secret: Optional[str] = None
    ym_campaign_id: Optional[str] = None
    status_filter: Optional[List[str]] = None
    schema_filter: Optional[List[str]] = None


@router.get("/")
async def list_shops(user_id: str = Depends(get_current_user)):
    client = await get_supabase_client()
    result = await client.table('shops').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
    return result.data


@router.post("/")
async def add_shop(body: CreateShopRequest, user_id: str = Depends(get_current_user)):
    if body.marketplace not in VALID_MARKETPLACES:
        raise HTTPException(status_code=400, detail="Invalid marketplace")

    if body.fulfillment_models:
        allowed_fm = MARKETPLACE_FULFILLMENT[body.marketplace]
        invalid = [fm for fm in body.fulfillment_models if fm not in allowed_fm]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid fulfillment model(s) for {body.marketplace}: {', '.join(invalid)}. Allowed: {', '.join(sorted(allowed_fm))}",
            )

    body_dict = body.model_dump()
    required = REQUIRED_CREDENTIALS[body.marketplace]
    missing = [f for f in required if not body_dict.get(f)]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required credentials for {body.marketplace}: {', '.join(missing)}",
        )

    allowed_creds = CREDENTIAL_FIELDS[body.marketplace]
    insert_data: dict = {
        "user_id": user_id,
        "name": body.name,
        "marketplace": body.marketplace,
    }

    if body.fulfillment_models:
        insert_data["fulfillment_models"] = body.fulfillment_models
    else:
        insert_data["fulfillment_models"] = []

    for field in allowed_creds:
        val = body_dict.get(field)
        if val:
            insert_data[field] = val

    insert_data["status_filter"] = body.status_filter if body.status_filter else []
    insert_data["schema_filter"] = body.schema_filter if body.schema_filter else []

    client = await get_supabase_client()
    result = await client.table('shops').insert(insert_data).execute()
    return result.data[0]


@router.patch("/{shop_id}")
async def update_shop(shop_id: str, body: UpdateShopRequest, user_id: str = Depends(get_current_user)):
    if not re.match(r"^[a-f0-9\-]{36}$", shop_id):
        raise HTTPException(status_code=400, detail="Invalid shop ID format")

    client = await get_supabase_client()
    shop_result = await client.table('shops').select('marketplace').eq('id', shop_id).eq('user_id', user_id).maybe_single().execute()
    if shop_result.data is None:
        raise HTTPException(status_code=404, detail="Shop not found")

    marketplace = shop_result.data['marketplace']
    allowed = CREDENTIAL_FIELDS[marketplace] | {"status_filter", "schema_filter"}
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items() if k in allowed}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    await client.table('shops').update(updates).eq('id', shop_id).execute()
    result = await client.table('shops').select('*').eq('id', shop_id).single().execute()
    return result.data


@router.delete("/{shop_id}")
async def delete_shop(shop_id: str, user_id: str = Depends(get_current_user)):
    if not re.match(r"^[a-f0-9\-]{36}$", shop_id):
        raise HTTPException(status_code=400, detail="Invalid shop ID format")

    client = await get_supabase_client()
    result = await client.table('shops').delete().eq('id', shop_id).eq('user_id', user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Shop not found")
    return {"status": "deleted"}
