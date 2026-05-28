"""Middlewares da aplicação — Correlation ID e segurança do webhook."""

from __future__ import annotations

import hashlib
import hmac
import logging
import uuid

from fastapi import HTTPException, Request

from src.config import get_settings

logger = logging.getLogger(__name__)

# Chave de contexto para o request_id (injetado por cada request)
REQUEST_ID_KEY = "request_id"


def gerar_request_id() -> str:
    return str(uuid.uuid4())[:8]


async def validar_assinatura_pipefy(request: Request) -> None:
    """
    Valida a assinatura HMAC-SHA256 do webhook Pipefy.
    Header esperado: X-Pipefy-Signature: sha256=<hex>

    Em dev (app_env=dev) ou sem secret configurado, a validação é ignorada.
    """
    cfg = get_settings()

    if not cfg.pipefy_webhook_secret:
        if cfg.is_production:
            logger.error("PIPEFY_WEBHOOK_SECRET não configurado em produção!")
            raise HTTPException(status_code=500, detail="Configuração de segurança ausente.")
        logger.warning("Webhook sem validação de assinatura (dev mode).")
        return

    signature_header = request.headers.get("X-Pipefy-Signature", "")
    if not signature_header.startswith("sha256="):
        raise HTTPException(
            status_code=401,
            detail="Assinatura do webhook ausente ou inválida.",
        )

    body = await request.body()
    expected = hmac.new(
        cfg.pipefy_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    received = signature_header.removeprefix("sha256=")

    if not hmac.compare_digest(expected, received):
        logger.warning("Assinatura inválida no webhook — possível chamada não autorizada.")
        raise HTTPException(status_code=401, detail="Assinatura do webhook inválida.")
