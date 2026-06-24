import os
import sqlite3
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_DB_PATH = "returns_history.db"

async def get_db_connection():
    # Still using asyncpg for Supabase (profiles, shops)
    if not DATABASE_URL:
        # Mock connection or raise clearer error for local testing
        raise ValueError("DATABASE_URL environment variable is not set. Please check your .env file.")
    return await asyncpg.connect(DATABASE_URL)

def get_sqlite_conn():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

async def ensure_returns_table(user_id: str, marketplace: str):
    prefix = user_id.replace("-", "")[:12]
    table_name = f"{prefix}_returns_{marketplace}"

    conn = get_sqlite_conn()
    cursor = conn.cursor()

    if marketplace == "wb":
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            srid TEXT PRIMARY KEY,
            orderDt TEXT,
            nmId BIGINT,
            brand TEXT,
            subjectName TEXT,
            techSize TEXT,
            barcode TEXT,
            shkId BIGINT,
            returnType TEXT,
            reason TEXT,
            status TEXT,
            isStatusActive INT,
            readyToReturnDt TEXT,
            completedDt TEXT,
            expiredDt TEXT,
            dstOfficeId INT,
            dstOfficeAddress TEXT,
            orderId BIGINT,
            stickerId BIGINT,
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    elif marketplace == "ym":
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id BIGINT PRIMARY KEY,
            orderId BIGINT,
            returnType TEXT,
            shipmentStatus TEXT,
            refundStatus TEXT,
            creationDate TEXT,
            updateDate TEXT,
            pickupTillDate TEXT,
            amount NUMERIC,
            currency TEXT,
            shipmentRecipientType TEXT,
            logisticPoint TEXT,
            items TEXT,
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    elif marketplace == "ozon":
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            posting_number TEXT PRIMARY KEY,
            added_at TEXT,
            barcode TEXT,
            clearing_id BIGINT,
            offer_id TEXT,
            status TEXT,
            return_reason TEXT,
            return_date TEXT,
            received_at TEXT,
            quantity INT,
            price NUMERIC,
            is_opened BOOLEAN,
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    else:
        conn.close()
        raise ValueError(f"Unknown marketplace: {marketplace}")

    cursor.execute(sql)
    conn.commit()
    conn.close()
    return table_name

async def init_billing_tables(conn):
    # Billing stays in Supabase
    sql = """
    CREATE TABLE IF NOT EXISTS public.subscriptions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL,
        plan TEXT NOT NULL,
        started_at TIMESTAMPTZ DEFAULT NOW(),
        expires_at TIMESTAMPTZ NOT NULL,
        yookassa_id TEXT,
        sbp_qr_code TEXT,
        status TEXT DEFAULT 'pending'
    );
    """
    await conn.execute(sql)

async def init_profiles_and_shops(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS public.profiles (
      id UUID PRIMARY KEY,
      fio TEXT,
      phone TEXT,
      plan TEXT NOT NULL DEFAULT 'free',
      is_admin BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS public.shops (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL,
      marketplace TEXT NOT NULL,
      name TEXT NOT NULL,
      google_sheet_id TEXT,
      ozon_client_id TEXT,
      ozon_client_secret TEXT,
      wb_token TEXT,
      ym_client_id TEXT,
      ym_client_secret TEXT,
      ym_campaign_id TEXT,
      status_filter TEXT[],
      schema_filter TEXT[],
      is_active BOOLEAN DEFAULT TRUE,
      last_synced_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    await conn.execute(sql)
