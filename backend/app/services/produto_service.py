from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflitoError, NaoEncontradoError, ValidacaoError
from app.models.material import Material
from app.models.produto import Produto
from app.models.produto_material import ProdutoMaterial
from app.repositories import material_repository as material_repo
from app.repositories import produto_repository as repo
from app.schemas.produto import (
    ComposicaoItemOut,
    ComposicaoItemRequest,
    PreviewCustoRequest,
    ProdutoCreateRequest,
    ProdutoOut,
    ProdutoUpdateRequest,
)

_DUAS_CASAS = Decimal("0.01")
_TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024
_TAMANHO_MAXIMO_VIDEO = 50 * 1024 * 1024
_TIPOS_IMAGEM = {
    "image/jpeg": (".jpg", lambda inicio: inicio.startswith(b"\xff\xd8\xff")),
    "image/png": (".png", lambda inicio: inicio.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (".webp", lambda inicio: inicio[:4] == b"RIFF" and inicio[8:12] == b"WEBP"),
}
_TIPOS_VIDEO = {
    "video/mp4": (".mp4", lambda inicio: inicio[4:8] == b"ftyp"),
    "video/webm": (".webm", lambda inicio: inicio.startswith(b"\x1aE\xdf\xa3")),
}


async def _validar_composicao(
    db: AsyncSession, composicao: list[ComposicaoItemRequest]
) -> list[Material]:
    materiais = []
    for item in composicao:
        material = await material_repo.obter_por_id(db, item.material_id)
        if material is None:
            raise ValidacaoError(f"Material de id {item.material_id} não encontrado")
        if not material.ativo:
            raise ValidacaoError(f"Material '{material.nome}' está inativo e não pode ser usado na composição")
        materiais.append(material)
    return materiais


def calcular_custo_producao(produto: Produto) -> Decimal:
    total = sum(
        (pm.quantidade_utilizada * pm.material.custo_unitario_base for pm in produto.composicao),
        start=Decimal("0"),
    )
    return total.quantize(_DUAS_CASAS, rounding=ROUND_HALF_UP)


def _montar_composicao_out(produto: Produto) -> list[ComposicaoItemOut]:
    itens = []
    for pm in produto.composicao:
        custo_item = (pm.quantidade_utilizada * pm.material.custo_unitario_base).quantize(
            _DUAS_CASAS, rounding=ROUND_HALF_UP
        )
        itens.append(
            ComposicaoItemOut(
                material_id=pm.material_id,
                material_nome=pm.material.nome,
                unidade_base=pm.material.unidade_base,
                valor_compra=pm.material.valor_compra,
                quantidade_por_compra=pm.material.fator_conversao,
                quantidade_utilizada=pm.quantidade_utilizada,
                custo_unitario_base=pm.material.custo_unitario_base,
                custo_item=custo_item,
            )
        )
    return itens


def montar_produto_out(produto: Produto) -> ProdutoOut:
    custo = calcular_custo_producao(produto)
    return ProdutoOut(
        id=produto.id,
        nome=produto.nome,
        preco_venda=produto.preco_venda,
        ativo=produto.ativo,
        imagem_url=produto.imagem_url,
        video_url=produto.video_url,
        custo_producao=custo,
        lucro_estimado=produto.preco_venda - custo,
        composicao=_montar_composicao_out(produto),
    )


async def listar(
    db: AsyncSession, *, ativo: bool | None = None, busca: str | None = None
) -> list[Produto]:
    return await repo.listar(db, ativo=ativo, busca=busca)


async def obter(db: AsyncSession, produto_id: int) -> Produto:
    produto = await repo.obter_por_id(db, produto_id)
    if produto is None:
        raise NaoEncontradoError("Produto não encontrado")
    return produto


async def criar(db: AsyncSession, dados: ProdutoCreateRequest) -> Produto:
    if await repo.existe_nome_ativo(db, dados.nome):
        raise ConflitoError("Já existe um produto ativo com este nome")
    await _validar_composicao(db, dados.composicao)
    produto = Produto(nome=dados.nome, preco_venda=dados.preco_venda)
    produto.composicao = [
        ProdutoMaterial(material_id=item.material_id, quantidade_utilizada=item.quantidade_utilizada)
        for item in dados.composicao
    ]
    return await repo.criar(db, produto)


async def atualizar(db: AsyncSession, produto_id: int, dados: ProdutoUpdateRequest) -> Produto:
    produto = await obter(db, produto_id)
    if dados.nome != produto.nome and await repo.existe_nome_ativo(db, dados.nome, ignorar_id=produto_id):
        raise ConflitoError("Já existe um produto ativo com este nome")
    await _validar_composicao(db, dados.composicao)
    produto.nome = dados.nome
    produto.preco_venda = dados.preco_venda
    produto.composicao = [
        ProdutoMaterial(material_id=item.material_id, quantidade_utilizada=item.quantidade_utilizada)
        for item in dados.composicao
    ]
    return await repo.salvar(db, produto)


async def alterar_ativo(db: AsyncSession, produto_id: int, ativo: bool) -> Produto:
    produto = await obter(db, produto_id)
    produto.ativo = ativo
    return await repo.salvar(db, produto)


async def excluir(db: AsyncSession, produto_id: int) -> None:
    produto = await obter(db, produto_id)
    urls_midia = (produto.imagem_url, produto.video_url)
    try:
        await repo.excluir(db, produto)
    except IntegrityError as exc:
        await db.rollback()
        raise ConflitoError(
            "Produto possui produções vinculadas e não pode ser excluído. Desative-o em vez de excluir."
        ) from exc
    for url in urls_midia:
        _excluir_arquivo(url)


def _diretorio_uploads_produtos() -> Path:
    diretorio = get_settings().uploads_dir / "produtos"
    diretorio.mkdir(parents=True, exist_ok=True)
    return diretorio


def _excluir_arquivo(url: str | None) -> None:
    if not url:
        return
    caminho = _diretorio_uploads_produtos() / Path(url).name
    caminho.unlink(missing_ok=True)


async def _salvar_upload(arquivo: UploadFile, tipo: str) -> str:
    configuracoes = _TIPOS_IMAGEM if tipo == "imagem" else _TIPOS_VIDEO
    limite = _TAMANHO_MAXIMO_IMAGEM if tipo == "imagem" else _TAMANHO_MAXIMO_VIDEO
    content_type = (arquivo.content_type or "").lower()
    configuracao = configuracoes.get(content_type)
    if configuracao is None:
        permitidos = ", ".join(configuracoes)
        raise ValidacaoError(f"Formato de {tipo} inválido. Permitidos: {permitidos}")

    extensao, assinatura_valida = configuracao
    nome = f"{uuid4().hex}{extensao}"
    caminho = _diretorio_uploads_produtos() / nome
    tamanho = 0

    try:
        with caminho.open("wb") as destino:
            while bloco := await arquivo.read(1024 * 1024):
                if tamanho == 0 and not assinatura_valida(bloco):
                    raise ValidacaoError(f"O conteúdo enviado não é um arquivo de {tipo} válido")
                tamanho += len(bloco)
                if tamanho > limite:
                    limite_mb = limite // (1024 * 1024)
                    raise ValidacaoError(f"{tipo.capitalize()} deve ter no máximo {limite_mb} MB")
                destino.write(bloco)
    except Exception:
        caminho.unlink(missing_ok=True)
        raise
    finally:
        await arquivo.close()

    if tamanho == 0:
        caminho.unlink(missing_ok=True)
        raise ValidacaoError(f"Arquivo de {tipo} vazio")
    return f"/api/uploads/produtos/{nome}"


async def atualizar_midia(
    db: AsyncSession, produto_id: int, arquivo: UploadFile, tipo: str
) -> Produto:
    produto = await obter(db, produto_id)
    campo = "imagem_url" if tipo == "imagem" else "video_url"
    url_anterior = getattr(produto, campo)
    nova_url = await _salvar_upload(arquivo, tipo)
    setattr(produto, campo, nova_url)
    try:
        produto_salvo = await repo.salvar(db, produto)
    except Exception:
        _excluir_arquivo(nova_url)
        raise
    _excluir_arquivo(url_anterior)
    return produto_salvo


async def remover_midia(db: AsyncSession, produto_id: int, tipo: str) -> Produto:
    produto = await obter(db, produto_id)
    campo = "imagem_url" if tipo == "imagem" else "video_url"
    url_anterior = getattr(produto, campo)
    setattr(produto, campo, None)
    produto_salvo = await repo.salvar(db, produto)
    _excluir_arquivo(url_anterior)
    return produto_salvo


async def calcular_preview_custo(db: AsyncSession, dados: PreviewCustoRequest) -> Decimal:
    materiais = await _validar_composicao(db, dados.composicao)
    total = sum(
        (
            item.quantidade_utilizada * material.custo_unitario_base
            for item, material in zip(dados.composicao, materiais, strict=True)
        ),
        start=Decimal("0"),
    )
    return total.quantize(_DUAS_CASAS, rounding=ROUND_HALF_UP)
