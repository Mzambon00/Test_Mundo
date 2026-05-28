"""Value object Email — imutável, auto-validado na criação."""

from __future__ import annotations

import re


_EMAIL_PATTERN = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$")


class EmailInvalidoError(ValueError):
    """Levantado quando o formato do e-mail é inválido."""


class Email:
    """Encapsula um endereço de e-mail validado e normalizado."""

    __slots__ = ("_valor",)

    def __init__(self, valor: str) -> None:
        normalizado = valor.strip().lower()
        if not _EMAIL_PATTERN.match(normalizado):
            raise EmailInvalidoError(f"E-mail inválido: '{valor}'")
        self._valor = normalizado

    # ── propriedades ─────────────────────────────────────────────────────────

    @property
    def valor(self) -> str:
        return self._valor

    # ── dunder ───────────────────────────────────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Email):
            return self._valor == other._valor
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._valor)

    def __str__(self) -> str:
        return self._valor

    def __repr__(self) -> str:
        return f"Email({self._valor!r})"
