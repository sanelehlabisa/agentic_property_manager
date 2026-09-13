import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.auth import router as auth_router
from app.api.categories import router as categories_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.predictions import router as predictions_router
from app.api.properties import router as properties_router
from app.api.provider import router as provider_router
from app.api.reports import router as reports_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="Agentic Property Manager API",
    version=__version__,
    description="Backend API for the Agentic Property Manager proof of concept.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.middleware("http")
async def log_request(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    started_at = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started_at) * 1000

    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s -> %s in %.2fms request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        request_id,
    )
    return response


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(properties_router)
app.include_router(reports_router)
app.include_router(predictions_router)
app.include_router(jobs_router)
app.include_router(provider_router)
