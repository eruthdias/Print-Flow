import asyncio
from datetime import date, timedelta
from decimal import Decimal

from app.core.database import async_session_factory
from app.models.enums import UnidadeMedida
from app.repositories import material_repository as material_repo
from app.schemas.desperdicio import DesperdicioCreateRequest
from app.schemas.material import MaterialCreateRequest
from app.schemas.producao import ProducaoCreateRequest
from app.schemas.produto import ComposicaoItemRequest, ProdutoCreateRequest
from app.services import desperdicio_service, material_service, producao_service, produto_service


async def _ja_semeado(db) -> bool:
    return await material_repo.existe_nome_ativo(db, "Papel A4")


async def semear() -> None:
    async with async_session_factory() as db:
        if await _ja_semeado(db):
            print("Dados de demonstração já existem. Nada foi feito.")
            return

        papel_a4 = await material_service.criar(
            db,
            MaterialCreateRequest(
                nome="Papel A4",
                unidade_compra=UnidadeMedida.PACOTE,
                unidade_base=UnidadeMedida.FOLHA,
                fator_conversao=Decimal("100"),
                valor_compra=Decimal("25.00"),
                quantidade_atual=Decimal("2000"),
                quantidade_minima=Decimal("200"),
            ),
        )
        papel_foto = await material_service.criar(
            db,
            MaterialCreateRequest(
                nome="Papel Fotográfico",
                unidade_compra=UnidadeMedida.PACOTE,
                unidade_base=UnidadeMedida.FOLHA,
                fator_conversao=Decimal("50"),
                valor_compra=Decimal("40.00"),
                quantidade_atual=Decimal("500"),
                quantidade_minima=Decimal("600"),
            ),
        )
        tinta_preta = await material_service.criar(
            db,
            MaterialCreateRequest(
                nome="Tinta Preta",
                unidade_compra=UnidadeMedida.L,
                unidade_base=UnidadeMedida.ML,
                fator_conversao=Decimal("1000"),
                valor_compra=Decimal("60.00"),
                quantidade_atual=Decimal("2000"),
                quantidade_minima=Decimal("300"),
            ),
        )
        tinta_colorida = await material_service.criar(
            db,
            MaterialCreateRequest(
                nome="Tinta Colorida",
                unidade_compra=UnidadeMedida.L,
                unidade_base=UnidadeMedida.ML,
                fator_conversao=Decimal("1000"),
                valor_compra=Decimal("80.00"),
                quantidade_atual=Decimal("5000"),
                quantidade_minima=Decimal("500"),
            ),
        )
        caneca = await material_service.criar(
            db,
            MaterialCreateRequest(
                nome="Caneca Cerâmica",
                unidade_compra=UnidadeMedida.UN,
                unidade_base=UnidadeMedida.UN,
                fator_conversao=Decimal("1"),
                valor_compra=Decimal("8.00"),
                quantidade_atual=Decimal("200"),
                quantidade_minima=Decimal("20"),
            ),
        )
        lona = await material_service.criar(
            db,
            MaterialCreateRequest(
                nome="Lona Banner",
                unidade_compra=UnidadeMedida.ROLO,
                unidade_base=UnidadeMedida.M,
                fator_conversao=Decimal("50"),
                valor_compra=Decimal("250.00"),
                quantidade_atual=Decimal("100"),
                quantidade_minima=Decimal("10"),
            ),
        )

        panfleto = await produto_service.criar(
            db,
            ProdutoCreateRequest(
                nome="Panfleto A4 Colorido",
                preco_venda=Decimal("0.50"),
                composicao=[
                    ComposicaoItemRequest(material_id=papel_a4.id, quantidade_utilizada=Decimal("1")),
                    ComposicaoItemRequest(material_id=tinta_colorida.id, quantidade_utilizada=Decimal("2")),
                ],
            ),
        )
        foto = await produto_service.criar(
            db,
            ProdutoCreateRequest(
                nome="Foto 15x21",
                preco_venda=Decimal("3.00"),
                composicao=[
                    ComposicaoItemRequest(material_id=papel_foto.id, quantidade_utilizada=Decimal("1")),
                    ComposicaoItemRequest(material_id=tinta_colorida.id, quantidade_utilizada=Decimal("5")),
                ],
            ),
        )
        caneca_personalizada = await produto_service.criar(
            db,
            ProdutoCreateRequest(
                nome="Caneca Personalizada",
                preco_venda=Decimal("15.00"),
                composicao=[
                    ComposicaoItemRequest(material_id=caneca.id, quantidade_utilizada=Decimal("1")),
                    ComposicaoItemRequest(material_id=tinta_colorida.id, quantidade_utilizada=Decimal("5")),
                ],
            ),
        )
        banner = await produto_service.criar(
            db,
            ProdutoCreateRequest(
                nome="Banner 1x1m",
                preco_venda=Decimal("45.00"),
                composicao=[
                    ComposicaoItemRequest(material_id=lona.id, quantidade_utilizada=Decimal("1")),
                    ComposicaoItemRequest(material_id=tinta_preta.id, quantidade_utilizada=Decimal("10")),
                ],
            ),
        )

        hoje = date.today()
        producoes = [
            (panfleto, Decimal("500"), 25),
            (panfleto, Decimal("300"), 10),
            (foto, Decimal("50"), 15),
            (caneca_personalizada, Decimal("20"), 5),
            (banner, Decimal("3"), 2),
        ]
        for produto, quantidade, dias_atras in producoes:
            await producao_service.registrar(
                db,
                ProducaoCreateRequest(
                    produto_id=produto.id,
                    quantidade_produzida=quantidade,
                    data_producao=hoje - timedelta(days=dias_atras),
                ),
            )

        await desperdicio_service.registrar(
            db,
            DesperdicioCreateRequest(
                material_id=papel_a4.id,
                quantidade_perdida=Decimal("30"),
                motivo="Erro de impressão",
                data=hoje - timedelta(days=8),
            ),
        )
        await desperdicio_service.registrar(
            db,
            DesperdicioCreateRequest(
                material_id=tinta_colorida.id,
                quantidade_perdida=Decimal("100"),
                motivo="Vazamento no cartucho",
                data=hoje - timedelta(days=3),
            ),
        )

        print("Dados de demonstração criados com sucesso:")
        print("  6 materiais, 4 produtos, 5 produções, 2 desperdícios.")


def main() -> None:
    asyncio.run(semear())


if __name__ == "__main__":
    main()
