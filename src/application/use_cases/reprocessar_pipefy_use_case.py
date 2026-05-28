"""Use case: reprocessar clientes com integração Pipefy pendente."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.domain.repositories.interfaces import ClienteRepository, PipefyService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReprocessarPipefyOutput:
    total: int
    sucesso: int
    falhou: int
    detalhes: list[dict]  # type: ignore[type-arg]


class ReprocessarPipefyUseCase:
    def __init__(
        self,
        cliente_repo: ClienteRepository,
        pipefy_service: PipefyService,
    ) -> None:
        self._repo = cliente_repo
        self._pipefy = pipefy_service

    def executar(self) -> ReprocessarPipefyOutput:
        pendentes = self._repo.buscar_pendentes_pipefy()
        logger.info("Reprocessando %d clientes com integration_pending.", len(pendentes))

        sucesso = 0
        falhou = 0
        detalhes = []

        for cliente in pendentes:
            try:
                card_id = self._pipefy.criar_card(cliente)
                cliente.card_id = card_id
                cliente.integracao_pipefy = "completo"
                self._repo.atualizar(cliente)
                sucesso += 1
                detalhes.append({"email": str(cliente.email), "status": "sucesso", "card_id": card_id})
                logger.info("Card criado para %s: %s", cliente.email, card_id)
            except Exception as exc:
                falhou += 1
                detalhes.append({"email": str(cliente.email), "status": "falhou", "erro": str(exc)})
                logger.exception("Falha ao reprocessar %s.", cliente.email)

        return ReprocessarPipefyOutput(
            total=len(pendentes),
            sucesso=sucesso,
            falhou=falhou,
            detalhes=detalhes,
        )
