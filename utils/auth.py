import streamlit as st

st.set_page_config(
    page_title="SIGPEC — Santa Vergínia",
    page_icon="🐄",
    layout="wide",
)

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🐄 SIGPEC — Santa Vergínia")
    st.caption("Acesso restrito · Gestão Pecuária")
    st.divider()
    pin = st.text_input("PIN de acesso", type="password", key="pin_input")
    if st.button("Entrar", type="primary"):
        if pin == st.secrets.get("PIN_ACESSO", "SV2027"):
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("PIN incorreto.")
    st.stop()

with st.sidebar:
    st.markdown("**SIGPEC — Santa Vergínia**")
    st.caption("Gestão Pecuária")
    st.divider()
    if st.button("Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

st.title("🐄 SIGPEC — Santa Vergínia")
st.caption("Sistema Integrado de Gestão Pecuária · Bataguassu-MS")
st.success("✅ App carregado.")
