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


async def _criar_material_tinta(client, headers, quantidade_atual="5000"):
    return await _criar_material(
        client,
        headers,
        nome="Tinta",
        unidade_compra="l",
        unidade_base="ml",
        fator_conversao="1000",
        valor_compra="20.00",
        quantidade_atual=quantidade_atual,
        quantidade_minima="500",
    )


async def _criar_material_papel(client, headers, quantidade_atual="1000"):
    return await _criar_material(
        client,
        headers,
        nome="Papel",
        unidade_compra="pacote",
        unidade_base="folha",
        fator_conversao="100",
        valor_compra="25.00",
        quantidade_atual=quantidade_atual,
        quantidade_minima="100",
    )


async def _criar_produto_caneca(client, headers, caneca, tinta, papel, preco_venda="15.00"):
    resposta = await client.post(
        "/api/produtos",
        json={
            "nome": "Caneca Personalizada",
            "preco_venda": preco_venda,
            "composicao": [
                {"material_id": caneca["id"], "quantidade_utilizada": "1"},
                {"material_id": tinta["id"], "quantidade_utilizada": "5"},
                {"material_id": papel["id"], "quantidade_utilizada": "1"},
            ],
        },
        headers=headers,
    )
    return resposta.json()


async def _cenario_completo(client, headers):
    caneca = await _criar_material(client, headers, quantidade_atual="100")
    tinta = await _criar_material_tinta(client, headers)
    papel = await _criar_material_papel(client, headers)
    produto = await _criar_produto_caneca(client, headers, caneca, tinta, papel)
    return caneca, tinta, papel, produto


async def test_rotas_de_producoes_exigem_autenticacao(client):
    resposta = await client.get("/api/producoes")
    assert resposta.status_code == 401


async def test_registrar_producao_baixa_estoque_multiplicado_pela_quantidade(client):
    headers = await _login(client)
    caneca, tinta, papel, produto = await _cenario_completo(client, headers)

    resposta = await client.post(
        "/api/producoes",
        json={"produto_id": produto["id"], "quantidade_produzida": "10"},
        headers=headers,
    )
    assert resposta.status_code == 201

    caneca_atualizada = (await client.get(f"/api/materiais/{caneca['id']}", headers=headers)).json()
    tinta_atualizada = (await client.get(f"/api/materiais/{tinta['id']}", headers=headers)).json()
    papel_atualizado = (await client.get(f"/api/materiais/{papel['id']}", headers=headers)).json()

    assert float(caneca_atualizada["quantidade_atual"]) == 90.0  # 100 - 1*10
    assert float(tinta_atualizada["quantidade_atual"]) == 4950.0  # 5000 - 5*10
    assert float(papel_atualizado["quantidade_atual"]) == 990.0  # 1000 - 1*10


async def test_registrar_producao_gera_snapshots_corretos(client):
    headers = await _login(client)
    caneca, tinta, papel, produto = await _cenario_completo(client, headers)

    resposta = await client.post(
        "/api/producoes",
        json={"produto_id": produto["id"], "quantidade_produzida": "10"},
        headers=headers,
    )
    corpo = resposta.json()

    assert corpo["custo_total"] == "53.50"  # 5.35 por unidade * 10
    assert corpo["valor_total"] == "150.00"  # 15.00 * 10
    assert corpo["lucro_total"] == "96.50"

    itens_por_material = {item["material_nome"]: item for item in corpo["itens"]}
    assert float(itens_por_material["Caneca"]["quantidade_consumida"]) == 10
    assert itens_por_material["Caneca"]["custo_unitario_snapshot"] == "5.0000"
    assert float(itens_por_material["Tinta"]["quantidade_consumida"]) == 50
    assert float(itens_por_material["Papel"]["quantidade_consumida"]) == 10


