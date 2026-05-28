from fastapi import FastAPI
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
        logger.info("Configuracoes validadas com sucesso")
    except ValueError as e:
        logger.error(f"Erro de configuracao: {e}")
        raise
    
    if settings.auto_create_tables:
        logger.warning("Auto create tables ativado - apenas para desenvolvimento")
        Base.metadata.create_all(bind=engine)
    
    yield
    logger.info("Encerrando aplicacao")

app = FastAPI(
    title="Mundo Invest API",
    version=settings.app_version,
    lifespan=lifespan
)

app.include_router(clientes.router, prefix="/api", tags=["clientes"])
app.include_router(webhook.router, prefix="/api", tags=["webhooks"])
app.include_router(admin.router, prefix="/api", tags=["admin"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.env}

@app.get("/")
async def root():
    return {
        "app": "Mundo Invest API",
        "version": settings.app_version,
        "environment": settings.env
    }
