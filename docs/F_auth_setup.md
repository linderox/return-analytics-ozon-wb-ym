# [F] Authentication Setup Reference

| Field          | Value                        |
|----------------|------------------------------|
| Date created   | 2026-06-25                   |
| Last updated   | 2026-06-25                   |
| Version        | 1.0                          |

## Changelog

| Date       | Version | Change                              |
|------------|---------|-------------------------------------|
| 2026-06-25 | 1.0     | Initial document — Google OAuth, Yandex OAuth, JWT setup |

---

## Overview

This app has three auth mechanisms:

| Mechanism    | Who handles it                        | Backend file                              |
|--------------|---------------------------------------|-------------------------------------------|
| Google OAuth | Supabase Auth (dashboard-only)        | None — frontend uses Supabase client      |
| Yandex OAuth | Custom backend flow                   | `webapp/backend/routers/yandex_auth.py`   |
| JWT verify   | Backend validates Supabase-issued JWT | `webapp/backend/auth.py`                  |

---

## 1. Environment Variables Reference

All variables go in `.env` at the project root (never commit this file).

### Supabase Core

| Variable                  | Where to get it                                            | Used by                                  |
|---------------------------|------------------------------------------------------------|------------------------------------------|
| `SUPABASE_URL`            | Supabase dashboard → Settings → API → Project URL          | backend routers, yandex_auth.py          |
| `SUPABASE_JWKS_URL`       | `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json` | `auth.py` JWT verification     |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase dashboard → Settings → API → `service_role` key | yandex_auth.py, admin.py (admin ops)     |
| `SUPABASE_ANON_KEY`       | Supabase dashboard → Settings → API → `anon` key           | `core/db/database.py`                    |
| `VITE_SUPABASE_URL`       | Same as `SUPABASE_URL`                                     | Frontend Supabase client                 |
| `VITE_SUPABASE_ANON_KEY`  | Same as `SUPABASE_ANON_KEY`                                | Frontend Supabase client                 |
| `DATABASE_URL`            | Supabase dashboard → Settings → Database → Connection string (Transaction mode port 6543) | `core/db/database.py` asyncpg |

### Yandex OAuth

| Variable              | Where to get it                                    | Used by          |
|-----------------------|----------------------------------------------------|------------------|
| `YANDEX_CLIENT_ID`    | https://oauth.yandex.ru/ → your app → Client ID   | `yandex_auth.py` |
| `YANDEX_CLIENT_SECRET`| https://oauth.yandex.ru/ → your app → Client Secret | `yandex_auth.py` |
| `YANDEX_REDIRECT_URI` | Must match exactly what you register in Yandex app | `yandex_auth.py` |
| `FRONTEND_URL`        | Base URL of your Vue frontend                      | `yandex_auth.py` |

### App URLs

| Variable       | Local dev value             | Production value              |
|----------------|-----------------------------|-------------------------------|
| `VITE_API_URL` | `http://localhost:8000`     | `https://yourdomain.com`      |
| `FRONTEND_URL` | `http://localhost:5173`     | `https://yourdomain.com`      |
| `YANDEX_REDIRECT_URI` | `http://localhost:8000/api/auth/yandex/callback` | `https://yourdomain.com/api/auth/yandex/callback` |

---

## 2. Google OAuth Setup

Google OAuth is handled entirely by Supabase — there is no backend code for it. The frontend uses the Supabase JS client which redirects to Supabase Auth, which then handles the Google flow.

### Steps

**Step 1 — Google Cloud Console**

1. Go to https://console.cloud.google.com/ → APIs & Services → Credentials
2. Create an **OAuth 2.0 Client ID** (type: Web application)
3. Under **Authorized redirect URIs**, add:
   ```
   https://<your-project-ref>.supabase.co/auth/v1/callback
   ```
   Replace `<your-project-ref>` with your Supabase project reference (visible in the project URL).
4. Copy the **Client ID** and **Client Secret**

**Step 2 — Supabase Dashboard**

1. Go to your Supabase project → Authentication → Providers → Google
2. Toggle **Enable Sign in with Google**
3. Paste your **Client ID** and **Client Secret** from Step 1
4. Save

**Step 3 — Frontend env vars**

The frontend only needs these two vars for the Supabase client to work:
```
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon key from Supabase settings>
```

No backend `.env` changes are needed for Google OAuth.

### How the flow works

```
User clicks "Login with Google"
  → Frontend calls supabase.auth.signInWithOAuth({ provider: 'google' })
  → Browser redirects to Supabase → Supabase redirects to Google
  → Google returns to Supabase callback URL
  → Supabase creates/updates user in auth.users, issues JWT
  → Frontend receives session with JWT access token
  → All subsequent API calls send: Authorization: Bearer <token>
```

---

## 3. Yandex OAuth Setup

This uses a custom backend flow. The backend exchanges the auth code with Yandex, creates or finds a Supabase user, then generates a Supabase magic link so the user gets a real Supabase session.

