# PrintFlow — Requisitos (versão final adaptada)

Este documento é a versão consolidada dos requisitos, já com as decisões do cliente aplicadas. Em caso de conflito com o PDF original, **este documento prevalece**.

## Decisões que alteram o documento original

| # | Original | Decisão final |
|---|---|---|
| D1 | RNF02: backend Java/Spring Boot | Backend em **Python/FastAPI** |
| D2 | RNF10: camadas Controller/Service/Repository/DTO/Entity | Equivalente FastAPI: router/service/repository/schema/model |
| D3 | Banco relacional genérico | **PostgreSQL 16** via Docker Compose |
| D4 | Execução | **Local**, na máquina da gráfica |
| D5 | Conversão de unidades subespecificada | Material tem `unidade_compra`, `unidade_base` e `fator_conversao`; estoque sempre em unidade base (ver docs/02) |
| D6 | Efeito de editar material sobre histórico | **Snapshot**: produções e desperdícios congelam o custo do momento do registro |
| D7 | Como cadastrar o único admin | Rota pública de setup, bloqueada permanentemente após o primeiro cadastro |
| D8 | Desperdício vinculado a produção? | Não. Desperdício é sempre registro avulso (conforme documento) |
| D9 | Escopo | Implementar **todos** os requisitos (sem MVP reduzido) |

## Requisitos Funcionais

| Código | Requisito | Observações de implementação |
|---|---|---|
| RF01 | Cadastro de um único usuário administrador | `POST /api/setup`; retorna 409 se já existe admin. `GET /api/setup/status` informa ao frontend se deve exibir tela de setup ou login |
| RF02 | Login do administrador | `POST /api/auth/login` com email + senha → JWT |
| RF03 | Cadastrar materiais no estoque | Inclui unidade de medida e fator de conversão |
| RF04 | Editar materiais | Não recalcula históricos (D6) |
| RF05 | Excluir ou desativar materiais | Soft delete (`ativo=false`). DELETE físico só se sem vínculos; senão 409 sugerindo desativação |
| RF06 | Visualizar quantidade disponível de cada material | Listagem com estoque em unidade base e em unidade de compra |
| RF07 | Definir quantidade mínima por material | Em unidade base |
| RF08 | Alertar material abaixo do mínimo | Flag `estoque_baixo` na listagem + card no dashboard + banner na tela de estoque |
| RF09 | Cadastrar produtos | |
| RF10 | Associar materiais a um produto | Composição (BOM) via ProdutoMaterial |
| RF11 | Informar quantidade utilizada de cada material no produto | Sempre em unidade base do material |
| RF12 | Calcular automaticamente custo de produção | Soma de (quantidade_utilizada × custo_unitario_base) dos materiais. Calculado no backend, exibido em tempo real na tela via endpoint de preview |
| RF13 | Informar preço de venda | |
| RF14 | Calcular lucro estimado do produto | `preco_venda − custo_producao` |
| RF15 | Registrar produção realizada | Produto + quantidade + data |
| RF16 | Atualizar estoque automaticamente na produção | Baixa = quantidade_utilizada × quantidade_produzida, por material, em unidade base. Operação transacional |
| RF17 | Impedir produção sem estoque suficiente | Validação ANTES de qualquer baixa; erro 422 listando os materiais insuficientes com faltante |
| RF18 | Registrar desperdícios | Material + quantidade (unidade base) + motivo + data |
| RF19 | Calcular custo/prejuízo do desperdício | `quantidade_perdida × custo_unitario_base` (snapshot) |
| RF20 | Histórico de produções | Listagem paginada, filtro por período e produto |
| RF21 | Histórico de desperdícios | Listagem paginada, filtro por período e material |
| RF22 | Relatórios de estoque, produção, custo e lucro | Endpoints agregados por período (ver docs/03) |
| RF23 | Dashboard resumido | Ver seção Dashboard |

## Requisitos Não Funcionais

