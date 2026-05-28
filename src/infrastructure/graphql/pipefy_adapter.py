"""Adaptador HTTP para a API GraphQL do Pipefy (especificação oficial)."""

from __future__ import annotations

import logging

import httpx

from src.config import get_settings
from src.domain.entities.cliente import Cliente
from src.domain.repositories.interfaces import PipefyService

logger = logging.getLogger(__name__)

_PIPEFY_URL = "https://api.pipefy.com/graphql"

# ── Mutations conforme documentação oficial do Pipefy ─────────────────────────

# Ref: https://developers.pipefy.com/reference/mutations-cards
CREATE_CARD_MUTATION = """
mutation CreateCard(
  $pipe_id: ID!
  $title: String!
  $email: String!
  $patrimonio: String!
  $tipo_solicitacao: String!
) {
  createCard(input: {
    pipe_id: $pipe_id
    title: $title
    fields_attributes: [
      { field_id: "email",            field_value: $email }
      { field_id: "tipo_solicitacao", field_value: $tipo_solicitacao }
      { field_id: "valor_patrimonio", field_value: $patrimonio }
    ]
  }) {
    card {
      id
      title
      current_phase { name }
    }
  }
}
"""

# Ref: https://developers.pipefy.com/reference/mutations-cards (updateCardField)
UPDATE_CARD_FIELD_STATUS = """
mutation UpdateCardFieldStatus($card_id: ID!, $status: String!) {
  updateCardField(input: {
    card_id: $card_id
    field_id: "status_cliente"
    new_value: [$status]
  }) {
    success
    clientMutationId
  }
}
"""

UPDATE_CARD_FIELD_PRIORIDADE = """
mutation UpdateCardFieldPrioridade($card_id: ID!, $prioridade: String!) {
  updateCardField(input: {
    card_id: $card_id
    field_id: "prioridade"
    new_value: [$prioridade]
  }) {
    success
    clientMutationId
  }
}
"""


class PipefyAdapter(PipefyService):
    def __init__(self) -> None:
        cfg = get_settings()
        self._headers = {
            "Authorization": f"Bearer {cfg.pipefy_token}",
            "Content-Type": "application/json",
        }
        self._pipe_id = cfg.pipefy_pipe_id

    def criar_card(self, cliente: Cliente) -> str:
        """Cria card no Pipefy usando a mutation createCard oficial."""
        payload = {
            "query": CREATE_CARD_MUTATION,
            "variables": {
                "pipe_id": self._pipe_id,
                "title": cliente.nome,
                "email": str(cliente.email),
                "patrimonio": str(cliente.valor_patrimonio),
                "tipo_solicitacao": cliente.tipo_solicitacao,
            },
        }
        response = self._post(payload)
        card_id: str = response["data"]["createCard"]["card"]["id"]
        logger.info("Card criado no Pipefy: %s", card_id)
        return card_id

    def atualizar_card(self, card_id: str, status: str, prioridade: str) -> None:
        """Atualiza campos do card usando updateCardField (especificação oficial Pipefy)."""
        # Atualiza status do cliente
        self._post({
            "query": UPDATE_CARD_FIELD_STATUS,
            "variables": {"card_id": card_id, "status": status},
        })
        # Atualiza prioridade
        self._post({
            "query": UPDATE_CARD_FIELD_PRIORIDADE,
            "variables": {"card_id": card_id, "prioridade": prioridade},
        })
        logger.info(
            "Card %s atualizado: status=%s, prioridade=%s", card_id, status, prioridade
        )

    def _post(self, payload: dict) -> dict:  # type: ignore[type-arg]
        with httpx.Client(timeout=10) as client:
            resp = client.post(_PIPEFY_URL, json=payload, headers=self._headers)
        resp.raise_for_status()
        data: dict = resp.json()  # type: ignore[type-arg]
        if "errors" in data:
            raise RuntimeError(f"Erro GraphQL Pipefy: {data['errors']}")
        return data
