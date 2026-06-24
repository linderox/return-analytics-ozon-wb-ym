from fastapi import APIRouter, Depends, HTTPException, Request
from webapp.backend.auth import get_current_user
from core.db.database import get_supabase_client
import uuid
from datetime import datetime, timedelta, timezone

router = APIRouter()

PLAN_PRICES_RUB = {"basic": 499, "pro": 999}

@router.post("/create")
async def create_payment(plan: str, user_id: str = Depends(get_current_user)):
    if plan not in PLAN_PRICES_RUB:
        raise HTTPException(status_code=400, detail="Invalid plan")

    payment_id = str(uuid.uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    client = await get_supabase_client()
    await client.table('subscriptions').insert({
        'user_id': user_id,
        'plan': plan,
        'expires_at': expires_at,
        'yookassa_id': payment_id,
        'status': 'pending',
    }).execute()

    return {
        "payment_id": payment_id,
        "confirmation_url": f"https://yookassa.ru/payments/external/confirmation?id={payment_id}",
        "sbp_qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    }

@router.get("/status/{payment_id}")
async def get_payment_status(payment_id: str, user_id: str = Depends(get_current_user)):
    client = await get_supabase_client()
    result = await client.table('subscriptions').select('status,plan').eq('yookassa_id', payment_id).eq('user_id', user_id).maybe_single().execute()
    if result.data is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"status": result.data['status'], "plan": result.data['plan']}

@router.post("/webhook")
async def yookassa_webhook(request: Request):
    data = await request.json()
    yookassa_id = data.get("object", {}).get("id")
    status = data.get("object", {}).get("status")

    if status == "succeeded":
        client = await get_supabase_client()
        sub_result = await client.table('subscriptions').update({'status': 'succeeded'}).eq('yookassa_id', yookassa_id).execute()
        if sub_result.data:
            sub = sub_result.data[0]
            await client.table('profiles').update({'plan': sub['plan']}).eq('id', sub['user_id']).execute()

    return {"status": "ok"}
