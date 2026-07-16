from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NaoEncontradoError, ValidacaoError
from app.models.material import Material
from app.models.desperdicio import Desperdicio
from app.models.producao import Producao
from app.models.producao_item import ProducaoItem
from app.models.produto import Produto
from app.repositories import producao_repository as repo
from app.repositories import produto_repository as produto_repo
from app.schemas.producao import (
    DesperdicioProducaoOut,
    ProducaoCreateRequest,
    ProducaoItemOut,
    ProducaoOut,
    ProducaoUpdateRequest,
)

_DUAS_CASAS = Decimal("0.01")


async def _carregar_produto_valido(db: AsyncSession, produto_id: int) -> Produto:
    produto = await produto_repo.obter_por_id(db, produto_id)
    if produto is None:
        raise NaoEncontradoError("Produto não encontrado")
    if not produto.ativo:
        raise ValidacaoError("Produto está inativo e não pode ser produzido")
    return produto


def montar_producao_out(producao: Producao) -> ProducaoOut:
    custo_desperdicios = sum(
        (item.custo_perda for item in producao.desperdicios), start=Decimal("0")
    )
    return ProducaoOut(
        id=producao.id,
        produto_id=producao.produto_id,
        produto_nome=producao.produto.nome,
        quantidade_produzida=producao.quantidade_produzida,
        data_producao=producao.data_producao,
        custo_materiais=producao.custo_total - custo_desperdicios,
        custo_desperdicios=custo_desperdicios,
        custo_total=producao.custo_total,
        valor_total=producao.valor_total,
        lucro_total=producao.lucro_total,
        itens=[
            ProducaoItemOut(
                material_id=item.material_id,
                material_nome=item.material.nome,
                unidade_base=item.material.unidade_base,
                quantidade_consumida=item.quantidade_consumida,
                custo_unitario_snapshot=item.custo_unitario_snapshot,
                custo_total_item=item.custo_total_item,
            )
            for item in producao.itens
        ],
        desperdicios=[
            DesperdicioProducaoOut(
                id=item.id,
                material_id=item.material_id,
                material_nome=item.material.nome,
                unidade_base=item.material.unidade_base,
                quantidade_perdida=item.quantidade_perdida,
                motivo=item.motivo,
                custo_perda=item.custo_perda,
            )
            for item in producao.desperdicios
        ],
    )


async def listar(
    db: AsyncSession,
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    produto_id: int | None = None,
) -> list[Producao]:
    return await repo.listar(
        db, data_inicio=data_inicio, data_fim=data_fim, produto_id=produto_id
    )


async def obter(db: AsyncSession, producao_id: int) -> Producao:
    producao = await repo.obter_por_id(db, producao_id)
    if producao is None:
        raise NaoEncontradoError("Produção não encontrada")
    return producao


def _calcular_efeitos(
    produto: Produto,
    dados: ProducaoCreateRequest,
    materiais_bloqueados: dict[int, Material],
) -> tuple[list[ProducaoItem], list[Desperdicio], Decimal, Decimal, Decimal]:
    materiais_composicao = {pm.material_id for pm in produto.composicao}
    desperdicios_por_material = {item.material_id: item for item in dados.desperdicios}
    invalidos = set(desperdicios_por_material) - materiais_composicao
    if invalidos:
        raise ValidacaoError(
            "Desperdício só pode usar materiais da composição do produto",
            materiais_invalidos=sorted(invalidos),
        )

    necessidades: list[tuple[Material, Decimal]] = []
    faltantes = []
    for pm in produto.composicao:
        material = materiais_bloqueados[pm.material_id]
        consumo_producao = pm.quantidade_utilizada * dados.quantidade_produzida
        perda = desperdicios_por_material.get(pm.material_id)
        quantidade_perdida = perda.quantidade_perdida if perda else Decimal("0")
        necessario = consumo_producao + quantidade_perdida
        necessidades.append((material, consumo_producao))
        if material.quantidade_atual < necessario:
            faltantes.append(
                {
                    "material": material.nome,
                    "necessario": str(necessario),
                    "disponivel": str(material.quantidade_atual),
                    "faltante": str(necessario - material.quantidade_atual),
                    "unidade": material.unidade_base.value,
                }
            )

    if faltantes:
        raise ValidacaoError("Estoque insuficiente", materiais=faltantes)

    itens = []
    custo_materiais = Decimal("0")
    for material, necessario in necessidades:
        custo_unitario_snapshot = material.custo_unitario_base
        custo_total_item = (necessario * custo_unitario_snapshot).quantize(
            _DUAS_CASAS, rounding=ROUND_HALF_UP
        )
        custo_materiais += custo_total_item
        material.quantidade_atual -= necessario
        itens.append(
            ProducaoItem(
                material_id=material.id,
                quantidade_consumida=necessario,
                custo_unitario_snapshot=custo_unitario_snapshot,
                custo_total_item=custo_total_item,
            )
        )

    desperdicios = []
    custo_desperdicios = Decimal("0")
    for material_id, perda in desperdicios_por_material.items():
        material = materiais_bloqueados[material_id]
        custo_perda = (perda.quantidade_perdida * material.custo_unitario_base).quantize(
            _DUAS_CASAS, rounding=ROUND_HALF_UP
        )
        material.quantidade_atual -= perda.quantidade_perdida
        custo_desperdicios += custo_perda
        desperdicios.append(
            Desperdicio(
                material_id=material_id,
                quantidade_perdida=perda.quantidade_perdida,
                motivo=perda.motivo.strip(),
                data=dados.data_producao or date.today(),
                custo_perda=custo_perda,
            )
        )

    custo_total = custo_materiais + custo_desperdicios
    valor_total = (produto.preco_venda * dados.quantidade_produzida).quantize(
        _DUAS_CASAS, rounding=ROUND_HALF_UP
    )
    lucro_total = valor_total - custo_total
    return itens, desperdicios, custo_total, valor_total, lucro_total


