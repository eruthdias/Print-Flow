import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://printflow:printflow@localhost:5433/printflow_test")
os.environ.setdefault("JWT_SECRET", "test-secret-nao-usar-em-producao")

import jwt
import pytest

from app.core.security import criar_token, decodificar_token, hash_senha, verificar_senha


def test_hash_senha_gera_hash_diferente_da_senha_original():
    senha = "minhaSenha123"
    resultado = hash_senha(senha)
    assert resultado != senha


def test_verificar_senha_aceita_senha_correta():
    senha = "minhaSenha123"
    hash_gerado = hash_senha(senha)
    assert verificar_senha(senha, hash_gerado) is True


def test_verificar_senha_rejeita_senha_incorreta():
    hash_gerado = hash_senha("minhaSenha123")
    assert verificar_senha("outraSenha", hash_gerado) is False


def test_criar_token_gera_jwt_decodificavel_com_sub_correto():
    token = criar_token("42")
    payload = decodificar_token(token)
    assert payload["sub"] == "42"


def test_decodificar_token_invalido_levanta_erro():
    with pytest.raises(jwt.PyJWTError):
        decodificar_token("token-invalido")
