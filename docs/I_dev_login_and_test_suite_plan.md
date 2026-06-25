# Plan: Dev Admin Login Script + Complete Test Suite

## Context

### Problem — admin login without Google OAuth
`Login.vue` already has an email/password tab, but the admin account (`linderox@gmail.com`)
was created via Google OAuth — it has **no password set** in Supabase, so email login fails.
The "forgot password" flow would work but requires waiting for email delivery.

For development and CI the cleanest solution is a **standalone Python script** that uses the
Supabase service role key to generate a one-time magic link for any email, then opens the
browser automatically. No new endpoints, no frontend changes, no password required.

### Also pending — backend fixes already applied
README port notice, auth.py JWKS hardening, database.py client-init hardening, and main.py
logging middleware are done. All 7 test files and pytest config still need to be created.

---

## Part A — Dev admin login script

### `scripts/dev_login.py`

Single-file script, no extra dependencies beyond what's already installed (`httpx`, `python-dotenv`).

**Usage:**
```bash
# WSL / terminal (from project root, venv active)
python scripts/dev_login.py                          # uses default admin email from .env
python scripts/dev_login.py other@example.com        # any registered Supabase user
```

**Logic:**
1. Load `.env` → read `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `FRONTEND_URL`, and optionally `ADMIN_EMAIL` (default `linderox@gmail.com`)
2. `POST {SUPABASE_URL}/auth/v1/admin/generate_link` with `{"type": "magiclink", "email": EMAIL, "options": {"redirect_to": FRONTEND_URL}}`
3. Extract `action_link` from response
4. Print the link to stdout with a short explanation
5. Call `webbrowser.open(action_link)` to open it in the default browser automatically
6. Guard: if either env var is missing, print a clear error and exit with code 1

**Key detail:** `generate_link` with `type="magiclink"` produces a one-time OTP link that
logs the user in through the normal Supabase session flow — the frontend receives the session
via the existing `onAuthStateChange` listener in `auth.ts`. No special frontend handling needed.

**Output example:**
```
[dev_login] Generating magic link for linderox@gmail.com ...
[dev_login] Done. Opening browser...

  Link (valid once, ~1 hour):
  https://<project>.supabase.co/auth/v1/verify?token=...

  If the browser didn't open, paste the link manually.
```

**File to create:** `scripts/dev_login.py` (new file, ~35 lines)
**Files to modify:** none

---

## Part B — Complete Test Suite

### Phase 1 — Shared infrastructure

#### `pytest.ini` (project root)
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
pythonpath = .
markers =
    integration: requires real credentials in .env
```

#### `tests/requirements.txt`
```
pytest>=7.4
pytest-asyncio>=0.23
httpx>=0.25
```

#### `tests/__init__.py`
Empty file.

---

### Phase 2 — `tests/conftest.py`

**Constants**
```python
TEST_USER_ID  = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
TEST_ADMIN_ID = "ffffffff-0000-1111-2222-333333333333"
TEST_SHOP_ID  = "11111111-2222-3333-4444-555555555555"
```

**`MockQueryChain`** — chainable mock for the Supabase query builder.
Tracks whether `maybe_single()` / `single()` was called to return dict vs list.
`insert(data)` stores the inserted payload; `execute()` returns it as `[data]`.
All other mutation methods (`update`, `delete`, `upsert`) return `self` unchanged.

```python
class MockQueryChain:
    def __init__(self, data=None):
        self._data = data          # pre-configured table data
        self._single_mode = False
        self._inserted = None

    def select(self, *a, **kw): return self
    def eq(self, *a, **kw): return self
    def order(self, *a, **kw): return self
    def limit(self, *a, **kw): return self
    def maybe_single(self):
        self._single_mode = True; return self
    def single(self):
        self._single_mode = True; return self
    def insert(self, data):
        self._inserted = data if isinstance(data, list) else [data]; return self
    def update(self, data): return self
    def delete(self): return self
    def upsert(self, data, **kw): return self

    async def execute(self):
        result = MagicMock()
        result.error = None
        if self._inserted is not None:
            result.data = self._inserted
        elif self._single_mode:
            result.data = (self._data[0] if isinstance(self._data, list) and self._data
                           else None if isinstance(self._data, list) else self._data)
        else:
            result.data = self._data if self._data is not None else []
        return result
```

**`MockSupabaseClient`**
```python
class MockSupabaseClient:
    def __init__(self): self._responses: dict = {}
    def configure(self, table: str, data): self._responses[table] = data; return self
    def table(self, name: str): return MockQueryChain(self._responses.get(name))
```

**Fixtures**

| Fixture | Scope | What it does |
|---------|-------|-------------|
| `app` | function | yields the FastAPI app; clears `dependency_overrides` on teardown |
| `client(app)` | function | unauthenticated `AsyncClient` via `ASGITransport` |
| `user_client(app)` | function | overrides `get_current_user → TEST_USER_ID` |
| `admin_client(app)` | function | overrides `get_current_user → TEST_ADMIN_ID` AND `check_admin → TEST_ADMIN_ID` |
| `mock_supabase(monkeypatch)` | function | `monkeypatch.setattr(db_module, "_supabase_client", MockSupabaseClient())` so `get_supabase_client()` returns the mock immediately |

