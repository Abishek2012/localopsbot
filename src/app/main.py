from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.database import initialize_database


app = FastAPI(
    title=settings.app_name,
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    initialize_database()


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "status": "running"
    }


@app.get("/healthz")
async def healthz():
    return {
        "status": "healthy"
    }


metrics_app = make_asgi_app()

app.mount(
    "/metrics",
    metrics_app
)