def _reverter_efeitos(producao: Producao, materiais_bloqueados: dict[int, Material]) -> None:
    for item in producao.itens:
        material = materiais_bloqueados[item.material_id]
        material.quantidade_atual += item.quantidade_consumida
    for desperdicio in producao.desperdicios:
        material = materiais_bloqueados[desperdicio.material_id]
        material.quantidade_atual += desperdicio.quantidade_perdida


async def registrar(db: AsyncSession, dados: ProducaoCreateRequest) -> tuple[Producao, list[Material]]:
    produto = await _carregar_produto_valido(db, dados.produto_id)

    material_ids = [pm.material_id for pm in produto.composicao]
    materiais_bloqueados = await repo.obter_materiais_para_atualizacao(db, material_ids)

    itens, desperdicios, custo_total, valor_total, lucro_total = _calcular_efeitos(
        produto, dados, materiais_bloqueados
    )

    alertas_estoque_baixo = [
        material
        for material in materiais_bloqueados.values()
        if material.quantidade_atual < material.quantidade_minima
    ]

    producao = Producao(
        produto_id=produto.id,
        quantidade_produzida=dados.quantidade_produzida,
        data_producao=dados.data_producao or date.today(),
        custo_total=custo_total,
        valor_total=valor_total,
        lucro_total=lucro_total,
        itens=itens,
        desperdicios=desperdicios,
    )

    producao_criada = await repo.salvar_novo(db, producao)
    return producao_criada, alertas_estoque_baixo


async def atualizar(
    db: AsyncSession, producao_id: int, dados: ProducaoUpdateRequest
) -> tuple[Producao, list[Material]]:
    producao_existente = await obter(db, producao_id)
    produto = await _carregar_produto_valido(db, dados.produto_id)

    ids_antigos = {item.material_id for item in producao_existente.itens} | {
        item.material_id for item in producao_existente.desperdicios
    }
    ids_novos = {pm.material_id for pm in produto.composicao}
    material_ids = list(ids_antigos | ids_novos)
    materiais_bloqueados = await repo.obter_materiais_para_atualizacao(db, material_ids)

    _reverter_efeitos(producao_existente, materiais_bloqueados)

    itens, desperdicios, custo_total, valor_total, lucro_total = _calcular_efeitos(
        produto, dados, materiais_bloqueados
    )

    alertas_estoque_baixo = [
        material
        for material in materiais_bloqueados.values()
        if material.quantidade_atual < material.quantidade_minima
    ]

    producao_existente.produto_id = produto.id
    producao_existente.quantidade_produzida = dados.quantidade_produzida
    producao_existente.data_producao = dados.data_producao or date.today()
    producao_existente.custo_total = custo_total
    producao_existente.valor_total = valor_total
    producao_existente.lucro_total = lucro_total
    producao_existente.itens = itens
    producao_existente.desperdicios = desperdicios

    producao_atualizada = await repo.salvar(db, producao_existente)
    return producao_atualizada, alertas_estoque_baixo


async def estornar(db: AsyncSession, producao_id: int) -> None:
    producao = await obter(db, producao_id)
    material_ids = list({
        *[item.material_id for item in producao.itens],
        *[item.material_id for item in producao.desperdicios],
    })
    materiais_bloqueados = await repo.obter_materiais_para_atualizacao(db, material_ids)
    _reverter_efeitos(producao, materiais_bloqueados)
    await repo.excluir(db, producao)
