"""Router: /webhooks - alinhado ao enunciado do teste tecnico."""
from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from src.application.use_cases.processar_webhook_use_case import (
    ProcessarWebhookInput,
    ProcessarWebhookUseCase,
)
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories_impl import (
    SQLAlchemyClienteRepository,
    SQLAlchemyEventoRepository,
)
from src.infrastructure.graphql.pipefy_adapter import PipefyAdapter
from src.security import verificar_assinatura_webhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

class WebhookPipefyRequest(BaseModel):
    event_id: str
    card_id: str
    cliente_email: EmailStr
    timestamp: datetime | None = None

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
async def webhook_pipefy(
    body: WebhookPipefyRequest,
    use_case: ProcessarWebhookUseCase = Depends(_use_case),
) -> dict:
    output = await use_case.execute(ProcessarWebhookInput(
        event_id=body.event_id,
        card_id=body.card_id,
        cliente_email=body.cliente_email,
    ))

    if output.status == "error":
        if "nao encontrado" in output.message.lower():
            raise HTTPException(status_code=404, detail=output.message)
        raise HTTPException(status_code=422, detail=output.message)

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