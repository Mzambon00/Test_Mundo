from fastapi import APIRouter, Depends, HTTPException, status
from src.application.use_cases.reprocessar_pendentes_use_case import ReprocessarPendentesUseCase
from src.domain.repositories import ClienteRepository
from src.infrastructure.graphql.pipefy_adapter import PipefyAdapter as PipefyClient
from src.infrastructure.database import get_db
from src.security import require_admin
from sqlalchemy.orm import Session
from src.infrastructure.database.repositories_impl import SQLAlchemyClienteRepository as ClienteRepositoryImpl
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

def get_cliente_repo(db: Session = Depends(get_db)) -> ClienteRepository:
    return ClienteRepositoryImpl(db)

def _pipefy() -> PipefyClient:
    return PipefyClient()

@router.post("/reprocessar-pendentes", dependencies=[Depends(require_admin)])
async def reprocessar_pendentes(
    cliente_repo: ClienteRepository = Depends(get_cliente_repo),
    pipefy_client: PipefyClient = Depends(_pipefy)
):
    try:
        use_case = ReprocessarPendentesUseCase(cliente_repo, pipefy_client)
        resultado = use_case.executar()
        return {
            "success": True,
            "message": "Reprocessamento concluido",
            "total_encontrados": resultado.total_encontrados,
            "total_sucesso": resultado.total_sucesso,
            "total_falha": resultado.total_falha,
            "detalhes": resultado.detalhes
        }
    except Exception as e:
        logger.error(f"Erro no reprocessamento: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao reprocessar: {str(e)}")