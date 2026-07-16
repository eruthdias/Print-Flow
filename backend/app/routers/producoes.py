from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.common import ListResponse
from app.schemas.producao import (
    AlertaEstoqueBaixoOut,
    ProducaoCreateRequest,
    ProducaoCriadaOut,
    ProducaoOut,
    ProducaoUpdateRequest,
)
from app.services import producao_service

router = APIRouter(prefix="/producoes", dependencies=[Depends(get_current_user)])


def _montar_alertas(alertas: list) -> list[AlertaEstoqueBaixoOut]:
    return [
        AlertaEstoqueBaixoOut(
            material_id=material.id,
            material_nome=material.nome,
            quantidade_atual=material.quantidade_atual,
            quantidade_minima=material.quantidade_minima,
        )
        for material in alertas
    ]


@router.get("", response_model=ListResponse[ProducaoOut])
async def listar_producoes(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    produto_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> ListResponse[ProducaoOut]:
    itens = await producao_service.listar(
        db, data_inicio=data_inicio, data_fim=data_fim, produto_id=produto_id
    )
    saida = [producao_service.montar_producao_out(item) for item in itens]
    return ListResponse(items=saida, total=len(saida))


@router.post("", response_model=ProducaoCriadaOut, status_code=201)
async def registrar_producao(dados: ProducaoCreateRequest, db: AsyncSession = Depends(get_db)):
    producao, alertas = await producao_service.registrar(db, dados)
    saida = producao_service.montar_producao_out(producao)
    return ProducaoCriadaOut(**saida.model_dump(), alertas_estoque_baixo=_montar_alertas(alertas))


@router.get("/{producao_id}", response_model=ProducaoOut)
async def obter_producao(producao_id: int, db: AsyncSession = Depends(get_db)):
    producao = await producao_service.obter(db, producao_id)
    return producao_service.montar_producao_out(producao)


@router.put("/{producao_id}", response_model=ProducaoCriadaOut)
async def atualizar_producao(
    producao_id: int, dados: ProducaoUpdateRequest, db: AsyncSession = Depends(get_db)
):
    producao, alertas = await producao_service.atualizar(db, producao_id, dados)
    saida = producao_service.montar_producao_out(producao)
    return ProducaoCriadaOut(**saida.model_dump(), alertas_estoque_baixo=_montar_alertas(alertas))


@router.delete("/{producao_id}", status_code=204)
async def estornar_producao(producao_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await producao_service.estornar(db, producao_id)
