from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflitoError, NaoEncontradoError, ValidacaoError
from app.models.enums import UnidadeMedida
from app.models.material import Material
from app.repositories import material_repository as repo
from app.schemas.material import (
    AjusteEstoqueRequest,
    MaterialCreateRequest,
    MaterialResumoOut,
    MaterialUpdateRequest,
    OperacaoEstoque,
)

CONVERSOES_VALIDAS: dict[UnidadeMedida, set[UnidadeMedida]] = {
    UnidadeMedida.PACOTE: {UnidadeMedida.UN, UnidadeMedida.FOLHA},
    UnidadeMedida.CX: {UnidadeMedida.UN, UnidadeMedida.FOLHA},
    UnidadeMedida.ROLO: {UnidadeMedida.M, UnidadeMedida.CM, UnidadeMedida.M2, UnidadeMedida.CM2},
    UnidadeMedida.KG: {UnidadeMedida.G},
    UnidadeMedida.L: {UnidadeMedida.ML},
    UnidadeMedida.M: {UnidadeMedida.CM},
    UnidadeMedida.M2: {UnidadeMedida.CM2},
}


def _validar_e_normalizar_unidades(
    unidade_compra: UnidadeMedida, unidade_base: UnidadeMedida, fator_conversao: Decimal
) -> Decimal:
    if unidade_compra == unidade_base:
        # Quantidade de unidades base recebidas na compra/lote.
        # Ex.: 500 folhas por R$ 35,00 deve manter o fator 500.
        return fator_conversao
    combinacoes_validas = CONVERSOES_VALIDAS.get(unidade_compra, set())
    if unidade_base not in combinacoes_validas:
        raise ValidacaoError(
            f"Combinação de unidades inválida: "
            f"{unidade_compra.value} não pode ser convertido para {unidade_base.value}"
        )
    return fator_conversao


def _calcular_custo_unitario_base(valor_compra: Decimal, fator_conversao: Decimal) -> Decimal:
    return (valor_compra / fator_conversao).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


async def listar(
    db: AsyncSession,
    *,
    ativo: bool | None = None,
    estoque_baixo: bool | None = None,
    busca: str | None = None,
) -> list[Material]:
    return await repo.listar(db, ativo=ativo, estoque_baixo=estoque_baixo, busca=busca)


async def obter(db: AsyncSession, material_id: int) -> Material:
    material = await repo.obter_por_id(db, material_id)
    if material is None:
        raise NaoEncontradoError("Material não encontrado")
    return material


async def obter_resumo(db: AsyncSession) -> MaterialResumoOut:
    (
        materiais_cadastrados,
        materiais_em_estoque,
        materiais_sem_estoque,
        produtos_cadastrados,
        desperdicios_registrados,
        precisando_compra,
    ) = await repo.obter_resumo(db)
    return MaterialResumoOut(
        materiais_cadastrados=materiais_cadastrados,
        materiais_em_estoque=materiais_em_estoque,
        materiais_sem_estoque=materiais_sem_estoque,
        produtos_cadastrados=produtos_cadastrados,
        desperdicios_registrados=desperdicios_registrados,
        precisando_compra=precisando_compra,
    )


async def criar(db: AsyncSession, dados: MaterialCreateRequest) -> Material:
    if await repo.existe_nome_ativo(db, dados.nome):
        raise ConflitoError("Já existe um material ativo com este nome")
    fator = _validar_e_normalizar_unidades(dados.unidade_compra, dados.unidade_base, dados.fator_conversao)
    material = Material(
        nome=dados.nome,
        unidade_compra=dados.unidade_compra,
        unidade_base=dados.unidade_base,
        fator_conversao=fator,
        valor_compra=dados.valor_compra,
        custo_unitario_base=_calcular_custo_unitario_base(dados.valor_compra, fator),
        quantidade_atual=dados.quantidade_atual,
        quantidade_minima=dados.quantidade_minima,
    )
    return await repo.criar(db, material)


async def atualizar(db: AsyncSession, material_id: int, dados: MaterialUpdateRequest) -> Material:
    material = await obter(db, material_id)
    if dados.nome != material.nome and await repo.existe_nome_ativo(db, dados.nome, ignorar_id=material_id):
        raise ConflitoError("Já existe um material ativo com este nome")
    fator = _validar_e_normalizar_unidades(dados.unidade_compra, dados.unidade_base, dados.fator_conversao)
    material.nome = dados.nome
    material.unidade_compra = dados.unidade_compra
    material.unidade_base = dados.unidade_base
    material.fator_conversao = fator
    material.valor_compra = dados.valor_compra
    material.custo_unitario_base = _calcular_custo_unitario_base(dados.valor_compra, fator)
    material.quantidade_minima = dados.quantidade_minima
    return await repo.salvar(db, material)


async def alterar_ativo(db: AsyncSession, material_id: int, ativo: bool) -> Material:
    material = await obter(db, material_id)
    material.ativo = ativo
    return await repo.salvar(db, material)


async def excluir(db: AsyncSession, material_id: int) -> None:
    material = await obter(db, material_id)
    try:
        await repo.excluir(db, material)
    except IntegrityError as exc:
        await db.rollback()
        raise ConflitoError(
            "Material possui vínculos e não pode ser excluído. Desative-o em vez de excluir."
        ) from exc


async def ajustar_estoque(db: AsyncSession, material_id: int, dados: AjusteEstoqueRequest) -> Material:
    material = await obter(db, material_id)
    if dados.operacao == OperacaoEstoque.ENTRADA:
        material.quantidade_atual += dados.quantidade
    else:
        if dados.quantidade > material.quantidade_atual:
            raise ValidacaoError(
                "Quantidade de saída maior que o estoque disponível",
                disponivel=str(material.quantidade_atual),
            )
        material.quantidade_atual -= dados.quantidade
    return await repo.salvar(db, material)
