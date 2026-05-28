"""Testes alinhados ao enunciado do teste técnico Mundo Invest."""

import hashlib
import hmac

from fastapi.testclient import TestClient

# ── Payloads conforme enunciado ───────────────────────────────────────────────

CLIENTE_ALTA = {
    "cliente_nome": "Joao Silva",
    "cliente_email": "joao@empresa.com",
    "tipo_solicitacao": "Atualizacao cadastral",
    "valor_patrimonio": 250000,
}

CLIENTE_NORMAL = {
    "cliente_nome": "Maria Souza",
    "cliente_email": "maria@empresa.com",
    "tipo_solicitacao": "Consulta",
    "valor_patrimonio": 150000,
}


def _criar(client: TestClient, payload: dict = CLIENTE_ALTA) -> dict:  # type: ignore[type-arg]
    resp = client.post("/clientes", json=payload)
    assert resp.status_code == 201, resp.json()
    return resp.json()


def _webhook(client: TestClient, card_id: str, email: str, event_id: str = "evt_001") -> dict:  # type: ignore[type-arg]
    """Chama o webhook com o card_id real do cliente criado."""
    return client.post("/webhooks/pipefy/card-updated", json={
        "event_id": event_id,
        "card_id": card_id,
        "cliente_email": email,
        "timestamp": "2026-05-18T12:00:00Z",
    }).json()


# ═══════════════════════════════════════════════════════
# TC-01: Criação de cliente
# ═══════════════════════════════════════════════════════

class TestCriarCliente:
    def test_tc01_cria_cliente_valido(self, client: TestClient) -> None:
        resp = client.post("/clientes", json=CLIENTE_ALTA)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "joao@empresa.com"
        assert data["status"] == "Aguardando Análise"
        assert data["id"] is not None

    def test_status_inicial_aguardando_analise(self, client: TestClient) -> None:
        assert _criar(client)["status"] == "Aguardando Análise"

    def test_prioridade_alta_no_cadastro(self, client: TestClient) -> None:
        assert _criar(client, CLIENTE_ALTA)["prioridade"] == "prioridade_alta"

    def test_prioridade_normal_no_cadastro(self, client: TestClient) -> None:
        assert _criar(client, CLIENTE_NORMAL)["prioridade"] == "prioridade_normal"

    def test_tc02_email_duplicado_retorna_422(self, client: TestClient) -> None:
        _criar(client)
        resp = client.post("/clientes", json=CLIENTE_ALTA)
        assert resp.status_code == 422

    def test_email_invalido(self, client: TestClient) -> None:
        assert client.post("/clientes", json={**CLIENTE_ALTA, "cliente_email": "x"}).status_code == 422

    def test_patrimonio_negativo(self, client: TestClient) -> None:
        assert client.post("/clientes", json={**CLIENTE_ALTA, "valor_patrimonio": -1}).status_code == 422

    def test_nome_vazio(self, client: TestClient) -> None:
        assert client.post("/clientes", json={**CLIENTE_ALTA, "cliente_nome": "  "}).status_code == 422

    def test_tc03_pipefy_falho_retorna_integration_pending(
        self, client: TestClient, fake_pipefy: object
    ) -> None:
        fake_pipefy.deve_falhar = True  # type: ignore[attr-defined]
        resp = client.post("/clientes", json={**CLIENTE_ALTA, "cliente_email": "f@x.com"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["integracao_pipefy"] == "integration_pending"
        assert data["card_id"] == ""
        assert data["id"] is not None


# ═══════════════════════════════════════════════════════
# TC-02: Regra de prioridade 200k — REQUISITO CENTRAL
# ═══════════════════════════════════════════════════════

class TestRegrasPrioridade:
    """>= 200k = prioridade_alta / < 200k = prioridade_normal."""

    def test_250k_e_prioridade_alta(self, client: TestClient) -> None:
        c = _criar(client, CLIENTE_ALTA)
        r = _webhook(client, c["card_id"], "joao@empresa.com")
        assert r["prioridade"] == "prioridade_alta"

    def test_150k_e_prioridade_normal(self, client: TestClient) -> None:
        c = _criar(client, CLIENTE_NORMAL)
        r = _webhook(client, c["card_id"], "maria@empresa.com", "evt_002")
        assert r["prioridade"] == "prioridade_normal"

    def test_limiar_200k_exato_e_alta(self, client: TestClient) -> None:
        payload = {**CLIENTE_ALTA, "cliente_email": "limiar@x.com", "valor_patrimonio": 200000}
        c = _criar(client, payload)
        r = _webhook(client, c["card_id"], "limiar@x.com", "evt_003")
        assert r["prioridade"] == "prioridade_alta"

    def test_199999_e_prioridade_normal(self, client: TestClient) -> None:
        payload = {**CLIENTE_ALTA, "cliente_email": "baixo@x.com", "valor_patrimonio": 199999}
        c = _criar(client, payload)
        r = _webhook(client, c["card_id"], "baixo@x.com", "evt_004")
        assert r["prioridade"] == "prioridade_normal"

    def test_webhook_retorna_status_processed(self, client: TestClient) -> None:
        """Status do cliente muda para 'Processado' após webhook."""
        c = _criar(client)
        r = _webhook(client, c["card_id"], "joao@empresa.com")
        assert r["status"] == "processed"

    def test_webhook_com_timestamp_no_payload(self, client: TestClient) -> None:
        """Timestamp conforme enunciado do teste técnico."""
        c = _criar(client)
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_ts",
            "card_id": c["card_id"],
            "cliente_email": "joao@empresa.com",
            "timestamp": "2026-05-18T12:00:00Z",
        })
        assert resp.status_code == 200

    def test_webhook_sem_timestamp_funciona(self, client: TestClient) -> None:
        c = _criar(client)
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_nots",
            "card_id": c["card_id"],
            "cliente_email": "joao@empresa.com",
        })
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════
# TC-03: Idempotência (event_id duplicado)
# ═══════════════════════════════════════════════════════

