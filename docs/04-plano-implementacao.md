# PrintFlow — Plano de Implementação

Executar as fases EM ORDEM. Cada fase tem critérios de aceite verificáveis — não avançar sem cumpri-los. Commits pequenos e frequentes, mensagens em português no padrão `feat|fix|test|chore(escopo): descrição`.

## Fase 0 — Infraestrutura

- [ ] Monorepo com estrutura de CLAUDE.md
- [ ] `docker-compose.yml` com PostgreSQL 16 (volume nomeado, porta 5432, healthcheck) e um serviço `db_test` na porta 5433 para testes de integração
- [ ] Backend: `pyproject.toml` (gerenciar com `uv`), FastAPI hello, config via `pydantic-settings` lendo `.env` (fornecer `.env.example`), CORS liberado para `http://localhost:4200`
- [ ] SQLAlchemy async + Alembic configurados; migration inicial vazia aplicando
- [ ] Frontend: Angular novo, Angular Material, proxy.conf para `/api`, layout base (toolbar + sidenav com rotas placeholder)
- [ ] README raiz com instruções de execução

**Aceite:** `docker compose up -d db` + backend + frontend sobem; `GET /api/health` responde; app Angular abre com menu lateral.

## Fase 1 — Setup, Autenticação e Segurança (RF01, RF02, RN01–RN03)

Backend (TDD nos services):
- [ ] Model/migration `usuario`
- [ ] `POST /setup`, `GET /setup/status` — testes: cria admin, bloqueia segundo cadastro (409), valida email
- [ ] `POST /auth/login` — testes: sucesso gera JWT válido, senha errada 401, email inexistente 401 (mesma mensagem)
- [ ] Dependency `get_current_user` protegendo rotas; testes de rota protegida sem/ com token
- [ ] `GET/PUT /auth/me`, `PUT /auth/me/senha`

Frontend:
- [ ] Guard de setup: se `configurado=false`, força rota /setup
- [ ] Telas de setup e login; AuthService com token em memória + localStorage; interceptor injetando Bearer; interceptor de 401 → logout → /login
- [ ] Tela "Minha conta"

**Aceite:** fluxo completo no navegador: setup → login → acessa app → logout. Testes backend verdes.

## Fase 2 — Materiais e Estoque (RF03–RF08, RN04, RN10)

Backend (TDD no service de materiais, especialmente conversão de unidades):
- [ ] Model/migration `material` com enum de unidades
- [ ] Testes ANTES: cálculo de `custo_unitario_base` (pacote 100 folhas R$25 → 0,25/folha), validação de combinações de unidade, fator forçado a 1 quando unidades iguais, `estoque_baixo`, ajuste de estoque não pode negativar, nome duplicado 409
- [ ] CRUD completo + PATCH ativo + ajuste-estoque conforme docs/03

Frontend:
- [ ] Listagem com busca, filtro de estoque baixo, badge de alerta (RF08), chips ativo/inativo
- [ ] Form de material com preview do custo unitário em tempo real e ajuda contextual das unidades
- [ ] Diálogo de ajuste de estoque

**Aceite:** cadastrar "Papel A4, pacote de 100 folhas, R$ 25" → estoque exibido em folhas, custo R$ 0,25/folha; alerta aparece quando abaixo do mínimo.

## Fase 3 — Produtos e Composição (RF09–RF14, RN05–RN07)

Backend (TDD):
- [ ] Models/migrations `produto`, `produto_material`
- [ ] Testes ANTES: custo de produção com múltiplos materiais, lucro (inclusive negativo), composição vazia 422, material inativo na composição 422, material duplicado na composição 422
- [ ] CRUD + preview-custo

Frontend:
- [ ] Listagem com custo e lucro (lucro negativo em vermelho)
- [ ] Form com editor de composição (adicionar/remover linhas material+quantidade, mostrando a unidade base de cada material) e custo/lucro atualizando em tempo real via preview-custo

**Aceite:** produto "Caneca personalizada" com caneca (1 un) + tinta (5 ml) + papel (1 folha) mostra custo somado corretamente e lucro coerente com o preço.

## Fase 4 — Produção (RF15–RF17, RF20, RN08, RN09) — núcleo do sistema

Backend (TDD rigoroso — é a regra mais crítica):
- [ ] Models/migrations `producao`, `producao_item`
- [ ] Testes ANTES: baixa correta de estoque multiplicada pela quantidade produzida; snapshots corretos; produção bloqueada com payload detalhado quando falta UM material (e nada é baixado — atomicidade); produção bloqueada quando faltam vários; produto sem composição 422; estorno devolve estoque exatamente
- [ ] POST/GET/DELETE conforme docs/03, com lock pessimista nos materiais

Frontend:
- [ ] Tela de registro: selecionar produto, quantidade, data; preview dos materiais que serão consumidos vs disponível ANTES de confirmar
- [ ] Tratamento amigável do erro de estoque insuficiente (tabela com faltantes)
- [ ] Histórico com filtros e detalhe expandindo itens consumidos; botão estornar com confirmação

**Aceite:** produzir 10 canecas baixa 10 un de caneca, 50 ml de tinta, 10 folhas; tentar produzir 1000 falha listando faltantes sem alterar estoque; estorno restaura tudo.

## Fase 5 — Desperdícios (RF18, RF19, RF21, RN11, RN12)

- [ ] Backend TDD: baixa de estoque, custo snapshot, quantidade > disponível 422, estorno
- [ ] Frontend: form de registro (material, quantidade com unidade exibida, motivo, data), histórico com filtros

**Aceite:** desperdiçar 20 folhas reduz estoque e registra custo 20 × 0,25 = R$ 5,00.

## Fase 6 — Relatórios e Dashboard (RF22, RF23)

- [ ] Backend: 5 endpoints de relatório + endpoint de dashboard (queries agregadas; testes de integração com dados semeados verificando somas)
- [ ] Frontend: página de relatórios com seletor de período e tabelas; dashboard com 7 cards + 2 gráficos (ng2-charts) + lista de estoque baixo
- [ ] Botão de exportar cada relatório como CSV (gerado no frontend a partir do JSON — simples)

**Aceite:** valores do dashboard batem com os registros criados nas fases anteriores.

## Fase 7 — Acabamento

- [ ] Seed opcional de dados de demonstração (`python -m app.seed`) — materiais, produtos e produções de exemplo de uma gráfica
- [ ] Revisão de mensagens/labels pt-BR, estados vazios ("Nenhum material cadastrado"), loading states, confirmações de exclusão
- [ ] Formatação monetária pt-BR (R$ 1.234,56) e datas dd/MM/yyyy em toda a UI (LOCALE_ID pt-BR)
- [ ] Rodar suíte completa de testes; cobertura dos services das RN04–RN12 = 100% dos caminhos
- [ ] README final com screenshots dos fluxos principais

## Observações para execução autônoma

- Em decisões ambíguas não cobertas pelos docs, escolher a opção mais simples que satisfaça o requisito e registrar a decisão em `docs/decisoes.md`.
- Nunca implementar cálculo de custo/lucro no frontend — sempre consumir do backend.
- Se um teste revelar conflito entre docs, `docs/01-requisitos.md` prevalece.
