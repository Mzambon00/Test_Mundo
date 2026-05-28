# Changelog

Todas as mudanças notáveis neste projeto são documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## [2.1.0] — 2026-05-26

### Adicionado
- `pyproject.toml` com configuração de Ruff, mypy e pytest-cov
- Linting e formatação via Ruff (substitui Flake8 + Black)
- Type checking estrito via mypy
- Cobertura mínima de 80% configurada no CI (quebra o build se cair abaixo)
- `pydantic-settings` substituindo variáveis de ambiente soltas
- `conftest.py` centralizado com fixtures de banco em memória e mock do Pipefy
- Handler global de erros inesperados no FastAPI
- Logging estruturado com `%(asctime)s | %(levelname)s | %(name)s`
- Dockerfile multi-stage com usuário não-root
- CI separado em dois jobs: `quality` (lint + typecheck) e `tests` (cobertura)
- `CHANGELOG.md` e `CONTRIBUTING.md`
- Propriedade `esta_processado` na entidade `Cliente`
- Exceções de domínio nomeadas: `EmailDuplicadoError`, `ClienteNaoEncontradoError`
- Falha isolada na criação de card Pipefy (não desfaz cadastro do cliente)

### Alterado
- `mapped_column` com tipos explícitos no SQLAlchemy 2.0 (`Mapped[str]` etc.)
- Use cases retornam dataclasses imutáveis (`frozen=True`) em vez de dicts
- `_to_entity` no repositório usa `__new__` para reconstruir entidades sem re-validar

### Corrigido
- Sessão do banco sempre fechada via `finally` em `get_db`
- Índice no campo `email` da tabela `clientes` para buscas performáticas

---

## [2.0.0] — 2026-05-01

### Adicionado
- Clean Architecture completa (domain / application / infrastructure / presentation)
- Value Objects `Email` e `Prioridade`
- Idempotência de webhooks via tabela `eventos`
- Suporte a Docker e docker-compose
- Migrations via Alembic
- Testes unitários e de integração
