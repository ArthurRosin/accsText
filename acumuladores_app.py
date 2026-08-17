import streamlit as st
import pandas as pd
from pandas.tseries.offsets import CustomBusinessDay
from datetime import date
from pathlib import Path

DADOS = Path(__file__).parent / "dados"

# ── Carregamento da base de dados (CSV) ─────────────────────────────────────
@st.cache_data
def carregar_feriados() -> pd.DataFrame:
    df = pd.read_csv(DADOS / "feriados.csv", parse_dates=["data"])
    df["data"] = df["data"].dt.date
    return df


@st.cache_data
def carregar_commodities() -> pd.DataFrame:
    return pd.read_csv(DADOS / "commodities.csv")


@st.cache_data
def carregar_pilares() -> pd.DataFrame:
    df = pd.read_csv(DADOS / "pilares.csv", parse_dates=["vencimento"])
    df["vencimento"] = df["vencimento"].dt.date
    return df


@st.cache_data
def construir_calendarios() -> dict[str, CustomBusinessDay]:
    """Monta os CustomBusinessDay de cada mercado a partir de feriados.csv.
    'AMBOS' entra tanto no calendário CBOT quanto no B3."""
    fer = carregar_feriados()
    cbot = fer.loc[fer["mercado"].isin(["CBOT", "AMBOS"]), "data"].tolist()
    b3   = fer.loc[fer["mercado"].isin(["B3",   "AMBOS"]), "data"].tolist()
    return {
        "cbot": CustomBusinessDay(holidays=cbot),
        "b3":   CustomBusinessDay(holidays=b3),
    }


@st.cache_data
def construir_commodities() -> dict:
    """Recria a estrutura COMMODITIES a partir das três CSVs."""
    calendarios = construir_calendarios()
    df_com = carregar_commodities()
    df_pil = carregar_pilares()

    out = {}
    for _, row in df_com.iterrows():
        nome = row["commodity"]
        pilares = (
            df_pil[df_pil["commodity"] == nome]
            .set_index("pilar")["vencimento"]
            .to_dict()
        )
        out[nome] = {
            "unidade": row["unidade"],
            "calendario": calendarios[row["calendario"]],
            "cod_calendario": row["calendario"],
            "pilares": pilares,
        }
    return out


def validar_pilares(commodities: dict) -> list[str]:
    """Retorna avisos para todo pilar que caia em fim de semana ou feriado —
    ou seja, num dia que não seja pregão no seu próprio calendário."""
    avisos = []
    for nome, info in commodities.items():
        cal = info["calendario"]
        for pilar, venc in info["pilares"].items():
            # Um dia é pregão se date_range(venc, venc) o inclui.
            eh_pregao = len(pd.date_range(start=venc, end=venc, freq=cal)) == 1
            if not eh_pregao:
                dia = venc.strftime("%A")
                avisos.append(f"{nome} · {pilar} → {venc} ({dia}) não é pregão")
    return avisos


