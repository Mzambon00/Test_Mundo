"""Schemas Pydantic de entrada e saída da API."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator


class CriarClienteRequest(BaseModel):
    cliente_nome: str
    cliente_email: EmailStr
    tipo_solicitacao: str
    valor_patrimonio: float

    @field_validator("valor_patrimonio")
    @classmethod
    def patrimonio_nao_negativo(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Patrimônio não pode ser negativo.")
        return v

    @field_validator("cliente_nome", "tipo_solicitacao")
    @classmethod
    def nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Campo não pode ser vazio.")
        return v


class WebhookPipefyRequest(BaseModel):
    event_id: str
    card_id: str
    cliente_email: EmailStr
