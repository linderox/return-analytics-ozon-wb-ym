# Testing & Debugging Implementation Plan

## What was already applied

### README.md
Added a **"Supabase port blocking"** notice above Prerequisites explaining:
- Ports 5432 and 6543 are commonly blocked by home ISPs / corporate firewalls
- The app communicates via HTTPS (port 443) only — no direct TCP DB connection is made
- `DATABASE_URL` in `.env` is reference-only; migrations tooling may use it but the running app does not

### webapp/backend/auth.py — JWKS fetch hardening
**Root cause of 500s on `/login`:** if `SUPABASE_JWKS_URL` was unset or the Supabase auth endpoint was unreachable, the unhandled exception bubbled up as HTTP 500 instead of a clear 503.

Changes:
- Move the `SUPABASE_JWKS_URL` guard into `_fetch_jwks()` (returns 503, not 500)
- Wrap `httpx.AsyncClient.get()` with typed exception handling:
  - `TimeoutException` → 503 "Authentication service timeout"
  - `HTTPStatusError` → 503 with upstream status code
  - Any other exception → 503 "Authentication service unavailable"
- `get_current_user()` now catches all `Exception` (not just `JWTError`) and returns 503 for unexpected auth failures
- Added `logging.getLogger("auth")` — every JWT decode, rejection, and JWKS load is logged

### core/db/database.py — Supabase client init hardening
**Root cause of 503s on admin page:** `create_async_client()` could throw if credentials were wrong or network was down; the exception was unhandled → HTTP 500.

Changes:
- Wrap `create_async_client()` in try/except → returns HTTP 503 with diagnostic message
- Added `logging.getLogger("database")` with info logs on connection attempt and success

### webapp/backend/main.py — request logging middleware + global handler
Added:
1. `log_requests` HTTP middleware:
   - Logs `→ METHOD /path` on every request
   - Logs `← METHOD /path STATUS (Xms)` on completion
   - WARNING level for 4xx/5xx, INFO for 2xx/3xx
   - Catches unhandled exceptions in middleware chain → returns JSON 500 + logs full traceback
2. `global_exception_handler` for `Exception` — last-resort catch that prevents bare 500s with no body

---

## Remaining work: Unit Test Suite

### File structure
```
tests/
├── __init__.py
├── conftest.py
├── requirements.txt
├── test_supabase_tables.py
├── test_shops.py
├── test_tokens.py
└── test_auth.py
pytest.ini
```

### pytest.ini
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
pythonpath = .
markers =
    integration: requires real credentials (.env must be populated)
```

### tests/requirements.txt
```
pytest>=7.4
pytest-asyncio>=0.23
httpx>=0.25
```

---

### tests/conftest.py

Key components:

**`MockQueryChain`** — mimics Supabase async query builder chaining:
```python
class MockQueryChain:
    def __init__(self, data=None):
        self._data = data
        self._inserted = None

    def select(self, *a, **kw): return self
    def eq(self, *a, **kw): return self
    def maybe_single(self): return self
    def single(self): return self
    def order(self, *a, **kw): return self
    def limit(self, *a, **kw): return self
    def insert(self, data):
        self._inserted = data if isinstance(data, list) else [data]
        return self
    def update(self, data): return self
    def delete(self): return self
    def upsert(self, data, **kw): return self

    async def execute(self):
        result = MagicMock()
        result.data = self._inserted if self._inserted is not None else self._data
        result.error = None
        return result
```

**`MockSupabaseClient`**:
```python
class MockSupabaseClient:
    def __init__(self):
        self._responses: dict = {}

    def set(self, table: str, data):
        self._responses[table] = data

    def table(self, name: str) -> MockQueryChain:
        return MockQueryChain(self._responses.get(name))
```

**Fixtures**:
```python
TEST_USER_ID  = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
TEST_ADMIN_ID = "ffffffff-0000-1111-2222-333333333333"
TEST_SHOP_ID  = "11111111-2222-3333-4444-555555555555"

@pytest.fixture
def app():
    from webapp.backend.main import app as fastapi_app
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()

@pytest.fixture
async def client(app): ...           # unauthenticated

