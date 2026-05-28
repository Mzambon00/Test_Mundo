from dataclasses import dataclass
from src.domain.repositories import ClienteRepository
from src.infrastructure.pipefy import PipefyClient
import logging

logger = logging.getLogger(__name__)

@dataclass
class ReprocessarPendentesOutput:
    total_pendentes: int
    processados_com_sucesso: int
    falhas: int

class ReprocessarPendentesUseCase:
    def __init__(self, cliente_repo: ClienteRepository, pipefy_client: PipefyClient):
        self.cliente_repo = cliente_repo
        self.pipefy_client = pipefy_client
    
    async def execute(self) -> ReprocessarPendentesOutput:
        # Buscar clientes com integração pendente
        clientes_pendentes = await self.cliente_repo.buscar_integracao_pendente()
        
        sucesso = 0
        falhas = 0
        
        for cliente in clientes_pendentes:
            try:
                # Tentar criar card no Pipefy novamente
                card_id = await self.pipefy_client.criar_card(
                    nome=cliente.nome,
                    email=cliente.email,
                    prioridade=cliente.prioridade.value
                )
                
                # Atualizar cliente com card_id
                await self.cliente_repo.atualizar_pipefy_card(cliente.id, card_id)
                sucesso += 1
                logger.info(f"Cliente {cliente.email} reprocessado com sucesso. Card: {card_id}")
                
            except Exception as e:
                falhas += 1
                logger.error(f"Falha ao reprocessar cliente {cliente.email}: {e}")
        
        return ReprocessarPendentesOutput(
            total_pendentes=len(clientes_pendentes),
            processados_com_sucesso=sucesso,
            falhas=falhas
        )
