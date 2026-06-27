import streamlit as st
from utils.auth import require_auth, logout

st.set_page_config(
    page_title="SIGPEC — Santa Vergínia",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Tema escuro customizado ────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0a0f0a; }
[data-testid="stSidebar"] .stMarkdown p { color: #c8d8c0; font-size: 0.78rem; }
.block-container { padding-top: 1.5rem; }
div[data-testid="metric-container"] {
    background: #111a11;
    border: 1px solid #2a3d2a;
    border-radius: 8px;
    padding: 0.8rem 1rem;
}
.stButton > button[kind="primary"] {
    background-color: #2e7d32;
    border: none;
}
.stButton > button[kind="primary"]:hover { background-color: #1b5e20; }
</style>
""", unsafe_allow_html=True)

require_auth()

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    try:
        st.image("assets/logo_sv.png", width=120)
    except Exception:
        st.markdown("### 🐄 SIGPEC")

    st.markdown("**SIGPEC — Santa Vergínia**")
    st.caption("Sistema Integrado de Gestão Pecuária")
    st.markdown("---")

    st.page_link("pages/01_cadastro.py",   label="📋 Cadastro",          icon="📋")
    st.page_link("pages/02_pesagens.py",   label="⚖️ Pesagens",          icon="⚖️")
    st.page_link("pages/03_manejo.py",     label="💉 Manejo Sanitário",  icon="💉")
    st.page_link("pages/04_insumos.py",    label="🧪 Insumos",           icon="🧪")
    st.page_link("pages/05_abate.py",      label="🔪 Abate",             icon="🔪")
    st.page_link("pages/06_painel.py",     label="📊 Painel",            icon="📊")

    st.markdown("---")
    if st.button("Sair", use_container_width=True):
        logout()

# ── Home ───────────────────────────────────────────────────────────────────
st.title("🐄 SIGPEC — Santa Vergínia")
st.caption("Sistema Integrado de Gestão Pecuária · Bataguassu-MS")
st.markdown("---")

from utils.queries import resumo_rebanho, projecao_abate, gargalos_engorda
import pandas as pd

try:
    resumo = resumo_rebanho()
    projecao = projecao_abate()
    gargalos = gargalos_engorda()

    # ── KPIs por etapa ─────────────────────────────────────────────────────
    if resumo:
        df_res = pd.DataFrame(resumo)
        total_geral = df_res["total_animais"].sum()
        etapas_ordem = ["nascimento", "cria", "recria", "desmama", "engorda", "abate"]

        st.subheader("Rebanho atual")
        cols = st.columns(len(etapas_ordem))
        for i, etapa in enumerate(etapas_ordem):
            sub = df_res[df_res["etapa_atual"] == etapa]
            total = int(sub["total_animais"].sum()) if not sub.empty else 0
            cols[i].metric(etapa.capitalize(), total)

        st.markdown("---")

    # ── Alertas ────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("⚠️ Gargalos na engorda")
        if gargalos:
            df_g = pd.DataFrame(gargalos)
            df_g["gmd_calculado"] = df_g["gmd_calculado"].apply(
                lambda x: f"{x:.3f}" if x else "—"
            )
            st.dataframe(df_g, use_container_width=True, hide_index=True)
        else:
            st.success("Nenhum animal com GMD crítico na engorda.")

    with col_b:
        st.subheader("🗓️ Próximos ao abate (30 dias)")
        if projecao:
            df_p = pd.DataFrame(projecao)
            df_p = df_p[df_p["dias_restantes"].notna()]
            df_p = df_p[df_p["dias_restantes"] <= 30].copy()
            if not df_p.empty:
                st.dataframe(
                    df_p[["brinco", "raca", "peso_atual_kg", "gmd_atual",
                           "dt_projecao_abate", "dias_restantes"]],
                    use_container_width=True, hide_index=True
                )
            else:
                st.info("Nenhum animal com abate previsto nos próximos 30 dias.")

except Exception as e:
    st.info("Configure a conexão com o banco em `.streamlit/secrets.toml` para visualizar os dados.")
    st.caption(str(e))
