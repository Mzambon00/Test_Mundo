"""Use case: reprocessar clientes com integração Pipefy pendente."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.domain.repositories.interfaces import ClienteRepository, PipefyService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReprocessarPendentesOutput:
    total_encontrados: int
    total_sucesso: int
    total_falha: int
    detalhes: list[dict]  # type: ignore[type-arg]


class ReprocessarPendentesUseCase:
    def __init__(self, cliente_repo: ClienteRepository, pipefy_service: PipefyService) -> None:
        self._repo = cliente_repo
        self._pipefy = pipefy_service

    def executar(self) -> ReprocessarPendentesOutput:
        pendentes = self._repo.buscar_pendentes_pipefy()
        logger.info("Reprocessando %d clientes com integração pendente.", len(pendentes))

        sucesso = 0
        falha = 0
        detalhes = []

        for cliente in pendentes:
            try:
                card_id = self._pipefy.criar_card(cliente)
                cliente.card_id = card_id
                cliente.integracao_pipefy = "completo"
                self._repo.atualizar(cliente)
                sucesso += 1
                detalhes.append({
                    "email": str(cliente.email),
                    "resultado": "sucesso",
                    "card_id": card_id,
                })
                logger.info("Card criado para %s: %s", cliente.email, card_id)
            except Exception as exc:
                falha += 1
                detalhes.append({
                    "email": str(cliente.email),
                    "resultado": "falha",
                    "erro": str(exc),
                })
                logger.exception("Falha ao reprocessar %s.", cliente.email)

        return ReprocessarPendentesOutput(
            total_encontrados=len(pendentes),
            total_sucesso=sucesso,
            total_falha=falha,
            detalhes=detalhes,
        )
