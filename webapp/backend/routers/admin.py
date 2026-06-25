from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from webapp.backend.auth import get_current_user
from core.db.database import get_supabase_client, get_sqlite_conn
import re
import os
import httpx

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

VALID_MARKETPLACES = {"wb", "ozon", "ym"}
VALID_PLANS = {"free", "basic", "pro"}

MARKETPLACE_FULFILLMENT = {
    "wb": {"FBS", "FBW"},
    "ozon": {"FBS", "FBO"},
    "ym": {"FBS", "FBY"},
}

CREDENTIAL_FIELDS = {
    "wb": ["wb_token"],
    "ozon": ["ozon_client_id", "ozon_client_secret", "ozon_performance_client_id", "ozon_performance_client_secret"],
    "ym": ["ym_token", "ym_campaign_id"],
}

_ADMIN_HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
}


async def _get_auth_users() -> dict:
    """Return {user_id: {email, created_at}} from Supabase admin API."""
    async with httpx.AsyncClient(timeout=15.0) as http:
        resp = await http.get(
            f"{SUPABASE_URL}/auth/v1/admin/users",
            headers=_ADMIN_HEADERS,
            params={"page": 1, "per_page": 1000},
        )
    if resp.status_code != 200:
        return {}
    users = resp.json().get("users", [])
    return {u["id"]: u for u in users}


async def check_admin(user_id: str = Depends(get_current_user)):
    print(f"[check_admin] user_id from token: {user_id!r}")
    client = await get_supabase_client()
    result = await client.table('profiles').select('id,is_admin').eq('id', user_id).maybe_single().execute()
    profile = result.data
    print(f"[check_admin] DB profile row: {profile}")
    if not profile:
        print(f"[check_admin] DENIED — no profile row found for user_id={user_id!r}")
        raise HTTPException(status_code=403, detail="Admin access required")
    if not profile['is_admin']:
        print(f"[check_admin] DENIED — is_admin={profile['is_admin']!r} for user_id={user_id!r}")
        raise HTTPException(status_code=403, detail="Admin access required")
    print(f"[check_admin] GRANTED — user_id={user_id!r}")
    return user_id


@router.get("/shops")
async def list_all_shops(_: str = Depends(check_admin)):
    client = await get_supabase_client()
    shops_result = await client.table('shops').select('*').execute()
    auth_users = await _get_auth_users()

    rows = []
    for shop in (shops_result.data or []):
        uid = shop.get('user_id', '')
        auth_user = auth_users.get(uid, {})
        rows.append({
            **shop,
            'user_email': auth_user.get('email', ''),
        })
    rows.sort(key=lambda s: (s.get('user_email', ''), s.get('name', '')))
    return rows


@router.get("/users")
async def list_users(_: str = Depends(check_admin)):
    client = await get_supabase_client()
    profiles_result = await client.table('profiles').select('*').execute()
    auth_users = await _get_auth_users()

    rows = []
    for profile in (profiles_result.data or []):
        uid = profile['id']
        auth_user = auth_users.get(uid, {})
        rows.append({
            **profile,
            'email': auth_user.get('email', ''),
            'shop_count': 0,
        })

    # Fetch shop counts
    shops_result = await client.table('shops').select('user_id').execute()
    shop_counts: dict = {}
    for s in (shops_result.data or []):
        shop_counts[s['user_id']] = shop_counts.get(s['user_id'], 0) + 1
    for row in rows:
        row['shop_count'] = shop_counts.get(row['id'], 0)

    rows.sort(key=lambda u: auth_users.get(u['id'], {}).get('created_at', ''), reverse=True)
    return rows


