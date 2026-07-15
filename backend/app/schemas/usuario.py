from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

TAMANHO_MINIMO_SENHA = 8


def _validar_senha(senha: str) -> str:
    if len(senha) < TAMANHO_MINIMO_SENHA:
        raise ValueError(f"Senha deve ter ao menos {TAMANHO_MINIMO_SENHA} caracteres")
    return senha


class SetupRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str

    @field_validator("nome")
    @classmethod
    def _nome_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nome é obrigatório")
        return v

    @field_validator("senha")
    @classmethod
    def _senha_valida(cls, v: str) -> str:
        return _validar_senha(v)


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SetupStatusResponse(BaseModel):
    configurado: bool


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr


class UsuarioUpdateRequest(BaseModel):
    nome: str
    email: EmailStr

    @field_validator("nome")
    @classmethod
    def _nome_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nome é obrigatório")
        return v


class SenhaUpdateRequest(BaseModel):
    senha_atual: str
    senha_nova: str

    @field_validator("senha_nova")
    @classmethod
    def _senha_nova_valida(cls, v: str) -> str:
        return _validar_senha(v)
