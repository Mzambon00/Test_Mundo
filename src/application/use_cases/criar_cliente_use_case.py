"""Use case: criar cliente, calcular prioridade, persistir e abrir card."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.domain.entities.cliente import Cliente
from src.domain.repositories.interfaces import ClienteRepository, PipefyService
from src.domain.value_objects.email import Email, EmailInvalidoError

logger = logging.getLogger(__name__)


class EmailDuplicadoError(ValueError):
    pass


@dataclass(frozen=True)
class CriarClienteInput:
    cliente_nome: str
    cliente_email: str
    tipo_solicitacao: str
    valor_patrimonio: float


@dataclass(frozen=True)
class CriarClienteOutput:
    id: int
    nome: str
    email: str
    status: str
    prioridade: str
    card_id: str
    integracao_pipefy: str  # "completo" | "integration_pending"


class CriarClienteUseCase:
    def __init__(self, cliente_repo: ClienteRepository, pipefy_service: PipefyService) -> None:
        self._repo = cliente_repo
        self._pipefy = pipefy_service

    def executar(self, dados: CriarClienteInput) -> CriarClienteOutput:
        logger.info("Criando cliente: %s", dados.cliente_email)

        try:
            email = Email(dados.cliente_email)
        except EmailInvalidoError as exc:
            raise ValueError(str(exc)) from exc

        if self._repo.buscar_por_email(str(email)):
            raise EmailDuplicadoError(f"E-mail '{email}' já cadastrado.")

        cliente = Cliente(
            nome=dados.cliente_nome,
            email=email,
            tipo_solicitacao=dados.tipo_solicitacao,
            valor_patrimonio=dados.valor_patrimonio,
            integracao_pipefy="integration_pending",
        )
        cliente = self._repo.salvar(cliente)

        card_id = ""
        try:
            card_id = self._pipefy.criar_card(cliente)
            cliente.card_id = card_id
            cliente.integracao_pipefy = "completo"
            self._repo.atualizar(cliente)
        except Exception:
            logger.exception("Falha ao criar card no Pipefy para %s — integration_pending.", email)

        assert cliente.id is not None
        return CriarClienteOutput(
            id=cliente.id,
            nome=cliente.nome,
            email=str(cliente.email),
            status=cliente.status,
            prioridade=cliente.prioridade.value,
            card_id=card_id,
            integracao_pipefy=cliente.integracao_pipefy,
        )
