import streamlit as st


def check_auth() -> bool:
    return st.session_state.get("autenticado", False)


def login_page():
    st.title("🐄 SIGPEC — Santa Vergínia")
    st.caption("Sistema Integrado de Gestão Pecuária · Acesso restrito")
    st.divider()

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        pin = st.text_input("PIN de acesso", type="password", key="pin_input")
        if st.button("Entrar", use_container_width=True, type="primary"):
            if pin == st.secrets.get("PIN_ACESSO", "SV2027"):
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("PIN incorreto.")


def logout():
    st.session_state["autenticado"] = False
    st.rerun()


def require_auth():
    if not check_auth():
        login_page()
        st.stop()
