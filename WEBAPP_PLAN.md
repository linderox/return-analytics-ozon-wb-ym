# Plan: Marketplace Returns Web App + Telegram Mini App

> **Author: Anton Mislawsky**
> All code, documentation, and commits in this project are authored solely by Anton Mislawsky.
> Do not add AI tool credits, co-authorship lines, or "Generated with" footers anywhere.

## Context

The existing project (`d:/python/ozon-api-nikita-victoria`) is a mature multi-marketplace ETL platform with FastAPI, PostgreSQL, and Google Sheets sync. It has no user-facing authentication, no billing, and no Telegram Mini App — only internal tooling for a fixed set of shops hardcoded in `config.json`.

This plan builds a **separate user-facing SaaS layer** on top of the same Supabase PostgreSQL database:
- Multi-user registration with per-user isolated returns tables
- Each user adds their own marketplace accounts (Ozon, WB, YM) with credentials
- Syncs returns data from marketplace APIs into their own DB tables
- Reads existing Google Sheets snapshots as reference
- Billing via СБП (Russian QR payments via ЮKassa)
- Telegram Mini App sharing the same React codebase

---

## Technology Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend API | FastAPI (Python 3.11) | Matches existing codebase |
| Database | Supabase (PostgreSQL 15) | Already targeted; built-in Auth + RLS |
| Frontend | Next.js 14 (App Router, TypeScript) | SSR for SEO, same code for TMA |
| Telegram Mini App | Next.js `/tma` route + `@tma.js/sdk` | Reuse React components |
| Auth | Supabase Auth (email, phone OTP, OAuth) | Built-in; supports Yandex, VK |
| Payments | ЮKassa SDK (yookassa-python) | СБП QR native support in РФ |
| Styling | Tailwind CSS + shadcn/ui | Fast, accessible components |
| State | Zustand + React Query (TanStack) | Lightweight, SSR-compatible |

---

## Repository Structure to Create

```
webapp/
├── backend/                    # New FastAPI app (separate from server/)
│   ├── main.py                 # App entry point
│   ├── auth.py                 # Supabase JWT verification middleware
│   ├── routers/
│   │   ├── shops.py            # CRUD for user's marketplace accounts
│   │   ├── returns.py          # Trigger sync + read returns data
│   │   ├── billing.py          # СБП payment creation + webhook
│   │   └── profile.py          # User FIO, email, plan info
│   ├── services/
│   │   ├── sync_ozon.py        # Ozon returns → user table
│   │   ├── sync_wb.py          # WB returns → user table
│   │   └── sync_ym.py          # YM returns → user table
│   ├── db.py                   # Supabase client + per-user table helpers
│   └── requirements.txt
├── frontend/                   # Next.js 14
│   ├── app/
│   │   ├── layout.tsx          # Root layout (providers)
│   │   ├── page.tsx            # Landing (unauthenticated)
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (app)/              # Authenticated layout with sidebar
│   │   │   ├── layout.tsx
│   │   │   ├── dashboard/page.tsx    # Returns table with filters
│   │   │   ├── shops/page.tsx        # Manage marketplace accounts
│   │   │   ├── profile/page.tsx      # FIO, email, plan
│   │   │   └── billing/page.tsx      # СБП QR + plan selection
│   │   └── tma/                # Telegram Mini App entry
│   │       ├── layout.tsx      # TMA root (loads @tma.js/sdk, dark bg)
│   │       └── page.tsx        # Compact returns view
│   ├── components/
│   │   ├── ui/                 # shadcn/ui primitives
│   │   ├── ReturnsTable.tsx    # Shared table for web + TMA
│   │   ├── ShopForm.tsx        # Add/edit marketplace account
│   │   ├── SbpQr.tsx           # СБП QR code display
│   │   └── MarketplaceBadge.tsx
│   ├── lib/
│   │   ├── supabase.ts         # Browser + server Supabase clients
│   │   ├── api.ts              # Fetch wrapper for backend calls
│   │   └── tma.ts              # Telegram Mini App SDK helpers
│   └── middleware.ts           # Auth redirect guard
```

---

## Database Schema (Supabase / PostgreSQL)

### Core tables (run as SQL in Supabase dashboard)

