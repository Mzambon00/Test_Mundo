"""Router: /clientes"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from src.application.use_cases.criar_cliente_use_case import (
    CriarClienteInput,
    CriarClienteUseCase,
    EmailDuplicadoError,
)
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories_impl import SQLAlchemyClienteRepository
from src.infrastructure.graphql.pipefy_adapter import PipefyAdapter

router = APIRouter(prefix="/clientes", tags=["clientes"])


class CriarClienteRequest(BaseModel):
    cliente_nome: str
    cliente_email: EmailStr
    tipo_solicitacao: str
    valor_patrimonio: float

    @field_validator("valor_patrimonio")
    @classmethod
    def patrimonio_nao_negativo(cls, v: float) -> float:
        if v < 0:
            raise ValueError("PatrimÃ´nio nÃ£o pode ser negativo.")
        return v

    @field_validator("cliente_nome", "tipo_solicitacao")
    @classmethod
    def nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Campo nÃ£o pode ser vazio.")
        return v


def _pipefy() -> PipefyAdapter:
    return PipefyAdapter()


def _use_case(
    db: Session = Depends(get_db),
    pipefy: PipefyAdapter = Depends(_pipefy),
) -> CriarClienteUseCase:
    return CriarClienteUseCase(SQLAlchemyClienteRepository(db), pipefy)


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_cliente(
    body: CriarClienteRequest,
    use_case: CriarClienteUseCase = Depends(_use_case),
) -> dict:  # type: ignore[type-arg]
    try:
        output = use_case.executar(CriarClienteInput(
            cliente_nome=body.cliente_nome,
            cliente_email=body.cliente_email,
            tipo_solicitacao=body.tipo_solicitacao,
            valor_patrimonio=body.valor_patrimonio,
        ))
    except EmailDuplicadoError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "id": output.id,
        "nome": output.nome,
        "email": output.email,
        "status": output.status,
        "prioridade": output.prioridade,
        "card_id": output.card_id,
        "integracao_pipefy": output.integracao_pipefy,
    }

