# Marketplace Returns SaaS

Analytics and management platform for marketplace returns across Wildberries, Ozon, and Yandex Market.

## Architecture

| Layer | Stack |
|---|---|
| Backend | FastAPI (Python 3.12), asyncpg |
| Frontend | Vue 3 + TypeScript, Vite, Tailwind CSS |
| Auth | Supabase (JWT / Google OAuth / Yandex OAuth) |
| DB (users/shops) | Supabase (PostgreSQL) |
| DB (returns history) | SQLite (`returns_history.db`) — local, unlimited history |

## Prerequisites

- Python 3.12+
- Node.js 18+
- A [Supabase](https://supabase.com) project

> **Important — Supabase port blocking**
>
> Supabase exposes two database ports that are commonly blocked by home ISPs and corporate firewalls:
>
> | Port | Use |
> |------|-----|
> | **5432** | Direct PostgreSQL (Transaction mode) |
> | **6543** | PgBouncer connection pooler (Session mode) |
>
> **Do NOT attempt to connect to these ports directly from a local machine** unless your ISP/VPN explicitly allows them.  
> The backend communicates with Supabase exclusively through the **Supabase REST API** (`https://<project-ref>.supabase.co`) and the **Supabase JS client** — both run over standard HTTPS (port 443) and work everywhere.
>
> The `DATABASE_URL` in `.env` is kept for reference and future migrations tooling, but the running application **does not open a direct TCP connection to port 5432 or 6543**.
>
> If you see `Connection refused` or `Temporary failure in name resolution` for `db.<project-ref>.supabase.co`, it is almost certainly a firewall/ISP block on port 5432 — not an application bug. Solutions:
> - Use the Supabase API (already the default in this app)
> - Switch to a VPN that allows port 5432
> - Use Supabase's IPv4 add-on (paid) and a compatible network

## Setup

### 1. Clone and configure environment

```bash
cp .env.example .env
# Fill in all values in .env — see comments inside the file
```

Required Supabase values (find in **Project Settings → API** and **Database**):
- `DATABASE_URL` — PostgreSQL connection URI
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWKS_URL`

### 2. Backend

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS/WSL
# .venv\Scripts\activate         # Windows cmd

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn webapp.backend.main:app --reload --port 8000
```

The backend runs at **http://localhost:8000**. API docs at http://localhost:8000/docs.

### 3. Frontend

```bash
cd webapp/frontend
npm install
npm run dev
```

The frontend runs at **http://localhost:5173**.

## Database

The backend auto-runs schema migrations on startup (`lifespan` in `main.py`). No manual migration steps needed on a fresh Supabase project — tables are created automatically.

> **Note — Schema Update**
>
> If you are working with an existing Supabase project, you may need to update your table schema to support new marketplace credentials and filters. Use the SQL script provided in `docs/K_fix_schema.sql`.

For the first admin user: set `is_admin = true` in the `public.profiles` table via the Supabase dashboard.

## Project Structure

```
.
├── core/
│   └── db/
│       └── database.py        # DB connections, SQLite helpers, migrations
├── webapp/
│   ├── backend/
│   │   ├── main.py            # FastAPI app + CORS + lifespan
│   │   ├── auth.py            # JWT validation via Supabase JWKS
│   │   └── routers/
│   │       ├── profile.py     # GET/PATCH /api/profile
│   │       ├── shops.py       # CRUD /api/shops
│   │       ├── returns.py     # /api/returns (WB, Ozon, YM)
│   │       ├── billing.py     # /api/billing
│   │       ├── admin.py       # /api/admin (requires is_admin=true)
│   │       └── yandex_auth.py # Yandex OAuth callback
│   └── frontend/
│       └── src/
│           ├── stores/auth.ts # Pinia auth store (user + isAdmin)
│           ├── router/        # Vue Router with auth guards
│           └── views/
│               ├── Profile.vue
│               ├── Dashboard.vue
│               ├── Billing.vue
│               └── admin/     # Admin panel (AdminLayout, Users, Shops, Tokens)
├── .env                       # Local secrets — do NOT commit
├── .env.example               # Template for environment variables
└── returns_history.db         # SQLite returns history (auto-created)
```

## User Roles

- **Regular user** — sees Profile, Dashboard, Billing
- **Admin** (`is_admin = true` in Supabase `profiles` table) — sees only the Admin panel (Users, Shops, Tokens management). Admin status is cached in `localStorage` so the panel stays accessible during brief DB outages.

## OAuth

### Google
Configure in Supabase dashboard under **Authentication → Providers → Google**. Uses Supabase's built-in OAuth flow.

### Yandex
Handled by the custom backend route (`/api/auth/yandex`). Register `http://localhost:8000/api/auth/yandex/callback` as a redirect URI in your Yandex OAuth application.

## WSL / DNS Notes

If running inside WSL and hitting `Temporary failure in name resolution` for the Supabase DB host, fix WSL DNS:

```bash
# /etc/wsl.conf
[network]
generateResolvConf = false

# /etc/resolv.conf
nameserver 8.8.8.8
nameserver 8.8.4.4
```

Then restart WSL: `wsl --shutdown` from Windows, reopen the terminal.
