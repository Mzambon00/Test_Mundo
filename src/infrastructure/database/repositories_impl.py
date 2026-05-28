"""Implementações SQLAlchemy dos repositórios do domínio."""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.entities.cliente import Cliente
from src.domain.repositories.interfaces import ClienteRepository, EventoRepository
from src.domain.value_objects.email import Email
from src.domain.value_objects.prioridade import Prioridade
from src.infrastructure.database.models import ClienteModel, EventoModel

logger = logging.getLogger(__name__)


class SQLAlchemyClienteRepository(ClienteRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def salvar(self, cliente: Cliente) -> Cliente:
        model = ClienteModel(
            nome=cliente.nome,
            email=str(cliente.email),
            tipo_solicitacao=cliente.tipo_solicitacao,
            valor_patrimonio=cliente.valor_patrimonio,
            status=cliente.status,
            prioridade=cliente.prioridade.value,
            card_id=cliente.card_id,
            integracao_pipefy=cliente.integracao_pipefy,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        cliente.id = model.id
        return cliente

    def buscar_por_email(self, email: str) -> Cliente | None:
        model = (
            self._db.query(ClienteModel)
            .filter(ClienteModel.email == email.strip().lower())
            .first()
        )
        return self._to_entity(model) if model else None

    def buscar_por_card_id(self, card_id: str) -> Cliente | None:
        model = (
            self._db.query(ClienteModel)
            .filter(ClienteModel.card_id == card_id)
            .first()
        )
        return self._to_entity(model) if model else None

    def buscar_pendentes_pipefy(self) -> list[Cliente]:
        """Retorna todos os clientes com integração Pipefy pendente."""
        models = (
            self._db.query(ClienteModel)
            .filter(ClienteModel.integracao_pipefy == "integration_pending")
            .all()
        )
        return [self._to_entity(m) for m in models]

    def atualizar(self, cliente: Cliente) -> Cliente:
        model = self._db.query(ClienteModel).filter_by(id=cliente.id).first()
        if not model:
            raise LookupError(f"Cliente id={cliente.id} não encontrado.")
        model.status = cliente.status
        model.prioridade = cliente.prioridade.value
        model.card_id = cliente.card_id
        model.integracao_pipefy = cliente.integracao_pipefy
        self._db.commit()
        self._db.refresh(model)
        return cliente

    @staticmethod
    def _to_entity(model: ClienteModel) -> Cliente:
        cliente = Cliente.__new__(Cliente)
        cliente.id = model.id
        cliente.nome = model.nome
        cliente.email = Email(model.email)
        cliente.tipo_solicitacao = model.tipo_solicitacao
        cliente.valor_patrimonio = model.valor_patrimonio
        cliente.status = model.status
        cliente.prioridade = Prioridade(model.prioridade)
        cliente.card_id = model.card_id
        cliente.integracao_pipefy = model.integracao_pipefy
        return cliente


class SQLAlchemyEventoRepository(EventoRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def registrar_se_novo(self, event_id: str, card_id: str) -> bool:
        """Tenta inserir evento como 'received'.
        - Se já existe com status 'processed' → retorna False (idempotente).
        - Se já existe com status 'failed' → reinsere como 'received' → retorna True (permite retry).
        - Se não existe → insere → retorna True.
        """
        existente = (
            self._db.query(EventoModel)
            .filter(EventoModel.event_id == event_id)
            .first()
        )
        if existente:
            if existente.status == "processed":
                return False
            # "failed" ou "received" travado → permite retry
            existente.status = "received"
            self._db.commit()
            return True

        try:
            self._db.add(EventoModel(event_id=event_id, card_id=card_id, status="received"))
            self._db.commit()
            return True
        except IntegrityError:
            self._db.rollback()
            logger.warning("Race condition detectada no evento %s — tratando como duplicado.", event_id)
            return False

    def marcar_processado(self, event_id: str) -> None:
        self._atualizar_status(event_id, "processed")

    def marcar_falhou(self, event_id: str) -> None:
        self._atualizar_status(event_id, "failed")

    def _atualizar_status(self, event_id: str, status: str) -> None:
        evento = self._db.query(EventoModel).filter_by(event_id=event_id).first()
        if evento:
            evento.status = status
            self._db.commit()
