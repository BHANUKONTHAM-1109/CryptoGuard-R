"""
CryptoGuard-R - Main Application Entry Point
AI & Cryptography Based Defense Against AI-Powered Phishing Attacks
"""

from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_crypto import router as crypto_router
from app.api.routes_phishing import router as phishing_router
from app.api.routes_robot import router as robot_router
from app.api.routes_auth import router as auth_router
from app.api.routes_admin import router as admin_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.rate_limit import RateLimitMiddleware

# Initialize logging (runs before FastAPI startup)
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("Starting %s (env=%s)", settings.app_name, settings.app_env)
    if not settings.is_production and "change-me" in settings.secret_key.lower():
        logger.warning("Using default SECRET_KEY; set a strong value in .env for production")
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title="CryptoGuard-R",
    description="AI & Cryptography Based Defense Against AI-Powered Phishing Attacks on Robotic and Enterprise Systems",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting (basic) - before CORS
app.add_middleware(RateLimitMiddleware)

# CORS - use "*" in dev; set CORS_ORIGINS env in production for restrictive list
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(phishing_router)
app.include_router(crypto_router)
app.include_router(robot_router)
app.include_router(admin_router)

# Serve frontend at /ui (main.py -> app -> backend -> cryptoguard-r)
_frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(_frontend_dir), html=True), name="ui")


@app.get("/")
def root():
    """Health check / root endpoint."""
    return {
        "status": "ok",
        "service": "CryptoGuard-R",
        "message": "AI & Cryptography defense system is running",
    }


@app.get("/health")
def health():
    """Health check for load balancers and monitoring."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
