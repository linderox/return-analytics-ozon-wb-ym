import os
import urllib.parse
import httpx
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from core.db.database import get_supabase_client

router = APIRouter()

YANDEX_CLIENT_ID = os.getenv("OAUTH_YANDEX_CLIENT_ID")
YANDEX_CLIENT_SECRET = os.getenv("OAUTH_YANDEX_CLIENT_SECRET")
YANDEX_REDIRECT_URI = os.getenv("YANDEX_REDIRECT_URI", "http://localhost:8000/api/auth/yandex/callback")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@router.get("")
async def yandex_login():
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": YANDEX_CLIENT_ID,
        "redirect_uri": YANDEX_REDIRECT_URI,
        "force_confirm": "yes",
    })
    return RedirectResponse(f"https://oauth.yandex.ru/authorize?{params}")


@router.get("/callback")
async def yandex_callback(code: str = None, error: str = None):
    if error or not code:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=yandex_denied")

    admin_headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 1. Exchange authorization code for Yandex access token
            token_resp = await client.post(
                "https://oauth.yandex.ru/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": YANDEX_CLIENT_ID,
                    "client_secret": YANDEX_CLIENT_SECRET,
                    "redirect_uri": YANDEX_REDIRECT_URI,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if token_resp.status_code != 200:
                print(f"Yandex token error: {token_resp.text}")
                return RedirectResponse(f"{FRONTEND_URL}/login?error=yandex_token")

            yandex_token = token_resp.json()["access_token"]

            # 2. Get user info from Yandex
            user_resp = await client.get(
                "https://login.yandex.ru/info?format=json",
                headers={"Authorization": f"OAuth {yandex_token}"},
            )
            user_resp.raise_for_status()
            yandex_user = user_resp.json()

            email = yandex_user.get("default_email")
            if not email:
                emails = yandex_user.get("emails", [])
                email = emails[0] if emails else None
            if not email:
                return RedirectResponse(f"{FRONTEND_URL}/login?error=no_email")

            name = yandex_user.get("real_name") or yandex_user.get("display_name") or ""

            # 3. Find existing Supabase user by email via admin API
            users_resp = await client.get(
                f"{SUPABASE_URL}/auth/v1/admin/users",
                headers=admin_headers,
                params={"page": 1, "per_page": 1000},
            )
            supabase_user_id = None
            if users_resp.status_code == 200:
                all_users = users_resp.json().get("users", [])
                existing = next((u for u in all_users if u.get("email") == email), None)
                if existing:
                    supabase_user_id = existing["id"]

            if not supabase_user_id:
                # Create user via Supabase admin API
                create_resp = await client.post(
                    f"{SUPABASE_URL}/auth/v1/admin/users",
                    headers=admin_headers,
                    json={
                        "email": email,
                        "email_confirm": True,
                        "user_metadata": {
                            "full_name": name,
                            "provider": "yandex",
                            "yandex_id": yandex_user.get("id"),
                        },
                    },
                )
                if create_resp.status_code not in (200, 201):
                    print(f"Supabase create user error: {create_resp.text}")
                    return RedirectResponse(f"{FRONTEND_URL}/login?error=create_user")

                supabase_user_id = create_resp.json()["id"]

                # Ensure profile row exists
                sb = await get_supabase_client()
                await sb.table('profiles').upsert({
                    'id': supabase_user_id,
                    'fio': name or None,
                    'plan': 'free',
                    'is_admin': False,
                }, on_conflict='id').execute()

            # 4. Generate a Supabase magic link for session creation
            link_resp = await client.post(
                f"{SUPABASE_URL}/auth/v1/admin/generate_link",
                headers=admin_headers,
                json={
                    "type": "magiclink",
                    "email": email,
                    "options": {"redirect_to": FRONTEND_URL},
                },
            )
            if link_resp.status_code != 200:
                print(f"Supabase generate_link error: {link_resp.text}")
                return RedirectResponse(f"{FRONTEND_URL}/login?error=session")

            action_link = link_resp.json()["action_link"]
            return RedirectResponse(action_link)

    except Exception as e:
        print(f"Yandex OAuth error: {e}")
        return RedirectResponse(f"{FRONTEND_URL}/login?error=oauth_error")
