import streamlit as st
import pandas as pd
from utils.auth import require_auth
from utils.queries import (
    listar_lotes, inserir_lote,
    buscar_animal_por_brinco, inserir_animal, listar_racas,
    ficha_animal, historico_pesagens, historico_manejo_animal,
)

require_auth()
st.title("📋 Cadastro")

tab_lotes, tab_animais, tab_ficha = st.tabs(["Lotes", "Animais", "Ficha do Animal"])

# ── LOTES ──────────────────────────────────────────────────────────────────
with tab_lotes:
    st.subheader("Lotes ativos")
    lotes = listar_lotes()
    if lotes:
        st.dataframe(pd.DataFrame(lotes), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lote cadastrado.")

    st.markdown("---")
    st.subheader("Novo lote")
    with st.form("form_lote"):
        c1, c2, c3 = st.columns(3)
        codigo       = c1.text_input("Código*", placeholder="MAT-2027-001")
        tipo         = c2.selectbox("Tipo*", ["maternidade", "engorda", "recria"])
        capacidade   = c3.number_input("Capacidade máx.", min_value=1, value=60)
        c4, c5       = st.columns(2)
        dt_formacao  = c4.date_input("Data formação*")
        setor        = c5.text_input("Fazenda / Setor")
        responsavel  = st.text_input("Responsável")
        obs          = st.text_area("Observações", height=80)
        if st.form_submit_button("Salvar lote", type="primary"):
            if not codigo:
                st.error("Código obrigatório.")
            else:
                try:
                    r = inserir_lote(codigo, tipo, capacidade, dt_formacao, setor, responsavel, obs)
                    st.success(f"Lote {r['codigo']} criado (id {r['id']}).")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

# ── ANIMAIS ────────────────────────────────────────────────────────────────
with tab_animais:
    st.subheader("Buscar animal")
    b_col, _ = st.columns([2, 3])
    brinco_busca = b_col.text_input("Brinco", key="busca_brinco")
    if brinco_busca:
        animal = buscar_animal_por_brinco(brinco_busca.strip().upper())
        if animal:
            st.success(f"Animal encontrado: {animal['brinco']} · {animal['raca_descricao']} · {animal['etapa_atual']}")
        else:
            st.warning("Animal não encontrado.")

    st.markdown("---")
    st.subheader("Cadastrar animal")
    racas = listar_racas()
    raca_map = {r["descricao"]: r["id"] for r in racas}
    lotes_mat = listar_lotes("maternidade")
    lote_map = {l["codigo"]: l["id"] for l in lotes_mat}

    with st.form("form_animal"):
        c1, c2, c3 = st.columns(3)
        brinco       = c1.text_input("Brinco*").strip().upper()
        sexo         = c2.selectbox("Sexo*", ["M", "F"])
        raca_sel     = c3.selectbox("Raça*", list(raca_map.keys()))
        c4, c5, c6  = st.columns(3)
        dt_nasc      = c4.date_input("Data nascimento*")
        peso_nasc    = c5.number_input("Peso nasc. (kg)", min_value=0.0, value=30.0, step=0.5)
        brinco_mae   = c6.text_input("Brinco da mãe").strip().upper()
        c7, _        = st.columns([2, 2])
        lote_sel     = c7.selectbox("Lote origem", ["— nenhum —"] + list(lote_map.keys()))
        obs          = st.text_area("Observações", height=60)

        if st.form_submit_button("Cadastrar animal", type="primary"):
            if not brinco:
                st.error("Brinco obrigatório.")
            else:
                id_lote = lote_map.get(lote_sel)
                try:
                    r = inserir_animal(
                        brinco, dt_nasc, sexo,
                        raca_map[raca_sel], id_lote,
                        brinco_mae or None, peso_nasc, obs
                    )
                    st.success(f"Animal {r['brinco']} cadastrado (id {r['id']}).")
                except Exception as e:
                    st.error(f"Erro: {e}")

# ── FICHA ──────────────────────────────────────────────────────────────────
with tab_ficha:
    st.subheader("Ficha completa do animal")
    f_col, _ = st.columns([2, 3])
    brinco_ficha = f_col.text_input("Brinco", key="ficha_brinco")

    if brinco_ficha:
        animal = ficha_animal(brinco_ficha.strip().upper())
        if not animal:
            st.warning("Animal não encontrado.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Brinco",          animal["brinco"])
            c2.metric("Raça",            animal["raca"])
            c3.metric("Etapa atual",     animal["etapa_atual"].capitalize())
            c4.metric("Último peso",     f"{animal['ultimo_peso'] or '—'} kg")

            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Nascimento",      str(animal["dt_nascimento"]))
            c6.metric("Sexo",            animal["sexo"])
            c7.metric("GMD atual",       f"{animal['gmd_calculado'] or '—'} kg/dia")
            c8.metric("Custo sanitário", f"R$ {animal['custo_sanitario_total'] or 0:.2f}")

            st.markdown("---")
            col_p, col_m = st.columns(2)

            with col_p:
                st.markdown("**Histórico de pesagens**")
                id_animal = animal["id"]
                pesagens = historico_pesagens(id_animal)
                if pesagens:
                    df_p = pd.DataFrame(pesagens)
                    st.dataframe(df_p, use_container_width=True, hide_index=True)
                else:
                    st.info("Sem pesagens registradas.")

            with col_m:
                st.markdown("**Histórico de manejo**")
                manejos = historico_manejo_animal(id_animal)
                if manejos:
                    df_m = pd.DataFrame(manejos)
                    st.dataframe(df_m, use_container_width=True, hide_index=True)
                else:
                    st.info("Sem manejos registrados.")

