import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------------
# Config & style — CSS usa variáveis do Streamlit para se adaptar
# automaticamente ao tema claro/escuro escolhido pelo usuário/SO.
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Painel Orçamentário — Marketing",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#1F3864"
GREEN = "#1E8449"
RED = "#C0392B"
NEUTRAL_GRAY = "#9CA3AF"

BRAND_COLORS = {
    "INFANTI": "#72A9A0",
    "QUINNY": "#2D2A26",
    "SAFETY 1ST": "#FCD920",
    "TINY LOVE": "#E01920",
    "MAXI COSI": "#0190BA",
    "BEBE CONFORT": "#0190BA",  # nome legado da Maxi-Cosi em alguns mercados
    "VOYAGE": "#F05423",
    "COSCO": "#645EC0",
}
BRAND_NEUTRAL = "#B0B4BA"

st.markdown(
    f"""
    <style>
    .main-header {{
        background-color: {NAVY};
        padding: 22px 28px;
        border-radius: 8px;
        margin-bottom: 6px;
    }}
    .main-header h1 {{ color: white; font-size: 26px; margin: 0; font-weight: 700; }}
    .main-header p {{ color: #D6DEEC; font-size: 13px; margin: 4px 0 0 0; }}
    .section-header {{
        background-color: {NAVY};
        color: white;
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 15px;
        font-weight: 700;
        margin-top: 26px;
        margin-bottom: 10px;
    }}
    .periodo-indicador {{
        font-size: 13px;
        color: var(--text-color);
        opacity: 0.75;
        margin: 2px 0 14px 0;
    }}
    div[data-testid="stMetric"] {{
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.35);
        border-radius: 8px;
        padding: 14px 16px 10px 16px;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    div[data-testid="stMetricLabel"] {{
        font-size: 12px; opacity: 0.75; text-transform: uppercase; font-weight: 600;
    }}
    div[data-testid="stMetricValue"] {{ font-size: 22px; font-weight: 700; }}
    .disclaimer {{ font-size: 12px; opacity: 0.65; margin-top: 4px; }}
    .historico-nota {{ font-size: 13px; opacity: 0.75; margin-top: 4px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------
# Formatação numérica — padrão brasileiro (ponto milhar, vírgula decimal)
# ------------------------------------------------------------------
def money_str(v, signed=False):
    if v is None or pd.isna(v):
        return "—"
    sign = "+" if (signed and v > 0) else ""
    neg = v < 0
    v = abs(v)
    s = f"{v:,.0f}"
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"{'-' if neg else sign}R$ {s}"


def pct_str(v, signed=True, decimals=1):
    if v is None or pd.isna(v):
        return "—"
    s = f"{v:.{decimals}f}"
    s = s.replace(".", ",")
    if signed and v > 0:
        s = "+" + s
    return f"{s}%"


def color_var(v):
    """Verde = abaixo do Forecast/referência (favorável). Vermelho = acima (desfavorável)."""
    if v is None or pd.isna(v):
        return ""
    if v > 0:
        return f"color: {RED}; font-weight:600"
    if v < 0:
        return f"color: {GREEN}; font-weight:600"
    return ""


# ------------------------------------------------------------------
# Data loading
# ------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/base.csv", encoding="utf-8")

    def parse_valor(v):
        if pd.isna(v):
            return 0.0
        s = str(v).strip()
        if s in ("-", ""):
            return 0.0
        neg = s.startswith("(") and s.endswith(")")
        s = s.replace("(", "").replace(")", "").replace("R$", "").strip()
        s = s.replace(".", "").replace(",", ".")
        try:
            val = float(s)
        except ValueError:
            return 0.0
        return -val if neg else val

    df["Valor"] = df["Valor"].apply(parse_valor)
    df["Mês"] = df["Mês"].astype(int)
    df["Ano"] = df["Ano"].astype(int)
    df["Marca"] = df["Marca"].fillna("Não disponível (2024)")
    df["Fornecedor (Extraído)"] = df["Fornecedor (Extraído)"].fillna("Não identificado")
    return df


df = load_data()

MESES_PT = {1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
            7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"}

ULTIMO_MES_ACTUAL_2026 = int(df.loc[(df["Ano"] == 2026) & (df["Tipo"] == "Actual"), "Mês"].max())

# ------------------------------------------------------------------
# Sidebar — filtros globais
# ------------------------------------------------------------------
st.sidebar.markdown("### Filtros")
st.sidebar.caption("Marca e Fornecedor existem apenas no Actual — não filtram o Forecast.")

anos = sorted(df["Ano"].unique())
quarters = sorted(df["Trimestre"].dropna().unique())
meses = sorted(df["Mês"].unique())
marcas = sorted(df["Marca"].unique())
ccs = sorted(df["Descrição CC"].dropna().unique())
fornecedores = sorted(df["Fornecedor (Extraído)"].dropna().unique())
categorias = sorted(df["Descrição Controller"].dropna().unique())

f_ano = st.sidebar.multiselect("Ano", anos, default=[])
f_quarter = st.sidebar.multiselect("Quarter", quarters, default=[])
f_mes = st.sidebar.multiselect("Mês", meses, default=[], format_func=lambda m: MESES_PT[m])
f_marca = st.sidebar.multiselect("Marca (2025+)", marcas, default=[])
f_cc = st.sidebar.multiselect("Centro de Custo", ccs, default=[])
f_fornecedor = st.sidebar.multiselect("Fornecedor", fornecedores, default=[])
f_categoria = st.sidebar.multiselect("Categoria (Descr. Controller)", categorias, default=[])

st.sidebar.markdown("---")
st.sidebar.caption("Snapshot estático — não atualiza sozinho. Reflete os dados no momento da exportação.")


def apply_filters(data):
    out = data.copy()
    if f_ano:
        out = out[out["Ano"].isin(f_ano)]
    if f_quarter:
        out = out[out["Trimestre"].isin(f_quarter)]
    if f_mes:
        out = out[out["Mês"].isin(f_mes)]
    if f_marca:
        out = out[out["Marca"].isin(f_marca)]
    if f_cc:
        out = out[out["Descrição CC"].isin(f_cc)]
    if f_fornecedor:
        out = out[out["Fornecedor (Extraído)"].isin(f_fornecedor)]
    if f_categoria:
        out = out[out["Descrição Controller"].isin(f_categoria)]
    return out


df_f = apply_filters(df)
actual = df_f[df_f["Tipo"] == "Actual"]

forecast = df[df["Tipo"] == "Forecast"].copy()
if f_ano:
    forecast = forecast[forecast["Ano"].isin(f_ano)]
if f_quarter:
    forecast = forecast[forecast["Trimestre"].isin(f_quarter)]
if f_mes:
    forecast = forecast[forecast["Mês"].isin(f_mes)]
if f_cc:
    forecast = forecast[forecast["Descrição CC"].isin(f_cc)]
if f_categoria:
    forecast = forecast[forecast["Descrição Controller"].isin(f_categoria)]
# Marca/Fornecedor não existem no Forecast — não filtram essa base, por design.

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------
st.markdown(
    f"""
    <div class="main-header">
        <h1>Dashboard Orçamentário — Marketing · Dorel Juvenile Brasil</h1>
        <p>Forecast x Actual 2024–2026 · Snapshot estático · Actual 2026 até {MESES_PT[ULTIMO_MES_ACTUAL_2026]}
        · dados consolidados e normalizados a partir da base original</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Resumo executivo — foco em 2026 (objetivo central do dashboard),
# histórico multi-ano como card de fechamento da grade.
# ------------------------------------------------------------------
st.markdown('<div class="section-header">RESUMO EXECUTIVO</div>', unsafe_allow_html=True)

if f_ano:
    periodo_txt = " · ".join(str(a) for a in sorted(f_ano))
else:
    periodo_txt = "todos os anos (2024–2026)"
st.markdown(
    f'<div class="periodo-indicador">Período em análise: <b>{periodo_txt}</b> · '
    f'Comparação Forecast x Actual referente a 2026, jan–{MESES_PT[ULTIMO_MES_ACTUAL_2026]} '
    f'(período com Actual disponível).</div>',
    unsafe_allow_html=True,
)

total_forecast = forecast["Valor"].sum()

actual_2026_full = actual[actual["Ano"] == 2026]["Valor"].sum()
saldo = total_forecast - actual_2026_full
pct_utilizado = (actual_2026_full / total_forecast * 100) if total_forecast else 0

actual_2026 = actual[actual["Ano"] == 2026]
forecast_2026_comp = forecast[(forecast["Ano"] == 2026) & (forecast["Mês"] <= ULTIMO_MES_ACTUAL_2026)]
var_r = actual_2026["Valor"].sum() - forecast_2026_comp["Valor"].sum()
var_pct = (var_r / forecast_2026_comp["Valor"].sum() * 100) if forecast_2026_comp["Valor"].sum() else None

meses_realizados_2026 = actual_2026["Mês"].nunique() or 1
burn_rate = actual_2026["Valor"].sum() / meses_realizados_2026

pct_ano_decorrido = ULTIMO_MES_ACTUAL_2026 / 12 * 100
desvio_ritmo = pct_utilizado - pct_ano_decorrido

# Gasto Histórico Total — todos os anos, ignora filtro de Ano, respeita os demais.
def apply_filters_sem_ano(data):
    out = data.copy()
    if f_quarter:
        out = out[out["Trimestre"].isin(f_quarter)]
    if f_mes:
        out = out[out["Mês"].isin(f_mes)]
    if f_marca:
        out = out[out["Marca"].isin(f_marca)]
    if f_cc:
        out = out[out["Descrição CC"].isin(f_cc)]
    if f_fornecedor:
        out = out[out["Fornecedor (Extraído)"].isin(f_fornecedor)]
    if f_categoria:
        out = out[out["Descrição Controller"].isin(f_categoria)]
    return out

gasto_historico = apply_filters_sem_ano(df[df["Tipo"] == "Actual"])["Valor"].sum()

# Linha 1 — Forecast x Actual 2026 (núcleo do dashboard)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Planejado 2026", money_str(total_forecast), delta=None, delta_color="off")
c2.metric("Gasto 2026 (YTD)", money_str(actual_2026_full), delta=None, delta_color="off")
c3.metric("Saldo Disponível 2026", money_str(saldo), delta=None, delta_color="off")
c4.metric("% Orçamento Utilizado 2026", pct_str(pct_utilizado, signed=False), delta=None, delta_color="off")

# Linha 2 — ritmo, contexto e histórico consolidado
c5, c6, c7, c8 = st.columns(4)
c5.metric("Variação F x A (comparável)", money_str(var_r, signed=True),
          pct_str(var_pct) if var_pct is not None else "—", delta_color="inverse")
c6.metric("Desvio de Ritmo", f"{desvio_ritmo:+.1f} pp".replace(".", ","),
          f"{pct_ano_decorrido:.0f}% do ano decorrido".replace(".", ","),
          delta_color="off")
c7.metric("Burn Rate Mensal (2026)", money_str(burn_rate), delta=None, delta_color="off")
c8.metric("Gasto Histórico Total", money_str(gasto_historico), delta=None, delta_color="off")

st.markdown(
    '<p class="disclaimer">Dados consolidados e normalizados a partir da base original. '
    'Ajustes de taxonomia (agrupamento de categorias) foram feitos por leitura automática de texto '
    'e ainda dependem de validação da área de Marketing. Fornecedor extraído por heurística do '
    'campo Histórico — aproximado, não é um cadastro de fornecedor limpo.</p>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# 1. Forecast x Actual mensal — tabela transposta (meses em coluna)
# ------------------------------------------------------------------
st.markdown('<div class="section-header">1 · FORECAST x ACTUAL — COMPARAÇÃO MENSAL 2026</div>', unsafe_allow_html=True)
st.caption("Variação calculada apenas no período com Actual disponível (jan–" + MESES_PT[ULTIMO_MES_ACTUAL_2026] + ").")

fa = df[df["Ano"] == 2026].groupby(["Mês", "Tipo"])["Valor"].sum().unstack(fill_value=0).reindex(range(1, 13), fill_value=0)
fa["Mês_nome"] = [MESES_PT[m] for m in fa.index]

fig1 = go.Figure()
fig1.add_bar(x=fa["Mês_nome"], y=fa.get("Forecast", 0), name="Forecast", marker_color=NAVY,
             customdata=[money_str(v) for v in fa.get("Forecast", 0)],
             hovertemplate="Forecast: %{customdata}<extra></extra>")
fig1.add_bar(x=fa["Mês_nome"], y=fa.get("Actual", 0), name="Actual", marker_color=NEUTRAL_GRAY,
             customdata=[money_str(v) for v in fa.get("Actual", 0)],
             hovertemplate="Actual: %{customdata}<extra></extra>")
fig1.update_layout(barmode="group", height=340, margin=dict(t=10, b=10, l=10, r=10),
                    legend=dict(orientation="h", y=1.1), plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig1, use_container_width=True)

tab_fa = fa.copy()
tab_fa["Var R$"] = tab_fa.get("Actual", 0) - tab_fa.get("Forecast", 0)
tab_fa["Var %"] = tab_fa["Var R$"] / tab_fa.get("Forecast", 1).replace(0, pd.NA) * 100
# Meses futuros (sem Actual real ainda): não é "-100%", é ausência de dado — deixa em branco.
mask_futuro = tab_fa.index > ULTIMO_MES_ACTUAL_2026
tab_fa.loc[mask_futuro, "Actual"] = pd.NA
tab_fa.loc[mask_futuro, ["Var R$", "Var %"]] = pd.NA

tab_fa_t = tab_fa.set_index("Mês_nome")[["Forecast", "Actual", "Var R$", "Var %"]].T
tab_fa_t = tab_fa_t.reindex(columns=[MESES_PT[m] for m in range(1, 13)])

sty = tab_fa_t.style.format(money_str, subset=pd.IndexSlice[["Forecast", "Actual", "Var R$"], :])
sty = sty.format(lambda v: pct_str(v, signed=True), subset=pd.IndexSlice[["Var %"], :])
sty = sty.map(color_var, subset=pd.IndexSlice[["Var R$", "Var %"], :])
st.dataframe(sty, use_container_width=True)

# ------------------------------------------------------------------
# 2. Fornecedores — lista completa, rolagem interna
# ------------------------------------------------------------------
st.markdown('<div class="section-header">2 · FORNECEDORES</div>', unsafe_allow_html=True)
fornecedores_ativos = actual["Fornecedor (Extraído)"].nunique()
st.caption(f"Ranking por valor gasto (Actual) · {fornecedores_ativos} fornecedores distintos no filtro atual. "
           "Fornecedor extraído do texto do Histórico — aproximado.")

forn = actual.groupby("Fornecedor (Extraído)")["Valor"].sum().sort_values(ascending=False)
forn = forn[forn.index != "Não identificado"]
total_forn = actual["Valor"].sum()
tab_forn = pd.DataFrame({
    "Fornecedor": forn.index,
    "Valor": forn.values,
    "% Participação": (forn.values / total_forn * 100) if total_forn else 0,
})
tab_forn["% Acumulado"] = tab_forn["% Participação"].cumsum()
st.dataframe(
    tab_forn.set_index("Fornecedor").style.format(
        {"Valor": money_str, "% Participação": pct_str, "% Acumulado": pct_str}
    ).bar(subset=["Valor"], color=NAVY),
    use_container_width=True,
    height=420,
)

# ------------------------------------------------------------------
# 3. Centro de Custo
# ------------------------------------------------------------------
st.markdown('<div class="section-header">3 · CENTRO DE CUSTO</div>', unsafe_allow_html=True)
ccs_ativos = df_f["Descrição CC"].nunique()
st.caption(f"Actual vs Forecast por Centro de Custo, período comparável 2026 (jan–{MESES_PT[ULTIMO_MES_ACTUAL_2026]}) "
           f"· {ccs_ativos} centros de custo ativos no filtro atual.")

cc_actual = actual[actual["Ano"] == 2026].groupby("Descrição CC")["Valor"].sum()
cc_forecast = forecast[(forecast["Ano"] == 2026) & (forecast["Mês"] <= ULTIMO_MES_ACTUAL_2026)].groupby("Descrição CC")["Valor"].sum()
cc_tab = pd.DataFrame({"Actual": cc_actual, "Forecast": cc_forecast}).fillna(0)
cc_tab["Var R$"] = cc_tab["Actual"] - cc_tab["Forecast"]
cc_tab["Var %"] = cc_tab["Var R$"] / cc_tab["Forecast"].replace(0, pd.NA) * 100
cc_tab = cc_tab.sort_values("Actual", ascending=False).head(10)

colA, colB = st.columns([1, 1])
with colA:
    st.dataframe(
        cc_tab.style.format(
            {"Actual": money_str, "Forecast": money_str, "Var R$": lambda v: money_str(v, signed=True),
             "Var %": lambda v: pct_str(v, signed=True)}
        ).map(color_var, subset=["Var R$", "Var %"]),
        use_container_width=True,
    )
with colB:
    cc_plot = cc_tab.sort_values("Actual")
    fig2 = go.Figure()
    fig2.add_bar(y=cc_plot.index, x=cc_plot["Forecast"], name="Forecast", orientation="h", marker_color=NAVY,
                 customdata=[money_str(v) for v in cc_plot["Forecast"]],
                 hovertemplate="Forecast: %{customdata}<extra></extra>")
    fig2.add_bar(y=cc_plot.index, x=cc_plot["Actual"], name="Actual", orientation="h", marker_color=NEUTRAL_GRAY,
                 customdata=[money_str(v) for v in cc_plot["Actual"]],
                 hovertemplate="Actual: %{customdata}<extra></extra>")
    fig2.update_layout(barmode="group", height=380, margin=dict(t=10, b=10, l=10, r=10),
                        legend=dict(orientation="h", y=1.1), plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------------------------------
# 4. Categoria de gasto
# ------------------------------------------------------------------
st.markdown('<div class="section-header">4 · CATEGORIA DE GASTO</div>', unsafe_allow_html=True)
st.caption("Ranking por natureza de despesa (Actual, respeita todos os filtros).")

cat = actual.groupby("Descrição Controller")["Valor"].sum().sort_values(ascending=False).head(15)
total_cat = actual["Valor"].sum()
tab_cat = pd.DataFrame({
    "Categoria": cat.index, "Gasto": cat.values,
    "% Part.": (cat.values / total_cat * 100) if total_cat else 0,
})
tab_cat["% Acum."] = tab_cat["% Part."].cumsum()
st.dataframe(
    tab_cat.set_index("Categoria").style.format(
        {"Gasto": money_str, "% Part.": pct_str, "% Acum.": pct_str}
    ).bar(subset=["Gasto"], color=NAVY),
    use_container_width=True,
)

# ------------------------------------------------------------------
# 5. Marca (2025+) — barras horizontais com cores oficiais
# ------------------------------------------------------------------
st.markdown('<div class="section-header">5 · MARCA (2025+)</div>', unsafe_allow_html=True)
st.caption("Marca não existe na base de 2024 — comparação restrita a 2025 e 2026. "
           "Cores identificam a marca (identidade visual), não indicam status — só vermelho/verde nas tabelas de variação têm esse sentido.")

marca_df = actual[actual["Ano"] >= 2025]
marca_agg = marca_df.groupby("Marca")["Valor"].sum().sort_values(ascending=False)
marca_agg = marca_agg[~marca_agg.index.isin(["Não disponível (2024)"])]

colC, colD = st.columns([1, 1.2])
with colC:
    tab_marca = pd.DataFrame({"Marca": marca_agg.index, "Gasto": marca_agg.values})
    tab_marca["% Part."] = tab_marca["Gasto"] / tab_marca["Gasto"].sum() * 100
    st.dataframe(
        tab_marca.set_index("Marca").style.format({"Gasto": money_str, "% Part.": pct_str}),
        use_container_width=True,
    )
with colD:
    marca_plot = marca_agg.sort_values()
    cores = [BRAND_COLORS.get(m, BRAND_NEUTRAL) for m in marca_plot.index]
    fig3 = go.Figure(go.Bar(
        x=marca_plot.values, y=marca_plot.index, orientation="h", marker_color=cores,
        text=[money_str(v) for v in marca_plot.values], textposition="outside",
        customdata=[money_str(v) for v in marca_plot.values],
        hovertemplate="%{y}: %{customdata}<extra></extra>",
    ))
    fig3.update_layout(height=340, margin=dict(t=10, b=10, l=10, r=60), plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3, use_container_width=True)

# ------------------------------------------------------------------
# 6. Evolução temporal — quarter x ano, com rótulos e variação YoY
# ------------------------------------------------------------------
st.markdown('<div class="section-header">6 · EVOLUÇÃO TEMPORAL</div>', unsafe_allow_html=True)
st.caption("Actual por trimestre, comparado entre anos equivalentes. 2026 parcial — Q3/Q4 ainda sem dado.")

evo = df[df["Tipo"] == "Actual"].groupby(["Trimestre", "Ano"])["Valor"].sum().unstack("Ano")
evo = evo.reindex(["Q1", "Q2", "Q3", "Q4"])

cores_ano = {2024: NEUTRAL_GRAY, 2025: "#4C6EA8", 2026: NAVY}
fig4 = go.Figure()
for ano in [2024, 2025, 2026]:
    y_vals = evo[ano] if ano in evo.columns else pd.Series([None] * 4, index=evo.index)
    fig4.add_bar(
        x=evo.index, y=y_vals, name=str(ano), marker_color=cores_ano[ano],
        text=[money_str(v) if pd.notna(v) else "" for v in y_vals], textposition="outside",
        customdata=[money_str(v) if pd.notna(v) else "—" for v in y_vals],
        hovertemplate="%{x} " + str(ano) + ": %{customdata}<extra></extra>",
    )
fig4.update_layout(barmode="group", height=380, margin=dict(t=30, b=10, l=10, r=10),
                    legend=dict(orientation="h", y=1.12), plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig4, use_container_width=True)

evo_var = pd.DataFrame(index=evo.index)
if 2024 in evo.columns and 2025 in evo.columns:
    evo_var["Var % 25 vs 24"] = (evo[2025] - evo[2024]) / evo[2024] * 100
if 2025 in evo.columns and 2026 in evo.columns:
    evo_var["Var % 26 vs 25"] = (evo[2026] - evo[2025]) / evo[2025] * 100

st.dataframe(
    evo_var.style.format(lambda v: pct_str(v, signed=True)).map(color_var),
    use_container_width=True,
)

st.markdown("---")
st.caption(
    "Dashboard de snapshot — não conectado à base viva. Para atualizar, gere um novo CSV da aba "
    "'Base Consolidada' no Excel e substitua o arquivo de dados deste app."
)
