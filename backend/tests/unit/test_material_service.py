from decimal import Decimal

import pytest

from app.core.exceptions import ValidacaoError
from app.models.enums import UnidadeMedida
from app.services.material_service import _calcular_custo_unitario_base, _validar_e_normalizar_unidades


def test_calcula_custo_unitario_base_pacote_100_folhas_25_reais():
    custo = _calcular_custo_unitario_base(Decimal("25.00"), Decimal("100"))
    assert custo == Decimal("0.2500")


def test_calcula_custo_unitario_base_com_arredondamento():
    custo = _calcular_custo_unitario_base(Decimal("10.00"), Decimal("3"))
    assert custo == Decimal("3.3333")


def test_respeita_quantidade_do_lote_quando_unidades_iguais():
    fator = _validar_e_normalizar_unidades(UnidadeMedida.FOLHA, UnidadeMedida.FOLHA, Decimal("500"))
    assert fator == Decimal("500")


def test_respeita_fator_informado_mesmo_quando_unidades_sao_iguais():
    fator = _validar_e_normalizar_unidades(UnidadeMedida.KG, UnidadeMedida.KG, Decimal("7"))
    assert fator == Decimal("7")


def test_calcula_500_folhas_por_35_reais():
    fator = _validar_e_normalizar_unidades(
        UnidadeMedida.FOLHA, UnidadeMedida.FOLHA, Decimal("500")
    )
    assert _calcular_custo_unitario_base(Decimal("35"), fator) == Decimal("0.0700")


def test_rejeita_combinacao_de_unidades_invalida():
    with pytest.raises(ValidacaoError):
        _validar_e_normalizar_unidades(UnidadeMedida.KG, UnidadeMedida.FOLHA, Decimal("10"))


@pytest.mark.parametrize(
    ("compra", "base"),
    [
        (UnidadeMedida.PACOTE, UnidadeMedida.UN),
        (UnidadeMedida.PACOTE, UnidadeMedida.FOLHA),
        (UnidadeMedida.CX, UnidadeMedida.UN),
        (UnidadeMedida.CX, UnidadeMedida.FOLHA),
        (UnidadeMedida.ROLO, UnidadeMedida.M),
        (UnidadeMedida.ROLO, UnidadeMedida.CM),
        (UnidadeMedida.ROLO, UnidadeMedida.M2),
        (UnidadeMedida.ROLO, UnidadeMedida.CM2),
        (UnidadeMedida.KG, UnidadeMedida.G),
        (UnidadeMedida.L, UnidadeMedida.ML),
        (UnidadeMedida.M, UnidadeMedida.CM),
        (UnidadeMedida.M2, UnidadeMedida.CM2),
    ],
)
def test_aceita_todas_as_combinacoes_documentadas(compra, base):
    fator = _validar_e_normalizar_unidades(compra, base, Decimal("10"))
    assert fator == Decimal("10")
