import os
import logging
import httpx
from fastapi import Request, HTTPException
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("auth")

SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL")
ALGORITHM = "ES256"

_jwks_cache: list | None = None


async def _fetch_jwks() -> list:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    if not SUPABASE_JWKS_URL:
        logger.error("[auth] SUPABASE_JWKS_URL is not set in environment")
        raise HTTPException(status_code=503, detail="Authentication service not configured (JWKS URL missing)")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(SUPABASE_JWKS_URL, timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json()["keys"]
            logger.info(f"[auth] JWKS loaded — {len(_jwks_cache)} key(s)")
            return _jwks_cache
    except httpx.TimeoutException:
        logger.error("[auth] JWKS fetch timed out")
        raise HTTPException(status_code=503, detail="Authentication service timeout — try again")
    except httpx.HTTPStatusError as e:
        logger.error(f"[auth] JWKS endpoint returned HTTP {e.response.status_code}")
        raise HTTPException(status_code=503, detail=f"Authentication service error: HTTP {e.response.status_code}")
    except Exception as e:
        logger.exception(f"[auth] Unexpected JWKS fetch error: {e}")
        raise HTTPException(status_code=503, detail=f"Authentication service unavailable: {type(e).__name__}")


async def get_current_user(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    token = auth_header.split(" ")[1]

    try:
        keys = await _fetch_jwks()
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        key = next((k for k in keys if k.get("kid") == kid), keys[0] if keys else None)
        if key is None:
            raise HTTPException(status_code=503, detail="No suitable key found in JWKS")

        # For local testing, we might want a fallback secret if JWKS is not used,
        # but here we strictly follow Supabase JWKS.
        payload = jwt.decode(token, key, algorithms=[ALGORITHM], options={"verify_aud": False})
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        logger.debug(f"[auth] JWT decoded — sub={user_id!r} email={email!r} role={role!r}")

        if user_id is None:
            logger.warning("[auth] JWT missing 'sub' claim — rejecting")
            raise HTTPException(status_code=401, detail="Invalid token: missing subject")

        return user_id

    except HTTPException:
        raise
    except JWTError as e:
        logger.warning(f"[auth] JWTError: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    except Exception as e:
        logger.exception(f"[auth] Unexpected error during JWT validation: {e}")
        raise HTTPException(status_code=503, detail="Authentication service error")
