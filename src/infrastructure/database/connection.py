"""Gerenciamento de conexão e sessão com o banco de dados."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings
from src.infrastructure.database.models import Base


def _make_engine() -> object:
    cfg = get_settings()
    connect_args = (
        {"check_same_thread": False} if "sqlite" in cfg.database_url else {}
    )
    return create_engine(
        cfg.database_url,
        echo=cfg.db_echo,
        connect_args=connect_args,
    )


engine = _make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Cria todas as tabelas (usado em dev/testes; produção usa Alembic)."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI — garante fechamento da sessão."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
