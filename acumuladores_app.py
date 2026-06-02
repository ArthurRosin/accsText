import streamlit as st
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay
from datetime import date

# ── Calendário USA ──────────────────────────────────────────────────────────
us_calendar = USFederalHolidayCalendar()
us_business_day = CustomBusinessDay(calendar=us_calendar)

# ── Pilares por commodity ───────────────────────────────────────────────────
COMMODITIES = {
    "Soja": {
        "unidade": "c/bu",
        "pilares": {
            "SN6": date(2026, 6, 26),
            "SQ6": date(2026, 7, 24),
            "SU6": date(2026, 8, 21),
            "SX6": date(2026, 10, 23),
            "SF7": date(2026, 12, 24),
            "SH7": date(2027, 2, 19),
            "SK7": date(2027, 4, 23),
            "SN7": date(2027, 6, 25),
            "SX7": date(2027, 10, 22),
        },
    },
    "Milho CBOT": {
        "unidade": "c/bu",
        "pilares": {
            "CN6": date(2026, 6, 12),
            "CU6": date(2026, 8, 21),
            "CZ6": date(2026, 11, 20),
            "CH7": date(2027, 2, 19),
            "CK7": date(2027, 4, 23),
            "CN7": date(2027, 6, 25),
            "CU7": date(2027, 8, 27),
            "CZ7": date(2027, 11, 26),
        },
    },
    "Milho B3": {
        "unidade": "R$/sc",
        "pilares": {
            "CCMN6": date(2026, 7, 16),
            "CCMU6": date(2026, 9, 15),
            "CCMX6": date(2026, 11, 13),
            "CCMF7": date(2027, 1, 18),
            "CCMU7": date(2027, 9, 15),
        },
    },
    "Algodão": {
        "unidade": "c/lb",
        "pilares": {
            "CTN6": date(2026, 6, 12),
            "CTV6": date(2026, 9, 11),
            "CTZ6": date(2026, 11, 13),
            "CTH7": date(2027, 2, 5),
            "CTK7": date(2027, 4, 16),
            "CTN7": date(2027, 6, 11),
            "CTV7": date(2027, 9, 10),
            "CTZ7": date(2027, 12, 11),
            "CTH8": date(2028, 2, 11),
            "CTK8": date(2028, 4, 13),
        },
    },
}

# ── Mapeamento de tipo → flags ──────────────────────────────────────────────
# (dobro_diario, dobro_exp, tem_ko, tem_paraquedas, tem_suspensao, tem_acelerador)
TIPOS_ACC = {
    "ACC com dobro diário e KO":                                  (True,  False, True,  False, False, False),
    "ACC sem dobro e com KO":                                     (False, False, True,  False, False, False),
    "ACC com dobro na expiração e KO":                            (False, True,  True,  False, False, False),
    "ACC com dobro diário, KO e paraquedas":                      (True,  False, True,  True,  False, False),
    "ACC sem dobro, com KO e paraquedas":                         (False, False, True,  True,  False, False),
    "ACC com dobro na expiração, KO e paraquedas":                (False, True,  True,  True,  False, False),
    "ACC com dobro diário e Suspensão":                           (True,  False, False, False, True,  False),
    "ACC sem dobro e com Suspensão":                              (False, False, False, False, True,  False),
    "ACC com dobro na expiração e Suspensão":                     (False, True,  False, False, True,  False),
    "ACC com dobro diário, Acelerador e KO":                      (True,  False, True,  False, False, True),
    "ACC com dobro na expiração, Acelerador e KO":                (False, True,  True,  False, False, True),
    "ACC com dobro diário, Acelerador, KO e Paraquedas":          (True,  False, True,  True,  False, True),
    "ACC sem dobro, com Acelerador, KO e Paraquedas":             (False, False, True,  True,  False, True),
    "ACC com dobro na expiração, Acelerador, KO e Paraquedas":    (False, True,  True,  True,  False, True),
}


def contar_pregoes(inicio: date, fim: date) -> int:
    return len(pd.date_range(start=inicio, end=fim, freq=us_business_day))


def _subtitulo(opcao: str) -> str:
    return opcao.replace("ACC ", "").upper()


