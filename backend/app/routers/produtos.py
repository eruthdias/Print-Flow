from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.common import AtivoUpdateRequest, ListResponse
from app.schemas.produto import (
    PreviewCustoRequest,
    PreviewCustoResponse,
    ProdutoCreateRequest,
    ProdutoOut,
    ProdutoUpdateRequest,
)
from app.services import produto_service

router = APIRouter(prefix="/produtos", dependencies=[Depends(get_current_user)])


@router.get("", response_model=ListResponse[ProdutoOut])
async def listar_produtos(
    ativo: bool | None = None,
    busca: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> ListResponse[ProdutoOut]:
    itens = await produto_service.listar(db, ativo=ativo, busca=busca)
    saida = [produto_service.montar_produto_out(item) for item in itens]
    return ListResponse(items=saida, total=len(saida))


@router.post("/preview-custo", response_model=PreviewCustoResponse)
async def preview_custo(dados: PreviewCustoRequest, db: AsyncSession = Depends(get_db)):
    custo = await produto_service.calcular_preview_custo(db, dados)
    return PreviewCustoResponse(custo_producao=custo)


@router.post("", response_model=ProdutoOut, status_code=201)
async def criar_produto(dados: ProdutoCreateRequest, db: AsyncSession = Depends(get_db)):
    produto = await produto_service.criar(db, dados)
    return produto_service.montar_produto_out(produto)


@router.get("/{produto_id}", response_model=ProdutoOut)
async def obter_produto(produto_id: int, db: AsyncSession = Depends(get_db)):
    produto = await produto_service.obter(db, produto_id)
    return produto_service.montar_produto_out(produto)


@router.put("/{produto_id}", response_model=ProdutoOut)
async def atualizar_produto(
    produto_id: int, dados: ProdutoUpdateRequest, db: AsyncSession = Depends(get_db)
):
    produto = await produto_service.atualizar(db, produto_id, dados)
    return produto_service.montar_produto_out(produto)


@router.delete("/{produto_id}", status_code=204)
async def excluir_produto(produto_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await produto_service.excluir(db, produto_id)


@router.patch("/{produto_id}/ativo", response_model=ProdutoOut)
async def alterar_ativo_produto(
    produto_id: int, dados: AtivoUpdateRequest, db: AsyncSession = Depends(get_db)
):
    produto = await produto_service.alterar_ativo(db, produto_id, dados.ativo)
    return produto_service.montar_produto_out(produto)


@router.post("/{produto_id}/imagem", response_model=ProdutoOut)
async def carregar_imagem_produto(
    produto_id: int,
    arquivo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    produto = await produto_service.atualizar_midia(db, produto_id, arquivo, "imagem")
    return produto_service.montar_produto_out(produto)


@router.delete("/{produto_id}/imagem", response_model=ProdutoOut)
async def remover_imagem_produto(produto_id: int, db: AsyncSession = Depends(get_db)):
    produto = await produto_service.remover_midia(db, produto_id, "imagem")
    return produto_service.montar_produto_out(produto)


@router.post("/{produto_id}/video", response_model=ProdutoOut)
async def carregar_video_produto(
    produto_id: int,
    arquivo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    produto = await produto_service.atualizar_midia(db, produto_id, arquivo, "video")
    return produto_service.montar_produto_out(produto)


@router.delete("/{produto_id}/video", response_model=ProdutoOut)
async def remover_video_produto(produto_id: int, db: AsyncSession = Depends(get_db)):
    produto = await produto_service.remover_midia(db, produto_id, "video")
    return produto_service.montar_produto_out(produto)
