# PrintFlow — Sistema de Gerenciamento de Gráfica

## Visão Geral

Sistema web para gerenciamento de uma gráfica de pequeno porte: controle de estoque de materiais, cadastro de produtos, registro de produções com baixa automática de estoque, registro de desperdícios, cálculo de custos/lucros e dashboard.

**Usuário único:** apenas um administrador. Não há multiusuário, perfis ou permissões.

## Stack (obrigatória)

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Banco | PostgreSQL 16 (via Docker Compose) |
| Auth | JWT (biblioteca `pyjwt`), senhas com `bcrypt` via `passlib` |
| Testes backend | pytest + pytest-asyncio + httpx (TestClient async) |
| Frontend | Angular 19+ (standalone components, signals), Angular Material |
| Gráficos | ng2-charts (Chart.js) |
| Testes frontend | Testes unitários com Jasmine/Karma apenas para services e lógica de cálculo |

**IMPORTANTE:** O documento original de requisitos citava Java/Spring Boot (RNF02, RNF03, RNF10). Isso foi **substituído por decisão do cliente**: backend é FastAPI. A equivalência de camadas é: Controller → router, Service → service, Repository → repository, DTO → schema Pydantic, Entity → model SQLAlchemy.

## Estrutura do Monorepo

```
printflow/
├── docker-compose.yml          # PostgreSQL + (opcional) backend/frontend
├── backend/
│   ├── pyproject.toml
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/               # config, security (JWT), deps
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── repositories/       # acesso a dados
│   │   ├── services/           # regras de negócio
│   │   └── routers/            # endpoints FastAPI
│   └── tests/
│       ├── unit/               # services (regras de negócio)
│       └── integration/        # endpoints com banco de teste
└── frontend/
    └── src/app/
        ├── core/               # auth interceptor, guards, api services
        ├── shared/             # componentes reutilizáveis, pipes
        └── features/
            ├── auth/           # setup inicial + login
            ├── materiais/
            ├── produtos/
            ├── producoes/
            ├── desperdicios/
            ├── relatorios/
            └── dashboard/
```

## Documentação de Referência (ler antes de implementar)

1. `docs/01-requisitos.md` — requisitos funcionais, não funcionais e regras de negócio (versão final, já adaptada)
2. `docs/02-modelo-dados.md` — entidades, tipos, relacionamentos e sistema de unidades de medida
3. `docs/03-api.md` — contrato completo da API REST
4. `docs/04-plano-implementacao.md` — ordem de implementação em fases, com critérios de aceite

## Regras de Desenvolvimento

- **TDD sempre que possível (RNF12):** para services com regras de negócio (cálculo de custo, baixa de estoque, validação de estoque insuficiente, conversão de unidades, cálculo de desperdício), escrever os testes ANTES da implementação.
- **Regras de negócio ficam nos services**, nunca em routers ou no frontend. O frontend apenas exibe valores calculados pelo backend.
- **Valores monetários:** usar `Decimal` no Python e `NUMERIC(12,2)` no banco. Nunca float para dinheiro. Quantidades de estoque: `NUMERIC(12,3)`.
- **Snapshot de custos:** produções e desperdícios gravam o custo unitário vigente no momento do registro. Editar um material NÃO recalcula registros históricos.
- **Soft delete para materiais e produtos** (campo `ativo`). Exclusão física só é permitida se não houver produções/desperdícios vinculados.
- **Todas as rotas protegidas por JWT**, exceto `POST /api/setup`, `GET /api/setup/status` e `POST /api/auth/login`.
- **Mensagens de erro da API em português**, com formato consistente `{"detail": "..."}`.
- **Idioma:** UI, mensagens e comentários de domínio em pt-BR; nomes de código (variáveis, funções, tabelas) em inglês OU português consistente — escolha `snake_case` em português para o domínio (ex: `quantidade_atual`, `custo_unitario`) para casar com o documento de requisitos.

## Como Rodar (alvo final)

```bash
# banco
docker compose up -d db

# backend
cd backend && uv sync && uv run alembic upgrade head && uv run uvicorn app.main:app --reload

# frontend
cd frontend && npm install && npm start
```

Backend em `http://localhost:8000` (docs em `/docs`), frontend em `http://localhost:4200` com proxy para `/api`.

## Critério de Pronto (Definition of Done)

Uma funcionalidade só está pronta quando:
1. Testes do service passam (regras de negócio cobertas);
2. Endpoint testado via teste de integração;
3. Tela Angular funcional consumindo a API real;
4. Validações e mensagens de erro em português exibidas na UI;
5. Nenhum cálculo de custo/lucro duplicado no frontend.