Import pattern for dependency override:
```python
from webapp.backend.auth import get_current_user
from webapp.backend.routers.admin import check_admin
app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID
```

---

### Phase 3 — `tests/test_supabase_tables.py`

All tests marked `@pytest.mark.integration`. Skip automatically if `SUPABASE_URL` not in env.

**Session fixture** `supabase_client` — calls `await get_supabase_client()` once per session.

**Tests** — each selects specific columns; PostgREST returns 400 if a column is missing:

| Test | Table | Columns verified |
|------|-------|-----------------|
| `test_profiles_table_exists` | profiles | `id,fio,phone,plan,is_admin,created_at` |
| `test_shops_table_exists` | shops | `id,user_id,name,marketplace,wb_token,ozon_client_id,ozon_client_secret,ozon_performance_client_id,ozon_performance_client_secret,ym_client_id,ym_client_secret,ym_campaign_id,fulfillment_models,last_synced_at` |
| `test_subscriptions_table_exists` | subscriptions | `id,user_id,plan,status,yookassa_id,expires_at` |

Assert: `result.data is not None` (list, possibly empty).

---

### Phase 4 — `tests/test_shops.py`

#### Unit tests (use `user_client` + `mock_supabase`)

Configure `mock_supabase.configure('shops', [...])` with a stub shop dict for read tests.
For create tests, `MockQueryChain.insert(data).execute()` auto-returns `[data]`.

| Test | Request | Expected |
|------|---------|---------|
| `test_create_wb_shop_success` | POST `/api/shops` `{name, marketplace:"wb", wb_token:"tok"}` | 200, response has `name` and `marketplace` |
| `test_create_ozon_shop_seller_only` | POST `/api/shops` `{marketplace:"ozon", ozon_client_id, ozon_client_secret}` | 200 |
| `test_create_ozon_shop_with_performance_api` | POST `/api/shops` with all 4 Ozon creds | 200, all 4 cred keys present |
| `test_create_ym_shop_success` | POST `/api/shops` `{marketplace:"ym", ym_client_id, ym_campaign_id}` | 200 |
| `test_create_shop_invalid_marketplace` | POST `/api/shops` `{marketplace:"badmkt"}` | 400 |
| `test_create_wb_shop_missing_token` | POST `/api/shops` `{marketplace:"wb"}` (no wb_token) | 400 |
| `test_create_ozon_shop_missing_secret` | POST `/api/shops` `{marketplace:"ozon", ozon_client_id only}` | 400 |
| `test_create_ym_shop_missing_campaign` | POST `/api/shops` `{marketplace:"ym", ym_client_id only}` | 400 |
| `test_list_shops` | GET `/api/shops` | 200, list |
| `test_delete_shop_not_found` | DELETE `/api/shops/{TEST_SHOP_ID}` (mock returns []) | 404 |

#### Integration tests (`@pytest.mark.integration`)

Tests read from the **same `.env` the app already uses** — no separate test-specific vars.
Token constants (top of `test_shops.py`, same pattern in `test_tokens.py`):

```python
WB_TOKEN       = os.getenv("WB_TOKEN", "")
YM_TOKEN       = os.getenv("YM_TOKEN", "")
YM_CAMPAIGN_ID = os.getenv("YM_CAMPAIGN_ID", "")
OZON_CLIENT_ID = os.getenv("OZON_CLIENT_ID", "")
OZON_API_KEY   = os.getenv("OZON_API_KEY", "")
OZON_PERF_CLIENT_ID = os.getenv("OZON_PERF_CLIENT_ID", "")
OZON_PERF_SECRET    = os.getenv("OZON_PERF_SECRET", "")
ADMIN_JWT      = os.getenv("ADMIN_JWT", "")
```

Each shop-creation integration test POSTs to `/api/admin/user/{TEST_ADMIN_ID}/shops` with real creds,
asserts 200, then DELETEs for cleanup.
All tests use `@pytest.mark.skipif(not VAR, reason="<VAR> not set in .env")` — graceful skip, not failure.

---

### Phase 5 — `tests/test_tokens.py`

All `@pytest.mark.integration`. Use `httpx.AsyncClient` directly (no FastAPI client needed).
Reads from the same env vars already in `.env` (same names as `test_shops.py`).

