"""Interfaces (portas) de repositório — o domínio depende só destas abstrações."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.cliente import Cliente


class ClienteRepository(ABC):
    @abstractmethod
    def salvar(self, cliente: Cliente) -> Cliente: ...

    @abstractmethod
    def buscar_por_email(self, email: str) -> Cliente | None: ...

    @abstractmethod
    def buscar_por_card_id(self, card_id: str) -> Cliente | None: ...

    @abstractmethod
    def buscar_pendentes_pipefy(self) -> list[Cliente]: ...

    @abstractmethod
    def atualizar(self, cliente: Cliente) -> Cliente: ...


class EventoRepository(ABC):
    @abstractmethod
    def registrar_se_novo(self, event_id: str, card_id: str) -> bool:
        """Insere evento com status='received'. Retorna False se já existia como 'processed'."""
        ...

    @abstractmethod
    def marcar_processado(self, event_id: str) -> None: ...

    @abstractmethod
    def marcar_falhou(self, event_id: str) -> None: ...


class PipefyService(ABC):
    @abstractmethod
    def criar_card(self, cliente: Cliente) -> str: ...

    @abstractmethod
    def atualizar_card(self, card_id: str, status: str, prioridade: str) -> None: ...
