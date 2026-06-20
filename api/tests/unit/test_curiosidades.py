"""Unidade — 'Você Sabia?' (curiosidades ancoradas). Regras puras, sem I/O (Invariante 3):
só afirma valores recuperados, cita a fonte, sem causalidade; sem dado → sem curiosidade.
"""

from app.indicadores.curiosidades import ValorIndicador, montar_curiosidades


def _v(valor: float, fonte: str = "SNIS/MDR") -> ValorIndicador:
    return ValorIndicador(valor=valor, fonte=fonte, periodo="2024-12")


def test_gap_agua_esgoto_dispara_quando_diferenca_grande() -> None:
    cs = montar_curiosidades(
        {
            "saneamento.agua.atendimento_pct": _v(95.0),
            "saneamento.esgoto.coleta_pct": _v(40.0),
        }
    )
    assert len(cs) == 1
    c = cs[0]
    assert "95%" in c.texto and "40%" in c.texto and "55 pontos" in c.texto
    assert c.produto == "esgoto-invisivel"
    assert c.fonte == "SNIS/MDR"  # proveniência da fonte usada


def test_gap_agua_esgoto_nao_dispara_quando_diferenca_pequena() -> None:
    cs = montar_curiosidades(
        {
            "saneamento.agua.atendimento_pct": _v(90.0),
            "saneamento.esgoto.coleta_pct": _v(85.0),  # gap 5 < 15
        }
    )
    assert cs == []


def test_gap_agua_esgoto_nao_dispara_sem_um_dos_indicadores() -> None:
    # Sem dado → sem curiosidade (não preenche lacuna com suposição).
    assert montar_curiosidades({"saneamento.agua.atendimento_pct": _v(95.0)}) == []
    assert montar_curiosidades({}) == []


def test_seca_dispara_em_alerta() -> None:
    cs = montar_curiosidades({"saneamento.agua.seca_indice": _v(4.0, fonte="ANA")})
    assert len(cs) == 1
    assert "4.0" in cs[0].texto and "0–5" in cs[0].texto
    assert cs[0].produto == "rio-em-risco"


def test_seca_nao_dispara_abaixo_do_limiar() -> None:
    assert montar_curiosidades({"saneamento.agua.seca_indice": _v(2.0)}) == []


def test_varias_regras_acumulam_na_ordem_do_registro() -> None:
    cs = montar_curiosidades(
        {
            "saneamento.agua.atendimento_pct": _v(95.0),
            "saneamento.esgoto.coleta_pct": _v(40.0),
            "saneamento.agua.seca_indice": _v(4.0),
        }
    )
    assert [c.produto for c in cs] == ["esgoto-invisivel", "rio-em-risco"]
