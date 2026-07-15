import pytest

pytestmark = pytest.mark.asyncio


async def test_status_indica_nao_configurado_quando_sem_admin(client):
    resposta = await client.get("/api/setup/status")
    assert resposta.status_code == 200
    assert resposta.json() == {"configurado": False}


async def test_setup_cria_admin_com_sucesso(client):
    resposta = await client.post(
        "/api/setup",
        json={"nome": "Administrador", "email": "admin@example.com", "senha": "senha12345"},
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome"] == "Administrador"
    assert corpo["email"] == "admin@example.com"
    assert "senha" not in corpo
    assert "senha_hash" not in corpo


async def test_status_indica_configurado_apos_setup(client):
    await client.post(
        "/api/setup",
        json={"nome": "Administrador", "email": "admin@example.com", "senha": "senha12345"},
    )
    resposta = await client.get("/api/setup/status")
    assert resposta.json() == {"configurado": True}


async def test_setup_bloqueia_segundo_cadastro(client):
    await client.post(
        "/api/setup",
        json={"nome": "Administrador", "email": "admin@example.com", "senha": "senha12345"},
    )
    resposta = await client.post(
        "/api/setup",
        json={"nome": "Outro Admin", "email": "outro@example.com", "senha": "senha12345"},
    )
    assert resposta.status_code == 409
    assert resposta.json() == {"detail": "Administrador já configurado"}


async def test_setup_valida_email_invalido(client):
    resposta = await client.post(
        "/api/setup",
        json={"nome": "Administrador", "email": "nao-e-um-email", "senha": "senha12345"},
    )
    assert resposta.status_code == 422


async def test_setup_valida_senha_curta(client):
    resposta = await client.post(
        "/api/setup",
        json={"nome": "Administrador", "email": "admin@example.com", "senha": "123"},
    )
    assert resposta.status_code == 422
