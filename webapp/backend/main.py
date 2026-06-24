from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from webapp.backend.routers import shops, profile, returns, billing, admin

app = FastAPI(title="Marketplace Returns SaaS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(shops.router, prefix="/api/shops", tags=["shops"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(returns.router, prefix="/api/returns", tags=["returns"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def root():
    return {"message": "Marketplace Returns API is running"}
