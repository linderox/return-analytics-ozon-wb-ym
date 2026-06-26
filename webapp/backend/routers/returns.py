from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from webapp.backend.auth import get_current_user
from core.db.database import get_supabase_client
from webapp.backend.services.sync_wb import sync_wb_returns
from webapp.backend.services.sync_ozon import sync_ozon_returns
from webapp.backend.services.sync_ym import sync_ym_returns
from uuid import UUID
from datetime import datetime, timezone

router = APIRouter()

MARKETPLACES = {"wb", "ozon", "ym"}

# Date and SKU column names differ per marketplace
DATE_COL = {"wb": "order_dt", "ozon": "return_date", "ym": "creation_date"}
SKU_COL  = {"wb": "barcode",  "ozon": "offer_id",    "ym": None}
STATUS_COL = {"wb": "status", "ozon": "status", "ym": "shipment_status"}


class UpdateReturnBody(BaseModel):
    user_status:  Optional[str] = None
    user_comment: Optional[str] = None


@router.post("/sync/{shop_id}")
async def sync_shop(shop_id: UUID, user_id: str = Depends(get_current_user)):
    client = await get_supabase_client()
    shop_result = await client.table("shops").select("*").eq("id", str(shop_id)).eq("user_id", user_id).maybe_single().execute()
    if shop_result.data is None:
        raise HTTPException(status_code=404, detail="Shop not found")

    shop = shop_result.data
    marketplace = shop["marketplace"]
    if marketplace == "wb":
        result = await sync_wb_returns(shop)
    elif marketplace == "ozon":
        result = await sync_ozon_returns(shop)
    elif marketplace == "ym":
        result = await sync_ym_returns(shop)
    else:
        raise HTTPException(status_code=400, detail="Unsupported marketplace")

    await client.table("shops").update(
        {"last_synced_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", str(shop_id)).execute()
    return result


@router.get("/{marketplace}")
async def get_returns(
    marketplace: str,
    shop_id:   Optional[str] = None,
    date_from: Optional[str] = None,
    date_to:   Optional[str] = None,
    status:    Optional[str] = None,
    sku:       Optional[str] = None,
    limit:     int = 200,
    offset:    int = 0,
    user_id: str = Depends(get_current_user),
):
    if marketplace not in MARKETPLACES:
        raise HTTPException(status_code=400, detail="Unsupported marketplace")

    client = await get_supabase_client()

    # Resolve which shop IDs belong to this user (and optionally filter to one)
    shops_q = client.table("shops").select("id").eq("user_id", user_id)
    shops_result = await shops_q.execute()
    user_shop_ids = [s["id"] for s in (shops_result.data or [])]

    if not user_shop_ids:
        return []

    if shop_id:
        if shop_id not in user_shop_ids:
            raise HTTPException(status_code=403, detail="Shop not found")
        filter_shop_ids = [shop_id]
    else:
        filter_shop_ids = user_shop_ids

    q = client.table(f"returns_{marketplace}").select("*").in_("shop_id", filter_shop_ids)

    if status:
        q = q.eq(STATUS_COL[marketplace], status)

    date_col = DATE_COL[marketplace]
    if date_from:
        q = q.gte(date_col, date_from)
    if date_to:
        # include the full end day
        q = q.lte(date_col, date_to + "T23:59:59Z")

    if sku:
        sku_col = SKU_COL.get(marketplace)
        if sku_col:
            q = q.ilike(sku_col, f"%{sku}%")

    q = q.order("synced_at", desc=True).range(offset, offset + limit - 1)

    try:
        result = await q.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Storage unavailable: {str(e)}")


@router.patch("/{marketplace}/{row_id}")
async def update_return(
    marketplace: str,
    row_id: str,
    body: UpdateReturnBody,
    user_id: str = Depends(get_current_user),
):
    if marketplace not in MARKETPLACES:
        raise HTTPException(status_code=400, detail="Unsupported marketplace")

    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    if not payload:
        raise HTTPException(status_code=400, detail="Nothing to update")

    client = await get_supabase_client()
    # Verify row belongs to one of the user's shops before updating
    shops_result = await client.table("shops").select("id").eq("user_id", user_id).execute()
    user_shop_ids = [s["id"] for s in (shops_result.data or [])]

    result = await (
        client.table(f"returns_{marketplace}")
        .update(payload)
        .eq("id", row_id)
        .in_("shop_id", user_shop_ids)
        .execute()
    )
    return result.data
