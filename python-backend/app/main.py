import json
import logging
import sys
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .routes import router

# ─── Logging setup ───────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("nh")

# ─── App ─────────────────────────────────────────────────────────

app = FastAPI(title="Azure Notification Hubs - Python Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request logging middleware ──────────────────────────────────


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = uuid.uuid4().hex[:8]
    start = time.perf_counter()

    logger.info(f"[{request_id}] --> {request.method} {request.url.path}")

    try:
        body = await request.body()
        if body:
            try:
                logger.debug(f"[{request_id}] Body: {body.decode()[:500]}")
            except Exception:
                pass
    except Exception:
        pass

    response = await call_next(request)

    elapsed = (time.perf_counter() - start) * 1000
    status = response.status_code
    level = "info" if status < 400 else "error"
    getattr(logger, level)(
        f"[{request_id}] <-- {request.method} {request.url.path} {status} ({elapsed:.0f}ms)"
    )

    return response


# ─── Global exception handler ───────────────────────────────────


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
    )


# ─── Routes ──────────────────────────────────────────────────────

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
