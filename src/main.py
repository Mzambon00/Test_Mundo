import uuid
from fastapi import FastAPI, Request
from starlette.responses import Response
from src.config import settings
from src.api.routers import clientes, webhook, admin
from src.infrastructure.database import engine, Base
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Iniciando aplicacao - Ambiente: {settings.env}")
    try:
        settings.validate_critical_production()
    except ValueError as e:
        logger.error(f"Erro de configuracao: {e}")
        raise
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    yield
    logger.info("Encerrando aplicacao")

app = FastAPI(title="Mundo Invest API", version=settings.app_version, lifespan=lifespan)

@app.middleware("http")
async def add_request_id(request: Request, call_next) -> Response:
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response

app.include_router(clientes.router)
app.include_router(webhook.router)
app.include_router(admin.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.app_version}

@app.get("/")
async def root():
    return {"app": "Mundo Invest API", "version": settings.app_version, "environment": settings.env}