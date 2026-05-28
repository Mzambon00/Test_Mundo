"""Testes unitários do value object Email."""

import pytest

from src.domain.value_objects.email import Email, EmailInvalidoError


class TestEmailValido:
    def test_cria_com_email_simples(self) -> None:
        assert str(Email("user@example.com")) == "user@example.com"

    def test_normaliza_para_lowercase(self) -> None:
        assert str(Email("USER@Example.COM")) == "user@example.com"

    def test_remove_espacos(self) -> None:
        assert str(Email("  user@example.com  ")) == "user@example.com"

    def test_email_com_subdominio(self) -> None:
        assert str(Email("a@b.c.com")) == "a@b.c.com"

    def test_email_com_ponto_no_local(self) -> None:
        assert str(Email("first.last@domain.org")) == "first.last@domain.org"

    def test_igualdade(self) -> None:
        assert Email("a@b.com") == Email("A@B.COM")

    def test_hashable(self) -> None:
        s = {Email("a@b.com"), Email("A@B.COM")}
        assert len(s) == 1

    def test_repr(self) -> None:
        assert repr(Email("a@b.com")) == "Email('a@b.com')"


class TestEmailInvalido:
    @pytest.mark.parametrize(
        "valor",
        [
            "nao-tem-arroba",
            "@sem-local.com",
            "sem-dominio@",
            "",
            "   ",
            "dois@@arroba.com",
        ],
    )
    def test_levanta_erro(self, valor: str) -> None:
        with pytest.raises(EmailInvalidoError):
            Email(valor)
