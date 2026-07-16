from decimal import Decimal

import pytest

pytestmark = pytest.mark.asyncio

MATERIAL_PADRAO = {
    "nome": "Papel A4",
    "unidade_compra": "pacote",
    "unidade_base": "folha",
    "fator_conversao": "100",
    "valor_compra": "25.00",
    "quantidade_atual": "500",
    "quantidade_minima": "100",
}


async def _login(client):
    await client.post(
        "/api/setup", json={"nome": "Admin", "email": "admin@example.com", "senha": "senha12345"}
    )
    resposta = await client.post(
        "/api/auth/login", json={"email": "admin@example.com", "senha": "senha12345"}
    )
    token = resposta.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_rotas_de_materiais_exigem_autenticacao(client):
    resposta = await client.get("/api/materiais")
    assert resposta.status_code == 401


async def test_criar_material_calcula_custo_unitario_base(client):
    headers = await _login(client)
    resposta = await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert Decimal(str(corpo["custo_unitario_base"])) == Decimal("0.2500")
    assert corpo["estoque_baixo"] is False
    assert corpo["quantidade_atual_unidade_compra"] is not None


async def test_criar_material_com_nome_duplicado_retorna_409(client):
    headers = await _login(client)
    await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)
    resposta = await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)
    assert resposta.status_code == 409


async def test_criar_material_com_combinacao_de_unidades_invalida_retorna_422(client):
    headers = await _login(client)
    dados = {
        **MATERIAL_PADRAO,
        "nome": "Tinta",
        "unidade_compra": "kg",
        "unidade_base": "folha",
        "fator_conversao": "1",
    }
    resposta = await client.post("/api/materiais", json=dados, headers=headers)
    assert resposta.status_code == 422


async def test_listar_materiais_com_filtro_estoque_baixo(client):
    headers = await _login(client)
    await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)
    baixo = {
        **MATERIAL_PADRAO,
        "nome": "Papel Fotográfico",
        "quantidade_atual": "5",
        "quantidade_minima": "50",
    }
    await client.post("/api/materiais", json=baixo, headers=headers)

    resposta = await client.get("/api/materiais?estoque_baixo=true", headers=headers)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["nome"] == "Papel Fotográfico"


async def test_listar_materiais_com_busca_por_nome(client):
    headers = await _login(client)
    await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)
    resposta = await client.get("/api/materiais?busca=a4", headers=headers)
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["nome"] == "Papel A4"


async def test_resumo_de_materiais_retorna_contadores_gerais(client):
    headers = await _login(client)
    material_ok = (
        await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)
    ).json()
    material_baixo = (
        await client.post(
            "/api/materiais",
            json={
                **MATERIAL_PADRAO,
                "nome": "Papel fotografico para resumo",
                "quantidade_atual": "10",
                "quantidade_minima": "50",
            },
            headers=headers,
        )
    ).json()
    await client.post(
        "/api/materiais",
        json={
            **MATERIAL_PADRAO,
            "nome": "Tinta sem estoque",
            "unidade_compra": "l",
            "unidade_base": "ml",
            "fator_conversao": "1000",
            "quantidade_atual": "0",
            "quantidade_minima": "100",
        },
        headers=headers,
    )
    await client.post(
        "/api/produtos",
        json={
            "nome": "Cartaz",
            "preco_venda": "20.00",
            "composicao": [
                {"material_id": material_ok["id"], "quantidade_utilizada": "1"}
            ],
        },
        headers=headers,
    )
    await client.post(
        "/api/desperdicios",
        json={
            "material_id": material_baixo["id"],
            "quantidade_perdida": "1",
            "motivo": "Teste do contador",
        },
        headers=headers,
    )

    resposta = await client.get("/api/materiais/resumo", headers=headers)

    assert resposta.status_code == 200
    assert resposta.json() == {
        "materiais_cadastrados": 3,
        "materiais_em_estoque": 2,
        "materiais_sem_estoque": 1,
        "produtos_cadastrados": 1,
        "desperdicios_registrados": 1,
        "precisando_compra": 2,
    }


async def test_obter_material_inexistente_retorna_404(client):
    headers = await _login(client)
    resposta = await client.get("/api/materiais/999", headers=headers)
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Material não encontrado"}


async def test_atualizar_material_recalcula_custo_unitario_base(client):
    headers = await _login(client)
    criado = (await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)).json()
    dados_atualizados = {
        "nome": "Papel A4",
        "unidade_compra": "pacote",
        "unidade_base": "folha",
        "fator_conversao": "100",
        "valor_compra": "30.00",
        "quantidade_minima": "100",
    }
    resposta = await client.put(
        f"/api/materiais/{criado['id']}", json=dados_atualizados, headers=headers
    )
    assert resposta.status_code == 200
    assert float(resposta.json()["custo_unitario_base"]) == 0.30


async def test_atualizar_material_com_nome_ja_usado_por_outro_ativo_retorna_409(client):
    headers = await _login(client)
    await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)
    outro = (
        await client.post(
            "/api/materiais", json={**MATERIAL_PADRAO, "nome": "Papel Fotográfico"}, headers=headers
        )
    ).json()

    dados_atualizados = {
        "nome": "Papel A4",
        "unidade_compra": "pacote",
        "unidade_base": "folha",
        "fator_conversao": "100",
        "valor_compra": "25.00",
        "quantidade_minima": "100",
    }
    resposta = await client.put(
        f"/api/materiais/{outro['id']}", json=dados_atualizados, headers=headers
    )
    assert resposta.status_code == 409


async def test_desativar_e_reativar_material(client):
    headers = await _login(client)
    criado = (await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)).json()

    resposta = await client.patch(
        f"/api/materiais/{criado['id']}/ativo", json={"ativo": False}, headers=headers
    )
    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is False

    resposta = await client.patch(
        f"/api/materiais/{criado['id']}/ativo", json={"ativo": True}, headers=headers
    )
    assert resposta.json()["ativo"] is True


async def test_ajuste_estoque_entrada_incrementa_quantidade(client):
    headers = await _login(client)
    criado = (await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)).json()
    resposta = await client.post(
        f"/api/materiais/{criado['id']}/ajuste-estoque",
        json={"quantidade": "50", "operacao": "entrada"},
        headers=headers,
    )
    assert resposta.status_code == 200
    assert float(resposta.json()["quantidade_atual"]) == 550.0


async def test_ajuste_estoque_saida_reduz_quantidade(client):
    headers = await _login(client)
    criado = (await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)).json()
    resposta = await client.post(
        f"/api/materiais/{criado['id']}/ajuste-estoque",
        json={"quantidade": "100", "operacao": "saida"},
        headers=headers,
    )
    assert resposta.status_code == 200
    assert float(resposta.json()["quantidade_atual"]) == 400.0


async def test_ajuste_estoque_saida_nao_pode_negativar(client):
    headers = await _login(client)
    criado = (await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)).json()
    resposta = await client.post(
        f"/api/materiais/{criado['id']}/ajuste-estoque",
        json={"quantidade": "1000", "operacao": "saida"},
        headers=headers,
    )
    assert resposta.status_code == 422


async def test_excluir_material_sem_vinculos_remove_fisicamente(client):
    headers = await _login(client)
    criado = (await client.post("/api/materiais", json=MATERIAL_PADRAO, headers=headers)).json()
    resposta = await client.delete(f"/api/materiais/{criado['id']}", headers=headers)
    assert resposta.status_code == 204

    verificacao = await client.get(f"/api/materiais/{criado['id']}", headers=headers)
    assert verificacao.status_code == 404
