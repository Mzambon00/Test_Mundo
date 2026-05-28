# Mundo Invest API

API de gestão de clientes com integração ao Pipefy, construída com **FastAPI + Clean Architecture**.

---

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/clientes` | Cadastra um cliente e cria card no Pipefy |
| `POST` | `/webhooks/pipefy/card-updated` | Processa atualização de card (idempotente) |
| `GET` | `/health` | Verifica se a API está de pé |

---

## Variáveis de ambiente

Crie um arquivo `.env` na raiz (veja `.env.example`):

```env
DATABASE_URL=sqlite:///./mundo_invest.db
PIPEFY_TOKEN=seu_token_aqui
PIPEFY_PIPE_ID=302428309
AUTO_CREATE_TABLES=true
DB_ECHO=false
```

> `AUTO_CREATE_TABLES=true` cria as tabelas automaticamente (dev/demo).  
> Em produção use `false` e rode as migrations com Alembic.

---

## Execução local

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Criar o .env
cp .env.example .env
# edite o .env com seu token Pipefy

# 3. Subir a API
uvicorn src.main:app --reload

# 4. Acessar docs interativas
# http://localhost:8000/docs
```

---

## Docker

```bash
# Build
docker build -t mundo-invest .

# Run
docker run -p 8000:8000 --env-file .env mundo-invest

# Verificar saúde
curl http://localhost:8000/health
```

---

## Testes

```bash
# Rodar todos os testes com cobertura
pytest tests/ -v --cov=src --cov-report=term-missing

# Rodar só testes unitários (sem banco)
pytest tests/test_email_value_object.py tests/test_cliente_entity.py -v
```

---

## Payloads de exemplo

**POST /clientes**
```json
{
  "cliente_nome": "João Silva",
  "cliente_email": "joao@empresa.com",
  "tipo_solicitacao": "Renda Fixa",
  "valor_patrimonio": 250000.00
}
```

Resposta `201`:
```json
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao@empresa.com",
  "status": "Aguardando Análise",
  "prioridade": "prioridade_alta",
  "card_id": "123456",
  "integracao_pipefy": "completo"
}
```

> Se o Pipefy falhar: `"integracao_pipefy": "integration_pending"` e `"card_id": ""`.

---

**POST /webhooks/pipefy/card-updated**
```json
{
  "event_id": "evt_001",
  "card_id": "123456",
  "cliente_email": "joao@empresa.com"
}
```

Resposta `200` (primeira chamada):
```json
{
  "status": "processed",
  "event_id": "evt_001",
  "card_id": "123456",
  "prioridade": "prioridade_alta",
  "cliente_nome": "João Silva"
}
```

Resposta `200` (reenvio — idempotente):
```json
{
  "status": "already_processed",
  "event_id": "evt_001",
  "card_id": "123456"
}
```

---

## Estrutura do projeto

```
src/
├── domain/             # Entidades, Value Objects, interfaces de repositório
├── application/        # Use cases (regras de negócio)
├── infrastructure/     # SQLAlchemy, Pipefy adapter
└── main.py             # FastAPI, rotas, injeção de dependências
tests/
alembic/                # Migrations (produção)
```

---

## CI/CD

O pipeline GitHub Actions roda em todo push:
1. **Lint** — Ruff
2. **Type check** — Mypy
3. **Testes** — Pytest com cobertura mínima de 80%
