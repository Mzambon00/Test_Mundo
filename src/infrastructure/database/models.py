"""Modelos ORM do SQLAlchemy (camada de infraestrutura)."""

from __future__ import annotations

from sqlalchemy import Float, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ClienteModel(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True, index=True)
    tipo_solicitacao: Mapped[str] = mapped_column(String(100), nullable=False)
    valor_patrimonio: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Aguardando Análise")
    prioridade: Mapped[str] = mapped_column(String(50), nullable=False)
    card_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Rastreia sincronização com Pipefy: "completo", "integration_pending", "sync_failed"
    integracao_pipefy: Mapped[str] = mapped_column(
        String(30), nullable=False, default="integration_pending"
    )


class EventoModel(Base):
    """Registro de eventos do webhook com controle de estado para idempotência transacional."""

    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    card_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Estados: "received" | "processed" | "failed"
    # "received"  → em processamento (ou crash durante)
    # "processed" → concluído com sucesso
    # "failed"    → falhou, pode ser retentado com um novo event_id
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="received")
