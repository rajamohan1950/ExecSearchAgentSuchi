import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.storage_service import storage_service
from app.routers import health, auth, users, profiles
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure storage bucket exists
    try:
        storage_service.ensure_bucket()
        logger.info("Storage bucket ready")
    except Exception as e:
        logger.warning(f"Could not initialize storage bucket: {e}")
    yield
    # Shutdown
    logger.info("Shutting down API gateway")


app = FastAPI(
    title="Suchi Exec Search Agent API",
    description="Phase-1: User profile management via LinkedIn PDF upload",
    version="1.0.0",
    lifespan=lifespan,
)

# Build CORS origins: local/dev + any from env (e.g. Vercel frontend URL)
_cors_origins = ["http://localhost:3000", "http://frontend:3000"]
if settings.cors_origins:
    _cors_origins = _cors_origins + [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(profiles.router, prefix="/api/v1")
