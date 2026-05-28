"""Fixtures compartilhadas entre todos os testes."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.domain.entities.cliente import Cliente
from src.domain.repositories.interfaces import PipefyService
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import Base
from src.main import app
from src.security import require_admin, verificar_assinatura_webhook


# ── Banco de dados em memória ─────────────────────────────────────────────────

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


# ── Fake Pipefy ───────────────────────────────────────────────────────────────

class FakePipefyService(PipefyService):
    def __init__(self) -> None:
        self.cards_criados: list[str] = []
        self.cards_atualizados: list[tuple[str, str, str]] = []
        self.deve_falhar: bool = False

    def criar_card(self, cliente: Cliente) -> str:
        if self.deve_falhar:
            raise RuntimeError("Pipefy indisponível (simulado)")
        card_id = f"card_{cliente.nome.lower().replace(' ', '_')}"
        self.cards_criados.append(card_id)
        return card_id

    def atualizar_card(self, card_id: str, status: str, prioridade: str) -> None:
        if self.deve_falhar:
            raise RuntimeError("Pipefy indisponível (simulado)")
        self.cards_atualizados.append((card_id, status, prioridade))


@pytest.fixture
def fake_pipefy() -> FakePipefyService:
    return FakePipefyService()


# ── Client padrão (HMAC e admin bypassados — testa lógica de negócio) ─────────

@pytest.fixture
def client(db_session: Session, fake_pipefy: FakePipefyService) -> Generator[TestClient, None, None]:
    from src.api.routers import clientes, webhook, admin

    def override_db() -> Generator[Session, None, None]:
        yield db_session

    async def skip_hmac() -> None:
        return None

    async def skip_admin() -> None:
        return None

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[verificar_assinatura_webhook] = skip_hmac
    app.dependency_overrides[require_admin] = skip_admin
    # Override pipefy em cada router
    app.dependency_overrides[clientes._pipefy] = lambda: fake_pipefy
    app.dependency_overrides[webhook._pipefy] = lambda: fake_pipefy
    app.dependency_overrides[admin._pipefy] = lambda: fake_pipefy

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ── Client com segurança REAL (para testar TC-04, TC-05, TC-07) ───────────────

@pytest.fixture
def client_com_secret(db_session: Session, fake_pipefy: FakePipefyService) -> Generator[TestClient, None, None]:
    from src.api.routers import clientes, webhook, admin
    from src.config import get_settings

    get_settings.cache_clear()

    def override_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[clientes._pipefy] = lambda: fake_pipefy
    app.dependency_overrides[webhook._pipefy] = lambda: fake_pipefy
    app.dependency_overrides[admin._pipefy] = lambda: fake_pipefy
    # NÃO faz override de HMAC nem admin — testa segurança real

    with patch.dict(
        "os.environ",
        {
            "WEBHOOK_SECRET": "test_secret_hmac",
            "ADMIN_TOKEN": "admin_test_token",
            "ENV": "producao",
            "PIPEFY_TOKEN": "fake_token",
        },
    ):
        get_settings.cache_clear()
        with TestClient(app) as c:
            yield c

    get_settings.cache_clear()
    app.dependency_overrides.clear()
