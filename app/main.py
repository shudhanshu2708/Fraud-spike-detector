import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.admin import router as admin_router
from app.api.transactions import router as transaction_router
from app.auth.router import router as auth_router
from app.services.ml_model import fraud_model


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)

logger = logging.getLogger("vendly")


@asynccontextmanager
async def lifespan(app: FastAPI):
    fraud_model.load()

    logger.info("Fraud model loaded successfully.")

    yield

    logger.info("Vendly shutting down.")


app = FastAPI(
    title="Vendly",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    transaction_router,
    prefix="/transactions",
    tags=["transactions"],
)

app.include_router(admin_router)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    request.state.request_id = request_id

    response = await call_next(request)

    duration_ms = (
        time.perf_counter() - start_time
    ) * 1000

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "request_id=%s method=%s path=%s "
        "status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model_loaded": fraud_model.model is not None,
    }