from dataclasses import dataclass
from typing import Optional
from src.domain.entities import Cliente
from src.domain.repositories import ClienteRepository, EventoRepository
from src.infrastructure.graphql.pipefy_adapter import PipefyAdapter as PipefyClient
from src.domain.exceptions import ClienteNaoEncontradoError, CardIdDivergentError
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProcessarWebhookInput:
    event_id: str
    card_id: str
    cliente_email: str

@dataclass
class ProcessarWebhookOutput:
    status: str
    event_id: str
    card_id: str
    pipefy_sync: str
    success: bool = True
    message: str = ""
    prioridade: str = ""
    cliente_nome: str = ""
    cliente: Optional[Cliente] = None

class ProcessarWebhookUseCase:
    def __init__(self, cliente_repo: ClienteRepository, evento_repo: EventoRepository, pipefy_client: PipefyClient):
        self.cliente_repo = cliente_repo
        self.evento_repo = evento_repo
        self.pipefy_client = pipefy_client

    async def execute(self, input_data: ProcessarWebhookInput) -> ProcessarWebhookOutput:
        if self.evento_repo.evento_existe(input_data.event_id):
            logger.warning(f"Evento {input_data.event_id} ja processado")
            return ProcessarWebhookOutput(
                status="already_processed",
                event_id=input_data.event_id,
                card_id=input_data.card_id,
                pipefy_sync="skipped",
                success=False,
                message="Evento ja processado anteriormente"
            )

        try:
            cliente = self.cliente_repo.buscar_por_email(input_data.cliente_email)
            if not cliente:
                raise ClienteNaoEncontradoError(f"Cliente {input_data.cliente_email} nao encontrado")

            if cliente.card_id and cliente.card_id != input_data.card_id:
                raise CardIdDivergentError(f"Card ID divergente: esperado {cliente.card_id}, recebido {input_data.card_id}")

            try:
                self.pipefy_client.atualizar_card(card_id=input_data.card_id, status="processed", prioridade=cliente.prioridade.value)
                pipefy_sync = "success"
            except Exception as e:
                logger.error(f"Falha ao atualizar Pipefy: {e}")
                pipefy_sync = "failed"

            self.evento_repo.registrar_evento(
                event_id=input_data.event_id,
                status="processed",
                metadata={"card_id": input_data.card_id, "email": input_data.cliente_email}
            )

            return ProcessarWebhookOutput(
                status="processed",
                event_id=input_data.event_id,
                card_id=input_data.card_id,
                pipefy_sync=pipefy_sync,
                success=True,
                message="Webhook processado com sucesso",
                prioridade=cliente.prioridade.value,
                cliente_nome=cliente.nome,
                cliente=cliente
            )

        except (ClienteNaoEncontradoError, CardIdDivergentError) as e:
            self.evento_repo.registrar_evento(
                event_id=input_data.event_id,
                status="failed",
                metadata={"error": str(e)}
            )
            return ProcessarWebhookOutput(
                status="error",
                event_id=input_data.event_id,
                card_id=input_data.card_id,
                pipefy_sync="failed",
                success=False,
                message=str(e)
            )