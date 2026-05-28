"""Use case: processar webhook do Pipefy com idempotência transacional por estados."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.domain.entities.cliente import ClienteJaProcessadoError
from src.domain.repositories.interfaces import ClienteRepository, EventoRepository, PipefyService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessarWebhookInput:
    event_id: str
    card_id: str
    cliente_email: str


@dataclass(frozen=True)
class ProcessarWebhookOutput:
    status: str           # "processed" | "already_processed"
    event_id: str
    card_id: str
    pipefy_sync: str      # "ok" | "failed" — estado da sincronização externa
    prioridade: str | None = None
    cliente_nome: str | None = None


class ClienteNaoEncontradoError(LookupError):
    pass


class CardIdDivergentError(ValueError):
    pass


class ProcessarWebhookUseCase:
    def __init__(
        self,
        cliente_repo: ClienteRepository,
        evento_repo: EventoRepository,
        pipefy_service: PipefyService,
    ) -> None:
        self._clientes = cliente_repo
        self._eventos = evento_repo
        self._pipefy = pipefy_service

    def executar(self, dados: ProcessarWebhookInput) -> ProcessarWebhookOutput:
        logger.info("Webhook recebido: event_id=%s", dados.event_id)

        # 1. Idempotência transacional — registra como "received" ou detecta "processed"
        if not self._eventos.registrar_se_novo(dados.event_id, dados.card_id):
            logger.info("Evento %s já processado — ignorando.", dados.event_id)
            return ProcessarWebhookOutput(
                status="already_processed",
                event_id=dados.event_id,
                card_id=dados.card_id,
                pipefy_sync="ok",
            )

        try:
            # 2. Buscar cliente
            cliente = self._clientes.buscar_por_email(dados.cliente_email)
            if not cliente:
                raise ClienteNaoEncontradoError(
                    f"Cliente '{dados.cliente_email}' não encontrado."
                )

            # 3. Validar que card_id pertence a este cliente
            if cliente.card_id and cliente.card_id != dados.card_id:
                raise CardIdDivergentError(
                    f"card_id '{dados.card_id}' não corresponde ao cliente '{dados.cliente_email}'."
                )

            # 4. Processar entidade (regra de domínio)
            try:
                cliente.processar()
            except ClienteJaProcessadoError:
                logger.warning("Cliente %s já estava processado.", dados.cliente_email)
                raise

            # 5. Persistir
            self._clientes.atualizar(cliente)

            # 6. Atualizar card no Pipefy — rastreia sucesso/falha separadamente
            pipefy_sync = "ok"
            try:
                self._pipefy.atualizar_card(
                    card_id=dados.card_id,
                    status=cliente.status,
                    prioridade=cliente.prioridade.value,
                )
            except Exception:
                pipefy_sync = "failed"
                logger.exception("Falha ao atualizar card %s no Pipefy.", dados.card_id)

            # 7. Marcar evento como processado com sucesso
            self._eventos.marcar_processado(dados.event_id)

            return ProcessarWebhookOutput(
                status="processed",
                event_id=dados.event_id,
                card_id=dados.card_id,
                pipefy_sync=pipefy_sync,
                prioridade=cliente.prioridade.value,
                cliente_nome=cliente.nome,
            )

        except Exception:
            # Qualquer falha marca o evento como "failed" — permite retry futuro
            self._eventos.marcar_falhou(dados.event_id)
            raise
