from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.common import ListResponse
from app.schemas.desperdicio import DesperdicioCreateRequest, DesperdicioOut
from app.services import desperdicio_service

router = APIRouter(prefix="/desperdicios", dependencies=[Depends(get_current_user)])


@router.get("", response_model=ListResponse[DesperdicioOut])
async def listar_desperdicios(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    material_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> ListResponse[DesperdicioOut]:
    itens = await desperdicio_service.listar(
        db, data_inicio=data_inicio, data_fim=data_fim, material_id=material_id
    )
    saida = [desperdicio_service.montar_desperdicio_out(item) for item in itens]
    return ListResponse(items=saida, total=len(saida))


@router.post("", response_model=DesperdicioOut, status_code=201)
async def registrar_desperdicio(dados: DesperdicioCreateRequest, db: AsyncSession = Depends(get_db)):
    desperdicio = await desperdicio_service.registrar(db, dados)
    return desperdicio_service.montar_desperdicio_out(desperdicio)


@router.get("/{desperdicio_id}", response_model=DesperdicioOut)
async def obter_desperdicio(desperdicio_id: int, db: AsyncSession = Depends(get_db)):
    desperdicio = await desperdicio_service.obter(db, desperdicio_id)
    return desperdicio_service.montar_desperdicio_out(desperdicio)


@router.delete("/{desperdicio_id}", status_code=204)
async def estornar_desperdicio(desperdicio_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await desperdicio_service.estornar(db, desperdicio_id)
