from fastapi import APIRouter, Depends, HTTPException, status
from src.config import settings
from src.application.use_cases.reprocessar_pendentes_use_case import ReprocessarPendentesUseCase
from src.domain.repositories import ClienteRepository
from src.infrastructure.graphql.pipefy_adapter import PipefyClient
from src.infrastructure.database import get_db
from sqlalchemy.orm import Session
from src.infrastructure.repositories.cliente_repository_impl import ClienteRepositoryImpl
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

def verify_admin_token(token: str) -> bool:
    """Verificar token administrativo"""
    if settings.is_production and not settings.admin_token:
        logger.error("ADMIN_TOKEN não configurado em produção")
        return False
    return token == settings.admin_token

def get_cliente_repo(db: Session = Depends(get_db)) -> ClienteRepository:
    return ClienteRepositoryImpl(db)

def get_pipefy_client() -> PipefyClient:
    return PipefyClient()

@router.post("/reprocessar-pendentes")
async def reprocessar_pendentes(
    admin_token: str,
    cliente_repo: ClienteRepository = Depends(get_cliente_repo),
    pipefy_client: PipefyClient = Depends(get_pipefy_client)
):
    """Reprocessar clientes com integração pendente"""
    
    # Validar token admin
    if not verify_admin_token(admin_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token administrativo inválido"
        )
    
    try:
        use_case = ReprocessarPendentesUseCase(cliente_repo, pipefy_client)
        resultado = use_case.executar()
        
        return {
            "success": True,
            "message": "Reprocessamento concluído",
            "total_encontrados": resultado.total_encontrados,
            "total_sucesso": resultado.total_sucesso,
            "total_falha": resultado.total_falha,
            "detalhes": resultado.detalhes
        }
        
    except Exception as e:
        logger.error(f"Erro no reprocessamento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao reprocessar: {str(e)}"
        )