def gerar_texto(
    opcao: str,
    tipo_operacao: str,
    commodity: str,
    pilar: str,
    vencimento: date,
    pregoes: int,
    preco_base: float,
    nivel_melhorado: float,
    unidade: str,
    nivel_ko: float | None,
    nivel_paraquedas: float | None,
    nivel_suspensao: float | None,
    nivel_acelerador: float | None,
) -> str:

    dobro_diario, dobro_exp, tem_ko, tem_par, tem_sus, tem_acel = TIPOS_ACC[opcao]

    op       = tipo_operacao
    op_lower = op.lower()
    op_flex  = "comprados" if op == "Compra" else "vendidos"
    posicao  = "abaixo"    if op == "Compra" else "acima"
    u        = unidade

    preco_acel = (nivel_acelerador + nivel_melhorado) if (tem_acel and nivel_acelerador is not None) else None

    # ── Cabeçalho
    primeira_linha = f"**{commodity} — {pilar} @ {preco_base} {u} — Exp. {vencimento} — {pregoes} Pregões**"

    linhas = [
        primeira_linha,
        f"Acumulador de {op} {_subtitulo(opcao)} — Custo Zero",
        f"Nível de {op} Melhorada @ {nivel_melhorado} {u}",
    ]

    if tem_acel:
        linhas.append(f"Nível do Acelerador @ {nivel_acelerador} {u} ({op} @ {preco_acel} {u})")
    if tem_ko:
        linhas.append(f"Nível de Knock Out @ {nivel_ko} {u}")
    if tem_par:
        linhas.append(f"Nível de Paraquedas @ {nivel_paraquedas} {u}")
    if tem_sus:
        linhas.append(f"Nível de Suspensão @ {nivel_suspensao} {u}")

    linhas.append("")

    # ── Regras de acumulação diária
    preco_normal = preco_acel if tem_acel else nivel_melhorado

    if tem_ko or tem_sus:
        limite_superior = nivel_ko if tem_ko else nivel_suspensao
        linhas.append(
            f"- Todo dia em que o mercado fechar entre {nivel_melhorado} e {limite_superior}, "
            f"{op_lower} 1x o volume diário a {preco_normal} {u}."
        )

    if dobro_diario:
        linhas.append(
            f"- Todo dia em que o mercado fechar a {nivel_melhorado} ou {posicao}, "
            f"{op_lower} 2x o volume diário a {nivel_melhorado} {u}."
        )
    elif not tem_ko and not tem_sus:
        linhas.append(
            f"- Todo dia em que o mercado fechar {op_flex} de {nivel_melhorado}, "
            f"{op_lower} 1x o volume diário a {preco_normal} {u}."
        )

    # ── Regras de KO
    if tem_ko:
        lotes_restantes = (
            f", e o restante dos lotes são {op_flex} a {nivel_paraquedas} {u}"
            if tem_par else ""
        )
        linhas.append(
            f"- Se, em qualquer momento, o mercado tocar {nivel_ko} {u}, o acumulador desmonta, "
            f"os lotes {op_flex} a {nivel_melhorado}"
            + (f" e {preco_acel}" if tem_acel else "")
            + f" {u} permanecem{lotes_restantes}."
        )

    # ── Regras de Suspensão
    if tem_sus:
        linhas.append(
            f"- Se, em qualquer momento, o mercado fechar a {nivel_suspensao} ou {posicao}, "
            f"nada é acumulado naquele pregão, mas a estrutura não desmonta."
        )

    # ── Dobro na expiração
    if dobro_exp:
        ref = nivel_ko if tem_ko else nivel_melhorado
        linhas.append(
            f"- Caso o mercado não negociar a {ref} {u} em nenhum momento ao longo da sua vida útil, "
            f"e no dia do vencimento fechar acima de {nivel_melhorado} {u}, "
            f"vende 1x o volume total adicional a {nivel_melhorado} {u}."
        )

    return "\n".join(linhas)


# ── UI
st.title("Gerador de Acumuladores")

# 1. Commodity
commodity = st.selectbox("Commodity:", list(COMMODITIES.keys()))
info_commodity = COMMODITIES[commodity]
unidade = info_commodity["unidade"]
pilares = info_commodity["pilares"]

st.subheader("Escolha o tipo de acumulador")
opcao = st.selectbox("Tipo:", list(TIPOS_ACC.keys()))
st.divider()

tipo_operacao = st.radio("Compra ou Venda?", ["Compra", "Venda"])

pilar = st.selectbox("Pilar:", list(pilares.keys()))
vencimento = pilares[pilar]
hoje = date.today()
pregoes = contar_pregoes(hoje, vencimento)
st.write(f"Vencimento: {vencimento}")
st.write(f"Número de pregões: {pregoes}")

preco_base      = st.number_input(f"Referência ({unidade}):", min_value=0.0)
nivel_melhorado = st.number_input(f"Nível melhorado ({unidade}):", min_value=0.0)

# ── Inputs condicionais
dobro_diario, dobro_exp, tem_ko, tem_par, tem_sus, tem_acel = TIPOS_ACC[opcao]

nivel_ko         = st.number_input(f"Nível de Knock Out ({unidade}):",  value=0.0) if tem_ko  else None
nivel_paraquedas = st.number_input(f"Nível de Paraquedas ({unidade}):", value=0.0) if tem_par else None
nivel_suspensao  = st.number_input(f"Nível de Suspensão ({unidade}):",  value=0.0) if tem_sus else None
nivel_acelerador = st.number_input(f"Nível do Acelerador ({unidade}):", value=0.0) if tem_acel else None

# ── Geração
if st.button("Gerar Texto"):
    texto = gerar_texto(
        opcao=opcao,
        tipo_operacao=tipo_operacao,
        commodity=commodity,
        pilar=pilar,
        vencimento=vencimento,
        pregoes=pregoes,
        preco_base=preco_base,
        nivel_melhorado=nivel_melhorado,
        unidade=unidade,
        nivel_ko=nivel_ko,
        nivel_paraquedas=nivel_paraquedas,
        nivel_suspensao=nivel_suspensao,
        nivel_acelerador=nivel_acelerador,
    )
    st.markdown(texto)
    st.divider()
    st.text_area("Copiar texto:", texto, height=300)