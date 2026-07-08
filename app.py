import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------------
# Config & style
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Orçamentário — Marketing · Dorel Juvenile Brasil",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#1F3864"
GRAY_BG = "#F5F6F8"
GRAY_TEXT = "#6B7280"
GREEN = "#1E8449"
RED = "#C0392B"

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: #FFFFFF; }}
    .main-header {{
        background-color: {NAVY};
        padding: 22px 28px;
        border-radius: 8px;
        margin-bottom: 6px;
    }}
    .main-header h1 {{
        color: white; font-size: 26px; margin: 0; font-weight: 700;
    }}
    .main-header p {{
        color: #D6DEEC; font-size: 13px; margin: 4px 0 0 0;
    }}
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
    div[data-testid="stMetric"] {{
        background-color: {GRAY_BG};
        border: 1px solid #E3E5E8;
        border-radius: 8px;
        padding: 14px 16px 10px 16px;
    }}
    div[data-testid="stMetricLabel"] {{
        font-size: 12px; color: {GRAY_TEXT}; text-transform: uppercase; font-weight: 600;
    }}
    div[data-testid="stMetricValue"] {{
        font-size: 24px; color: #111827; font-weight: 700;
    }}
    .disclaimer {{
        font-size: 12px; color: {GRAY_TEXT}; margin-top: 4px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


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
        if s == "-" or s == "":
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
# Sidebar — filtros globais (multi-select nativo)
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
forecast = df_f[df_f["Tipo"] == "Forecast"]

# Forecast não tem Marca/Fornecedor reais — filtros dessas dimensões não devem restringir o Forecast
forecast_dim_free = apply_filters(df[df["Tipo"] == "Forecast"]) if not (f_marca or f_fornecedor) else \
    df[(df["Tipo"] == "Forecast")].pipe(lambda d: d[d["Ano"].isin(f_ano)] if f_ano else d) \
        .pipe(lambda d: d[d["Trimestre"].isin(f_quarter)] if f_quarter else d) \
        .pipe(lambda d: d[d["Mês"].isin(f_mes)] if f_mes else d) \
        .pipe(lambda d: d[d["Descrição CC"].isin(f_cc)] if f_cc else d) \
        .pipe(lambda d: d[d["Descrição Controller"].isin(f_categoria)] if f_categoria else d)
forecast = forecast_dim_free

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
# Resumo executivo
# ------------------------------------------------------------------
st.markdown('<div class="section-header">RESUMO EXECUTIVO</div>', unsafe_allow_html=True)

total_actual = actual["Valor"].sum()
total_forecast = forecast["Valor"].sum()
saldo = total_forecast - total_actual
pct_utilizado = (total_actual / total_forecast * 100) if total_forecast else 0

actual_2026 = actual[actual["Ano"] == 2026]
forecast_2026_comp = forecast[(forecast["Ano"] == 2026) & (forecast["Mês"] <= ULTIMO_MES_ACTUAL_2026)]
var_r = actual_2026["Valor"].sum() - forecast_2026_comp["Valor"].sum()
var_pct = (var_r / forecast_2026_comp["Valor"].sum() * 100) if forecast_2026_comp["Valor"].sum() else 0

meses_com_actual = actual["Mês"].nunique() or 1
burn_rate = actual["Valor"].sum() / meses_com_actual
fornecedores_ativos = actual["Fornecedor (Extraído)"].nunique()
ccs_ativos = df_f["Descrição CC"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Gasto (Actual)", f"R$ {total_actual:,.0f}".replace(",", "."))
c2.metric("Total Planejado", f"R$ {total_forecast:,.0f}".replace(",", "."))
c3.metric("Saldo Disponível", f"R$ {saldo:,.0f}".replace(",", "."))
c4.metric("% Orçamento Utilizado", f"{pct_utilizado:.1f}%")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Variação F x A (comparável)", f"R$ {var_r:,.0f}".replace(",", "."), f"{var_pct:+.1f}%",
          delta_color="inverse")
c6.metric("Burn Rate Mensal Médio", f"R$ {burn_rate:,.0f}".replace(",", "."))
c7.metric("Fornecedores Ativos", f"{fornecedores_ativos}")
c8.metric("Centros de Custo Ativos", f"{ccs_ativos}")

# Saúde orçamentária
desvio_pct = var_pct
if desvio_pct > 10:
    saude, cor = "VERMELHO — gasto acima do planejado, ação necessária", RED
elif desvio_pct > 3:
    saude, cor = "AMARELO — levemente acima do proporcional", "#B7791F"
else:
    saude, cor = "VERDE — dentro do ritmo esperado", GREEN
st.markdown(
    f'<p style="margin-top:8px;"><b>Saúde orçamentária:</b> '
    f'<span style="color:{cor}; font-weight:700;">● {saude}</span></p>',
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="disclaimer">Dados consolidados e normalizados a partir da base original. '
    'Ajustes de taxonomia (agrupamento de categorias) foram feitos por leitura automática de texto '
    'e ainda dependem de validação da área de Marketing. Fornecedor extraído por heurística do campo '
    'Histórico — aproximado, não é um cadastro de fornecedor limpo.</p>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# 1. Forecast x Actual mensal
# ------------------------------------------------------------------
st.markdown('<div class="section-header">1 · FORECAST x ACTUAL — COMPARAÇÃO MENSAL 2026</div>', unsafe_allow_html=True)
st.caption("Variação calculada apenas no período com Actual disponível (jan–" + MESES_PT[ULTIMO_MES_ACTUAL_2026] + ").")

fa = df[df["Ano"] == 2026].groupby(["Mês", "Tipo"])["Valor"].sum().unstack(fill_value=0).reindex(range(1, 13), fill_value=0)
fa = fa.rename(columns={"Actual": "Actual", "Forecast": "Forecast"})
fa["Mês_nome"] = [MESES_PT[m] for m in fa.index]

fig1 = go.Figure()
fig1.add_bar(x=fa["Mês_nome"], y=fa.get("Forecast", 0), name="Forecast", marker_color=NAVY)
fig1.add_bar(x=fa["Mês_nome"], y=fa.get("Actual", 0), name="Actual", marker_color="#9CA3AF")
fig1.update_layout(barmode="group", height=340, margin=dict(t=10, b=10, l=10, r=10),
                    legend=dict(orientation="h", y=1.1), plot_bgcolor="white")
st.plotly_chart(fig1, use_container_width=True)

tab_fa = fa.copy()
tab_fa["Var R$"] = tab_fa.get("Actual", 0) - tab_fa.get("Forecast", 0)
tab_fa["Var %"] = (tab_fa["Var R$"] / tab_fa.get("Forecast", 1).replace(0, pd.NA) * 100)
disp = tab_fa[["Mês_nome", "Forecast", "Actual", "Var R$", "Var %"]].rename(columns={"Mês_nome": "Mês"})
disp = disp.set_index("Mês")
st.dataframe(
    disp.style.format({"Forecast": "R$ {:,.0f}", "Actual": "R$ {:,.0f}", "Var R$": "R$ {:,.0f}", "Var %": "{:+.1f}%"}),
    use_container_width=True,
)

# ------------------------------------------------------------------
# 2. Ritmo do orçamento (pacing)
# ------------------------------------------------------------------
st.markdown('<div class="section-header">2 · RITMO DO ORÇAMENTO (PACING)</div>', unsafe_allow_html=True)
pct_ano_decorrido = ULTIMO_MES_ACTUAL_2026 / 12 * 100
total_forecast_2026 = df[(df["Ano"] == 2026) & (df["Tipo"] == "Forecast")]["Valor"].sum()
total_actual_2026 = df[(df["Ano"] == 2026) & (df["Tipo"] == "Actual")]["Valor"].sum()
pct_orcamento_consumido = (total_actual_2026 / total_forecast_2026 * 100) if total_forecast_2026 else 0
desvio_ritmo = pct_orcamento_consumido - pct_ano_decorrido

r1, r2, r3 = st.columns(3)
r1.metric("% do ano decorrido", f"{pct_ano_decorrido:.1f}%")
r2.metric("% do orçamento anual já consumido", f"{pct_orcamento_consumido:.1f}%")
r3.metric("Desvio de ritmo", f"{desvio_ritmo:+.1f} pp", delta_color="inverse" if desvio_ritmo > 0 else "normal")

# ------------------------------------------------------------------
# 3. Fornecedores (só tabela — sem gráfico redundante)
# ------------------------------------------------------------------
st.markdown('<div class="section-header">3 · FORNECEDORES</div>', unsafe_allow_html=True)
st.caption("Ranking por valor gasto (Actual). Fornecedor extraído do texto do Histórico — aproximado.")

forn = actual.groupby("Fornecedor (Extraído)")["Valor"].sum().sort_values(ascending=False)
forn = forn[forn.index != "Não identificado"].head(15)
total_forn = actual["Valor"].sum()
tab_forn = pd.DataFrame({
    "Fornecedor": forn.index,
    "Valor": forn.values,
    "% Participação": (forn.values / total_forn * 100) if total_forn else 0,
})
tab_forn["% Acumulado"] = tab_forn["% Participação"].cumsum()
st.dataframe(
    tab_forn.set_index("Fornecedor").style.format(
        {"Valor": "R$ {:,.0f}", "% Participação": "{:.1f}%", "% Acumulado": "{:.1f}%"}
    ).bar(subset=["Valor"], color=NAVY),
    use_container_width=True,
)

# ------------------------------------------------------------------
# 4. Centro de Custo
# ------------------------------------------------------------------
st.markdown('<div class="section-header">4 · CENTRO DE CUSTO</div>', unsafe_allow_html=True)
st.caption("Actual vs Forecast por Centro de Custo, período comparável 2026 (jan–" + MESES_PT[ULTIMO_MES_ACTUAL_2026] + ").")

cc_actual = actual[actual["Ano"] == 2026].groupby("Descrição CC")["Valor"].sum()
cc_forecast = forecast[(forecast["Ano"] == 2026) & (forecast["Mês"] <= ULTIMO_MES_ACTUAL_2026)].groupby("Descrição CC")["Valor"].sum()
cc_tab = pd.DataFrame({"Actual": cc_actual, "Forecast": cc_forecast}).fillna(0)
cc_tab["Var R$"] = cc_tab["Actual"] - cc_tab["Forecast"]
cc_tab["Var %"] = (cc_tab["Var R$"] / cc_tab["Forecast"].replace(0, pd.NA) * 100)
cc_tab = cc_tab.sort_values("Actual", ascending=False).head(10)

colA, colB = st.columns([1, 1])
with colA:
    st.dataframe(
        cc_tab.style.format({"Actual": "R$ {:,.0f}", "Forecast": "R$ {:,.0f}", "Var R$": "R$ {:,.0f}", "Var %": "{:+.1f}%"}),
        use_container_width=True,
    )
with colB:
    cc_plot = cc_tab.sort_values("Actual")
    fig2 = go.Figure()
    fig2.add_bar(y=cc_plot.index, x=cc_plot["Forecast"], name="Forecast", orientation="h", marker_color=NAVY)
    fig2.add_bar(y=cc_plot.index, x=cc_plot["Actual"], name="Actual", orientation="h", marker_color="#9CA3AF")
    fig2.update_layout(barmode="group", height=380, margin=dict(t=10, b=10, l=10, r=10),
                        legend=dict(orientation="h", y=1.1), plot_bgcolor="white")
    st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------------------------------
# 5. Categoria de gasto
# ------------------------------------------------------------------
st.markdown('<div class="section-header">5 · CATEGORIA DE GASTO</div>', unsafe_allow_html=True)
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
        {"Gasto": "R$ {:,.0f}", "% Part.": "{:.1f}%", "% Acum.": "{:.1f}%"}
    ).bar(subset=["Gasto"], color=NAVY),
    use_container_width=True,
)

# ------------------------------------------------------------------
# 6. Marca (2025+)
# ------------------------------------------------------------------
st.markdown('<div class="section-header">6 · MARCA (2025+)</div>', unsafe_allow_html=True)
st.caption("Marca não existe na base de 2024 — comparação restrita a 2025 e 2026.")

marca_df = actual[actual["Ano"] >= 2025]
marca_agg = marca_df.groupby("Marca")["Valor"].sum().sort_values(ascending=False)
marca_agg = marca_agg[~marca_agg.index.isin(["Não disponível (2024)"])]

colC, colD = st.columns([1, 1])
with colC:
    tab_marca = pd.DataFrame({"Marca": marca_agg.index, "Gasto": marca_agg.values})
    tab_marca["% Part."] = tab_marca["Gasto"] / tab_marca["Gasto"].sum() * 100
    st.dataframe(
        tab_marca.set_index("Marca").style.format({"Gasto": "R$ {:,.0f}", "% Part.": "{:.1f}%"}),
        use_container_width=True,
    )
with colD:
    fig3 = px.pie(values=marca_agg.values, names=marca_agg.index, hole=0.5,
                   color_discrete_sequence=px.colors.sequential.Blues_r)
    fig3.update_layout(height=340, margin=dict(t=10, b=10, l=10, r=10), showlegend=True)
    st.plotly_chart(fig3, use_container_width=True)

# ------------------------------------------------------------------
# 7. Alertas de variação (duplo critério)
# ------------------------------------------------------------------
st.markdown('<div class="section-header">7 · ALERTAS DE VARIAÇÃO</div>', unsafe_allow_html=True)
st.caption("Entram no alerta apenas itens que ultrapassam os dois critérios: percentual E piso em R$.")

col_p, col_v = st.columns(2)
limite_pct = col_p.slider("Limite percentual (%)", 5, 50, 10)
limite_valor = col_v.number_input("Piso em R$", min_value=0, value=20000, step=5000)

alerta_tab = cc_tab.copy()
alerta_tab = alerta_tab[(alerta_tab["Var %"].abs() >= limite_pct) & (alerta_tab["Var R$"].abs() >= limite_valor)]
alerta_tab = alerta_tab.sort_values("Var R$", ascending=False)

if alerta_tab.empty:
    st.info("Nenhum Centro de Custo ultrapassa os dois critérios definidos.")
else:
    def cor_var(v):
        return f"color: {RED}; font-weight:700" if v > 0 else f"color: {GREEN}; font-weight:700"
    st.dataframe(
        alerta_tab.style.format({"Actual": "R$ {:,.0f}", "Forecast": "R$ {:,.0f}", "Var R$": "R$ {:,.0f}", "Var %": "{:+.1f}%"})
        .map(cor_var, subset=["Var R$"]),
        use_container_width=True,
    )

# ------------------------------------------------------------------
# 8. Evolução temporal
# ------------------------------------------------------------------
st.markdown('<div class="section-header">8 · EVOLUÇÃO TEMPORAL</div>', unsafe_allow_html=True)
st.caption("Actual por ano e trimestre — 2024, 2025, 2026 (parcial).")

evo_ano = df[df["Tipo"] == "Actual"].groupby("Ano")["Valor"].sum()
evo_q = df[df["Tipo"] == "Actual"].groupby(["Ano", "Trimestre"])["Valor"].sum().unstack(fill_value=0)

colE, colF = st.columns([1, 1.4])
with colE:
    st.dataframe(
        pd.DataFrame({"Total Actual": evo_ano}).style.format({"Total Actual": "R$ {:,.0f}"}),
        use_container_width=True,
    )
with colF:
    fig4 = go.Figure()
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        if q in evo_q.columns:
            fig4.add_bar(x=evo_q.index.astype(str), y=evo_q[q], name=q)
    fig4.update_layout(barmode="stack", height=320, margin=dict(t=10, b=10, l=10, r=10),
                        legend=dict(orientation="h", y=1.1), plot_bgcolor="white",
                        colorway=[NAVY, "#4C6EA8", "#9CA3AF", "#D6DEEC"])
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")
st.caption(
    "Dashboard de snapshot — não conectado à base viva. Para atualizar, gere um novo CSV da aba "
    "'Base Consolidada' no Excel e substitua o arquivo de dados deste app."
)
