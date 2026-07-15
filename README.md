# PrintFlow

Sistema de gerenciamento de gráfica: estoque de materiais, produtos, produções, desperdícios, custos/lucros e dashboard.

Documentação de referência em [`docs/`](docs/):
- [`docs/01-requisitos.md`](docs/01-requisitos.md)
- [`docs/02-modelo-dados.md`](docs/02-modelo-dados.md)
- [`docs/03-api.md`](docs/03-api.md)
- [`docs/04-plano-implementacao.md`](docs/04-plano-implementacao.md)

## Stack

Backend Python 3.12+/FastAPI/SQLAlchemy async/Alembic/PostgreSQL 16. Frontend Angular 19 (standalone) + Angular Material + ng2-charts. Ver [`CLAUDE.md`](CLAUDE.md) para detalhes.

## Como rodar

### 1. Banco de dados

```bash
docker compose up -d db db_test
```

Sobe o Postgres principal (porta 5432) e um banco de testes de integração (porta 5433).

### 2. Backend

```bash
cd backend
uv sync
cp .env.example .env   # ajustar se necessário
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API em `http://localhost:8000`, docs interativas em `http://localhost:8000/docs`.

Testes (usam o banco `db_test` na porta 5433):

```bash
cd backend
uv run pytest
uv run pytest --cov=app --cov-report=term-missing   # com cobertura
```

Dados de demonstração (opcional — materiais, produtos, produções e desperdícios de exemplo de uma gráfica; não cria usuário, faça o setup normalmente pela API/tela):

```bash
cd backend
uv run python -m app.seed
```

### 3. Frontend

A base do frontend (Angular 19 + Angular Material, layout com menu lateral) foi criada na Fase 0, mas as telas que consomem a API (materiais, produtos, produções, desperdícios, relatórios, dashboard) ainda não foram implementadas — o trabalho deste projeto está focado no backend.

```bash
cd frontend
npm install
npm start
```

App em `http://localhost:4200`, com proxy configurado para `/api` → `http://localhost:8000`.

## Estrutura

```
printflow/
├── docker-compose.yml
├── backend/    # FastAPI (router → service → repository), completo (Fases 0-7)
└── frontend/   # Angular standalone (core/shared/features), apenas esqueleto (Fase 0)
```

## Status de implementação

Todas as fases do backend descritas em [`docs/04-plano-implementacao.md`](docs/04-plano-implementacao.md) estão concluídas: setup/autenticação, materiais/estoque, produtos/composição, produções (com baixa transacional e lock pessimista), desperdícios, relatórios e dashboard. Regras de negócio (RN01-RN12) cobertas por testes automatizados (TDD), com 100% de cobertura nos services.
