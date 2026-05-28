"""Composition root — monta a aplicação, registra routers, middlewares e handlers."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.routers import admin, clientes, webhook
from src.config import get_settings
from src.infrastructure.database.connection import create_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    cfg = get_settings()

    # P0: validações obrigatórias em produção
    if cfg.env != "dev":
        erros = []
        if not cfg.pipefy_token:
            erros.append("PIPEFY_TOKEN")
        if not cfg.webhook_secret:
            erros.append("WEBHOOK_SECRET")
        if not cfg.admin_token:
            erros.append("ADMIN_TOKEN")
        if erros:
            raise RuntimeError(
                f"Variáveis obrigatórias não configuradas em env='{cfg.env}': {', '.join(erros)}. "
                "Configure antes de iniciar em produção."
            )

    if cfg.auto_create_tables:
        create_tables()
        logger.info("Tabelas criadas/verificadas (AUTO_CREATE_TABLES=true — apenas dev).")
    else:
        logger.info("AUTO_CREATE_TABLES=false — use Alembic para migrations.")

    logger.info("Mundo Invest API v%s iniciada [env=%s]", cfg.app_version, cfg.env)
    yield


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mundo Invest API",
    version=get_settings().app_version,
    description="API de gestão de clientes com integração ao Pipefy.",
    lifespan=lifespan,
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(clientes.router)
app.include_router(webhook.router)
app.include_router(admin.router)


# ── Middleware: Correlation ID ────────────────────────────────────────────────

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["infra"])
def health() -> dict:  # type: ignore[type-arg]
    return {"status": "ok", "version": get_settings().app_version}


# ── Handler global de erros ───────────────────────────────────────────────────

@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro inesperado em %s", request.url)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor."})
