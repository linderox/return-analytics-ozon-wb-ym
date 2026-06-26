import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from webapp.backend.routers import shops, profile, returns, billing, admin, yandex_auth

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
for _noisy in ("httpx", "httpcore", "hpack"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)
logger = logging.getLogger("main")

app = FastAPI(title="Marketplace Returns SaaS")

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    logger.info(f"→ {request.method} {request.url.path}")
    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        logger.exception(
            f"✗ UNHANDLED {request.method} {request.url.path} ({elapsed:.0f}ms): {type(exc).__name__}: {exc}"
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": type(exc).__name__},
        )
    elapsed = (time.perf_counter() - start) * 1000
    status = response.status_code
    level = logging.WARNING if status >= 400 else logging.INFO
    logger.log(level, f"← {request.method} {request.url.path} {status} ({elapsed:.0f}ms)")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        f"[global_exception_handler] Unhandled {type(exc).__name__} on "
        f"{request.method} {request.url.path}: {exc}"
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


app.include_router(shops.router, prefix="/api/shops", tags=["shops"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(returns.router, prefix="/api/returns", tags=["returns"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(yandex_auth.router, prefix="/api/auth/yandex", tags=["auth"])


@app.get("/")
async def root():
    return {"message": "Marketplace Returns API is running"}
