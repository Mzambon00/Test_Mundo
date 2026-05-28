"""Value object Prioridade — regra de cálculo centralizada aqui."""

from __future__ import annotations

from enum import Enum


class Prioridade(str, Enum):
    ALTA = "prioridade_alta"
    NORMAL = "prioridade_normal"

    # ── limiar centralizado em um único lugar ─────────────────────────────────
    LIMIAR_ALTA: float  # declarado abaixo como class-var

    @classmethod
    def calcular(cls, valor_patrimonio: float) -> "Prioridade":
        """Retorna a prioridade adequada com base no patrimônio."""
        if valor_patrimonio < 0:
            raise ValueError("Patrimônio não pode ser negativo.")
        return cls.ALTA if valor_patrimonio >= cls._limiar() else cls.NORMAL

    @classmethod
    def _limiar(cls) -> float:  # isolado para facilitar testes
        return 200_000.0


# Mantém compatibilidade: Prioridade.LIMIAR_ALTA acessível como atributo
Prioridade.LIMIAR_ALTA = 200_000.0  # type: ignore[attr-defined]
