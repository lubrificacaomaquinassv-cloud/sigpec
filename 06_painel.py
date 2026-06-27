import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
from utils.auth import require_auth
from utils.queries import (
    resumo_rebanho, projecao_abate, gargalos_engorda,
    indicadores_abate, orcamento_realizado,
)
from utils.db import fetch_all

require_auth()
st.title("📊 Painel Analítico")

# ── KPI CARDS ──────────────────────────────────────────────────────────────
resumo = resumo_rebanho()
projecao = projecao_abate()
gargalos = gargalos_engorda()

df_res = pd.DataFrame(resumo) if resumo else pd.DataFrame()

st.subheader("Rebanho")
etapas = ["nascimento", "cria", "recria", "desmama", "engorda", "abate"]
cols = st.columns(len(etapas))
for i, etapa in enumerate(etapas):
    if not df_res.empty:
        sub = df_res[df_res["etapa_atual"] == etapa]
        total = int(sub["total_animais"].sum()) if not sub.empty else 0
        gmd_m = sub["gmd_medio"].mean() if not sub.empty and "gmd_medio" in sub else None
        delta = f"GMD {gmd_m:.3f}" if gmd_m else None
    else:
        total, delta = 0, None
    cols[i].metric(etapa.capitalize(), total, delta=delta)

st.markdown("---")

# ── LINHA 2: PROJEÇÃO + GARGALOS ───────────────────────────────────────────
col_proj, col_garg = st.columns(2)

with col_proj:
    st.subheader("🗓️ Projeção de abate")
    if projecao:
        df_proj = pd.DataFrame(projecao)
        df_proj = df_proj[df_proj["gmd_atual"].notna()].copy()
        df_proj["dias_restantes"] = pd.to_numeric(df_proj["dias_restantes"], errors="coerce")
        df_proj = df_proj.sort_values("dias_restantes")
        st.dataframe(
            df_proj[["brinco", "raca", "peso_atual_kg", "gmd_atual",
                      "kg_faltando", "dt_projecao_abate", "dias_restantes"]],
            use_container_width=True, hide_index=True,
            column_config={
                "gmd_atual":      st.column_config.NumberColumn("GMD kg/dia", format="%.3f"),
                "peso_atual_kg":  st.column_config.NumberColumn("Peso atual", format="%.1f"),
                "kg_faltando":    st.column_config.NumberColumn("Faltam (kg)", format="%.1f"),
                "dias_restantes": st.column_config.NumberColumn("Dias"),
            }
        )
    else:
        st.info("Nenhum animal em engorda com dados de projeção.")

with col_garg:
    st.subheader("⚠️ Gargalos — GMD crítico na engorda")
    if gargalos:
        df_g = pd.DataFrame(gargalos)
        st.dataframe(
            df_g,
            use_container_width=True, hide_index=True,
            column_config={
                "gmd_calculado": st.column_config.NumberColumn("GMD kg/dia", format="%.3f"),
                "peso_atual":    st.column_config.NumberColumn("Peso atual", format="%.1f"),
                "kg_faltando":   st.column_config.NumberColumn("Faltam (kg)", format="%.1f"),
            }
        )
    else:
        st.success("✅ Nenhum animal com GMD crítico.")

st.markdown("---")

# ── GMD POR ETAPA × RAÇA ───────────────────────────────────────────────────
st.subheader("GMD médio por etapa e raça")
if not df_res.empty and "gmd_medio" in df_res.columns:
    df_gmd = df_res[df_res["gmd_medio"].notna()].copy()
    if not df_gmd.empty:
        fig_gmd = px.bar(
            df_gmd, x="etapa_atual", y="gmd_medio", color="raca",
            barmode="group", text_auto=".3f",
            labels={"etapa_atual": "Etapa", "gmd_medio": "GMD (kg/dia)", "raca": "Raça"},
            color_discrete_map={"NEL": "#4caf50", "CRZ": "#ff9800",
                                 "ANG": "#2196f3", "SIM": "#9c27b0"},
            template="plotly_dark"
        )
        fig_gmd.update_layout(height=340, legend_title="Raça")
        st.plotly_chart(fig_gmd, use_container_width=True)
    else:
        st.info("Sem dados de GMD por etapa ainda.")