# ── Tipos de acumulador ─────────────────────────────────────────────────────
# (dobro_diario, dobro_exp, tem_ko, tem_paraquedas, tem_suspensao, tem_acelerador, tem_protecao)
TIPOS_ACC = {
    "ACC com dobro diário e KO":                                              (True,  False, True,  False, False, False, False),
    "ACC sem dobro e com KO":                                                 (False, False, True,  False, False, False, False),
    "ACC com dobro na expiração e KO":                                        (False, True,  True,  False, False, False, False),

    "ACC com dobro diário, KO e paraquedas":                                  (True,  False, True,  True,  False, False, False),
    "ACC sem dobro, com KO e paraquedas":                                     (False, False, True,  True,  False, False, False),
    "ACC com dobro na expiração, KO e paraquedas":                            (False, True,  True,  True,  False, False, False),

    "ACC com dobro diário e Suspensão":                                       (True,  False, False, False, True,  False, False),
    "ACC sem dobro e com Suspensão":                                          (False, False, False, False, True,  False, False),
    "ACC com dobro na expiração e Suspensão":                                 (False, True,  False, False, True,  False, False),

    "ACC com dobro diário, Acelerador e KO":                                  (True,  False, True,  False, False, True, False),
    "ACC com dobro na expiração, Acelerador e KO":                            (False, True,  True,  False, False, True, False),

    "ACC com dobro diário, Acelerador, KO e Paraquedas":                      (True, False, True, True, False, True, False),
    "ACC com dobro na expiração, Acelerador, KO e Paraquedas":                (False, True, True, True, False, True, False),

    "ACC com dobro diário, Acelerador e Suspensão":                           (True, False, False, False, True, True, False),
    "ACC com dobro na expiração, Acelerador e Suspensão":                     (False, True, False, False, True, True, False),
    
    "ACC com dobro diário, KO e Proteção de Dobro":                           (True, False, True, False, False, False, True),
    "ACC com dobro na expiração, KO e Proteção de Dobro":                     (False, True, True, False, False, False, True),
    "ACC com dobro diário, Suspensão e Proteção de Dobro":                    (True, False, False, False, True, False, True),
    "ACC com dobro diário, Paraquedas, KO e Proteção de Dobro":               (True, False, True, True, False, False, True),

    "ACC com dobro diário, Acelerador, KO e Proteção de Dobro":               (True, False, True, False, False, True, True),
    "ACC com dobro diário, Acelerador, KO, Paraquedas e Proteção de Dobro":   (True, False, True, True, False, True, True),
    "ACC com dobro diário, Acelerador, Suspensão e Proteção de Dobro":        (True, False, True, False, True, True, True),

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
    nivel_protecao: float | None,
    modo: str = "Cotação",
    lotes: float | None = None,
) -> str:

    dobro_diario, dobro_exp, tem_ko, tem_par, tem_sus, tem_acel, tem_prot = TIPOS_ACC[opcao]

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
    if pilar:
        cabecalho_base = f"{commodity} — {pilar} @ {preco_base} {u} — Exp. {vencimento} ({pregoes} Pregões)"
    else:
        cabecalho_base = f"{commodity} @ {preco_base} {u} — Exp. {vencimento} ({pregoes} Pregões)"
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
    if tem_prot:
        linhas.append(f"Nível de Proteção de dobro @ {nivel_protecao} {u}")
    linhas.append("")

    # ── Regras diárias
    if tem_acel:
        preco_normal = preco_acel
    else:
        preco_normal = nivel_melhorado

    # Faixa central entre melhorado e o cap (KO ou Suspensão): 1x
    if tem_ko or tem_sus:
        if commodity == "FX":
            limite = nivel_ko
            linhas.append(
                f"- Todo dia em que a PTAX fechar entre {nivel_melhorado} e {limite} {u}, "
                f"{op_lower} 1x{sufixo_1x} o montante diário a {preco_normal} {u}."
            )
        else:
            limite = nivel_ko if tem_ko else nivel_suspensao
            linhas.append(
                f"- Todo dia em que o mercado fechar entre {nivel_melhorado} e {limite} {u}, "
                f"{op_lower} 1x{sufixo_1x} o volume diário a {preco_normal} {u}."
            )

    # Lado desfavorável ao cliente — dispara o dobro (2x) ou a acumulação normal (1x)
    if not tem_prot:
        multiplicador = "2x" if dobro_diario else "1x"
        sufixo_multi  = sufixo_2x if dobro_diario else sufixo_1x
        if commodity == "FX":
            linhas.append(
                f"- Todo dia em que a PTAX fechar a {nivel_melhorado} {u} ou {lado_desfavoravel}, "
                f"{op_lower} {multiplicador}{sufixo_multi} o montante diário a {nivel_melhorado} {u}."
            )
        else:
            linhas.append(
                f"- Todo dia em que o mercado fechar a {nivel_melhorado} {u} ou {lado_desfavoravel}, "
                f"{op_lower} {multiplicador}{sufixo_multi} o volume diário a {nivel_melhorado} {u}."
            )
    else:
        linhas.append(
            f"- Todo dia em que o mercado fechar entre {nivel_melhorado} e {nivel_protecao} {u}, "
            f"{op_lower} 1x{sufixo_1x} o volume diário a {nivel_melhorado} {u}."
        )

    # ── Proteção de dobro ────────────────────────────────────────────────────────
    if tem_prot:
        linhas.append(
            f"- Todo dia em que o mercado fechar a {nivel_protecao} {u} ou {lado_desfavoravel}, "
            f"{op_lower} 2x{sufixo_2x} o volume diário a {nivel_melhorado} {u}."
        )

    # ── Knock Out ────────────────────────────────────────────────────────
    if tem_ko:
        if commodity == "FX":
            linhas.append(
                f"- Se, em qualquer momento, a PTAX tocar {nivel_ko} {u}, o acumulador desmonta. "
                f"O montante já acumulado a {nivel_melhorado} {u} permanece."
            )
        else:
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