```sql
-- 1. Extended user profiles (supplements Supabase auth.users)
CREATE TABLE public.profiles (
  id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  fio         TEXT,
  phone       TEXT,
  plan        TEXT NOT NULL DEFAULT 'free',  -- 'free' | 'basic' | 'pro'
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own profile" ON public.profiles
  USING (auth.uid() = id);

-- 2. Marketplace shop accounts (many per user)
CREATE TABLE public.shops (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  marketplace     TEXT NOT NULL CHECK (marketplace IN ('ozon','wb','ym')),
  name            TEXT NOT NULL,                -- display name
  google_sheet_id TEXT,
  -- Ozon
  ozon_client_id      TEXT,
  ozon_client_secret  TEXT,
  -- WB
  wb_token            TEXT,
  -- YM
  ym_client_id        TEXT,
  ym_client_secret    TEXT,
  ym_campaign_id      TEXT,
  -- Filters
  status_filter   TEXT[] DEFAULT ARRAY['Выдано'],    -- WB/YM filter value
  schema_filter   TEXT[] DEFAULT ARRAY['FBO','FBS'], -- Ozon: FBO|FBS
  is_active       BOOLEAN DEFAULT TRUE,
  last_synced_at  TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE public.shops ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own shops" ON public.shops
  USING (auth.uid() = user_id);

-- 3. Billing / subscriptions
CREATE TABLE public.subscriptions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES auth.users(id),
  plan            TEXT NOT NULL,
  started_at      TIMESTAMPTZ DEFAULT NOW(),
  expires_at      TIMESTAMPTZ NOT NULL,
  yookassa_id     TEXT,        -- ЮKassa payment object ID
  sbp_qr_code     TEXT,        -- base64 QR for display
  status          TEXT DEFAULT 'pending'  -- 'pending'|'succeeded'|'cancelled'
);
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own subs" ON public.subscriptions
  USING (auth.uid() = user_id);

-- 4. Per-user returns tables — created dynamically on first sync
-- Pattern: {user_uuid_no_dashes[:12]}_returns_{marketplace}
-- Example:  a1b2c3d4e5f6_returns_wb
-- Created by webapp/backend/db.py::ensure_returns_table(user_id, marketplace)

-- WB template:
-- CREATE TABLE IF NOT EXISTS public.{prefix}_returns_wb (
--   srid TEXT PRIMARY KEY, orderDt TEXT, nmId BIGINT, brand TEXT,
--   subjectName TEXT, techSize TEXT, barcode TEXT, shkId BIGINT,
--   returnType TEXT, reason TEXT, status TEXT, isStatusActive INT,
--   readyToReturnDt TEXT, completedDt TEXT, expiredDt TEXT,
--   dstOfficeId INT, dstOfficeAddress TEXT, orderId BIGINT, stickerId BIGINT,
--   synced_at TIMESTAMPTZ DEFAULT NOW()
-- );

-- YM template:
-- CREATE TABLE IF NOT EXISTS public.{prefix}_returns_ym (
--   id BIGINT PRIMARY KEY, orderId BIGINT, returnType TEXT,
--   shipmentStatus TEXT, refundStatus TEXT, creationDate TEXT,
--   updateDate TEXT, pickupTillDate TEXT, amount NUMERIC, currency TEXT,
--   shipmentRecipientType TEXT, logisticPoint TEXT, items TEXT,
--   synced_at TIMESTAMPTZ DEFAULT NOW()
-- );

-- Ozon template:
-- CREATE TABLE IF NOT EXISTS public.{prefix}_returns_oz (
--   posting_number TEXT PRIMARY KEY, added_at TEXT, barcode TEXT,
--   clearing_id BIGINT, offer_id TEXT, status TEXT, return_reason TEXT,
--   return_date TEXT, received_at TEXT, quantity INT, price NUMERIC,
--   is_opened BOOLEAN, synced_at TIMESTAMPTZ DEFAULT NOW()
-- );
```

### Plan limits (enforced in backend)
```python
PLAN_LIMITS = {
    "free":  {"max_shops": 1,   "max_rows": 1_000},
    "basic": {"max_shops": 5,   "max_rows": 10_000},
    "pro":   {"max_shops": 999, "max_rows": 999_999},
}
PLAN_PRICES_RUB = {"basic": 499, "pro": 999}
```

Credentials stored as **plaintext** in Supabase, protected by RLS + service role key only.

---

## Backend API — `webapp/backend/`

### `main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import shops, returns, billing, profile

