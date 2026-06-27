import streamlit as st
from utils.auth import require_auth, logout

st.set_page_config(
    page_title="SIGPEC — Santa Vergínia",
    page_icon="🐄",
    layout="wide",
)

require_auth()

with st.sidebar:
    st.markdown("**SIGPEC — Santa Vergínia**")
    st.caption("Gestão Pecuária")
    st.divider()
    if st.button("Sair", use_container_width=True):
        logout()

st.title("🐄 SIGPEC — Santa Vergínia")
st.caption("Sistema Integrado de Gestão Pecuária · Bataguassu-MS")
st.info("App carregado com sucesso. Navegue pelo menu lateral.")
