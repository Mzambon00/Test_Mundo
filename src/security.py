"""Seguranca: HMAC para webhook e token para endpoints administrativos."""
from __future__ import annotations
import hashlib
import hmac
import logging
from fastapi import Header, HTTPException, Request
from src.config import Settings

logger = logging.getLogger(__name__)

async def verificar_assinatura_webhook(
    request: Request,
    x_pipefy_signature: str | None = Header(default=None),
) -> None:
    cfg = Settings()
    secret = cfg.webhook_secret
    if not secret:
        if cfg.env != "dev":
            raise HTTPException(
                status_code=503,
                detail="WEBHOOK_SECRET nao configurado.",
            )
        logger.warning("WEBHOOK_SECRET vazio - validacao HMAC ignorada (apenas dev).")
        return
    if not x_pipefy_signature:
        raise HTTPException(status_code=401, detail="Header X-Pipefy-Signature ausente.")
    body = await request.body()
    esperada = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(esperada, x_pipefy_signature):
        logger.warning("Assinatura HMAC invalida recebida no webhook.")
        raise HTTPException(status_code=401, detail="Assinatura do webhook invalida.")

async def require_admin(
    x_admin_token: str | None = Header(default=None),
) -> None:
    cfg = Settings()
    token_esperado = cfg.admin_token
    if not token_esperado:
        if cfg.env != "dev":
            raise HTTPException(
                status_code=503,
                detail="ADMIN_TOKEN nao configurado.",
            )
        logger.warning("ADMIN_TOKEN vazio - autenticacao admin ignorada (apenas dev).")
        return
    if not x_admin_token or x_admin_token != token_esperado:
        logger.warning("Tentativa de acesso admin com token invalido ou ausente.")
        raise HTTPException(status_code=401, detail="Token administrativo invalido ou ausente.")