# ── Gerador de texto da cotação de opções ────────────────────────────────────
def gerar_cotacao(
    legs: pd.DataFrame,
    futures_ref: float,
    spot_ref: float,
    custo_cbu: float,
    preco_final: float,
    rs_saca: float,
    tipo_preco: str = "Custo",
    rotulo: str = "Compo",
) -> str:
    # Maturidade do cabeçalho: pega a(s) do(s) leg(s), sem repetir
    mats = list(dict.fromkeys(legs["Maturity"].tolist()))
    mat_header = " / ".join(mats)

    linhas = [f"{mat_header} @ {futures_ref:.2f} / Spot ref. {spot_ref:.4f}", ""]

    for _, row in legs.iterrows():
        acao = "Compra de" if row["Buy/Sell"] == "Buy" else "Venda de"
        linhas.append(
            f"{acao} {rotulo} {row['Call/Put']} {row['Maturity']} @{row['Strike [BRL]']:.2f}"
        )

    linhas.append("")

    rotulo_custo = "Custo de" if tipo_preco == "Custo" else "Crédito de"
    linhas.append(
        f"{rotulo_custo} {custo_cbu:.2f} c/bu = "
        f"{preco_final:,.2f} US$/contrato = "
        f"{rs_saca:.2f} R$/Saca"
    )

    return "\n".join(linhas)


# ── Diálogo de confirmação ───────────────────────────────────────────────────
@st.dialog("Confirmar estrutura")
def confirmar_estrutura(resumo: str):
    st.markdown(resumo)
    c1, c2 = st.columns(2)
    if c1.button("Confirmar", type="primary", width="stretch"):
        st.session_state["gerar_confirmado"] = True
        st.rerun()
    if c2.button("Cancelar", width="stretch"):
        st.rerun()


# ── UI ──────────────────────────────────────────────────────────────────────
st.title("Gerador de Acumuladores")

COMMODITIES = construir_commodities()

# Health-check da base: avisa se algum pilar cai fora de pregão
avisos = validar_pilares(COMMODITIES)
if avisos:
    with st.expander(f"⚠️ {len(avisos)} pilar(es) com data suspeita", expanded=True):
        for a in avisos:
            st.warning(a)

# ── Abas ─────────────────────────────────────────────────────────────────────
tab_gerador, tab_calc = st.tabs(["Gerador de Texto", "Calculadora"])

# ═════════════════════════════════════════════════════════════════════════════
# ABA 1 — GERADOR DE TEXTO
# ═════════════════════════════════════════════════════════════════════════════
with tab_gerador:
    modo = st.radio("Modo:", ["Cotação", "Confirmação de ordem"], horizontal=True)

    lotes = None
    if modo == "Confirmação de ordem":
        lotes = st.number_input("Quantidade de lotes:", min_value=1.0, value=10.0, step=1.0)

    commodity = st.selectbox("Commodity:", list(COMMODITIES.keys()))
    info_commodity = COMMODITIES[commodity]
    unidade = info_commodity["unidade"]
    pilares = info_commodity["pilares"]
    calendario = info_commodity["calendario"]

    st.subheader("Escolha o tipo de acumulador")
    if commodity == "FX":
        opcao = "ACC com dobro diário e KO"
        st.write(f"Tipo: {opcao}")
    else:
        opcao = st.selectbox("Tipo:", list(TIPOS_ACC.keys()))

    st.divider()

    tipo_operacao = st.radio("Compra ou Venda?", ["Compra", "Venda"])

    if commodity == "FX":
        vencimento = st.date_input("Vencimento:")
        pilar = ""                      # FX não tem pilar — cliente escolhe a data
    else:
        pilar = st.selectbox("Pilar:", list(pilares.keys()))
        vencimento = pilares[pilar]

    hoje = date.today()
    pregoes = contar_pregoes(hoje, vencimento, calendario)
    st.write(f"Vencimento: {vencimento}")
    st.write(f"Número de pregões: {pregoes}")

    preco_base      = st.number_input(f"Referência ({unidade}):", min_value=0.0)
    nivel_melhorado = st.number_input(f"Nível melhorado ({unidade}):", min_value=0.0)

    # ── Inputs condicionais
    dobro_diario, dobro_exp, tem_ko, tem_par, tem_sus, tem_acel, tem_prot = TIPOS_ACC[opcao]

    nivel_ko         = st.number_input(f"Nível de Knock Out ({unidade}):",  value=0.0, min_value=0.0) if tem_ko  else None
    nivel_paraquedas = st.number_input(f"Nível de Paraquedas ({unidade}):", value=0.0, min_value=0.0) if tem_par else None
    nivel_suspensao  = st.number_input(f"Nível de Suspensão ({unidade}):",  value=0.0, min_value=0.0) if tem_sus else None
    nivel_acelerador = st.number_input(f"Nível do Acelerador ({unidade}):", value=0.0, min_value=0.0) if tem_acel else None
    nivel_protecao   = st.number_input(f"Nível de Proteção de Dobro ({unidade}):", value=0.0, min_value=0.0) if tem_prot else None

    # ── Geração (com confirmação)
    if st.button("Gerar Texto"):
        resumo = (
            f"Você selecionou um **acumulador de {tipo_operacao.lower()}**.\n\n"
            f"- **Estrutura:** {opcao}\n"
            f"- **Commodity:** {commodity}"
            + (f" · **Pilar:** {pilar}" if pilar else "")
            + f"\n- **Vencimento:** {vencimento} ({pregoes} pregões)\n"
            f"- **Nível melhorado:** {nivel_melhorado} {unidade}"
        )
        extras = []
        if nivel_ko is not None:         extras.append(f"KO {nivel_ko}")
        if nivel_paraquedas is not None: extras.append(f"Paraquedas {nivel_paraquedas}")
        if nivel_suspensao is not None:  extras.append(f"Suspensão {nivel_suspensao}")
        if nivel_acelerador is not None: extras.append(f"Acelerador {nivel_acelerador}")
        if nivel_protecao is not None:   extras.append(f"Proteção {nivel_protecao}")
        if extras:
            resumo += f"\n- **Níveis:** " + " · ".join(extras) + f" {unidade}"
        confirmar_estrutura(resumo)

    if st.session_state.get("gerar_confirmado"):
        st.session_state["gerar_confirmado"] = False
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
            nivel_protecao=nivel_protecao,
            modo=modo,
            lotes=lotes,
        )
        st.markdown(texto.replace("$", r"\$"))
        st.divider()
        st.text_area("Copiar texto:", texto, height=300)

