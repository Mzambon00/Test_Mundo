"""Segurança: HMAC para webhook e token para endpoints administrativos."""

from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import Header, HTTPException, Request

from src.config import get_settings

logger = logging.getLogger(__name__)


async def verificar_assinatura_webhook(
    request: Request,
    x_pipefy_signature: str | None = Header(default=None),
) -> None:
    """Valida assinatura HMAC do Pipefy.

    - Em dev com webhook_secret vazio: avisa no log, não bloqueia.
    - Em produção (env != dev): rejeita com 401 se secret vazio ou assinatura inválida.
    """
    cfg = get_settings()
    secret = cfg.webhook_secret

    if not secret:
        if cfg.env != "dev":
            # P0: produção sem secret configurado — bloqueia
            raise HTTPException(
                status_code=503,
                detail="WEBHOOK_SECRET não configurado. Configure antes de processar webhooks em produção.",
            )
        logger.warning("WEBHOOK_SECRET vazio — validação HMAC ignorada (apenas dev).")
        return

    if not x_pipefy_signature:
        raise HTTPException(status_code=401, detail="Header X-Pipefy-Signature ausente.")

    body = await request.body()
    esperada = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(esperada, x_pipefy_signature):
        logger.warning("Assinatura HMAC inválida recebida no webhook.")
        raise HTTPException(status_code=401, detail="Assinatura do webhook inválida.")


async def require_admin(
    x_admin_token: str | None = Header(default=None),
) -> None:
    """Protege endpoints /admin/*.

    - Em dev com admin_token vazio: avisa no log, não bloqueia.
    - Em produção: exige token válido; rejeita com 401 caso contrário.
    """
    cfg = get_settings()
    token_esperado = cfg.admin_token

    if not token_esperado:
        if cfg.env != "dev":
            raise HTTPException(
                status_code=503,
                detail="ADMIN_TOKEN não configurado. Configure antes de usar endpoints administrativos em produção.",
            )
        logger.warning("ADMIN_TOKEN vazio — autenticação admin ignorada (apenas dev).")
        return

    if not x_admin_token or x_admin_token != token_esperado:
        logger.warning("Tentativa de acesso admin com token inválido ou ausente.")
        raise HTTPException(status_code=401, detail="Token administrativo inválido ou ausente.")