@pytest.fixture
async def user_client(app): ...      # overrides get_current_user → TEST_USER_ID

@pytest.fixture
async def admin_client(app): ...     # overrides get_current_user + check_admin → TEST_ADMIN_ID

@pytest.fixture
def mock_supabase(monkeypatch):
    """Patches core.db.database._supabase_client with MockSupabaseClient."""
    mock = MockSupabaseClient()
    import core.db.database as db_module
    monkeypatch.setattr(db_module, "_supabase_client", mock)
    return mock
```

---

### tests/test_supabase_tables.py  *(integration)*

All tests require `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` in `.env`.  
Marked `@pytest.mark.integration`.

| Test | What it checks |
|------|---------------|
| `test_profiles_table_exists` | SELECT from `profiles` succeeds, `data` is a list |
| `test_profiles_columns` | Row contains `id`, `fio`, `phone`, `plan`, `is_admin`, `created_at` |
| `test_shops_table_exists` | SELECT from `shops` succeeds |
| `test_shops_credential_columns` | All credential columns present: `wb_token`, `ozon_client_id`, `ozon_client_secret`, `ozon_performance_client_id`, `ozon_performance_client_secret`, `ym_client_id`, `ym_client_secret`, `ym_campaign_id` |
| `test_subscriptions_table_exists` | SELECT from `subscriptions` succeeds |
| `test_subscriptions_columns` | Row contains `id`, `user_id`, `plan`, `status`, `yookassa_id`, `expires_at` |

---

### tests/test_shops.py

#### Unit tests (mocked Supabase)

| Test | Endpoint | Validates |
|------|----------|-----------|
| `test_create_wb_shop_success` | `POST /api/shops` | WB shop created with `wb_token` — 200 |
| `test_create_ozon_shop_seller_only` | `POST /api/shops` | Ozon shop with `ozon_client_id` + `ozon_client_secret` — 200 |
| `test_create_ozon_shop_with_performance_api` | `POST /api/shops` | Ozon shop with all 4 credentials (`ozon_performance_client_id`, `ozon_performance_client_secret`) — 200 |
| `test_create_ym_shop_success` | `POST /api/shops` | YM shop with `ym_client_id` + `ym_campaign_id` — 200 |
| `test_create_shop_invalid_marketplace` | `POST /api/shops` | `marketplace="badmkt"` → 400 |
| `test_create_wb_shop_missing_token` | `POST /api/shops` | WB shop without `wb_token` → 400 |
| `test_create_ozon_shop_missing_secret` | `POST /api/shops` | Ozon shop with only `ozon_client_id` → 400 |
| `test_create_ym_shop_missing_campaign` | `POST /api/shops` | YM shop without `ym_campaign_id` → 400 |
| `test_list_shops` | `GET /api/shops` | Returns list — 200 |
| `test_delete_shop_not_found` | `DELETE /api/shops/{uuid}` | Non-existent shop → 404 |

#### Integration tests (real Supabase, `@pytest.mark.integration`)

Tokens sourced from `*_returns_fashion.gs` files — set these env vars:
- `WB_TEST_TOKEN` = `API_KEY` constant from `wb_returns_fashion.gs`
- `YM_TEST_TOKEN` = `API_KEY` constant from `ym_returns_fashion.gs`
- `YM_TEST_CAMPAIGN_ID` = `CAMPAIGN_ID` from `ym_returns_fashion.gs`
- `OZON_TEST_CLIENT_ID` = col B of 'Настройка' sheet in `ozon_returns_fashion.gs`
- `OZON_TEST_API_KEY` = col A of 'Настройка' sheet
- `OZON_TEST_PERF_CLIENT_ID` = Ozon Performance Client ID (if available)
- `OZON_TEST_PERF_SECRET` = Ozon Performance Secret (if available)

| Test | What it does |
|------|-------------|
| `test_admin_create_wb_shop` | POST `/api/admin/user/{id}/shops` with real WB token, verify row in Supabase, cleanup |
| `test_admin_create_ozon_shop` | Same for Ozon seller credentials |
| `test_admin_create_ym_shop` | Same for YM credentials |

---

### tests/test_tokens.py  *(integration only)*

All tests skip if the corresponding env var is not set.

| Test | What it does | Pass condition |
|------|-------------|---------------|
| `test_wb_token_valid` | GET `https://seller-analytics-api.wildberries.ru/api/v1/analytics/goods-return` with `WB_TEST_TOKEN` | HTTP 200 or 204 (not 401/403) |
| `test_ozon_seller_token_valid` | POST `https://api-seller.ozon.ru/v1/returns/list` with `OZON_TEST_CLIENT_ID` + `OZON_TEST_API_KEY` | HTTP 200 |
| `test_ozon_performance_token_valid` | POST Ozon Performance API with `OZON_TEST_PERF_CLIENT_ID` + `OZON_TEST_PERF_SECRET` | HTTP 200 (skip if vars not set) |
| `test_ym_token_valid` | GET `https://api.partner.market.yandex.ru/v2/campaigns/{YM_TEST_CAMPAIGN_ID}/returns` with `YM_TEST_TOKEN` | HTTP 200 or 204 |

