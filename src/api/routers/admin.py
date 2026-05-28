"""Router: /admin — endpoints operacionais protegidos."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.application.use_cases.reprocessar_pendentes_use_case import ReprocessarPendentesUseCase
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories_impl import SQLAlchemyClienteRepository
from src.infrastructure.graphql.pipefy_adapter import PipefyAdapter
from src.security import require_admin

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],  # P0: toda rota /admin exige token
)


def _pipefy() -> PipefyAdapter:
    return PipefyAdapter()


def _use_case(
    db: Session = Depends(get_db),
    pipefy: PipefyAdapter = Depends(_pipefy),
) -> ReprocessarPendentesUseCase:
    return ReprocessarPendentesUseCase(SQLAlchemyClienteRepository(db), pipefy)


@router.post("/reprocessar-pendentes")
def reprocessar_pendentes(
    use_case: ReprocessarPendentesUseCase = Depends(_use_case),
) -> dict:  # type: ignore[type-arg]
    """Reprocessa clientes com integration_pending. Requer X-Admin-Token."""
    output = use_case.executar()
    return {
        "total_encontrados": output.total_encontrados,
        "total_sucesso": output.total_sucesso,
        "total_falha": output.total_falha,
        "detalhes": output.detalhes,
    }
