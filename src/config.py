"""Configurações da aplicação via variáveis de ambiente."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Fonte única de versão — pyproject.toml e health check usam este valor
APP_VERSION = "2.2.0"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "sqlite:///./mundo_invest.db"
    pipefy_token: str = ""
    pipefy_pipe_id: str = "302428309"
    db_echo: bool = False
    app_version: str = APP_VERSION

    # "dev" ignora validações obrigatórias; qualquer outro valor = produção
    env: str = "dev"

    # Secret HMAC para validar webhooks do Pipefy (obrigatório fora de dev)
    webhook_secret: str = ""

    # Token para proteger endpoints /admin/* (obrigatório fora de dev)
    admin_token: str = ""

    # True apenas para demo/dev — em produção use Alembic
    auto_create_tables: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
