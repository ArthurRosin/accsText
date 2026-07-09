import streamlit as st
import pandas as pd
from pandas.tseries.offsets import CustomBusinessDay
from datetime import date

# ── Calendários de feriados ─────────────────────────────────────────────────
# Feriados Brasil e EUA (CBOT e B3 fechadas)
FERIADOS_COMUNS = [
    date(2026, 2, 16),   # Carnaval / Presidents Day
    date(2026, 4, 3),    # Sexta-Feira Santa
    date(2026, 9, 7),    # Labor Day / Independência do Brasil
    date(2026, 12, 25),  # Natal
    date(2027, 1, 1),    # Ano Novo
    date(2027, 3, 26),   # Sexta-Feira Santa 2027
]

# Feriados EUA (apenas CBOT fechada)
FERIADOS_CBOT = FERIADOS_COMUNS + [
    # 2026
    date(2026, 5, 25),   # Memorial Day
    date(2026, 6, 19),   # Juneteenth Day
    date(2026, 7, 3),    # Independence Day (observado)
    date(2026, 11, 26),  # Thanksgiving
    # 2027
    date(2027, 1, 18),   # MLK Day
    date(2027, 2, 15),   # Presidents Day
    date(2027, 5, 31),   # Memorial Day
    date(2027, 6, 18),   # Juneteenth (observado, 19/6 = sáb)
    date(2027, 7, 5),    # Independence Day (observado, 4/7 = dom)
    date(2027, 9, 6),    # Labor Day
    date(2027, 11, 25),  # Thanksgiving
    date(2027, 12, 24),  # Natal (observado, 25/12 = sáb)
    # 2028 (até os pilares mais longos)
    date(2028, 1, 17),   # MLK Day
    date(2028, 2, 21),   # Presidents Day
    date(2028, 4, 14),   # Sexta-Feira Santa 2028
]

# Feriados Brasil (apenas B3 fechada)
# Obs.: 18/02/2026 (Quarta de Cinzas) a B3 abre ao meio-dia — contado como pregão.
FERIADOS_B3 = FERIADOS_COMUNS + [
    # 2026
    date(2026, 2, 17),   # Carnaval
    date(2026, 4, 21),   # Tiradentes
    date(2026, 5, 1),    # Dia do Trabalhador
    date(2026, 6, 4),    # Corpus Christi
    date(2026, 10, 12),  # N. Sra. Aparecida / Dia das Crianças
    date(2026, 11, 2),   # Finados
    date(2026, 11, 20),  # Consciência Negra
    date(2026, 12, 24),  # Véspera de Natal — B3 não abre
    date(2026, 12, 31),  # Véspera de Ano Novo — B3 não abre
    # 2027
    date(2027, 2, 8),    # Carnaval (seg)
    date(2027, 2, 9),    # Carnaval (ter)
    date(2027, 4, 21),   # Tiradentes
    date(2027, 5, 27),   # Corpus Christi
    date(2027, 9, 7),    # Independência
    date(2027, 10, 12),  # N. Sra. Aparecida
    date(2027, 11, 2),   # Finados
    date(2027, 11, 15),  # Proclamação da República (cai em segunda em 2027)
    date(2027, 12, 24),  # Véspera de Natal — B3 não abre
    date(2027, 12, 31),  # Véspera de Ano Novo — B3 não abre
]

bday_cbot = CustomBusinessDay(holidays=FERIADOS_CBOT)
bday_b3   = CustomBusinessDay(holidays=FERIADOS_B3)