| Test | API endpoint | Auth | Skip if |
|------|-------------|------|---------|
| `test_wb_token_valid` | `GET seller-analytics-api.wildberries.ru/api/v1/analytics/goods-return` (7-day window) | `Authorization: {WB_TOKEN}` | `WB_TOKEN` not set |
| `test_ozon_seller_token_valid` | `POST api-seller.ozon.ru/v1/returns/list` | `Client-Id + Api-Key` | `OZON_CLIENT_ID` not set |
| `test_ozon_performance_token_valid` | `POST performance.ozon.ru/api/client/campaign` | `Client-Id + Api-Key` | `OZON_PERF_CLIENT_ID` not set |
| `test_ym_token_valid` | `GET api.partner.market.yandex.ru/v2/campaigns/{YM_CAMPAIGN_ID}/returns` | `Api-Key: {YM_TOKEN}` | `YM_TOKEN` not set |

Pass condition for all: HTTP status not 401 and not 403.

---

### Phase 6 — `tests/test_auth.py`

#### Unit tests (no real credentials needed)

| Test | Setup | Expected |
|------|-------|---------|
| `test_no_token_profile_returns_401` | bare `client` (no auth) | GET `/api/profile` → 401 |
| `test_no_token_returns_ozon_returns_401` | bare `client` | GET `/api/returns/ozon` → 401 |
| `test_no_token_admin_users_returns_401` | bare `client` | GET `/api/admin/users` → 401 |
| `test_invalid_token_returns_401` | `Authorization: Bearer not.a.jwt` | GET `/api/profile` → 401 |
| `test_non_admin_user_admin_endpoint_returns_403` | `user_client` + `mock_supabase` with `is_admin=False` profile | GET `/api/admin/users` → 403 |
| `test_yandex_oauth_redirect` | bare `client`, `follow_redirects=False` | GET `/api/auth/yandex` → 3xx, Location contains `oauth.yandex.ru` |
| `test_yandex_callback_no_code` | bare `client` | GET `/api/auth/yandex/callback` (no params) → redirect to `/login?error=yandex_denied` |
| `test_yandex_callback_with_error_param` | bare `client` | GET `/api/auth/yandex/callback?error=access_denied` → redirect to `/login?error=yandex_denied` |

Note on `test_non_admin_user_admin_endpoint_returns_403`:
- `user_client` overrides `get_current_user → TEST_USER_ID` but NOT `check_admin`
- `check_admin` runs for real and calls `get_supabase_client()`
- `mock_supabase.configure('profiles', {"id": TEST_USER_ID, "is_admin": False})`
- `maybe_single()` mode returns the dict; `is_admin=False` → 403

#### Integration tests (`@pytest.mark.integration`)

Require `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` in `.env`.

| Test | What it does | Pass |
|------|-------------|------|
| `test_login_email_password_success` | POST `{SUPABASE_URL}/auth/v1/token?grant_type=password` with `linderox@gmail.com` / `12345678Aa` | response has `access_token` |
| `test_login_wrong_password_fails` | Same endpoint, wrong password `"WrongPass!"` | response status 400 |
| `test_google_provider_enabled` | GET `{SUPABASE_URL}/auth/v1/settings` | JSON contains `external.google.enabled = true` |
| `test_create_user_via_admin_endpoint` | POST `/api/admin/users/create` with admin JWT header, `email=test_qa_{uuid}@example.com` | 200 + user id; cleanup via Supabase admin DELETE |

---

## Verification

```bash
# In WSL with venv activated
pip install -r tests/requirements.txt

# Unit tests only (no credentials required)
pytest -m "not integration" -v

# All tests including integration (requires populated .env)
pytest -v

# Dev login script
python scripts/dev_login.py
```

Expected: all unit tests pass without any `.env` credentials.
Integration tests skip (not fail) when the relevant env var is missing.

---

## Files to create / modify

| File | Action | Notes |
|------|--------|-------|
| `scripts/dev_login.py` | **create** | Part A — dev admin login |
| `.env.example` | **modify** | Append marketplace token keys + `ADMIN_EMAIL` |
| `pytest.ini` | create | |
| `tests/__init__.py` | create | empty |
| `tests/requirements.txt` | create | |
| `tests/conftest.py` | create | |
| `tests/test_supabase_tables.py` | create | |
| `tests/test_shops.py` | create | |
| `tests/test_tokens.py` | create | |
| `tests/test_auth.py` | create | |

### `.env.example` addition (append to end of file)

```dotenv
# ── Dev tools ───────────────────────────────────────────────────────────────
# Email used by scripts/dev_login.py (defaults to linderox@gmail.com if not set)
ADMIN_EMAIL=linderox@gmail.com

# ── Marketplace tokens (GAS scripts + integration tests) ────────────────────
# wb_returns_fashion.gs → const API_KEY
WB_TOKEN=

# ym_returns_fashion.gs → const API_KEY / CAMPAIGN_ID
YM_TOKEN=
YM_CAMPAIGN_ID=

# Ozon seller API — from Ozon seller account (or Google Sheet 'Настройка')
OZON_CLIENT_ID=
OZON_API_KEY=

# Ozon Performance API (optional)
OZON_PERF_CLIENT_ID=
OZON_PERF_SECRET=

# Admin JWT — Bearer token for an admin user (for admin integration tests)
ADMIN_JWT=
```
