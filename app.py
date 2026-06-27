import streamlit as st

st.set_page_config(
    page_title="SIGPEC — Santa Vergínia",
    page_icon="🐄",
    layout="wide",
)

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-image: url("https://images.unsplash.com/photo-1570042225831-d98fa7577f1e?w=1600&q=80");
        background-size: cover;
        background-position: center;
    }
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(5, 20, 5, 0.72);
        z-index: 0;
    }
    [data-testid="stAppViewContainer"] > * { position: relative; z-index: 1; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { display: none; }
    .login-box {
        max-width: 420px;
        padding: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        try:
            st.image("assets/logo_sv.png", width=150)
        except:
            pass
    with col2:
        st.markdown("## SIGPEC — Santa Vergínia")
        st.caption("Sistema Integrado de Gestão Pecuária")
        st.markdown("[@fazendasantaverginia](https://instagram.com/fazendasantaverginia)")

    st.markdown("---")
    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        pin = st.text_input("PIN de acesso", type="password", key="pin_input")
        if st.button("Entrar", type="primary", use_container_width=True):
            if pin == st.secrets.get("PIN_ACESSO", "SV2027"):
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("PIN incorreto.")
    st.stop()

# App autenticado
with st.sidebar:
    try:
        st.image("assets/logo_sv.png", width=120)
    except:
        st.markdown("### 🐄 SIGPEC")
    st.markdown("**SIGPEC — Santa Vergínia**")
    st.caption("Gestão Pecuária")
    st.divider()
    if st.button("Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

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
