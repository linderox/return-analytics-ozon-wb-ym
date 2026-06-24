from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from webapp.backend.auth import get_current_user
from core.db.database import get_db_connection, get_sqlite_conn
import re
import os
import httpx

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

VALID_MARKETPLACES = {"wb", "ozon", "ym"}
VALID_PLANS = {"free", "basic", "pro"}


async def check_admin(user_id: str = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        profile = await conn.fetchrow("SELECT is_admin FROM public.profiles WHERE id = $1", user_id)
        if not profile or not profile['is_admin']:
            raise HTTPException(status_code=403, detail="Admin access required")
        return user_id
    finally:
        await conn.close()


@router.get("/shops")
async def list_all_shops(_: str = Depends(check_admin)):
    conn = await get_db_connection()
    try:
        shops = await conn.fetch("""
            SELECT s.*, p.fio, u.email AS user_email
            FROM public.shops s
            JOIN public.profiles p ON p.id = s.user_id
            JOIN auth.users u ON u.id = s.user_id
            ORDER BY u.email, s.name
        """)
        return [dict(s) for s in shops]
    finally:
        await conn.close()


@router.get("/users")
async def list_users(_: str = Depends(check_admin)):
    conn = await get_db_connection()
    try:
        users = await conn.fetch("""
            SELECT p.*,
                   u.email,
                   (SELECT COUNT(*) FROM public.shops WHERE user_id = p.id) AS shop_count
            FROM public.profiles p
            JOIN auth.users u ON u.id = p.id
            ORDER BY u.created_at DESC
        """)
        return [dict(u) for u in users]
    finally:
        await conn.close()


@router.get("/user/{user_id}/shops")
async def get_user_shops(user_id: str, _: str = Depends(check_admin)):
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
            if marketplace not in VALID_MARKETPLACES:
                continue

            table_name = f"{prefix}_returns_{marketplace}"
            row_count = 0
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
            except Exception:
                pass

            shop_dict['row_count'] = row_count
            results.append(shop_dict)

        db_sqlite.close()
        return results
    finally:
        await conn.close()


# ── User creation ──────────────────────────────────────────────────────────────

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    fio: Optional[str] = None
    plan: str = "free"


@router.post("/users/create")
async def create_user(body: CreateUserRequest, _: str = Depends(check_admin)):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=500, detail="Supabase admin credentials not configured")

    auth_url = f"{SUPABASE_URL}/auth/v1/admin/users"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": body.email,
        "password": body.password,
        "email_confirm": True,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(auth_url, json=payload, headers=headers)

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.json().get("message", resp.text))

    new_user = resp.json()
    new_user_id = new_user["id"]

    conn = await get_db_connection()
    try:
        await conn.execute(
            """
            INSERT INTO public.profiles (id, fio, plan, is_admin)
            VALUES ($1, $2, $3, false)
            ON CONFLICT (id) DO UPDATE SET fio = EXCLUDED.fio, plan = EXCLUDED.plan
            """,
            new_user_id, body.fio, body.plan,
        )
    finally:
        await conn.close()

    return {"id": new_user_id, "email": body.email, "plan": body.plan}


# ── Plan update ────────────────────────────────────────────────────────────────

class UpdatePlanRequest(BaseModel):
    plan: str


@router.patch("/user/{user_id}/plan")
async def admin_update_plan(user_id: str, body: UpdatePlanRequest, _: str = Depends(check_admin)):
    if not re.match(r'^[a-f0-9\-]{36}$', user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    if body.plan not in VALID_PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {', '.join(VALID_PLANS)}")

    conn = await get_db_connection()
    try:
        result = await conn.execute(
            "UPDATE public.profiles SET plan = $1 WHERE id = $2",
            body.plan, user_id,
        )
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "updated", "plan": body.plan}
    finally:
        await conn.close()


# ── Shop / token management ────────────────────────────────────────────────────

# Allowed credential columns per marketplace
CREDENTIAL_FIELDS = {
    "wb": ["wb_token"],
    "ozon": ["ozon_client_id", "ozon_client_secret"],
    "ym": ["ym_client_id", "ym_client_secret", "ym_campaign_id"],
}


class CreateShopRequest(BaseModel):
    name: str
    marketplace: str
    wb_token: Optional[str] = None
    ozon_client_id: Optional[str] = None
    ozon_client_secret: Optional[str] = None
    ym_client_id: Optional[str] = None
    ym_client_secret: Optional[str] = None
    ym_campaign_id: Optional[str] = None


class UpdateCredentialsRequest(BaseModel):
    wb_token: Optional[str] = None
    ozon_client_id: Optional[str] = None
    ozon_client_secret: Optional[str] = None
    ym_client_id: Optional[str] = None
    ym_client_secret: Optional[str] = None
    ym_campaign_id: Optional[str] = None


@router.post("/user/{user_id}/shops")
async def admin_create_shop(user_id: str, body: CreateShopRequest, _: str = Depends(check_admin)):
    if not re.match(r'^[a-f0-9\-]{36}$', user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    if body.marketplace not in VALID_MARKETPLACES:
        raise HTTPException(status_code=400, detail="Invalid marketplace")

    allowed = CREDENTIAL_FIELDS[body.marketplace]
    body_dict = body.model_dump(exclude={"name", "marketplace"})
    cred_values = {k: v for k, v in body_dict.items() if k in allowed and v is not None}

    if not cred_values:
        raise HTTPException(status_code=400, detail=f"At least one credential required for {body.marketplace}: {allowed}")

    cols = ", ".join(cred_values.keys())
    placeholders = ", ".join([f"${i + 4}" for i in range(len(cred_values))])
    query = f"""
        INSERT INTO public.shops (user_id, name, marketplace, {cols})
        VALUES ($1, $2, $3, {placeholders})
        RETURNING *
    """

    conn = await get_db_connection()
    try:
        shop = await conn.fetchrow(query, user_id, body.name, body.marketplace, *cred_values.values())
        return dict(shop)
    finally:
        await conn.close()


@router.patch("/user/{user_id}/shops/{shop_id}/token")
async def admin_update_credentials(user_id: str, shop_id: str, body: UpdateCredentialsRequest, _: str = Depends(check_admin)):
    if not re.match(r'^[a-f0-9\-]{36}$', user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    conn = await get_db_connection()
    try:
        shop = await conn.fetchrow(
            "SELECT marketplace FROM public.shops WHERE id = $1 AND user_id = $2",
            shop_id, user_id,
        )
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")

        marketplace = shop['marketplace']
        allowed = CREDENTIAL_FIELDS.get(marketplace, [])
        body_dict = body.model_dump()
        updates = {k: v for k, v in body_dict.items() if k in allowed and v is not None}

        if not updates:
            raise HTTPException(status_code=400, detail="No valid credential fields provided")

        set_clause = ", ".join([f"{col} = ${i + 2}" for i, col in enumerate(updates.keys())])
        query = f"UPDATE public.shops SET {set_clause} WHERE id = $1"
        await conn.execute(query, shop_id, *updates.values())
        return {"status": "updated"}
    finally:
        await conn.close()


@router.delete("/user/{user_id}/shops/{shop_id}")
async def admin_delete_shop(user_id: str, shop_id: str, _: str = Depends(check_admin)):
    if not re.match(r'^[a-f0-9\-]{36}$', user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    conn = await get_db_connection()
    try:
        result = await conn.execute(
            "DELETE FROM public.shops WHERE id = $1 AND user_id = $2",
            shop_id, user_id,
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Shop not found")
        return {"status": "deleted"}
    finally:
        await conn.close()