| Código | Requisito |
|---|---|
| RNF01 | Interface simples e intuitiva (Angular Material, layout com menu lateral) |
| RNF02 | Backend em Python com FastAPI (substituído — D1) |
| RNF03 | Frontend em Angular (19+, standalone components) |
| RNF04 | PostgreSQL 16 para persistência |
| RNF05 | Integridade: FKs, constraints (quantidades ≥ 0, preços ≥ 0), transações nas operações de estoque |
| RNF06 | Todas as rotas internas protegidas por autenticação |
| RNF07 | Senhas com hash bcrypt |
| RNF08 | JWT no header `Authorization: Bearer` |
| RNF09 | Tempo de resposta < 3s nas operações principais |
| RNF10 | Camadas: router → service → repository; schemas Pydantic; models SQLAlchemy |
| RNF11 | Testes automatizados para as principais regras de negócio (RN04–RN12 no mínimo) |
| RNF12 | TDD sempre que possível nos services |

## Regras de Negócio

| Código | Regra | Detalhamento |
|---|---|---|
| RN01 | Apenas um admin | Setup bloqueia após primeiro cadastro; constraint de aplicação |
| RN02 | Senha criptografada antes de salvar | bcrypt |
| RN03 | Login só com email e senha válidos | 401 com mensagem genérica ("Email ou senha inválidos") |
| RN04 | Quantidade atual do material = total em estoque | Sempre em unidade base |
| RN05 | Produto exige ao menos 1 material na composição | Validar no cadastro: composição vazia → 422 |
| RN06 | Custo de produção baseado nos materiais | `Σ (qtd_utilizada × custo_unitario_base)`; recalculado quando a composição muda ou quando materiais da composição são editados (o custo do PRODUTO reflete o presente; só os REGISTROS de produção são congelados) |
| RN07 | Lucro estimado = preço de venda − custo de produção | Pode ser negativo; exibir em vermelho na UI |
| RN08 | Produção reduz estoque automaticamente | Transação única: valida tudo, depois baixa tudo |
| RN09 | Produção bloqueada com estoque insuficiente | Comparação em unidade base; erro lista material, necessário, disponível e faltante |
| RN10 | Alerta quando material abaixo do mínimo | `quantidade_atual < quantidade_minima` |
| RN11 | Desperdício reduz estoque | Permitir desperdício mesmo que deixe estoque em zero; nunca negativo (422 se quantidade_perdida > quantidade_atual) |
| RN12 | Custo do desperdício = custo unitário do material | Snapshot no momento do registro |

## Dashboard (RF23)

| Card | Cálculo |
|---|---|
| Total de materiais cadastrados | count(materiais ativos) |
| Materiais em estoque baixo | count(ativos com quantidade_atual < quantidade_minima) + lista |
| Produtos cadastrados | count(produtos ativos) |
| Produções realizadas | count(producoes) no período selecionado |
| Lucro estimado | Σ lucro_total das produções no período |
| Desperdício total | Σ custo_perda no período |
| Custo total de produção | Σ custo_total das produções no período |

Período padrão: mês corrente, com seletor (mês atual, últimos 30 dias, ano, personalizado). Incluir 2 gráficos: produções × lucro por mês (barras) e top 5 materiais mais consumidos (barras horizontais).

## Casos de Uso

UC01 Setup do admin · UC02 Login · UC03 Cadastrar material · UC04 Editar material · UC05 Consultar estoque · UC06 Cadastrar produto · UC07 Associar materiais ao produto · UC08 Registrar produção · UC09 Registrar desperdício · UC10 Consultar lucro · UC11 Dashboard · UC12 Relatórios

## Fora de escopo (explícito)

- Multiusuário, perfis, recuperação de senha por email (não há servidor de email local; trocar senha via tela "Minha conta" autenticada)
- Vendas/clientes/pedidos (o sistema registra produções, não vendas)
- Compras/entrada de estoque automatizada (entrada de estoque = editar quantidade do material ou endpoint de ajuste manual)
- Impressão fiscal, integração com terceiros
