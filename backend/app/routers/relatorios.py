from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.relatorio import (
    RelatorioCustosResponse,
    RelatorioDesperdiciosResponse,
    RelatorioEstoqueResponse,
    RelatorioLucroResponse,
    RelatorioProducaoResponse,
)
from app.services import relatorio_service

router = APIRouter(prefix="/relatorios", dependencies=[Depends(get_current_user)])


@router.get("/estoque", response_model=RelatorioEstoqueResponse)
async def relatorio_estoque(db: AsyncSession = Depends(get_db)):
    return await relatorio_service.relatorio_estoque(db)


@router.get("/producao", response_model=RelatorioProducaoResponse)
async def relatorio_producao(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await relatorio_service.relatorio_producao(db, data_inicio, data_fim)


@router.get("/custos", response_model=RelatorioCustosResponse)
async def relatorio_custos(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await relatorio_service.relatorio_custos(db, data_inicio, data_fim)


@router.get("/lucro", response_model=RelatorioLucroResponse)
async def relatorio_lucro(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await relatorio_service.relatorio_lucro(db, data_inicio, data_fim)


@router.get("/desperdicios", response_model=RelatorioDesperdiciosResponse)
async def relatorio_desperdicios(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await relatorio_service.relatorio_desperdicios(db, data_inicio, data_fim)
