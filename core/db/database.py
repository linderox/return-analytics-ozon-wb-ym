import os
import sqlite3
import logging
from fastapi import HTTPException
from supabase import create_async_client, AsyncClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("database")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SQLITE_DB_PATH = "returns_history.db"

_supabase_client: AsyncClient | None = None


async def get_supabase_client() -> AsyncClient:
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        logger.error("[db] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
        raise HTTPException(
            status_code=503,
            detail="Supabase credentials not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env."
        )

    try:
        logger.info(f"[db] Connecting to Supabase: {SUPABASE_URL}")
        _supabase_client = await create_async_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("[db] Supabase client initialised")
        return _supabase_client
    except Exception as e:
        logger.exception(f"[db] Failed to create Supabase client: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Supabase: {type(e).__name__} — check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )


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