### Steps

**Step 1 — Create a Yandex OAuth App**

1. Go to https://oauth.yandex.ru/ and click **Create application**
2. Fill in the app name (e.g. "Marketplace Returns")
3. Under **Platforms**, select **Web services**
4. Set **Callback URI** to:
   - Dev: `http://localhost:8000/api/auth/yandex/callback`
   - Prod: `https://yourdomain.com/api/auth/yandex/callback`
5. Under **Access**, grant these permissions:
   - `login:email` — read email address
   - `login:info` — read name and profile info
6. Save and copy **ClientID** and **Client secret**

**Step 2 — Add to `.env`**

```
YANDEX_CLIENT_ID=<your ClientID>
YANDEX_CLIENT_SECRET=<your Client secret>
YANDEX_REDIRECT_URI=http://localhost:8000/api/auth/yandex/callback
FRONTEND_URL=http://localhost:5173
```

The backend also needs `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (see section 1) to create users and generate magic links.

### How the flow works

```
User clicks "Login with Yandex"
  → GET /api/auth/yandex → redirects to oauth.yandex.ru/authorize
  → User grants permission → Yandex redirects to /api/auth/yandex/callback?code=...
  → Backend exchanges code for Yandex access_token
  → Backend fetches user info (email, name) from login.yandex.ru/info
  → Backend looks up email in auth.users (direct DB query)
  → If user not found: creates via POST /auth/v1/admin/users (email_confirm=true, no email sent)
     → Inserts row in public.profiles (plan='free', is_admin=false)
  → Backend generates magic link via POST /auth/v1/admin/generate_link
  → Browser follows action_link → Supabase redirects to FRONTEND_URL with JWT in URL hash
  → Frontend Supabase client picks up the session
```

---

## 4. JWT Token Setup

Supabase issues **ES256** (ECDSA) JWTs. The backend does not manage any signing key — it only needs the public JWKS endpoint to verify tokens.

### How verification works (`webapp/backend/auth.py`)

1. Frontend sends `Authorization: Bearer <token>` with every API request
2. Backend reads `SUPABASE_JWKS_URL` and fetches the public keys (JWKS)
3. Keys are cached in memory (`_jwks_cache`) — they are fetched once per backend process lifetime
4. Token header's `kid` is matched to a key in the JWKS
5. Token is decoded using `python-jose` with `algorithms=["ES256"]`
6. `sub` claim (Supabase user UUID) is returned as the current user ID

### Required `.env` variable

```
SUPABASE_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
```

Find your project ref in Supabase dashboard URL: `https://supabase.com/dashboard/project/<project-ref>`

### Token expiry

Token expiry is set in Supabase dashboard → Authentication → Configuration → JWT expiry (default: **3600 seconds / 1 hour**). The backend does not control this.

### Admin access

Admin-only endpoints (all `/api/admin/*` routes) require `is_admin = true` in the user's `public.profiles` row. There is no special JWT claim for this — the backend queries the database on every admin request.

To grant admin access, run in Supabase SQL editor:
```sql
UPDATE public.profiles SET is_admin = true WHERE id = '<user-uuid>';
```

### JWKS key rotation

If Supabase rotates its JWT signing keys, the in-memory JWKS cache will become stale and all token verifications will fail with 401. Fix: **restart the backend process** to clear `_jwks_cache` and re-fetch fresh keys.

---

## 5. Supabase Key Reference

| Key type           | Where to find                                    | Keep secret? | Used for                              |
|--------------------|--------------------------------------------------|--------------|---------------------------------------|
| `anon` key         | Settings → API → Project API keys → `anon`       | No           | Frontend client, unauthenticated reads |
| `service_role` key | Settings → API → Project API keys → `service_role` | **YES** — never expose to frontend | Creating users, admin DB operations |
| JWT secret         | Settings → API → JWT Settings                    | Supabase only | Signs tokens — you never need this locally |

The `service_role` key bypasses Row Level Security. Never include it in `VITE_*` variables or ship it to the browser.

---

## 6. Local Dev `.env` Template

Copy this to `.env` and fill in the values:

```env
# --- Supabase ---
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_ANON_KEY=<anon key>
SUPABASE_SERVICE_ROLE_KEY=<service_role key>
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres

# --- Frontend (Vite) ---
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon key>
VITE_API_URL=http://localhost:8000

# --- Yandex OAuth ---
YANDEX_CLIENT_ID=<yandex client id>
YANDEX_CLIENT_SECRET=<yandex client secret>
YANDEX_REDIRECT_URI=http://localhost:8000/api/auth/yandex/callback

# --- App URLs ---
FRONTEND_URL=http://localhost:5173
```

> Google OAuth does not require any `.env` variables — it is configured in Supabase dashboard and the Yandex OAuth keys already cover the Supabase keys needed by the backend.
