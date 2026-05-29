from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class CriarClienteRequest(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100, description="Nome do cliente")
    email: EmailStr = Field(..., description="Email do cliente")
    valor_patrimonio: float = Field(..., gt=0, description="Valor do patrimônio")
    tipo_solicitacao: str = Field(..., description="Tipo de solicitação")

class ClienteResponse(BaseModel):
    id: int
    nome: str
    email: str
    valor_patrimonio: float
    tipo_solicitacao: str
    prioridade: str
    status: str
    pipefy_card_id: Optional[str]
    integracao_pipefy: str
    criado_em: datetime

class WebhookPipefyRequest(BaseModel):
    event_id: str
    card_id: str
    cliente_email: EmailStr

class WebhookResponse(BaseModel):
    success: bool
    message: str
    pipefy_sync: Optional[str] = None