# ═════════════════════════════════════════════════════════════════════════════
# ABA 2 — CALCULADORA (Cotação de Opções)
# ═════════════════════════════════════════════════════════════════════════════
with tab_calc:
    st.header("Cotação de Opções")

    c1, c2 = st.columns(2)
    futures_ref = c1.number_input("Futuro (ref)", value=0.0, step=0.01,
                                  format="%.2f", key="opc_fut")
    spot_ref    = c2.number_input("Spot ref (USD/BRL)", value=0.0, step=0.0001,
                                  format="%.4f", key="opc_spot")

    legs_default = pd.DataFrame([
        {"Buy/Sell": None, "Maturity": None, "Call/Put": None, "Strike [BRL]": 0.00},
        {"Buy/Sell": None, "Maturity": None, "Call/Put": None, "Strike [BRL]": 0.00},
    ])

    legs = st.data_editor(
        legs_default,
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        key="opc_legs",
        column_config={
            "Buy/Sell":     st.column_config.SelectboxColumn(options=["Buy", "Sell"], required=True),
            "Maturity":     st.column_config.SelectboxColumn(
                                options=["SU6", "SN6", "SX6", "SF7", "SH7", "SK7", "SN7"], required=True),
            "Call/Put":     st.column_config.SelectboxColumn(options=["Call", "Put"], required=True),
            "Strike [BRL]": st.column_config.NumberColumn(format="%.2f", min_value=0.0),
        },
    )

    # ── Preço + spread → preço final → conversões ──────────────────────
    with st.container(border=True):
        st.caption("Custo / conversões")

        tipo_preco = st.radio("Tipo:", ["Custo", "Crédito"],
                              horizontal=True, key="opc_tipo")

        p1, p2 = st.columns(2)
        preco_usd  = p1.number_input("Preço (USD)", value=0.0, step=0.01,
                                     format="%.2f", key="opc_preco")   # nosso custo/crédito
        spread_usd = p2.number_input("Spread (USD)", value=0.0, step=0.01,
                                     format="%.2f", key="opc_spread")  # nossa receita

        # Custo soma, Crédito subtrai
        if tipo_preco == "Custo":
            preco_final = preco_usd + spread_usd
        else:
            preco_final = preco_usd - spread_usd

        # Conversões partem do preço final
        custo_cbu = preco_final / 50
        rs_saca   = (custo_cbu / 100) * 2.2046 * spot_ref

        st.metric("Preço final (USD)", f"{preco_final:,.2f}")
        m1, m2 = st.columns(2)
        m1.metric("c/bu",    f"{custo_cbu:,.2f}")
        m2.metric("R$/Saca", f"{rs_saca:.2f}")

    # ── Texto da cotação ───────────────────────────────────────────────
    st.divider()
    st.subheader("Texto da cotação")

    if st.button("Gerar Cotação", key="opc_btn"):
        legs_validos = legs.dropna(subset=["Buy/Sell", "Maturity", "Call/Put"])
        texto_cot = gerar_cotacao(
            legs=legs_validos,
            futures_ref=futures_ref,
            spot_ref=spot_ref,
            custo_cbu=custo_cbu,
            preco_final=preco_final,
            rs_saca=rs_saca,
            tipo_preco=tipo_preco,
        )
        st.text_area("Copiar cotação:", texto_cot, height=220, key="opc_out")
