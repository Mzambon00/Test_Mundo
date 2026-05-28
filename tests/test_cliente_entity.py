"""Testes unitários da entidade Cliente."""

import pytest

from src.domain.entities.cliente import Cliente, ClienteJaProcessadoError
from src.domain.value_objects.email import Email
from src.domain.value_objects.prioridade import Prioridade


def _make_cliente(patrimonio: float = 300_000.0) -> Cliente:
    return Cliente(
        nome="João Silva",
        email=Email("joao@empresa.com"),
        tipo_solicitacao="Renda Fixa",
        valor_patrimonio=patrimonio,
    )


class TestCriacaoCliente:
    def test_status_inicial(self) -> None:
        assert _make_cliente().status == "Aguardando Análise"

    def test_prioridade_alta(self) -> None:
        assert _make_cliente(250_000).prioridade == Prioridade.ALTA

    def test_prioridade_normal(self) -> None:
        assert _make_cliente(100_000).prioridade == Prioridade.NORMAL

    def test_limiar_exato_e_alta(self) -> None:
        assert _make_cliente(200_000).prioridade == Prioridade.ALTA

    def test_nome_vazio_levanta_erro(self) -> None:
        with pytest.raises(ValueError, match="Nome"):
            Cliente(
                nome="  ",
                email=Email("a@b.com"),
                tipo_solicitacao="X",
                valor_patrimonio=100,
            )

    def test_patrimonio_negativo_levanta_erro(self) -> None:
        with pytest.raises(ValueError, match="negativo"):
            Cliente(
                nome="Ana",
                email=Email("a@b.com"),
                tipo_solicitacao="X",
                valor_patrimonio=-1,
            )


class TestProcessarCliente:
    def test_processar_muda_status(self) -> None:
        c = _make_cliente()
        c.processar()
        assert c.status == "Processado"
        assert c.esta_processado

    def test_reprocessar_levanta_erro(self) -> None:
        c = _make_cliente()
        c.processar()
        with pytest.raises(ClienteJaProcessadoError):
            c.processar()

    def test_esta_processado_antes_de_processar(self) -> None:
        assert not _make_cliente().esta_processado
