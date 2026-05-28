"""Entidade Cliente — núcleo do domínio, sem dependências externas."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.value_objects.email import Email
from src.domain.value_objects.prioridade import Prioridade


class ClienteJaProcessadoError(Exception):
    pass


@dataclass
class Cliente:
    nome: str
    email: Email
    tipo_solicitacao: str
    valor_patrimonio: float
    prioridade: Prioridade = field(init=False)
    status: str = field(default="Aguardando Análise")
    integracao_pipefy: str = field(default="integration_pending")
    id: int | None = field(default=None)
    card_id: str | None = field(default=None)

    def __post_init__(self) -> None:
        self._validar()
        self.prioridade = Prioridade.calcular(self.valor_patrimonio)

    def _validar(self) -> None:
        if not self.nome.strip():
            raise ValueError("Nome não pode ser vazio.")
        if not self.tipo_solicitacao.strip():
            raise ValueError("Tipo de solicitação não pode ser vazio.")
        if self.valor_patrimonio < 0:
            raise ValueError("Patrimônio não pode ser negativo.")

    def processar(self) -> None:
        if self.status == "Processado":
            raise ClienteJaProcessadoError(f"Cliente '{self.email}' já foi processado.")
        self.status = "Processado"
        self.prioridade = Prioridade.calcular(self.valor_patrimonio)

    @property
    def esta_processado(self) -> bool:
        return self.status == "Processado"
