"""Router: /webhooks â€” alinhado ao enunciado do teste tÃ©cnico."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.application.use_cases.processar_webhook_use_case import (
    CardIdDivergentError,
    ClienteNaoEncontradoError,
    ProcessarWebhookInput,
    ProcessarWebhookUseCase,
)
from src.domain.entities.cliente import ClienteJaProcessadoError
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories_impl import (
    SQLAlchemyClienteRepository,
    SQLAlchemyEventoRepository,
)
from src.infrastructure.graphql.pipefy_adapter import PipefyAdapter
from src.security import verificar_assinatura_webhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Payload exato conforme enunciado do teste tÃ©cnico
class WebhookPipefyRequest(BaseModel):
    event_id: str
    card_id: str
    cliente_email: EmailStr
    timestamp: datetime | None = None  # campo do enunciado


def _pipefy() -> PipefyAdapter:
    return PipefyAdapter()


def _use_case(
    db: Session = Depends(get_db),
    pipefy: PipefyAdapter = Depends(_pipefy),
) -> ProcessarWebhookUseCase:
    return ProcessarWebhookUseCase(
        SQLAlchemyClienteRepository(db),
        SQLAlchemyEventoRepository(db),
        pipefy,
    )


@router.post(
    "/pipefy/card-updated",
    dependencies=[Depends(verificar_assinatura_webhook)],
)
def webhook_pipefy(
    body: WebhookPipefyRequest,
    use_case: ProcessarWebhookUseCase = Depends(_use_case),
) -> dict:  # type: ignore[type-arg]
    try:
        output = use_case.executar(ProcessarWebhookInput(
            event_id=body.event_id,
            card_id=body.card_id,
            cliente_email=body.cliente_email,
        ))
    except ClienteNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CardIdDivergentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ClienteJaProcessadoError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "status": output.status,
        "event_id": output.event_id,
        "card_id": output.card_id,
        "pipefy_sync": output.pipefy_sync,
        **(
            {"prioridade": output.prioridade, "cliente_nome": output.cliente_nome}
            if output.status == "processed"
            else {}
        ),
    }

