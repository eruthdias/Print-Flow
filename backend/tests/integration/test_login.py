import jwt
import pytest

from app.core.config import get_settings

pytestmark = pytest.mark.asyncio


async def _criar_admin(client, senha="senha12345"):
    await client.post(
        "/api/setup",
        json={"nome": "Administrador", "email": "admin@example.com", "senha": senha},
    )


async def test_login_com_credenciais_corretas_gera_token_valido(client):
    await _criar_admin(client)
    resposta = await client.post(
        "/api/auth/login", json={"email": "admin@example.com", "senha": "senha12345"}
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    settings = get_settings()
    payload = jwt.decode(corpo["access_token"], settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert "sub" in payload


async def test_login_com_senha_incorreta_retorna_401_generico(client):
    await _criar_admin(client)
    resposta = await client.post(
        "/api/auth/login", json={"email": "admin@example.com", "senha": "senhaErrada"}
    )
    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Email ou senha inválidos"}


async def test_login_com_email_inexistente_retorna_mesma_mensagem_401(client):
    resposta = await client.post(
        "/api/auth/login", json={"email": "naoexiste@example.com", "senha": "senha12345"}
    )
    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Email ou senha inválidos"}
