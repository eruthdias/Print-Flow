# PrintFlow — Contrato da API

Base: `http://localhost:8000/api`. Todas as rotas exigem `Authorization: Bearer <jwt>`, EXCETO as marcadas com 🔓. Erros no formato `{"detail": "mensagem em português"}` (+ campos extras quando indicado). Listagens paginadas: query `?page=1&size=20` → resposta `{"items": [...], "total": n, "page": 1, "size": 20}`.

## Setup e Autenticação

| Método | Rota | Descrição |
|---|---|---|
| 🔓 GET | /setup/status | `{"configurado": bool}` — frontend decide entre tela de setup e login |
| 🔓 POST | /setup | Cria o único admin `{nome, email, senha}`. 409 se já configurado |
| 🔓 POST | /auth/login | `{email, senha}` → `{"access_token", "token_type": "bearer"}`. 401 genérico |
| GET | /auth/me | Dados do usuário logado |
| PUT | /auth/me | Atualiza nome/email |
| PUT | /auth/me/senha | `{senha_atual, senha_nova}`. 400 se senha atual incorreta |

JWT: expiração 12h (uso local, usuário único), algoritmo HS256, secret via variável de ambiente.

## Materiais

| Método | Rota | Descrição |
|---|---|---|
| GET | /materiais | Lista paginada. Filtros: `?ativo=true&estoque_baixo=true&busca=papel` |
| POST | /materiais | Cria. Valida combinações de unidade (docs/02). Retorna com `custo_unitario_base` calculado |
| GET | /materiais/{id} | Detalhe |
| PUT | /materiais/{id} | Edita (recalcula custo_unitario_base; não toca em históricos) |
| DELETE | /materiais/{id} | Físico se sem vínculos; 409 com mensagem sugerindo desativação se houver |
| PATCH | /materiais/{id}/ativo | `{"ativo": bool}` — desativar/reativar |
| POST | /materiais/{id}/ajuste-estoque | `{quantidade, operacao: "entrada"\|"saida", observacao?}` — entrada de compras / correções manuais. Saída não pode deixar negativo |

## Produtos

| Método | Rota | Descrição |
|---|---|---|
| GET | /produtos | Lista com custo_producao e lucro_estimado calculados |
| POST | /produtos | `{nome, preco_venda, composicao: [{material_id, quantidade_utilizada}]}` — composição ≥ 1 item (RN05); materiais devem estar ativos |
| GET | /produtos/{id} | Detalhe com composição expandida (nome do material, unidade, custo por item) |
| PUT | /produtos/{id} | Atualiza dados e substitui composição completa |
| DELETE | /produtos/{id} | Físico se sem produções; senão 409 |
| PATCH | /produtos/{id}/ativo | Desativar/reativar |
| POST | /produtos/preview-custo | `{composicao: [...]}` → `{custo_producao}` — usado pela tela de cadastro para exibir custo em tempo real (RF12) sem salvar |

## Produções

| Método | Rota | Descrição |
|---|---|---|
| GET | /producoes | Histórico paginado. Filtros: `?data_inicio=&data_fim=&produto_id=` (RF20) |
| POST | /producoes | `{produto_id, quantidade_produzida, data_producao?}`. Fluxo transacional de docs/02. 422 detalhado se estoque insuficiente (RF17) |
| GET | /producoes/{id} | Detalhe com itens consumidos (snapshots) |
| DELETE | /producoes/{id} | Estorna: devolve quantidades ao estoque e remove o registro (mesma transação) |

## Desperdícios

| Método | Rota | Descrição |
|---|---|---|
| GET | /desperdicios | Histórico paginado. Filtros: `?data_inicio=&data_fim=&material_id=` (RF21) |
| POST | /desperdicios | `{material_id, quantidade_perdida, motivo, data?}`. Baixa estoque; 422 se quantidade > disponível |
| GET | /desperdicios/{id} | Detalhe |
| DELETE | /desperdicios/{id} | Estorna estoque e remove |

## Relatórios (RF22)

Todos aceitam `?data_inicio=&data_fim=` (default: mês corrente).

| Método | Rota | Retorna |
|---|---|---|
| GET | /relatorios/estoque | Snapshot atual: materiais com quantidades, valor imobilizado (`quantidade_atual × custo_unitario_base`), flag estoque_baixo; total geral |
| GET | /relatorios/producao | Por produto no período: qtd de produções, quantidade produzida, custo, valor, lucro; totais |
| GET | /relatorios/custos | Custo de produção + custo de desperdício por mês do período; totais |
| GET | /relatorios/lucro | Lucro por mês e por produto; total |
| GET | /relatorios/desperdicios | Por material e por motivo no período; total |

## Dashboard (RF23)

| Método | Rota | Retorna |
|---|---|---|
| GET | /dashboard?data_inicio=&data_fim= | Objeto único com os 7 cards de docs/01 + `producoes_por_mes: [{mes, quantidade, lucro}]` + `top_materiais_consumidos: [{material, quantidade, unidade}]` (top 5) + `materiais_estoque_baixo: [...]` |

## Códigos de erro padronizados

- 401: token ausente/inválido/expirado, login incorreto
- 404: recurso não encontrado ("Material não encontrado")
- 409: conflito (setup já feito, nome duplicado, exclusão com vínculos)
- 422: validação de negócio (estoque insuficiente, composição vazia, quantidade inválida, combinação de unidades inválida)
