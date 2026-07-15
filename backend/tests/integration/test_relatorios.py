from datetime import date

import pytest

pytestmark = pytest.mark.asyncio


async def _login(client):
    await client.post(
        "/api/setup", json={"nome": "Admin", "email": "admin@example.com", "senha": "senha12345"}
    )
    resposta = await client.post(
        "/api/auth/login", json={"email": "admin@example.com", "senha": "senha12345"}
    )
    token = resposta.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _criar_material(client, headers, **overrides):
    dados = {
        "nome": "Caneca",
        "unidade_compra": "un",
        "unidade_base": "un",
        "fator_conversao": "1",
        "valor_compra": "5.00",
        "quantidade_atual": "100",
        "quantidade_minima": "10",
    }
    dados.update(overrides)
    resposta = await client.post("/api/materiais", json=dados, headers=headers)
    return resposta.json()


async def _criar_produto(client, headers, material, preco_venda="15.00", nome="Caneca Personalizada"):
    resposta = await client.post(
        "/api/produtos",
        json={
            "nome": nome,
            "preco_venda": preco_venda,
            "composicao": [{"material_id": material["id"], "quantidade_utilizada": "1"}],
        },
        headers=headers,
    )
    return resposta.json()


async def _cenario_com_producao_e_desperdicio(client, headers):
    material = await _criar_material(client, headers)
    produto = await _criar_produto(client, headers, material)
    hoje = date.today().isoformat()

    producao = (
        await client.post(
            "/api/producoes",
            json={"produto_id": produto["id"], "quantidade_produzida": "10", "data_producao": hoje},
            headers=headers,
        )
    ).json()

    desperdicio = (
        await client.post(
            "/api/desperdicios",
            json={"material_id": material["id"], "quantidade_perdida": "5", "motivo": "Quebra", "data": hoje},
            headers=headers,
        )
    ).json()

    return material, produto, producao, desperdicio


async def test_relatorios_exigem_autenticacao(client):
    resposta = await client.get("/api/relatorios/estoque")
    assert resposta.status_code == 401


async def test_relatorio_estoque_calcula_valor_imobilizado(client):
    headers = await _login(client)
    await _criar_material(client, headers, quantidade_atual="100", valor_compra="5.00")

    resposta = await client.get("/api/relatorios/estoque", headers=headers)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["valor_total_imobilizado"] == "500.00"
    assert corpo["itens"][0]["valor_imobilizado"] == "500.00"


async def test_relatorio_producao_agrega_por_produto(client):
    headers = await _login(client)
    material, produto, producao, _ = await _cenario_com_producao_e_desperdicio(client, headers)

    resposta = await client.get("/api/relatorios/producao", headers=headers)
    assert resposta.status_code == 200
    corpo = resposta.json()
    item = corpo["itens"][0]
    assert item["produto_nome"] == "Caneca Personalizada"
    assert item["quantidade_producoes"] == 1
    assert item["custo_total"] == "50.00"
    assert item["lucro_total"] == "100.00"
    assert corpo["total_lucro"] == "100.00"


async def test_relatorio_custos_soma_producao_e_desperdicio_no_mes(client):
    headers = await _login(client)
    await _cenario_com_producao_e_desperdicio(client, headers)

    resposta = await client.get("/api/relatorios/custos", headers=headers)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo["itens"]) == 1
    item = corpo["itens"][0]
    assert item["custo_producao"] == "50.00"
    assert item["custo_desperdicio"] == "25.00"
    assert item["custo_total"] == "75.00"
    assert corpo["total_geral"] == "75.00"


async def test_relatorio_lucro_por_mes_e_por_produto(client):
    headers = await _login(client)
    await _cenario_com_producao_e_desperdicio(client, headers)

    resposta = await client.get("/api/relatorios/lucro", headers=headers)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total_lucro"] == "100.00"
    assert corpo["por_mes"][0]["lucro_total"] == "100.00"
    assert corpo["por_produto"][0]["lucro_total"] == "100.00"


async def test_relatorio_desperdicios_por_material_e_motivo(client):
    headers = await _login(client)
    await _cenario_com_producao_e_desperdicio(client, headers)

    resposta = await client.get("/api/relatorios/desperdicios", headers=headers)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["por_material"][0]["material_nome"] == "Caneca"
    assert corpo["por_material"][0]["custo_total"] == "25.00"
    assert corpo["por_motivo"][0]["motivo"] == "Quebra"
    assert corpo["por_motivo"][0]["quantidade_ocorrencias"] == 1
    assert corpo["total_custo"] == "25.00"


async def test_relatorios_respeitam_filtro_de_periodo(client):
    headers = await _login(client)
    await _cenario_com_producao_e_desperdicio(client, headers)

    resposta = await client.get(
        "/api/relatorios/producao?data_inicio=2000-01-01&data_fim=2000-01-31", headers=headers
    )
    corpo = resposta.json()
    assert corpo["itens"] == []
    assert corpo["total_lucro"] == "0"


async def test_dashboard_exige_autenticacao(client):
    resposta = await client.get("/api/dashboard")
    assert resposta.status_code == 401


async def test_dashboard_agrega_todos_os_cards(client):
    headers = await _login(client)
    material, produto, producao, desperdicio = await _cenario_com_producao_e_desperdicio(client, headers)

    resposta = await client.get("/api/dashboard", headers=headers)
    assert resposta.status_code == 200
    corpo = resposta.json()

    assert corpo["total_materiais"] == 1
    assert corpo["total_produtos"] == 1
    assert corpo["producoes_realizadas"] == 1
    assert corpo["lucro_estimado"] == "100.00"
    assert corpo["desperdicio_total"] == "25.00"
    assert corpo["custo_total_producao"] == "50.00"
    assert len(corpo["producoes_por_mes"]) == 1
    assert corpo["producoes_por_mes"][0]["quantidade"] == 1
    assert len(corpo["top_materiais_consumidos"]) == 1
    assert corpo["top_materiais_consumidos"][0]["material"] == "Caneca"


async def test_dashboard_lista_materiais_em_estoque_baixo(client):
    headers = await _login(client)
    await _criar_material(
        client, headers, nome="Papel", quantidade_atual="5", quantidade_minima="50"
    )

    resposta = await client.get("/api/dashboard", headers=headers)
    corpo = resposta.json()
    assert corpo["materiais_estoque_baixo_total"] == 1
    assert corpo["materiais_estoque_baixo"][0]["material_nome"] == "Papel"


async def test_dashboard_usa_mes_corrente_como_periodo_padrao(client):
    headers = await _login(client)
    resposta = await client.get("/api/dashboard", headers=headers)
    corpo = resposta.json()
    hoje = date.today()
    assert corpo["data_inicio"] == hoje.replace(day=1).isoformat()
