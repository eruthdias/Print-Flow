from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NaoEncontradoError, ValidacaoError
from app.models.desperdicio import Desperdicio
from app.models.material import Material
from app.repositories import desperdicio_repository as repo
from app.schemas.desperdicio import DesperdicioCreateRequest, DesperdicioOut

_DUAS_CASAS = Decimal("0.01")


def montar_desperdicio_out(desperdicio: Desperdicio) -> DesperdicioOut:
    return DesperdicioOut(
        id=desperdicio.id,
        material_id=desperdicio.material_id,
        material_nome=desperdicio.material.nome,
        unidade_base=desperdicio.material.unidade_base,
        quantidade_perdida=desperdicio.quantidade_perdida,
        motivo=desperdicio.motivo,
        data=desperdicio.data,
        custo_perda=desperdicio.custo_perda,
    )


async def listar(
    db: AsyncSession,
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    material_id: int | None = None,
) -> list[Desperdicio]:
    return await repo.listar(
        db, data_inicio=data_inicio, data_fim=data_fim, material_id=material_id
    )


async def obter(db: AsyncSession, desperdicio_id: int) -> Desperdicio:
    desperdicio = await repo.obter_por_id(db, desperdicio_id)
    if desperdicio is None:
        raise NaoEncontradoError("Desperdício não encontrado")
    return desperdicio


async def _carregar_material_valido(db: AsyncSession, material_id: int) -> Material:
    material = await repo.obter_material_para_atualizacao(db, material_id)
    if material is None:
        raise NaoEncontradoError("Material não encontrado")
    return material


async def registrar(db: AsyncSession, dados: DesperdicioCreateRequest) -> Desperdicio:
    material = await _carregar_material_valido(db, dados.material_id)

    if dados.quantidade_perdida > material.quantidade_atual:
        raise ValidacaoError(
            "Quantidade perdida maior que o estoque disponível",
            disponivel=str(material.quantidade_atual),
        )

    custo_perda = (dados.quantidade_perdida * material.custo_unitario_base).quantize(
        _DUAS_CASAS, rounding=ROUND_HALF_UP
    )
    material.quantidade_atual -= dados.quantidade_perdida

    desperdicio = Desperdicio(
        material_id=material.id,
        quantidade_perdida=dados.quantidade_perdida,
        motivo=dados.motivo,
        data=dados.data or date.today(),
        custo_perda=custo_perda,
    )
    return await repo.salvar_novo(db, desperdicio)


async def estornar(db: AsyncSession, desperdicio_id: int) -> None:
    desperdicio = await obter(db, desperdicio_id)
    material = await repo.obter_material_para_atualizacao(db, desperdicio.material_id)
    material.quantidade_atual += desperdicio.quantidade_perdida
    await repo.excluir(db, desperdicio)
