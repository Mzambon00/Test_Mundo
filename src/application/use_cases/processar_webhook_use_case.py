from dataclasses import dataclass
from typing import Optional
from src.domain.entities import Cliente
from src.domain.repositories import ClienteRepository, EventoRepository
from src.infrastructure.pipefy import PipefyClient
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
    success: bool
    message: str
    pipefy_sync: str  # "success", "failed", "skipped"
    cliente: Optional[Cliente] = None

class ProcessarWebhookUseCase:
    def __init__(
        self,
        cliente_repo: ClienteRepository,
        evento_repo: EventoRepository,
        pipefy_client: PipefyClient
    ):
        self.cliente_repo = cliente_repo
        self.evento_repo = evento_repo
        self.pipefy_client = pipefy_client
    
    async def execute(self, input_data: ProcessarWebhookInput) -> ProcessarWebhookOutput:
        # Verificar idempotência
        if await self.evento_repo.evento_existe(input_data.event_id):
            logger.warning(f"Evento {input_data.event_id} já processado")
            return ProcessarWebhookOutput(
                success=False,
                message="Evento já processado anteriormente",
                pipefy_sync="skipped"
            )
        
        try:
            # Buscar cliente
            cliente = await self.cliente_repo.buscar_por_email(input_data.cliente_email)
            if not cliente:
                raise ClienteNaoEncontradoError(f"Cliente {input_data.cliente_email} não encontrado")
            
            # Validar card_id
            if cliente.pipefy_card_id and cliente.pipefy_card_id != input_data.card_id:
                raise CardIdDivergentError(
                    f"Card ID divergente: esperado {cliente.pipefy_card_id}, recebido {input_data.card_id}"
                )
            
            # Atualizar status no Pipefy
            try:
                await self.pipefy_client.atualizar_card(
                    card_id=input_data.card_id,
                    status="processed"
                )
                pipefy_sync = "success"
                logger.info(f"Card {input_data.card_id} atualizado com sucesso")
            except Exception as e:
                logger.error(f"Falha ao atualizar Pipefy: {e}")
                pipefy_sync = "failed"
            
            # Registrar evento processado
            await self.evento_repo.registrar_evento(
                event_id=input_data.event_id,
                status="processed",
                metadata={"card_id": input_data.card_id, "email": input_data.cliente_email}
            )
            
            return ProcessarWebhookOutput(
                success=True,
                message="Webhook processado com sucesso",
                pipefy_sync=pipefy_sync,
                cliente=cliente
            )
            
        except (ClienteNaoEncontradoError, CardIdDivergentError) as e:
            # Registrar erro mas não bloquear reprocessamento
            await self.evento_repo.registrar_evento(
                event_id=input_data.event_id,
                status="failed",
                metadata={"error": str(e)}
            )
            return ProcessarWebhookOutput(
                success=False,
                message=str(e),
                pipefy_sync="failed"
            )