app = FastAPI(title="Returns SaaS API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(profile.router,  prefix="/api/profile",  tags=["profile"])
app.include_router(shops.router,    prefix="/api/shops",    tags=["shops"])
app.include_router(returns.router,  prefix="/api/returns",  tags=["returns"])
app.include_router(billing.router,  prefix="/api/billing",  tags=["billing"])
```

### Auth middleware (`auth.py`)
- Extract `Authorization: Bearer <supabase_jwt>` from request
- Verify with `SUPABASE_JWT_SECRET` (from env) using `python-jose`
- Inject `user_id: UUID` into request state
- FastAPI dependency: `get_current_user() -> str`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/profile` | Return user FIO, email, plan, shop count |
| PATCH | `/api/profile` | Update FIO |
| GET | `/api/shops` | List user's shops |
| POST | `/api/shops` | Add shop (validate credentials against API) |
| PUT | `/api/shops/{id}` | Update shop credentials/filters |
| DELETE | `/api/shops/{id}` | Remove shop |
| POST | `/api/returns/sync/{shop_id}` | Trigger sync for one shop |
| POST | `/api/returns/sync-all` | Sync all active shops |
| GET | `/api/returns/{marketplace}` | Paginated returns (`?page=1&limit=50&date_from=&date_to=`) |
| POST | `/api/billing/create` | Create СБП payment, return QR |
| POST | `/api/billing/webhook` | ЮKassa webhook → activate plan |
| GET | `/api/billing/status/{payment_id}` | Poll payment status |
| POST | `/api/auth/telegram` | Validate Telegram initData HMAC → return Supabase JWT |

### Sync services — reuse existing fetch functions

`services/sync_wb.py` — adapt `fetch_wb_returns()` from `returns/wb_returns.py`:
```python
async def sync_wb_returns(shop: dict, user_id: str, conn) -> dict:
    # 1. GET https://seller-analytics-api.wildberries.ru/api/v1/analytics/goods-return
    #    headers={"Authorization": shop["wb_token"]}, last 30 days
    # 2. Filter: item["status"] in shop["status_filter"]
    # 3. ensure_returns_table(conn, user_id, "wb")
    # 4. INSERT ... ON CONFLICT (srid) DO UPDATE SET ...
    # 5. Enforce PLAN_LIMITS[plan]["max_rows"]
    # 6. UPDATE shops SET last_synced_at=NOW() WHERE id=shop["id"]
    # Returns: {"added": int, "updated": int}
```

`services/sync_ozon.py` — adapt `fetch_ozon_returns()` from `returns/ozon_returns.py`:
```python
# POST https://api-seller.ozon.ru/v1/returns/list
# headers={"Client-Id": shop["ozon_client_id"], "Api-Key": shop["ozon_client_secret"]}
# Paginate with last_id until has_next==False
# Filter by schema_filter: 'FBO' → schema=='ArrivedAtReturnPlace'
#                          'FBS' → schema=='ReceivedBySeller'
# Upsert by posting_number
```

`services/sync_ym.py` — adapt `fetch_ym_returns()` from `returns/ym_returns.py`:
```python
# GET https://api.partner.market.yandex.ru/v2/campaigns/{campaign_id}/returns
# headers={"Api-Key": shop["ym_client_id"]}  (client_id IS the API key for YM)
# Paginate via nextPageToken
# Filter: item["shipmentStatus"] in shop["status_filter"]  (default: ["PICKED"])
# Upsert by id
```

### `db.py` — key helpers
```python
def table_prefix(user_id: str) -> str:
    return user_id.replace("-", "")[:12]  # first 12 hex chars of UUID

async def ensure_returns_table(conn, user_id: str, marketplace: str):
    prefix = table_prefix(user_id)
    table = f"{prefix}_returns_{marketplace}"  # e.g. a1b2c3d4e5f6_returns_wb
    # Execute CREATE TABLE IF NOT EXISTS using marketplace-specific template above
    return table
```

### `requirements.txt` (webapp/backend)
```
fastapi>=0.110
uvicorn>=0.29
python-jose[cryptography]>=3.3
supabase>=2.4
yookassa>=3.0
requests>=2.31
pydantic>=2.6
python-dotenv>=1.0
asyncpg>=0.29
```

---

## Frontend — `webapp/frontend/`

### Authentication Flow
1. `/login` → Supabase Auth (email+password OR phone OTP)
2. OAuth buttons: Yandex, VKontakte (configured in Supabase Dashboard → Auth → Providers)
3. On success → redirect to `/dashboard`
4. `middleware.ts` protects all `/(app)/*` routes via `supabase.auth.getSession()`

### Key Pages

**`/dashboard`** — Main returns view
- Marketplace tab switcher: Ozon | WB | YM
- Date range picker
- `ReturnsTable` (columns vary by marketplace — see column configs below)
- "Sync now" button → `POST /api/returns/sync-all` → toast notification
- Ozon: FBO / FBS / Both toggle

**`/shops`** — Shop management
- Card list: marketplace logo + name + last synced timestamp
- "Add shop" → `ShopForm` modal with marketplace selector
- Fields per marketplace:
  - **Ozon**: name, `ozon_client_id`, `ozon_client_secret`, `google_sheet_id`, FBO/FBS checkboxes
  - **WB**: name, `wb_token` (JWT), `google_sheet_id`, status filter (default: Выдано)
  - **YM**: name, `ym_campaign_id`, `ym_client_id` (= API key), `google_sheet_id`, status filter (default: PICKED)
- On save: backend validates credentials with a test API call

**`/profile`** — User profile
- FIO (editable text field)
- Email (read-only)
- Current plan badge + expiry date
- Change password link

**`/billing`** — Payment
- Three plan cards: Free | Basic 499₽/мес | Pro 999₽/мес
- Click paid plan → `POST /api/billing/create {plan}` → receive QR + payment_id
- `SbpQr`: renders base64 QR image + deep link button "Оплатить в банке"
- Polls `GET /api/billing/status/{payment_id}` every 3s → on `succeeded` show success banner

### `ReturnsTable.tsx` column configs
```typescript
const WB_COLS  = ['srid','orderDt','nmId','brand','subjectName','techSize',
                  'barcode','returnType','reason','status','completedDt','dstOfficeAddress']

const YM_COLS  = ['id','orderId','returnType','shipmentStatus','creationDate',
                  'amount','currency','logisticPoint','items']

const OZ_COLS  = ['posting_number','added_at','offer_id','status','return_reason',
                  'return_date','received_at','quantity','price','is_opened']
```

---

## Telegram Mini App — `/tma` route

### Setup
1. Create Bot via @BotFather → set Web App URL to `https://yourdomain.com/tma`
2. `tma/layout.tsx`: import `@tma.js/sdk`, call `miniApp.ready()` on mount
3. Auth: extract `window.Telegram.WebApp.initData` → `POST /api/auth/telegram`
   - Backend verifies HMAC-SHA256 of initData using `TELEGRAM_BOT_TOKEN`
   - On success: create/find Supabase user by `telegram_id`, return JWT
4. Store JWT in `zustand` store, attach to all API calls

### TMA differences from web
- No sidebar → bottom tab bar: Dashboard | Shops | Profile
- Colors from `themeParams`: `bg_color`, `text_color`, `button_color`
- `ReturnsTable` compact: 4 columns max, horizontal scroll
- Use Telegram `backButton` for nested navigation

---

## СБП Payment Flow (ЮKassa)

```
User clicks "Basic 499₽"
  → POST /api/billing/create {"plan": "basic"}
  → yookassa.Payment.create({
        amount: {value: "499.00", currency: "RUB"},
        payment_method_type: "sbp",
        capture: True,
        description: "Подписка Basic — 1 месяц"
    })
  → Returns {payment_id, confirmation.confirmation_url, sbp_qr_code}
  → SbpQr renders QR image
  → User pays in bank app
  → ЮKassa POSTs webhook to /api/billing/webhook
  → Backend verifies X-Jkassa-Signature header
  → INSERT INTO subscriptions (plan='basic', expires_at=NOW()+30d, status='succeeded')
  → Frontend poll returns succeeded → plan badge updates
```

ЮKassa sandbox: `Configuration.configure(account_id, secret_key)` from env vars.

---

## Auth Providers (Supabase Dashboard → Auth → Providers)

| Provider | Required env vars |
|----------|------------------|
| Email | enabled by default |
| Phone OTP | Twilio `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_MESSAGE_SERVICE_SID` |
| Yandex | `YANDEX_CLIENT_ID`, `YANDEX_CLIENT_SECRET` |
| VKontakte | `VK_CLIENT_ID`, `VK_CLIENT_SECRET` |

WB has no public OAuth — users enter token manually in `/shops`.

---

## Environment Variables

```env
# webapp/backend/.env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret
DATABASE_URL=postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres
YOOKASSA_ACCOUNT_ID=123456
YOOKASSA_SECRET_KEY=test_xxx
YOOKASSA_WEBHOOK_SECRET=xxx
TELEGRAM_BOT_TOKEN=xxx:yyy

# webapp/frontend/.env.local
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## Implementation Order for Jules

### Phase 1 — Database (Day 1)
1. Run SQL DDL above in Supabase SQL editor (profiles, shops, subscriptions)
2. Verify RLS policies block cross-user access
3. Enable Supabase Auth providers: email, Yandex, VK

### Phase 2 — Backend (Days 2–3)
1. Create `webapp/backend/` with `main.py`, `auth.py`, `db.py`, `requirements.txt`
2. `routers/shops.py`: CRUD + credential validation (make one test API call before saving)
3. `services/sync_wb.py`: adapt `fetch_wb_returns()` from `returns/wb_returns.py`
4. `services/sync_ozon.py`: adapt `fetch_ozon_returns()` from `returns/ozon_returns.py`
5. `services/sync_ym.py`: adapt `fetch_ym_returns()` from `returns/ym_returns.py`
6. `routers/returns.py`: paginated SELECT from `{prefix}_returns_{marketplace}`
7. `routers/billing.py`: ЮKassa СБП create + webhook handler + status poll
8. `routers/profile.py`: read/update FIO, return plan info

### Phase 3 — Frontend (Days 4–6)
```bash
cd webapp
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir
cd frontend
npm install @supabase/ssr @supabase/supabase-js @tanstack/react-query zustand
npx shadcn@latest init
```
Steps:
1. `lib/supabase.ts` — browser client + server client (using `@supabase/ssr`)
2. `middleware.ts` — protect `/(app)/*`, redirect to `/login` if no session
3. `/login` and `/(auth)/register` pages with Supabase Auth forms
4. `/(app)/layout.tsx` — sidebar with nav: Dashboard / Shops / Profile / Billing
5. `/dashboard` — tabs + `ReturnsTable` + Sync button
6. `/shops` — card list + `ShopForm` modal
7. `/profile` — FIO form + plan badge
8. `/billing` — plan cards + `SbpQr` component + polling

### Phase 4 — Telegram Mini App (Day 7)
1. Add `app/tma/layout.tsx` with `@tma.js/sdk` init
2. Add `POST /api/auth/telegram` to backend (HMAC-SHA256 of initData)
3. Bottom tab bar component (no sidebar in TMA)
4. Compact `ReturnsTable` variant (4 cols + horizontal scroll)

### Phase 5 — Deploy & Verify (Day 8)
```bash
# Backend
cd webapp/backend && uvicorn main:app --host 0.0.0.0 --port 8001

# Frontend
cd webapp/frontend && vercel deploy --prod
```
Set Telegram Bot Web App URL via @BotFather → `/setmenubutton`.

---

---

## Adding More Reports (Plugin Architecture)

### Current scope: `returns/*.py`

Phase 2 targets only returns data. The three fetch functions live in:

| File | Fetch function | Primary key |
|------|---------------|-------------|
| `returns/wb_returns.py` | `fetch_wb_returns(token, days)` | `srid` |
| `returns/ozon_returns.py` | `fetch_ozon_returns(client_id, api_key, days)` | `posting_number` |
| `returns/ym_returns.py` | `fetch_ym_returns(api_key, campaign_id, days)` | `id` |

These are debug/reference scripts — the webapp sync services in `webapp/backend/services/` adapt only the `fetch_*()` functions from them, stripping the CSV/XLSX comparison logic.

---

### Future scope: all `tools/` report types

The existing codebase has 40+ production report tools, each following the same pattern:

```
fetch_*(credentials, params) → list[dict]   # API call with pagination + retry
items_to_rows(items) → list[list]           # flat transform for GS / DB
process_shop(shop_cfg) → None               # orchestrate one shop
```

Key tool files available to adapt:

**WB** (`tools/wb/`)
| File | Report | GS tab |
|------|--------|--------|
| `wb_stocks_wb_wh.py` | FBW warehouse stocks | "WB Остатки FBW" |

**Ozon** (`tools/ozon/`)
| File | Report |
|------|--------|
| `ozon_postings_report_common.py` | Postings (отправления) |
| `ozon_get_transactions_common.py` | Transactions (начисления) |
| `ozon_products_report_common.py` | Products catalog |
| `ozon_get_prices_common.py` | Price history |
| `ozon_fbo_stocks_analytics_common.py` | FBO stocks analytics |
| `ozon_fbs_stocks_common.py` | FBS stocks |
| `ozon_sales_14_report_common.py` | 14-day sales |
| `ozon_realization_v2_report_common.py` | Realization report |
| `ozon_average_delivery_time_details_common.py` | Avg delivery time |
| `ozon_reviews.py` | Reviews |

**YM** (`services/yandex_market/`)
| File | Report |
|------|--------|
| `get_boost_consolidated.py` | Boost ads consolidated |

---

### Report Registry — `webapp/backend/report_registry.py`

Central dict that drives routing, DB table creation, and frontend column config:

```python
from typing import TypedDict

class ReportDef(TypedDict):
    label: str              # display name in UI
    marketplace: str        # "wb" | "oz" | "ym"
    table_suffix: str       # suffix for DB table name: {prefix}_{table_suffix}
    sync_module: str        # dotted path: "services.sync_wb_returns"
    schema_sql: str         # CREATE TABLE IF NOT EXISTS template (use {table} placeholder)
    columns: list[str]      # ordered column list for frontend table
    pk: str                 # primary key column for upsert

REPORTS: dict[str, ReportDef] = {
    # ── Phase 2 (initial build) ──────────────────────────────────────────────
    "returns_wb": {
        "label": "Возвраты WB",
        "marketplace": "wb",
        "table_suffix": "returns_wb",
        "sync_module": "services.sync_wb",
        "schema_sql": WB_RETURNS_SQL,
        "columns": ["srid", "orderDt", "nmId", "brand", "subjectName",
                    "techSize", "barcode", "returnType", "reason",
                    "status", "completedDt", "dstOfficeAddress"],
        "pk": "srid",
    },
    "returns_oz": {
        "label": "Возвраты Ozon",
        "marketplace": "oz",
        "table_suffix": "returns_oz",
        "sync_module": "services.sync_ozon",
        "schema_sql": OZ_RETURNS_SQL,
        "columns": ["posting_number", "added_at", "offer_id", "status",
                    "return_reason", "return_date", "received_at",
                    "quantity", "price", "is_opened"],
        "pk": "posting_number",
    },
    "returns_ym": {
        "label": "Возвраты YM",
        "marketplace": "ym",
        "table_suffix": "returns_ym",
        "sync_module": "services.sync_ym",
        "schema_sql": YM_RETURNS_SQL,
        "columns": ["id", "orderId", "returnType", "shipmentStatus",
                    "creationDate", "amount", "currency",
                    "logisticPoint", "items"],
        "pk": "id",
    },
    # ── Phase 6 (future reports) ─────────────────────────────────────────────
    # "stocks_wb": {
    #     "label": "Остатки FBW",
    #     "marketplace": "wb",
    #     "table_suffix": "stocks_wb",
    #     "sync_module": "services.sync_stocks_wb",   # adapt tools/wb/wb_stocks_wb_wh.py
    #     "schema_sql": WB_STOCKS_SQL,
    #     "columns": ["nmId", "chrtId", "warehouseName", "regionName",
    #                 "quantity", "inWayToClient", "inWayFromClient", "updatedAt"],
    #     "pk": "chrtId",
    # },
    # "postings_oz": { ... },   # tools/ozon/ozon_postings_report_common.py
    # "transactions_oz": { ... },  # tools/ozon/ozon_get_transactions_common.py
}
```

---

### Generalized DB table naming

Current (returns only): `{prefix}_returns_{marketplace}`
Generalized (any report): `{prefix}_{table_suffix}`

Examples:
- `a1b2c3d4e5f6_returns_wb`
- `a1b2c3d4e5f6_stocks_wb`
- `a1b2c3d4e5f6_postings_oz`
- `a1b2c3d4e5f6_returns_ym`

Update `db.py`:
```python
async def ensure_report_table(conn, user_id: str, report_slug: str) -> str:
    report = REPORTS[report_slug]
    prefix = table_prefix(user_id)
    table = f"{prefix}_{report['table_suffix']}"
    sql = report["schema_sql"].replace("{table}", table)
    await conn.execute(sql)
    return table
```

---

### Sync service interface (standard contract)

Each sync service in `webapp/backend/services/` must expose:

```python
async def sync(shop: dict, user_id: str, conn, plan: str) -> dict:
    """
    Fetch data from marketplace API and upsert into the user's DB table.
    
    shop:    row from public.shops (credentials + filters)
    user_id: UUID string
    conn:    asyncpg connection
    plan:    "free" | "basic" | "pro"
    
    Returns: {"added": int, "updated": int, "table": str}
    Raises:  PlanLimitExceeded if max_rows would be exceeded
    """
```

This interface makes `routers/returns.py` (and any future `routers/reports.py`) work generically:

```python
@router.post("/sync/{shop_id}/{report_slug}")
async def trigger_sync(shop_id: UUID, report_slug: str, user=Depends(get_current_user)):
    report = REPORTS[report_slug]        # raises KeyError → 404
    module = importlib.import_module(report["sync_module"])
    result = await module.sync(shop, user.id, conn, user.plan)
    return result
```

---

### Adapting `tools/` → `services/`

The mapping from existing tool to new sync service:

| Existing tool | New service | What to keep |
|--------------|-------------|--------------|
| `returns/wb_returns.py` | `services/sync_wb.py` | `fetch_wb_returns()` only |
| `returns/ozon_returns.py` | `services/sync_ozon.py` | `fetch_ozon_returns()` only |
| `returns/ym_returns.py` | `services/sync_ym.py` | `fetch_ym_returns()` only |
| `tools/wb/wb_stocks_wb_wh.py` | `services/sync_stocks_wb.py` | `fetch_stocks()` + `items_to_rows()` |
| `tools/ozon/ozon_postings_report_common.py` | `services/sync_postings_oz.py` | `build_postings_report_payloads()` |
| `tools/ozon/ozon_get_transactions_common.py` | `services/sync_transactions_oz.py` | fetch + pagination |

Drop from each tool when porting: `process_shop()`, `main()`, `parse_args()`, GS write calls, `core/gs_handler` imports, `send_report_notification()` — all that is handled by the webapp layer.

---

### Mapping files (`mappings/`) and `core/mappings.py`

The existing `core/mappings.py` loads JSON mapping files that define column order, display labels, and storage policy (replace vs. upsert). These are already used by `tools/ozon/ozon_postings_report_common.py` via `load_report_mapping()` and `build_header_rows()`.

For the webapp:
- Column lists in `REPORTS[slug]["columns"]` replace the GS-specific `HEADERS_ROW1`
- Russian labels for the frontend come from the same mapping `fields[col]["label_ru"]`
- Storage policy (`replace` vs. `upsert_by_pk`) maps to the DB upsert strategy

When adding a new report, create `mappings/{report_slug}.json` following the existing pattern, then reference it in `REPORTS`:
```python
"postings_oz": {
    ...
    "mapping_path": "mappings/postings_oz.json",  # optional: load via core.mappings
}
```

---

### Frontend: generic `ReportTable.tsx`

Replace the three marketplace-specific column arrays with a registry-driven component:

```typescript
// components/ReportTable.tsx
interface ReportTableProps {
  reportSlug: string       // "returns_wb" | "stocks_wb" | ...
  shopId: string
  dateFrom?: string
  dateTo?: string
}

// Columns fetched once from GET /api/reports/{slug}/columns
// Same component renders all report types — no code change to add a new report
```

New endpoints to add alongside existing `/api/returns/*`:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/reports` | List `REPORTS` keys + labels available for user's shops |
| GET | `/api/reports/{slug}/columns` | Column names + Russian labels from mapping |
| POST | `/api/reports/sync/{shop_id}/{slug}` | Trigger sync for any registered report |
| GET | `/api/reports/{slug}` | Paginated rows (`?shop_id=&page=&limit=&date_from=&date_to=`) |

---

### Phase 6 — New Reports (after TMA)

When adding a new report type (e.g. WB stocks):

1. Add entry to `REPORTS` in `report_registry.py` with `table_suffix`, `schema_sql`, `columns`, `pk`
2. Create `webapp/backend/services/sync_stocks_wb.py` — copy `fetch_stocks()` + `items_to_rows()` from `tools/wb/wb_stocks_wb_wh.py`, implement `sync()` interface
3. Add `schema_sql` string (CREATE TABLE template) to `report_registry.py` or a separate `schemas.py`
4. Run `ensure_report_table()` on first sync — table auto-created per user
5. Frontend: new report slug automatically appears in `/dashboard` tab list via `/api/reports`
6. No router changes needed — `routers/reports.py` handles all slugs generically

---

---

## Cyrillic Support

All three marketplaces return Cyrillic text in API responses (brand names, return reasons, statuses, addresses). This must be handled end-to-end.

### Backend (Python / asyncpg)

- asyncpg connects with UTF-8 by default on Supabase — no extra config needed, but verify:
  ```python
  conn = await asyncpg.connect(DATABASE_URL, server_settings={"client_encoding": "utf8"})
  ```
- All `requests` calls already decode Cyrillic correctly because `response.json()` uses UTF-8 by default.
- FastAPI `JSONResponse` defaults to UTF-8. Do **not** set `ensure_ascii=True` on any custom serializer.

### Database

- Supabase databases are UTF-8 (`ENCODING='UTF8'`, `LC_COLLATE='C'`). No DDL change needed.
- Text search on Cyrillic columns: use `ILIKE` with `pg_trgm` extension for fuzzy search in future.
  ```sql
  -- Enable once in Supabase SQL editor:
  CREATE EXTENSION IF NOT EXISTS pg_trgm;
  -- Then index Cyrillic-heavy columns:
  CREATE INDEX ON public.{prefix}_returns_wb USING GIN (reason gin_trgm_ops);
  ```
- Column names in per-user tables remain **lowercase English** (e.g. `return_reason`, `brand`) to avoid quoting issues in asyncpg dynamic SQL.

### Frontend (Next.js)

- Add Cyrillic font in `app/layout.tsx`:
  ```typescript
  import { Inter } from "next/font/google";
  // Inter ships Cyrillic subset — no extra package needed:
  const inter = Inter({ subsets: ["latin", "cyrillic"] });
  ```
- All API responses are `application/json; charset=utf-8`. Fetch wrapper in `lib/api.ts` needs no special handling.
- Table cell widths: Cyrillic strings are ~30% wider than Latin at same font size — use `min-w-[120px]` on address / reason columns and `truncate` with tooltip.
- Date columns from WB/YM come as ISO strings with Cyrillic month names in some fields — parse with `new Date(value)`, not locale-specific string parsing.

---

## Credentials Migration: config.json → Supabase

The existing internal tools (`returns/*.py`, `tools/**`) hardcode credentials in two places:

1. **`config.json`** — per-shop `client_id`, `client_secret`, `seller_api_key`, `seller_client_id`, WB token
2. **Inline constants** — e.g. `CLIENT_SECRET_OZON` / `CLIENT_ID_OZON` in `returns/ozon_returns.py`, `GS_TOKEN` in `returns/wb_returns.py`

### Migration goal

After this phase, credentials live **only** in `public.shops` (Supabase). The internal tools read them from Supabase at runtime using the service role key.

### Phase 1-B — Migrate existing shops (run after Phase 1 DDL)

Add a one-time migration script `webapp/backend/migrate_config_shops.py`:

```python
"""
One-time script: reads config.json and inserts rows into public.shops
for a fixed admin user_id (the project owner's Supabase auth.users UUID).
Run once: python migrate_config_shops.py
"""
import json, asyncio, asyncpg, os
from dotenv import load_dotenv

load_dotenv()
ADMIN_USER_ID = os.environ["ADMIN_USER_ID"]  # project owner's Supabase UUID
DATABASE_URL  = os.environ["DATABASE_URL"]

MARKETPLACE_MAP = {
    "ozon": {"client_id": "seller_client_id", "client_secret": "client_secret"},
    "wb":   {"wb_token": "seller_api_key"},
    "ym":   {"ym_client_id": "client_id", "ym_client_secret": "client_secret",
              "ym_campaign_id": "campaign_id"},
}

async def main():
    cfg = json.load(open("config.json"))
    conn = await asyncpg.connect(DATABASE_URL)
    for shop_key, shop in cfg.items():
        mp = shop.get("marketplace", "ozon")
        mapping = MARKETPLACE_MAP.get(mp, {})
        row = {
            "user_id":      ADMIN_USER_ID,
            "marketplace":  mp,
            "name":         shop_key,
            "google_sheet_id": shop.get("google_sheet_id"),
        }
        for supabase_col, config_key in mapping.items():
            row[supabase_col] = shop.get(config_key)
        cols = ", ".join(row.keys())
        vals = ", ".join(f"${i+1}" for i in range(len(row)))
        await conn.execute(
            f"INSERT INTO public.shops ({cols}) VALUES ({vals}) ON CONFLICT DO NOTHING",
            *row.values()
        )
        print(f"  inserted {shop_key} ({mp})")
    await conn.close()

asyncio.run(main())
```

**Required env vars for migration**: `DATABASE_URL`, `ADMIN_USER_ID`

### Phase 2-B — Update internal tools to read from Supabase

Add `core/supabase_creds.py`:

```python
"""Fetch shop credentials from Supabase for internal tools (replaces config.json reads)."""
import asyncpg, asyncio, os
from functools import lru_cache

DATABASE_URL = os.environ["DATABASE_URL"]

def get_shop_creds(shop_key: str) -> dict:
    """Sync wrapper for use in existing CLI tools."""
    return asyncio.run(_fetch(shop_key))

async def _fetch(shop_key: str) -> dict:
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow(
        "SELECT * FROM public.shops WHERE name = $1", shop_key
    )
    await conn.close()
    return dict(row) if row else {}
```

Internal tools then replace:
```python
# Before
cfg = json.load(open("config.json"))
shop = cfg[shop_key]

# After
from core.supabase_creds import get_shop_creds
shop = get_shop_creds(shop_key)
```

### Cleanup

Once migration is verified:
1. Remove hardcoded credential constants from `returns/ozon_returns.py`, `returns/wb_returns.py`, `returns/ym_returns.py`
2. Keep `config.json` in `.gitignore` but can eventually delete it
3. Update `CLAUDE.md` Google Sheets Audit Dump section to note credentials now come from Supabase

---

## Verification Checklist

- [ ] New user registers → `profiles` row created, empty `/shops` list
- [ ] Add WB shop → `POST /api/shops` with token → credential validated → stored
- [ ] `POST /api/returns/sync/{shop_id}` → table `{prefix}_returns_wb` created, rows inserted
- [ ] Free plan: sync stops at 1001 rows with 429 + message
- [ ] СБП: payment created → QR shown → webhook received → plan=basic, expires+30d
- [ ] Yandex OAuth: redirect completes → session active → `/dashboard` loads
- [ ] Telegram Mini App: initData validates → returns table renders in compact mode
- [ ] Ozon FBO-only filter: only `ArrivedAtReturnPlace` rows synced when FBS unchecked
- [ ] Cyrillic brand/reason text displays correctly in frontend table cells
- [ ] `migrate_config_shops.py` runs without errors → all shops appear in `/shops` page

---

## Questions Jules Will Likely Ask

Before Jules can start or during implementation, expect these questions:

### Blocking (Jules cannot proceed without answers)

1. **Supabase project URL + anon key + service role key** — needed for `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` in both backend `.env` and frontend `.env.local`. Jules cannot connect to DB or run migrations without these.

2. **`DATABASE_URL` (direct Postgres connection string)** — needed by asyncpg. Format: `postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres`. Found in Supabase Dashboard → Project Settings → Database.

3. **`SUPABASE_JWT_SECRET`** — needed by `auth.py` to verify user JWTs. Found in Supabase Dashboard → Project Settings → API → JWT Secret.

4. **`ADMIN_USER_ID`** — the Supabase `auth.users` UUID for the project owner. Needed by `migrate_config_shops.py`. Found after creating an account via the webapp's `/register` page (or Supabase Dashboard → Authentication → Users).

### Required before Phase 4 (Billing)

5. **ЮKassa `YOOKASSA_ACCOUNT_ID` + `YOOKASSA_SECRET_KEY`** — test credentials from ЮKassa dashboard. Jules will use sandbox mode but needs real test account IDs.

6. **`YOOKASSA_WEBHOOK_SECRET`** — set in ЮKassa dashboard → Webhooks section, then copy the generated secret.

### Required before Phase 4 (Telegram Mini App)

7. **`TELEGRAM_BOT_TOKEN`** — create a bot via @BotFather, set Web App URL to the deployed frontend's `/tma` path.

### Nice to have (Jules can scaffold without but needs for real deployment)

8. **Deployment target for backend** — Railway / Render / Fly.io / own VPS? Affects `Dockerfile` vs `Procfile` vs `fly.toml` that Jules should generate.

9. **Yandex OAuth credentials** (`YANDEX_CLIENT_ID`, `YANDEX_CLIENT_SECRET`) — configured in Yandex OAuth console, then entered in Supabase Dashboard → Auth → Providers → Yandex.

10. **VK OAuth credentials** (`VK_CLIENT_ID`, `VK_CLIENT_SECRET`) — same pattern.

11. **Twilio credentials** — only if phone OTP auth is needed immediately (can be deferred).

### Design decisions Jules may ask to confirm

- Should the `/dashboard` default to showing all shops combined, or one shop at a time? (Affects the paginated `GET /api/returns/{marketplace}` query — add `?shop_id=` filter or aggregate all shops for user.)
- Should syncing be **manual-only** (button click) in Phase 2, or should Jules also wire up a scheduled background sync? (Adds a `tasks/` module with APScheduler or Celery — defer to Phase 5 unless explicitly needed.)
- Should the free plan show a banner/paywall overlay or just return a 429 error when limit is hit?
