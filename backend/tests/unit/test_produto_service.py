from decimal import Decimal

from app.models.material import Material
from app.models.produto import Produto
from app.models.produto_material import ProdutoMaterial
from app.models.enums import UnidadeMedida
from app.services.produto_service import calcular_custo_producao, montar_produto_out


_proximo_id = iter(range(1, 1000))


def _material(nome: str, custo_unitario_base: str, unidade_base: UnidadeMedida = UnidadeMedida.UN) -> Material:
    material = Material(
        nome=nome,
        unidade_compra=unidade_base,
        unidade_base=unidade_base,
        fator_conversao=Decimal("1"),
        valor_compra=Decimal(custo_unitario_base),
        custo_unitario_base=Decimal(custo_unitario_base),
        quantidade_atual=Decimal("1000"),
        quantidade_minima=Decimal("0"),
    )
    material.id = next(_proximo_id)
    return material


def _produto_com_composicao(preco_venda: str, itens: list[tuple[Material, str]]) -> Produto:
    produto = Produto(nome="Produto Teste", preco_venda=Decimal(preco_venda))
    produto.id = next(_proximo_id)
    produto.ativo = True
    produto.composicao = [
        ProdutoMaterial(material=material, material_id=material.id, quantidade_utilizada=Decimal(quantidade))
        for material, quantidade in itens
    ]
    return produto


def test_calcula_custo_producao_com_multiplos_materiais():
    caneca = _material("Caneca", "5.00")
    tinta = _material("Tinta", "0.10", UnidadeMedida.ML)
    papel = _material("Papel", "0.25", UnidadeMedida.FOLHA)

    produto = _produto_com_composicao(
        "15.00", [(caneca, "1"), (tinta, "5"), (papel, "1")]
    )

    custo = calcular_custo_producao(produto)
    assert custo == Decimal("5.75")


def test_lucro_estimado_positivo():
    material = _material("Caneca", "5.00")
    produto = _produto_com_composicao("15.00", [(material, "1")])

    saida = montar_produto_out(produto)
    assert saida.custo_producao == Decimal("5.00")
    assert saida.lucro_estimado == Decimal("10.00")


def test_lucro_estimado_pode_ser_negativo():
    material = _material("Caneca", "20.00")
    produto = _produto_com_composicao("15.00", [(material, "1")])

    saida = montar_produto_out(produto)
    assert saida.lucro_estimado == Decimal("-5.00")
