from dataclasses import dataclass
from typing import List, Dict, Any
from src.domain.repositories import ClienteRepository
from src.infrastructure.graphql.pipefy_adapter import PipefyAdapter as PipefyClient
import logging

logger = logging.getLogger(__name__)

@dataclass
class ReprocessarPendentesOutput:
    total_encontrados: int
    total_sucesso: int
    total_falha: int
    detalhes: List[Dict[str, Any]]

class ReprocessarPendentesUseCase:
    def __init__(self, cliente_repo: ClienteRepository, pipefy_client: PipefyClient):
        self.cliente_repo = cliente_repo
        self.pipefy_client = pipefy_client
    
    def executar(self) -> ReprocessarPendentesOutput:
        """Método síncrono para reprocessar clientes pendentes"""
        # Buscar clientes com integração pendente
        clientes_pendentes = self.cliente_repo.buscar_pendentes_pipefy()
        
        total_encontrados = len(clientes_pendentes)
        detalhes = []
        sucesso = 0
        falha = 0
        
        for cliente in clientes_pendentes:
            try:
                # Tentar criar card no Pipefy
                card_id = self.pipefy_client.criar_card(
                    nome=cliente.nome,
                    email=cliente.email,
                    prioridade=cliente.prioridade.value
                )
                
                # Atualizar cliente
                self.cliente_repo.atualizar_pipefy_card(cliente.id, card_id)
                
                sucesso += 1
                detalhes.append({
                    "cliente_id": cliente.id,
                    "email": cliente.email,
                    "status": "sucesso",
                    "card_id": card_id
                })
                logger.info(f"Cliente {cliente.email} reprocessado com sucesso")
                
            except Exception as e:
                falha += 1
                detalhes.append({
                    "cliente_id": cliente.id,
                    "email": cliente.email,
                    "status": "falha",
                    "erro": str(e)
                })
                logger.error(f"Falha ao reprocessar {cliente.email}: {e}")
        
        return ReprocessarPendentesOutput(
            total_encontrados=total_encontrados,
            total_sucesso=sucesso,
            total_falha=falha,
            detalhes=detalhes
        )