else:
    st.info("Sem dados de resumo de rebanho ainda.")

st.markdown("---")

# ── CUSTO ACUMULADO POR FASE ───────────────────────────────────────────────
st.subheader("Custo sanitário médio por fase")
custo_rows = fetch_all("""
    SELECT
        ROUND(AVG(custo_nascimento_rs), 2) AS nascimento,
        ROUND(AVG(custo_cria_recria_rs), 2) AS cria_recria,
        ROUND(AVG(custo_desmama_rs), 2) AS desmama,
        ROUND(AVG(custo_engorda_rs), 2) AS engorda,
        ROUND(AVG(custo_curativo_rs), 2) AS curativo
    FROM pecuaria.vw_custo_acumulado_animal
""")
if custo_rows and any(v for v in custo_rows[0].values() if v):
    row = custo_rows[0]
    fases = list(row.keys())
    valores = [float(row[f] or 0) for f in fases]
    fig_custo = go.Figure(go.Bar(
        x=fases, y=valores, text=[f"R$ {v:.2f}" for v in valores],
        textposition="outside",
        marker_color=["#4caf50", "#8bc34a", "#ff9800", "#f44336", "#e91e63"]
    ))
    fig_custo.update_layout(
        title="Custo sanitário médio R$/cabeça por fase",
        yaxis_title="R$/cab", template="plotly_dark", height=340
    )
    st.plotly_chart(fig_custo, use_container_width=True)
else:
    st.info("Sem dados de custo acumulado ainda.")

st.markdown("---")

# ── REALIZADO VS ORÇADO ────────────────────────────────────────────────────
st.subheader("Realizado vs Orçado mensal")
ano_sel = st.selectbox("Ano", [date.today().year, date.today().year - 1],
                        key="ano_painel")
realizado = orcamento_realizado(ano_sel)
ORCAMENTO_MENSAL = 917155 / 12

if realizado:
    df_real = pd.DataFrame(realizado)
    df_mensal = df_real.groupby("mes")["custo_realizado_rs"].sum().reset_index()
    df_mensal.columns = ["mes", "realizado"]
    df_mensal["orcado"] = round(ORCAMENTO_MENSAL, 2)

    fig_orc = go.Figure()
    fig_orc.add_trace(go.Bar(
        x=df_mensal["mes"], y=df_mensal["realizado"],
        name="Realizado", marker_color="#4caf50"
    ))
    fig_orc.add_trace(go.Scatter(
        x=df_mensal["mes"], y=df_mensal["orcado"],
        name="Orçado mensal", mode="lines+markers",
        line=dict(color="#ff9800", dash="dot", width=2)
    ))
    fig_orc.update_layout(
        xaxis=dict(tickmode="array", tickvals=list(range(1, 13)),
                   ticktext=["Jan","Fev","Mar","Abr","Mai","Jun",
                              "Jul","Ago","Set","Out","Nov","Dez"]),
        yaxis_title="R$", template="plotly_dark", height=360,
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_orc, use_container_width=True)
else:
    st.info(f"Sem dados de manejo registrados em {ano_sel}.")

st.markdown("---")

# ── INDICADORES DE ABATE ───────────────────────────────────────────────────
st.subheader("Indicadores de abate")
ind_abate = indicadores_abate()
if ind_abate:
    df_ia = pd.DataFrame(ind_abate)
    st.dataframe(
        df_ia,
        use_container_width=True, hide_index=True,
        column_config={
            "mes_abate":           st.column_config.DateColumn("Mês"),
            "rendimento_medio_pct":st.column_config.NumberColumn("Rendimento %", format="%.2f"),
            "gmd_total_medio":     st.column_config.NumberColumn("GMD total", format="%.3f"),
            "gmp_medio_kg":        st.column_config.NumberColumn("GMP (kg)", format="%.1f"),
            "margem_media_rs":     st.column_config.NumberColumn("Margem média R$", format="%.2f"),
            "receita_total_rs":    st.column_config.NumberColumn("Receita total R$", format="%.2f"),
        }
    )
else:
    st.info("Sem registros de abate ainda.")
