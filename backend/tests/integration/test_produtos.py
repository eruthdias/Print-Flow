import pytest

from app.core.config import get_settings

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
        "quantidade_atual": "1000",
        "quantidade_minima": "10",
    }
    dados.update(overrides)
    resposta = await client.post("/api/materiais", json=dados, headers=headers)
    return resposta.json()


async def _criar_material_tinta(client, headers):
    return await _criar_material(
        client,
        headers,
        nome="Tinta",
        unidade_compra="l",
        unidade_base="ml",
        fator_conversao="1000",
        valor_compra="20.00",
    )


async def test_rotas_de_produtos_exigem_autenticacao(client):
    resposta = await client.get("/api/produtos")
    assert resposta.status_code == 401


async def test_criar_produto_calcula_custo_e_lucro(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    tinta = await _criar_material_tinta(client, headers)

    dados = {
        "nome": "Caneca Personalizada",
        "preco_venda": "15.00",
        "composicao": [
            {"material_id": caneca["id"], "quantidade_utilizada": "1"},
            {"material_id": tinta["id"], "quantidade_utilizada": "5"},
        ],
    }
    resposta = await client.post("/api/produtos", json=dados, headers=headers)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["custo_producao"] == "5.10"
    assert corpo["lucro_estimado"] == "9.90"
    assert len(corpo["composicao"]) == 2
    assert corpo["imagem_url"] is None
    assert corpo["video_url"] is None


async def test_produto_usa_valor_unitario_do_material_e_nao_o_valor_total_do_pacote(client):
    headers = await _login(client)
    # Pacote de 100 folhas por R$ 25,00 -> valor unitário deve ser R$ 0,25/folha, não R$ 25,00.
    papel = await _criar_material(
        client,
        headers,
        nome="Papel A4",
        unidade_compra="pacote",
        unidade_base="folha",
        fator_conversao="100",
        valor_compra="25.00",
        quantidade_atual="1000",
    )

    dados = {
        "nome": "Cartão de visita",
        "preco_venda": "5.00",
        "composicao": [{"material_id": papel["id"], "quantidade_utilizada": "1"}],
    }
    resposta = await client.post("/api/produtos", json=dados, headers=headers)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["custo_producao"] == "0.25"
    assert corpo["composicao"][0]["custo_unitario_base"] == "0.2500"


async def test_carregar_substituir_e_remover_imagem_e_video_do_produto(
    client, tmp_path, monkeypatch
):
    monkeypatch.setattr(get_settings(), "uploads_dir", tmp_path)
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    produto = (
        await client.post(
            "/api/produtos",
            json={
                "nome": "Caneca com mídia",
                "preco_venda": "15.00",
                "composicao": [
                    {"material_id": caneca["id"], "quantidade_utilizada": "1"}
                ],
            },
            headers=headers,
        )
    ).json()

    imagem = await client.post(
        f"/api/produtos/{produto['id']}/imagem",
        files={"arquivo": ("produto.png", b"\x89PNG\r\n\x1a\nconteudo", "image/png")},
        headers=headers,
    )
    assert imagem.status_code == 200
    primeira_url = imagem.json()["imagem_url"]
    primeiro_arquivo = tmp_path / "produtos" / primeira_url.rsplit("/", 1)[-1]
    assert primeiro_arquivo.exists()

    imagem_substituida = await client.post(
        f"/api/produtos/{produto['id']}/imagem",
        files={"arquivo": ("nova.jpg", b"\xff\xd8\xffconteudo", "image/jpeg")},
        headers=headers,
    )
    assert imagem_substituida.status_code == 200
    assert imagem_substituida.json()["imagem_url"].endswith(".jpg")
    assert not primeiro_arquivo.exists()

    video = await client.post(
        f"/api/produtos/{produto['id']}/video",
        files={"arquivo": ("produto.mp4", b"\x00\x00\x00\x18ftypmp42", "video/mp4")},
        headers=headers,
    )
    assert video.status_code == 200
    assert video.json()["video_url"].endswith(".mp4")

    sem_imagem = await client.delete(
        f"/api/produtos/{produto['id']}/imagem", headers=headers
    )
    sem_video = await client.delete(
        f"/api/produtos/{produto['id']}/video", headers=headers
    )
    assert sem_imagem.json()["imagem_url"] is None
    assert sem_video.json()["video_url"] is None
    assert list((tmp_path / "produtos").iterdir()) == []


async def test_upload_rejeita_tipo_ou_conteudo_de_midia_invalido(client, tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "uploads_dir", tmp_path)
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    produto = (
        await client.post(
            "/api/produtos",
            json={
                "nome": "Caneca para mídia inválida",
                "preco_venda": "15.00",
                "composicao": [
                    {"material_id": caneca["id"], "quantidade_utilizada": "1"}
                ],
            },
            headers=headers,
        )
    ).json()

    tipo_invalido = await client.post(
        f"/api/produtos/{produto['id']}/imagem",
        files={"arquivo": ("arquivo.gif", b"GIF89a", "image/gif")},
        headers=headers,
    )
    conteudo_invalido = await client.post(
        f"/api/produtos/{produto['id']}/video",
        files={"arquivo": ("falso.mp4", b"isto nao e video", "video/mp4")},
        headers=headers,
    )

    assert tipo_invalido.status_code == 422
    assert conteudo_invalido.status_code == 422


async def test_criar_produto_com_lucro_negativo(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers, valor_compra="20.00")

    dados = {
        "nome": "Caneca Cara",
        "preco_venda": "15.00",
        "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
    }
    resposta = await client.post("/api/produtos", json=dados, headers=headers)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["lucro_estimado"] == "-5.00"


async def test_criar_produto_com_composicao_vazia_retorna_422(client):
    headers = await _login(client)
    dados = {"nome": "Produto Vazio", "preco_venda": "10.00", "composicao": []}
    resposta = await client.post("/api/produtos", json=dados, headers=headers)
    assert resposta.status_code == 422


async def test_criar_produto_com_material_inativo_retorna_422(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    await client.patch(f"/api/materiais/{caneca['id']}/ativo", json={"ativo": False}, headers=headers)

    dados = {
        "nome": "Produto com Material Inativo",
        "preco_venda": "10.00",
        "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
    }
    resposta = await client.post("/api/produtos", json=dados, headers=headers)
    assert resposta.status_code == 422


async def test_criar_produto_com_material_inexistente_na_composicao_retorna_422(client):
    headers = await _login(client)
    dados = {
        "nome": "Produto com Material Inexistente",
        "preco_venda": "10.00",
        "composicao": [{"material_id": 999999, "quantidade_utilizada": "1"}],
    }
    resposta = await client.post("/api/produtos", json=dados, headers=headers)
    assert resposta.status_code == 422


async def test_criar_produto_com_material_duplicado_na_composicao_retorna_422(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)

    dados = {
        "nome": "Produto Duplicado",
        "preco_venda": "10.00",
        "composicao": [
            {"material_id": caneca["id"], "quantidade_utilizada": "1"},
            {"material_id": caneca["id"], "quantidade_utilizada": "2"},
        ],
    }
    resposta = await client.post("/api/produtos", json=dados, headers=headers)
    assert resposta.status_code == 422


async def test_criar_produto_com_nome_duplicado_retorna_409(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    dados = {
        "nome": "Caneca Personalizada",
        "preco_venda": "15.00",
        "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
    }
    await client.post("/api/produtos", json=dados, headers=headers)
    resposta = await client.post("/api/produtos", json=dados, headers=headers)
    assert resposta.status_code == 409


async def test_atualizar_produto_com_nome_ja_usado_por_outro_ativo_retorna_409(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    await client.post(
        "/api/produtos",
        json={
            "nome": "Caneca Personalizada",
            "preco_venda": "15.00",
            "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
        },
        headers=headers,
    )
    outro = (
        await client.post(
            "/api/produtos",
            json={
                "nome": "Caneca Simples",
                "preco_venda": "10.00",
                "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
            },
            headers=headers,
        )
    ).json()

    resposta = await client.put(
        f"/api/produtos/{outro['id']}",
        json={
            "nome": "Caneca Personalizada",
            "preco_venda": "10.00",
            "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
        },
        headers=headers,
    )
    assert resposta.status_code == 409


async def test_excluir_produto_com_producao_vinculada_retorna_409(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    produto = (
        await client.post(
            "/api/produtos",
            json={
                "nome": "Caneca Personalizada",
                "preco_venda": "15.00",
                "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
            },
            headers=headers,
        )
    ).json()
    await client.post(
        "/api/producoes",
        json={"produto_id": produto["id"], "quantidade_produzida": "1"},
        headers=headers,
    )

    resposta = await client.delete(f"/api/produtos/{produto['id']}", headers=headers)
    assert resposta.status_code == 409


async def test_preview_custo_nao_persiste_produto(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)

    resposta = await client.post(
        "/api/produtos/preview-custo",
        json={"composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "3"}]},
        headers=headers,
    )
    assert resposta.status_code == 200
    assert resposta.json() == {"custo_producao": "15.00"}

    listagem = await client.get("/api/produtos", headers=headers)
    assert listagem.json() == {"items": [], "total": 0}


async def test_obter_produto_com_composicao_expandida(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    criado = (
        await client.post(
            "/api/produtos",
            json={
                "nome": "Caneca Personalizada",
                "preco_venda": "15.00",
                "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
            },
            headers=headers,
        )
    ).json()

    resposta = await client.get(f"/api/produtos/{criado['id']}", headers=headers)
    assert resposta.status_code == 200
    item = resposta.json()["composicao"][0]
    assert item["material_nome"] == "Caneca"
    assert item["unidade_base"] == "un"


async def test_atualizar_produto_substitui_composicao_completa(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    tinta = await _criar_material_tinta(client, headers)
    criado = (
        await client.post(
            "/api/produtos",
            json={
                "nome": "Caneca Personalizada",
                "preco_venda": "15.00",
                "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
            },
            headers=headers,
        )
    ).json()

    resposta = await client.put(
        f"/api/produtos/{criado['id']}",
        json={
            "nome": "Caneca Personalizada",
            "preco_venda": "15.00",
            "composicao": [{"material_id": tinta["id"], "quantidade_utilizada": "10"}],
        },
        headers=headers,
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo["composicao"]) == 1
    assert corpo["composicao"][0]["material_nome"] == "Tinta"


async def test_produto_reflete_custo_atual_do_material_apos_edicao(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    criado = (
        await client.post(
            "/api/produtos",
            json={
                "nome": "Caneca Personalizada",
                "preco_venda": "15.00",
                "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
            },
            headers=headers,
        )
    ).json()
    assert criado["custo_producao"] == "5.00"

    await client.put(
        f"/api/materiais/{caneca['id']}",
        json={
            "nome": "Caneca",
            "unidade_compra": "un",
            "unidade_base": "un",
            "fator_conversao": "1",
            "valor_compra": "8.00",
            "quantidade_minima": "10",
        },
        headers=headers,
    )

    resposta = await client.get(f"/api/produtos/{criado['id']}", headers=headers)
    assert resposta.json()["custo_producao"] == "8.00"


async def test_desativar_e_reativar_produto(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    criado = (
        await client.post(
            "/api/produtos",
            json={
                "nome": "Caneca Personalizada",
                "preco_venda": "15.00",
                "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
            },
            headers=headers,
        )
    ).json()

    resposta = await client.patch(
        f"/api/produtos/{criado['id']}/ativo", json={"ativo": False}, headers=headers
    )
    assert resposta.json()["ativo"] is False


async def test_excluir_produto_sem_producoes_remove_fisicamente(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    criado = (
        await client.post(
            "/api/produtos",
            json={
                "nome": "Caneca Personalizada",
                "preco_venda": "15.00",
                "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
            },
            headers=headers,
        )
    ).json()

    resposta = await client.delete(f"/api/produtos/{criado['id']}", headers=headers)
    assert resposta.status_code == 204

    verificacao = await client.get(f"/api/produtos/{criado['id']}", headers=headers)
    assert verificacao.status_code == 404


async def test_excluir_material_usado_em_produto_retorna_409(client):
    headers = await _login(client)
    caneca = await _criar_material(client, headers)
    await client.post(
        "/api/produtos",
        json={
            "nome": "Caneca Personalizada",
            "preco_venda": "15.00",
            "composicao": [{"material_id": caneca["id"], "quantidade_utilizada": "1"}],
        },
        headers=headers,
    )

    resposta = await client.delete(f"/api/materiais/{caneca['id']}", headers=headers)
    assert resposta.status_code == 409
