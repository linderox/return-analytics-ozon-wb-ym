from fastapi import APIRouter, Depends, HTTPException, Request
from webapp.backend.auth import get_current_user
from core.db.database import get_db_connection
import os
from datetime import datetime, timedelta
import uuid

router = APIRouter()

PLAN_PRICES_RUB = {"basic": 499, "pro": 999}

@router.post("/create")
async def create_payment(plan: str, user_id: str = Depends(get_current_user)):
    if plan not in PLAN_PRICES_RUB:
        raise HTTPException(status_code=400, detail="Invalid plan")

    amount = PLAN_PRICES_RUB[plan]
    payment_id = str(uuid.uuid4())

    conn = await get_db_connection()
    try:
        expires_at = datetime.now() + timedelta(days=30)
        await conn.execute(
            "INSERT INTO public.subscriptions (user_id, plan, expires_at, yookassa_id, status) VALUES ($1, $2, $3, $4, 'pending')",
            user_id, plan, expires_at, payment_id
        )
        return {
            "payment_id": payment_id,
            "confirmation_url": f"https://yookassa.ru/payments/external/confirmation?id={payment_id}",
            "sbp_qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        }
    finally:
        await conn.close()

@router.get("/status/{payment_id}")
async def get_payment_status(payment_id: str, user_id: str = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        sub = await conn.fetchrow("SELECT * FROM public.subscriptions WHERE yookassa_id = $1 AND user_id = $2", payment_id, user_id)
        if not sub:
            raise HTTPException(status_code=404, detail="Payment not found")
        return {"status": sub['status'], "plan": sub['plan']}
    finally:
        await conn.close()

@router.post("/webhook")
async def yookassa_webhook(request: Request):
    data = await request.json()
    yookassa_id = data.get("object", {}).get("id")
    status = data.get("object", {}).get("status")

    if status == "succeeded":
        conn = await get_db_connection()
        try:
            sub = await conn.fetchrow("UPDATE public.subscriptions SET status = 'succeeded' WHERE yookassa_id = $1 RETURNING user_id, plan", yookassa_id)
            if sub:
                await conn.execute("UPDATE public.profiles SET plan = $1 WHERE id = $2", sub['plan'], sub['user_id'])
        finally:
            await conn.close()

    return {"status": "ok"}
