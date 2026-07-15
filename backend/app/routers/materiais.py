from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.common import AtivoUpdateRequest, ListResponse
from app.schemas.material import (
    AjusteEstoqueRequest,
    MaterialCreateRequest,
    MaterialOut,
    MaterialResumoOut,
    MaterialUpdateRequest,
)
from app.services import material_service

router = APIRouter(prefix="/materiais", dependencies=[Depends(get_current_user)])


@router.get("", response_model=ListResponse[MaterialOut])
async def listar_materiais(
    ativo: bool | None = None,
    estoque_baixo: bool | None = None,
    busca: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> ListResponse[MaterialOut]:
    itens = await material_service.listar(
        db, ativo=ativo, estoque_baixo=estoque_baixo, busca=busca
    )
    return ListResponse(items=itens, total=len(itens))


@router.get("/resumo", response_model=MaterialResumoOut)
async def obter_resumo_materiais(
    db: AsyncSession = Depends(get_db),
) -> MaterialResumoOut:
    return await material_service.obter_resumo(db)


@router.post("", response_model=MaterialOut, status_code=201)
async def criar_material(dados: MaterialCreateRequest, db: AsyncSession = Depends(get_db)):
    return await material_service.criar(db, dados)


@router.get("/{material_id}", response_model=MaterialOut)
async def obter_material(material_id: int, db: AsyncSession = Depends(get_db)):
    return await material_service.obter(db, material_id)


@router.put("/{material_id}", response_model=MaterialOut)
async def atualizar_material(
    material_id: int, dados: MaterialUpdateRequest, db: AsyncSession = Depends(get_db)
):
    return await material_service.atualizar(db, material_id, dados)


@router.delete("/{material_id}", status_code=204)
async def excluir_material(material_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await material_service.excluir(db, material_id)


@router.patch("/{material_id}/ativo", response_model=MaterialOut)
async def alterar_ativo_material(
    material_id: int, dados: AtivoUpdateRequest, db: AsyncSession = Depends(get_db)
):
    return await material_service.alterar_ativo(db, material_id, dados.ativo)


@router.post("/{material_id}/ajuste-estoque", response_model=MaterialOut)
async def ajustar_estoque_material(
    material_id: int, dados: AjusteEstoqueRequest, db: AsyncSession = Depends(get_db)
):
    return await material_service.ajustar_estoque(db, material_id, dados)