---

### tests/test_auth.py

#### Unit tests

| Test | Validates |
|------|-----------|
| `test_no_token_profile_returns_401` | `GET /api/profile` with no Authorization header → 401 |
| `test_no_token_returns_ozon_returns_401` | `GET /api/returns/ozon` with no token → 401 |
| `test_no_token_admin_users_returns_401` | `GET /api/admin/users` with no token → 401 |
| `test_invalid_token_returns_401` | Bearer `"not.a.jwt"` → 401 |
| `test_non_admin_user_admin_endpoint_returns_403` | Authenticated non-admin user → `GET /api/admin/users` → 403 |
| `test_yandex_oauth_redirect` | `GET /api/auth/yandex` → 302 redirect to `oauth.yandex.ru` |
| `test_yandex_callback_no_code` | `GET /api/auth/yandex/callback` without `code` param → redirect to `/login?error=yandex_denied` |
| `test_yandex_callback_with_error_param` | `GET /api/auth/yandex/callback?error=access_denied` → redirect to `/login?error=yandex_denied` |

#### Integration tests (`@pytest.mark.integration`)

Requires real Supabase credentials + test user `linderox@gmail.com` with password `12345678Aa`.

| Test | What it does |
|------|-------------|
| `test_login_email_password_success` | POST `{SUPABASE_URL}/auth/v1/token?grant_type=password` with `linderox@gmail.com` / `12345678Aa` → access_token in response |
| `test_login_wrong_password_fails` | Same endpoint, wrong password → 400 |
| `test_login_google_configured` | GET `{SUPABASE_URL}/auth/v1/settings` → Google provider is enabled (`external.google.enabled = true`) |
| `test_create_user_via_admin_endpoint` | POST `/api/admin/users/create` with admin JWT → new user created in Supabase, cleanup via admin delete |

---

## Debugging checklist for 500/503 on /login and /admin

Run the backend with `LOG_LEVEL=DEBUG` to get full request traces:

```bash
LOG_LEVEL=DEBUG uvicorn webapp.backend.main:app --reload --port 8000
```

Common failure modes and their fix:

| Symptom | Root cause | Fix applied |
|---------|-----------|------------|
| `GET /api/profile` → 500 on fresh startup | `SUPABASE_JWKS_URL` unset OR JWKS network unreachable → unhandled exception | auth.py: try/except in `_fetch_jwks()` → 503 |
| `GET /api/profile` → 503 | `SUPABASE_URL` or `SUPABASE_SERVICE_ROLE_KEY` not in `.env` | database.py: explicit 503 with clear message |
| `GET /api/returns/ozon` → 503 | SQLite `returns_history.db` permission error | returns.py already handles this; check file permissions |
| Admin page blank / 403 | `is_admin` not set to `true` in Supabase `profiles` table | Set manually in Supabase dashboard |
| Admin page → 503 on load | `create_async_client()` threw on first admin request | database.py: try/except in `get_supabase_client()` → 503 |
| Frontend sees CORS error | Backend returned non-2xx before CORS headers were added | Fixed by middleware catching unhandled errors before response |
