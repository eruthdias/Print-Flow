import pytest

pytestmark = pytest.mark.asyncio


async def _criar_admin_e_logar(client, senha="senha12345"):
    await client.post(
        "/api/setup",
        json={"nome": "Administrador", "email": "admin@example.com", "senha": senha},
    )
    resposta = await client.post("/api/auth/login", json={"email": "admin@example.com", "senha": senha})
    token = resposta.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_rota_protegida_sem_token_retorna_401(client):
    resposta = await client.get("/api/auth/me")
    assert resposta.status_code == 401


async def test_rota_protegida_com_token_invalido_retorna_401(client):
    resposta = await client.get("/api/auth/me", headers={"Authorization": "Bearer token-invalido"})
    assert resposta.status_code == 401


async def test_rota_protegida_com_token_valido_retorna_perfil(client):
    headers = await _criar_admin_e_logar(client)
    resposta = await client.get("/api/auth/me", headers=headers)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["nome"] == "Administrador"
    assert corpo["email"] == "admin@example.com"


async def test_atualizar_perfil_altera_nome_e_email(client):
    headers = await _criar_admin_e_logar(client)
    resposta = await client.put(
        "/api/auth/me",
        json={"nome": "Novo Nome", "email": "novo@example.com"},
        headers=headers,
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["nome"] == "Novo Nome"
    assert corpo["email"] == "novo@example.com"


async def test_atualizar_senha_com_senha_atual_incorreta_retorna_400(client):
    headers = await _criar_admin_e_logar(client)
    resposta = await client.put(
        "/api/auth/me/senha",
        json={"senha_atual": "senhaErrada", "senha_nova": "novaSenha123"},
        headers=headers,
    )
    assert resposta.status_code == 400
    assert resposta.json() == {"detail": "Senha atual incorreta"}


async def test_atualizar_senha_com_sucesso_permite_login_com_nova_senha(client):
    headers = await _criar_admin_e_logar(client)
    resposta = await client.put(
        "/api/auth/me/senha",
        json={"senha_atual": "senha12345", "senha_nova": "novaSenha123"},
        headers=headers,
    )
    assert resposta.status_code == 200

    login_com_senha_antiga = await client.post(
        "/api/auth/login", json={"email": "admin@example.com", "senha": "senha12345"}
    )
    assert login_com_senha_antiga.status_code == 401

    login_com_senha_nova = await client.post(
        "/api/auth/login", json={"email": "admin@example.com", "senha": "novaSenha123"}
    )
    assert login_com_senha_nova.status_code == 200