# ── Pilares por commodity ───────────────────────────────────────────────────
COMMODITIES = {
    "Soja": {
        "unidade": "c/bu",
        "calendario": bday_cbot,
        "pilares": {
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
        "calendario": bday_cbot,
        "pilares": {
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
        "calendario": bday_b3,
        "pilares": {
            "CCMU6": date(2026, 9, 14),
            "CCMX6": date(2026, 11, 16),
            "CCMF7": date(2027, 1, 15),
            "CCMU7": date(2027, 9, 14),
        },
    },
    "Algodão": {
        "unidade": "c/lb",
        "calendario": bday_cbot,
        "pilares": {
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
    "Óleo de soja": {
        "unidade": "c/lb",
        "calendario": bday_cbot,
        "pilares": {
            "BOQ6": date(2026, 7, 24),
            "BOU6": date(2026, 8, 21),
            "BOV6": date(2026, 9, 25),
            "BOZ6": date(2026, 11, 20),
            "BOH7": date(2027, 2, 19),
            "BOK7": date(2027, 2, 19),
            "BON7": date(2027, 6, 25),
            "BOQ7": date(2027, 7, 23),
            "BOU7": date(2027, 8, 27),
        },
    },
    "Farelo de soja": {
        "unidade": "US$/sTON",
        "calendario": bday_cbot,
        "pilares": {
            "SMQ6": date(2026, 7, 24),
            "SMU6": date(2026, 8, 21),
            "SMV6": date(2026, 9, 25),
            "SMZ6": date(2027, 11, 20),
            "SMF7": date(2026, 12, 24),
            "SMH7": date(2027, 2, 19),
            "SMK7": date(2027, 4, 23),
        },
    },
}

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
    "ACC com dobro na expiração, Acelerador, KO e Paraquedas":    (False, True,  True,  True,  False, True),
}


def contar_pregoes(inicio: date, fim: date, calendario: CustomBusinessDay) -> int:
    return len(pd.date_range(start=inicio, end=fim, freq=calendario))


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
    modo: str = "Cotação",
    lotes: float | None = None,
) -> str:

    dobro_diario, dobro_exp, tem_ko, tem_par, tem_sus, tem_acel = TIPOS_ACC[opcao]

    op       = tipo_operacao
    op_lower = op.lower()
    op_flex  = "comprados" if op == "Compra" else "vendidos"

    lado_cap = "acima"  if op == "Compra" else "abaixo"
    lado_desfavoravel = "abaixo" if op == "Compra" else "acima"

    u = unidade

    if tem_acel and nivel_acelerador is not None:
        if tipo_operacao == "Venda":
            preco_acel = (nivel_acelerador + nivel_melhorado)
        else:
            preco_acel = (nivel_melhorado - nivel_acelerador)
    else:
        preco_acel = None

    # ── Sufixo de lotes por pregão (somente em confirmação de ordem) ────
    confirmacao = (modo == "Confirmação de ordem") and (lotes is not None) and (pregoes > 0)
    if confirmacao:
        lotes_1x = lotes / pregoes
        lotes_2x = 2 * lotes / pregoes
        sufixo_1x = f" ({lotes_1x:.4f} lotes)"
        sufixo_2x = f" ({lotes_2x:.4f} lotes)"
    else:
        sufixo_1x = ""
        sufixo_2x = ""

    # ── Cabeçalho
    cabecalho_base = f"{commodity} — {pilar} @ {preco_base} {u} — Exp. {vencimento} ({pregoes} Pregões)"
    if confirmacao:
        primeira_linha = f"*Confirmação de ordem*\n*{lotes:g} Lotes {cabecalho_base}*"
    else:
        primeira_linha = f"*{cabecalho_base}*"

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

    # ── Regras diárias

    if tem_acel:
        preco_normal = preco_acel
    else:
        preco_normal = nivel_melhorado

    # Faixa central entre melhorado e o cap (KO ou Suspensão): 1x
    if tem_ko or tem_sus:
        limite = nivel_ko if tem_ko else nivel_suspensao
        linhas.append(
            f"- Todo dia em que o mercado fechar entre {nivel_melhorado} e {limite} {u}, "
            f"{op_lower} 1x{sufixo_1x} o volume diário a {preco_normal} {u}."
        )

    # Lado desfavorável ao cliente — dispara o dobro (2x) ou a acumulação normal (1x)
    multiplicador = "2x" if dobro_diario else "1x"
    sufixo_multi   = sufixo_2x if dobro_diario else sufixo_1x
    linhas.append(
        f"- Todo dia em que o mercado fechar a {nivel_melhorado} {u} ou {lado_desfavoravel}, "
        f"{op_lower} {multiplicador}{sufixo_multi} o volume diário a {nivel_melhorado} {u}."
    )

    # ── Knock Out ────────────────────────────────────────────────────────
    if tem_ko:
        lotes_restantes = (
            f", e o restante dos lotes são {op_flex} a {nivel_paraquedas} {u}"
            if tem_par else ""
        )
        linhas.append(
            f"- Se, em qualquer momento, o mercado tocar {nivel_ko} {u}, o acumulador desmonta. "
            f"Os lotes {op_flex} a {nivel_melhorado}"
            + (f" e {preco_acel}" if tem_acel else "")
            + f" {u} permanecem{lotes_restantes}."
        )

    # ── Suspensão ────────────────────────────────────────────────────────
    if tem_sus:
        linhas.append(
            f"- Se em algum pregão o mercado fechar a {nivel_suspensao} {u} ou {lado_cap}, "
            f"nada é acumulado naquele pregão, mas a estrutura não desmonta."
        )

    # ── Dobro na expiração ───────────────────────────────────────────────
    if dobro_exp and tem_sus:
        linhas.append(
            f"- Se no dia do vencimento fechar {lado_desfavoravel} de {nivel_melhorado} {u}, "
            f"{op_lower} 1x o volume total adicional a {nivel_melhorado} {u}."
        )
    elif dobro_exp:
        linhas.append(
            f"- Caso o mercado não negociar a {nivel_ko} {u} em nenhum momento, "
            f"e no dia do vencimento fechar {lado_desfavoravel} de {nivel_melhorado} {u}, "
            f"{op_lower} mais 1x o volume total adicional a {nivel_melhorado} {u}."
        )

    return "\n".join(linhas)


# ── UI
st.title("Gerador de Acumuladores")

modo = st.radio("Modo:", ["Cotação", "Confirmação de ordem"], horizontal=True)

# Quantidade de lotes — só aparece em modo Confirmação
lotes = None
if modo == "Confirmação de ordem":
    lotes = st.number_input("Quantidade de lotes:", min_value=1.0, value=10.0, step=1.0)

# Commodity
commodity = st.selectbox("Commodity:", list(COMMODITIES.keys()))
info_commodity = COMMODITIES[commodity]
unidade = info_commodity["unidade"]
pilares = info_commodity["pilares"]
calendario = info_commodity["calendario"]

st.subheader("Escolha o tipo de acumulador")
opcao = st.selectbox("Tipo:", list(TIPOS_ACC.keys()))
st.divider()

tipo_operacao = st.radio("Compra ou Venda?", ["Compra", "Venda"])

pilar = st.selectbox("Pilar:", list(pilares.keys()))
vencimento = pilares[pilar]
hoje = date.today()
pregoes = contar_pregoes(hoje, vencimento, calendario)
st.write(f"Vencimento: {vencimento}")
st.write(f"Número de pregões: {pregoes}")

preco_base      = st.number_input(f"Referência ({unidade}):", min_value=0.0)
nivel_melhorado = st.number_input(f"Nível melhorado ({unidade}):", min_value=0.0)

# ── Inputs condicionais
dobro_diario, dobro_exp, tem_ko, tem_par, tem_sus, tem_acel = TIPOS_ACC[opcao]

nivel_ko         = st.number_input(f"Nível de Knock Out ({unidade}):",  value=0.0, min_value=0.0) if tem_ko  else None
nivel_paraquedas = st.number_input(f"Nível de Paraquedas ({unidade}):", value=0.0, min_value=0.0) if tem_par else None
nivel_suspensao  = st.number_input(f"Nível de Suspensão ({unidade}):",  value=0.0, min_value=0.0) if tem_sus else None
nivel_acelerador = st.number_input(f"Nível do Acelerador ({unidade}):", value=0.0, min_value=0.0) if tem_acel else None

if tem_ko and nivel_ko is None: nivel_ko = 0.0
if tem_par and nivel_paraquedas is None: nivel_paraquedas = 0.0
if tem_sus and nivel_suspensao is None: nivel_suspensao = 0.0
if tem_acel and nivel_acelerador is None: nivel_acelerador = 0.0

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
        modo=modo,
        lotes=lotes,
    )
    st.markdown(texto.replace("$", r"\$"))
    st.divider()
    st.text_area("Copiar texto:", texto, height=300)