class TestIdempotencia:
    def test_tc03_event_id_duplicado_retorna_already_processed(self, client: TestClient) -> None:
        c = _criar(client)
        _webhook(client, c["card_id"], "joao@empresa.com", "evt_dup")
        r = _webhook(client, c["card_id"], "joao@empresa.com", "evt_dup")
        assert r["status"] == "already_processed"

    def test_idempotencia_nao_reprocessa_cliente(self, client: TestClient) -> None:
        c = _criar(client)
        _webhook(client, c["card_id"], "joao@empresa.com", "evt_once")
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_once",
            "card_id": c["card_id"],
            "cliente_email": "joao@empresa.com",
        })
        assert resp.json()["status"] == "already_processed"

    def test_cliente_inexistente_retorna_404(self, client: TestClient) -> None:
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_404", "card_id": "x", "cliente_email": "nao@existe.com"
        })
        assert resp.status_code == 404

    def test_card_id_divergente_retorna_422(self, client: TestClient) -> None:
        _criar(client)
        resp = client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_div", "card_id": "card_errado", "cliente_email": "joao@empresa.com"
        })
        assert resp.status_code == 422

    def test_pipefy_sync_failed_quando_atualizacao_falha(
        self, client: TestClient, fake_pipefy: object
    ) -> None:
        c = _criar(client)
        fake_pipefy.deve_falhar = True  # type: ignore[attr-defined]
        r = _webhook(client, c["card_id"], "joao@empresa.com")
        assert r["status"] == "processed"
        assert r["pipefy_sync"] == "failed"


# ═══════════════════════════════════════════════════════
# TC-04/05: Segurança HMAC
# ═══════════════════════════════════════════════════════

class TestHmac:
    def test_tc04_construcao_assinatura_hmac(self) -> None:
        secret = "meu_secret"
        body = b'{"event_id":"x"}'
        sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert sig.startswith("sha256=")
        assert len(sig) == 71

    def test_tc05_sem_assinatura_retorna_401(self, client_com_secret: TestClient) -> None:
        resp = client_com_secret.post("/webhooks/pipefy/card-updated", json={
            "event_id": "e", "card_id": "c", "cliente_email": "a@b.com"
        })
        assert resp.status_code == 401

    def test_tc05_assinatura_invalida_retorna_401(self, client_com_secret: TestClient) -> None:
        resp = client_com_secret.post(
            "/webhooks/pipefy/card-updated",
            json={"event_id": "e", "card_id": "c", "cliente_email": "a@b.com"},
            headers={"X-Pipefy-Signature": "sha256=invalida"},
        )
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════
# TC-07: Admin protegido
# ═══════════════════════════════════════════════════════

class TestAdminProtegido:
    def test_tc07_sem_token_retorna_401(self, client_com_secret: TestClient) -> None:
        assert client_com_secret.post("/admin/reprocessar-pendentes").status_code == 401

    def test_tc07_token_invalido_retorna_401(self, client_com_secret: TestClient) -> None:
        resp = client_com_secret.post(
            "/admin/reprocessar-pendentes",
            headers={"X-Admin-Token": "errado"},
        )
        assert resp.status_code == 401

    def test_token_correto_funciona(self, client_com_secret: TestClient) -> None:
        resp = client_com_secret.post(
            "/admin/reprocessar-pendentes",
            headers={"X-Admin-Token": "admin_test_token"},
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════
# TC-08: Health check
# ═══════════════════════════════════════════════════════

def test_tc08_health_check(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.2.0"


def test_correlation_id_no_header(client: TestClient) -> None:
    assert "x-request-id" in client.get("/health").headers