@router.get("/user/{user_id}/shops")
async def get_user_shops(user_id: str, _: str = Depends(check_admin)):
    if not re.match(r'^[a-f0-9\-]{36}$', user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    client = await get_supabase_client()
    shops_result = await client.table('shops').select('*').eq('user_id', user_id).execute()

    results = []
    db_sqlite = get_sqlite_conn()
    cursor = db_sqlite.cursor()

    for shop in (shops_result.data or []):
        marketplace = shop['marketplace']
        if marketplace not in VALID_MARKETPLACES:
            continue
        prefix = user_id.replace("-", "")[:12]
        table_name = f"{prefix}_returns_{marketplace}"
        row_count = 0
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
        except Exception:
            pass
        results.append({**shop, 'row_count': row_count})

    db_sqlite.close()
    return results


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

    async with httpx.AsyncClient() as http:
        resp = await http.post(
            f"{SUPABASE_URL}/auth/v1/admin/users",
            json={"email": body.email, "password": body.password, "email_confirm": True},
            headers=_ADMIN_HEADERS,
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.json().get("message", resp.text))

    new_user_id = resp.json()["id"]
    client = await get_supabase_client()
    await client.table('profiles').upsert({
        'id': new_user_id,
        'fio': body.fio,
        'plan': body.plan,
        'is_admin': False,
    }).execute()

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

    client = await get_supabase_client()
    result = await client.table('profiles').update({'plan': body.plan}).eq('id', user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "updated", "plan": body.plan}


# ── Shop / token management ────────────────────────────────────────────────────

class CreateShopRequest(BaseModel):
    name: str
    marketplace: str
    fulfillment_models: Optional[List[str]] = None
    wb_token: Optional[str] = None
    ozon_client_id: Optional[str] = None
    ozon_client_secret: Optional[str] = None
    ozon_performance_client_id: Optional[str] = None
    ozon_performance_client_secret: Optional[str] = None
    ym_token: Optional[str] = None
    ym_campaign_id: Optional[str] = None
    google_sheet_id: Optional[str] = None


class UpdateCredentialsRequest(BaseModel):
    wb_token: Optional[str] = None
    ozon_client_id: Optional[str] = None
    ozon_client_secret: Optional[str] = None
    ozon_performance_client_id: Optional[str] = None
    ozon_performance_client_secret: Optional[str] = None
    ym_campaign_id: Optional[str] = None
    ym_token: Optional[str] = None



@router.post("/user/{user_id}/shops")
async def admin_create_shop(user_id: str, body: CreateShopRequest, _: str = Depends(check_admin)):
    if not re.match(r'^[a-f0-9\-]{36}$', user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
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

    allowed = CREDENTIAL_FIELDS[body.marketplace]
    body_dict = body.model_dump(exclude={"name", "marketplace", "fulfillment_models"})
    cred_values = {k: v for k, v in body_dict.items() if k in allowed and v is not None}

    if not cred_values:
        raise HTTPException(status_code=400, detail=f"At least one credential required for {body.marketplace}: {allowed}")

    insert_data: dict = {
        'user_id': user_id,
        'name': body.name,
        'marketplace': body.marketplace,
        **cred_values,
    }
    if body.fulfillment_models:
        insert_data['fulfillment_models'] = body.fulfillment_models
    else:
        insert_data['fulfillment_models'] = []

    insert_data['status_filter'] = []
    insert_data['schema_filter'] = []
    
    if body.google_sheet_id:
        insert_data['google_sheet_id'] = body.google_sheet_id

    client = await get_supabase_client()
    result = await client.table('shops').insert(insert_data).execute()
    return result.data[0]


@router.patch("/user/{user_id}/shops/{shop_id}/token")
async def admin_update_credentials(user_id: str, shop_id: str, body: UpdateCredentialsRequest, _: str = Depends(check_admin)):
    if not re.match(r'^[a-f0-9\-]{36}$', user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    client = await get_supabase_client()
    shop_result = await client.table('shops').select('marketplace').eq('id', shop_id).eq('user_id', user_id).maybe_single().execute()
    if shop_result.data is None:
        raise HTTPException(status_code=404, detail="Shop not found")

    marketplace = shop_result.data['marketplace']
    allowed = CREDENTIAL_FIELDS.get(marketplace, [])
    updates = {k: v for k, v in body.model_dump().items() if k in allowed and v is not None}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid credential fields provided")

    await client.table('shops').update(updates).eq('id', shop_id).execute()
    return {"status": "updated"}


# ── Invite user (generate link, no email sent) ────────────────────────────────

class InviteUserRequest(BaseModel):
    email: EmailStr
    fio: Optional[str] = None
    plan: str = "free"


@router.post("/users/invite")
async def invite_user(body: InviteUserRequest, _: str = Depends(check_admin)):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=500, detail="Supabase admin credentials not configured")

    if body.plan not in VALID_PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {body.plan}")

    async with httpx.AsyncClient() as http:
        resp = await http.post(
            f"{SUPABASE_URL}/auth/v1/admin/generate_link",
            json={"type": "invite", "email": body.email},
            headers=_ADMIN_HEADERS,
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.json().get("message", resp.text))

    data = resp.json()
    action_link = data.get("action_link") or data.get("properties", {}).get("action_link")
    user_id = data.get("user", {}).get("id") if isinstance(data.get("user"), dict) else None

    if user_id:
        client = await get_supabase_client()
        await client.table('profiles').upsert({
            'id': user_id,
            'fio': body.fio,
            'plan': body.plan,
            'is_admin': False,
        }, on_conflict='id').execute()

    return {"action_link": action_link, "email": body.email}


@router.delete("/user/{user_id}/shops/{shop_id}")
async def admin_delete_shop(user_id: str, shop_id: str, _: str = Depends(check_admin)):
    if not re.match(r'^[a-f0-9\-]{36}$', user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    client = await get_supabase_client()
    result = await client.table('shops').delete().eq('id', shop_id).eq('user_id', user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Shop not found")
    return {"status": "deleted"}