async def test_producao_com_desperdicio_baixa_estoque_e_reduz_lucro(client):
    headers = await _login(client)
    caneca, tinta, papel, produto = await _cenario_completo(client, headers)
    resposta = await client.post(
        "/api/producoes",
        json={"produto_id": produto["id"], "quantidade_produzida": "1", "desperdicios": [
            {"material_id": papel["id"], "quantidade_perdida": "70", "motivo": "Erro de impressão"}
        ]},
        headers=headers,
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["custo_materiais"] == "5.35"
    assert corpo["custo_desperdicios"] == "17.50"
    assert corpo["custo_total"] == "22.85"
    assert corpo["lucro_total"] == "-7.85"
    papel_atualizado = (await client.get(f"/api/materiais/{papel['id']}", headers=headers)).json()
    assert float(papel_atualizado["quantidade_atual"]) == 929


async def test_desperdicio_rejeita_material_fora_da_composicao(client):
    headers = await _login(client)
    caneca, tinta, papel, produto = await _cenario_completo(client, headers)
    outro = await _criar_material(client, headers, nome="Outro material")
    resposta = await client.post(
        "/api/producoes",
        json={"produto_id": produto["id"], "quantidade_produzida": "1", "desperdicios": [
            {"material_id": outro["id"], "quantidade_perdida": "1", "motivo": "Erro"}
        ]},
        headers=headers,
    )
    assert resposta.status_code == 422


async def test_producao_bloqueada_quando_falta_um_material_e_nada_e_baixado(client):
    headers = await _login(client)
    caneca, tinta, papel, produto = await _cenario_completo(
        client, headers
    )
    # tinta tem 5000ml disponível; produzir 2000 unidades exigiria 10000ml -> falta
    resposta = await client.post(
        "/api/producoes",
        json={"produto_id": produto["id"], "quantidade_produzida": "2000"},
        headers=headers,
    )
    assert resposta.status_code == 422
    corpo = resposta.json()
    assert corpo["detail"] == "Estoque insuficiente"
    materiais_faltantes = {m["material"] for m in corpo["materiais"]}
    assert "Tinta" in materiais_faltantes

    # nada foi baixado (atomicidade) - inclusive materiais que tinham estoque suficiente
    caneca_apos = (await client.get(f"/api/materiais/{caneca['id']}", headers=headers)).json()
    papel_apos = (await client.get(f"/api/materiais/{papel['id']}", headers=headers)).json()
    assert float(caneca_apos["quantidade_atual"]) == 100.0
    assert float(papel_apos["quantidade_atual"]) == 1000.0


async def test_producao_bloqueada_quando_faltam_varios_materiais(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers, quantidade_atual="5")
    tinta = await _criar_material_tinta(client, headers, quantidade_atual="10")
    papel = await _criar_material_papel(client, headers)
    produto = await _criar_produto_caneca(client, headers, caneca, tinta, papel)

    resposta = await client.post(
        "/api/producoes",
        json={"produto_id": produto["id"], "quantidade_produzida": "100"},
        headers=headers,
    )
    assert resposta.status_code == 422
    materiais_faltantes = {m["material"] for m in resposta.json()["materiais"]}
    assert materiais_faltantes == {"Caneca", "Tinta"}


async def test_producao_bloqueada_para_produto_inexistente_ou_inativo(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    produto = await _criar_produto_caneca(
        client,
        headers,
        caneca,
        await _criar_material_tinta(client, headers),
        await _criar_material_papel(client, headers),
    )
    resposta_inexistente = await client.post(
        "/api/producoes",
        json={"produto_id": 999999, "quantidade_produzida": "1"},
        headers=headers,
    )
    assert resposta_inexistente.status_code == 404

    await client.patch(f"/api/produtos/{produto['id']}/ativo", json={"ativo": False}, headers=headers)
    resposta_inativo = await client.post(
        "/api/producoes",
        json={"produto_id": produto["id"], "quantidade_produzida": "1"},
        headers=headers,
    )
    assert resposta_inativo.status_code == 422


async def test_producao_gera_alerta_de_estoque_baixo(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers, quantidade_atual="12", quantidade_minima="10")
    tinta = await _criar_material_tinta(client, headers)
    papel = await _criar_material_papel(client, headers)
    produto = await _criar_produto_caneca(client, headers, caneca, tinta, papel)

    resposta = await client.post(
        "/api/producoes",
        json={"produto_id": produto["id"], "quantidade_produzida": "5"},
        headers=headers,
    )
    corpo = resposta.json()
    nomes_alertados = {a["material_nome"] for a in corpo["alertas_estoque_baixo"]}
    assert "Caneca" in nomes_alertados  # 12 - 5 = 7 < minimo 10


async def test_listar_producoes_com_filtro_por_produto(client):
    headers = await _login(client)
    caneca, tinta, papel, produto = await _cenario_completo(client, headers)
    await client.post(
        "/api/producoes",
        json={"produto_id": produto["id"], "quantidade_produzida": "1"},
        headers=headers,
    )

    resposta = await client.get(f"/api/producoes?produto_id={produto['id']}", headers=headers)
    assert resposta.status_code == 200
    assert resposta.json()["total"] == 1


async def test_obter_producao_com_itens_consumidos(client):
    headers = await _login(client)
    caneca, tinta, papel, produto = await _cenario_completo(client, headers)
    criada = (
        await client.post(
            "/api/producoes",
            json={"produto_id": produto["id"], "quantidade_produzida": "1"},
            headers=headers,
        )
    ).json()

    resposta = await client.get(f"/api/producoes/{criada['id']}", headers=headers)
    assert resposta.status_code == 200
    assert len(resposta.json()["itens"]) == 3


async def test_estornar_producao_devolve_estoque_exatamente(client):
    headers = await _login(client)
    caneca, tinta, papel, produto = await _cenario_completo(client, headers)

    criada = (
        await client.post(
            "/api/producoes",
            json={"produto_id": produto["id"], "quantidade_produzida": "10"},
            headers=headers,
        )
    ).json()

    resposta = await client.delete(f"/api/producoes/{criada['id']}", headers=headers)
    assert resposta.status_code == 204

    caneca_apos = (await client.get(f"/api/materiais/{caneca['id']}", headers=headers)).json()
    tinta_apos = (await client.get(f"/api/materiais/{tinta['id']}", headers=headers)).json()
    papel_apos = (await client.get(f"/api/materiais/{papel['id']}", headers=headers)).json()

    assert float(caneca_apos["quantidade_atual"]) == 100.0
    assert float(tinta_apos["quantidade_atual"]) == 5000.0
    assert float(papel_apos["quantidade_atual"]) == 1000.0

    verificacao = await client.get(f"/api/producoes/{criada['id']}", headers=headers)
    assert verificacao.status_code == 404
