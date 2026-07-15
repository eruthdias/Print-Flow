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


async def _criar_material_papel(client, headers, quantidade_atual="1000"):
    dados = {
        "nome": "Papel A4",
        "unidade_compra": "pacote",
        "unidade_base": "folha",
        "fator_conversao": "100",
        "valor_compra": "25.00",
        "quantidade_atual": quantidade_atual,
        "quantidade_minima": "100",
    }
    resposta = await client.post("/api/materiais", json=dados, headers=headers)
    return resposta.json()


async def test_rotas_de_desperdicios_exigem_autenticacao(client):
    resposta = await client.get("/api/desperdicios")
    assert resposta.status_code == 401


async def test_registrar_desperdicio_reduz_estoque_e_calcula_custo(client):
    headers = await _login(client)
    papel = await _criar_material_papel(client, headers)

    resposta = await client.post(
        "/api/desperdicios",
        json={"material_id": papel["id"], "quantidade_perdida": "20", "motivo": "Erro de impressão"},
        headers=headers,
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["custo_perda"] == "5.00"  # 20 * 0.25
    assert corpo["material_nome"] == "Papel A4"

    papel_atualizado = (await client.get(f"/api/materiais/{papel['id']}", headers=headers)).json()
    assert float(papel_atualizado["quantidade_atual"]) == 980.0


async def test_desperdicio_pode_zerar_o_estoque(client):
    headers = await _login(client)
    papel = await _criar_material_papel(client, headers, quantidade_atual="20")

    resposta = await client.post(
        "/api/desperdicios",
        json={"material_id": papel["id"], "quantidade_perdida": "20", "motivo": "Descarte total"},
        headers=headers,
    )
    assert resposta.status_code == 201

    papel_atualizado = (await client.get(f"/api/materiais/{papel['id']}", headers=headers)).json()
    assert float(papel_atualizado["quantidade_atual"]) == 0.0


async def test_desperdicio_maior_que_estoque_retorna_422_e_nao_altera_estoque(client):
    headers = await _login(client)
    papel = await _criar_material_papel(client, headers, quantidade_atual="10")

    resposta = await client.post(
        "/api/desperdicios",
        json={"material_id": papel["id"], "quantidade_perdida": "11", "motivo": "Teste"},
        headers=headers,
    )
    assert resposta.status_code == 422

    papel_atualizado = (await client.get(f"/api/materiais/{papel['id']}", headers=headers)).json()
    assert float(papel_atualizado["quantidade_atual"]) == 10.0


async def test_registrar_desperdicio_com_material_inexistente_retorna_404(client):
    headers = await _login(client)
    resposta = await client.post(
        "/api/desperdicios",
        json={"material_id": 999999, "quantidade_perdida": "1", "motivo": "Teste"},
        headers=headers,
    )
    assert resposta.status_code == 404


async def test_registrar_desperdicio_sem_motivo_retorna_422(client):
    headers = await _login(client)
    papel = await _criar_material_papel(client, headers)
    resposta = await client.post(
        "/api/desperdicios",
        json={"material_id": papel["id"], "quantidade_perdida": "1", "motivo": "   "},
        headers=headers,
    )
    assert resposta.status_code == 422


async def test_listar_desperdicios_com_filtro_por_material(client):
    headers = await _login(client)
    papel = await _criar_material_papel(client, headers)
    outro = await _criar_material_papel(client, headers, quantidade_atual="500")
    await client.post(
        "/api/desperdicios",
        json={"material_id": papel["id"], "quantidade_perdida": "5", "motivo": "Teste"},
        headers=headers,
    )

    resposta = await client.get(f"/api/desperdicios?material_id={papel['id']}", headers=headers)
    assert resposta.status_code == 200
    assert resposta.json()["total"] == 1


async def test_obter_desperdicio_por_id(client):
    headers = await _login(client)
    papel = await _criar_material_papel(client, headers)
    criado = (
        await client.post(
            "/api/desperdicios",
            json={"material_id": papel["id"], "quantidade_perdida": "5", "motivo": "Teste"},
            headers=headers,
        )
    ).json()

    resposta = await client.get(f"/api/desperdicios/{criado['id']}", headers=headers)
    assert resposta.status_code == 200
    assert resposta.json()["motivo"] == "Teste"


async def test_estornar_desperdicio_devolve_estoque_e_remove_registro(client):
    headers = await _login(client)
    papel = await _criar_material_papel(client, headers)
    criado = (
        await client.post(
            "/api/desperdicios",
            json={"material_id": papel["id"], "quantidade_perdida": "20", "motivo": "Teste"},
            headers=headers,
        )
    ).json()

    resposta = await client.delete(f"/api/desperdicios/{criado['id']}", headers=headers)
    assert resposta.status_code == 204

    papel_atualizado = (await client.get(f"/api/materiais/{papel['id']}", headers=headers)).json()
    assert float(papel_atualizado["quantidade_atual"]) == 1000.0

    verificacao = await client.get(f"/api/desperdicios/{criado['id']}", headers=headers)
    assert verificacao.status_code == 404
