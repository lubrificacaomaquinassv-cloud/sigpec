import streamlit as st
from utils.auth import require_auth, logout

st.set_page_config(
    page_title="SIGPEC — Santa Vergínia",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_auth()

with st.sidebar:
    try:
        st.image("assets/logo_sv.png", width=120)
    except Exception:
        st.markdown("### 🐄 SIGPEC")
    st.markdown("**SIGPEC — Santa Vergínia**")
    st.caption("Sistema Integrado de Gestão Pecuária")
    st.divider()
    if st.button("Sair", use_container_width=True):
        logout()

st.title("🐄 SIGPEC — Santa Vergínia")
st.caption("Sistema Integrado de Gestão Pecuária · Bataguassu-MS")
st.divider()

from utils.queries import resumo_rebanho, projecao_abate, gargalos_engorda
import pandas as pd

try:
    resumo   = resumo_rebanho()
    projecao = projecao_abate()
    gargalos = gargalos_engorda()

    if resumo:
        df_res = pd.DataFrame(resumo)
        etapas = ["nascimento", "cria", "recria", "desmama", "engorda", "abate"]
        st.subheader("Rebanho atual")
        cols = st.columns(len(etapas))
        for i, etapa in enumerate(etapas):
            sub   = df_res[df_res["etapa_atual"] == etapa]
            total = int(sub["total_animais"].sum()) if not sub.empty else 0
            cols[i].metric(etapa.capitalize(), total)
        st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("⚠️ Gargalos na engorda")
        if gargalos:
            st.dataframe(pd.DataFrame(gargalos), use_container_width=True, hide_index=True)
        else:
            st.success("Nenhum animal com GMD crítico.")

    with col_b:
        st.subheader("🗓️ Próximos ao abate (30 dias)")
        if projecao:
            df_p = pd.DataFrame(projecao)
            df_p = df_p[df_p["dias_restantes"].notna()]
            df_p = df_p[df_p["dias_restantes"] <= 30].copy()
            if not df_p.empty:
                st.dataframe(
                    df_p[["brinco","raca","peso_atual_kg","gmd_atual",
                          "dt_projecao_abate","dias_restantes"]],
                    use_container_width=True, hide_index=True
                )
            else:
                st.info("Nenhum animal com abate previsto nos próximos 30 dias.")

except Exception as e:
    st.info("Configure DATABASE_URL e PIN_ACESSO nos Secrets do Streamlit Cloud.")
    st.caption(str(e))
