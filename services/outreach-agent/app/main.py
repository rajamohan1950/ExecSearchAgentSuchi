import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, firms, outreach, metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Global scheduler reference for graceful shutdown
_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage scheduler lifecycle with graceful shutdown."""
    global _scheduler

    # Late import to avoid circular dependencies
    from app.agent.scheduler import create_scheduler, setup_jobs

    try:
        _scheduler = create_scheduler()
        setup_jobs(_scheduler)
        _scheduler.start()
        logger.info("Agent scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        # Service still starts — scheduler can be retried via restart
        _scheduler = None

    # Register signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(_graceful_shutdown(s)))
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

    yield

    # Shutdown
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=True)
        logger.info("Agent scheduler stopped gracefully")
    logger.info("Outreach agent service shut down")


async def _graceful_shutdown(sig):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {sig.name}, initiating graceful shutdown...")
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=True)


app = FastAPI(
    title="Suchi Outreach Agent",
    description="Autonomous executive search outreach agent — plans, emails, follows up, and adapts independently.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
_cors_origins = ["http://localhost:3000", "http://frontend:3000", "http://localhost:8000"]
if settings.cors_origins:
    _cors_origins += [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(firms.router, prefix="/api/v1")
app.include_router(outreach.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")
