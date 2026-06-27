import streamlit as st
import pandas as pd
from datetime import date
from utils.auth import require_auth
from utils.queries import (
    buscar_animal_por_brinco, listar_operacoes,
    componentes_operacao, inserir_manejo,
    historico_manejo_animal, listar_lotes,
)
from utils.db import fetch_all

require_auth()
st.title("💉 Manejo Sanitário")

tab_camp, tab_curativo, tab_hist = st.tabs(["Campanhas", "Tratamento Curativo", "Histórico"])

# ── CAMPANHAS ──────────────────────────────────────────────────────────────
with tab_camp:
    st.subheader("Registrar campanha")
    operacoes = listar_operacoes()
    op_map = {f"Op.{o['numero']} — {o['descricao']} (R${o['custo_base_rs']:.2f}/cab)": o
              for o in operacoes if o["etapa_ciclo"] != "tropa"}

    with st.form("form_campanha"):
        op_sel = st.selectbox("Operação*", list(op_map.keys()))
        op = op_map[op_sel]

        # Mostra componentes da operação selecionada
        componentes = componentes_operacao(op["id"])
        if componentes:
            df_comp = pd.DataFrame(componentes)
            st.caption("Componentes desta operação:")
            st.dataframe(df_comp[["nome", "dose_padrao", "unidade", "custo_total"]],
                         use_container_width=True, hide_index=True)

        c1, c2, c3 = st.columns(3)
        dt_aplicacao = c1.date_input("Data aplicação*", value=date.today())
        qtd_animais  = c2.number_input("Qtd. animais tratados*", min_value=1, value=60)
        responsavel  = c3.text_input("Responsável")

        # Brincos individuais ou lote
        modo = st.radio("Aplicar em", ["Lote inteiro", "Animais específicos (brincos)"],
                        horizontal=True)
        brincos_input = ""
        lote_sel = None
        if modo == "Lote inteiro":
            lotes = listar_lotes()
            lote_map = {l["codigo"]: l["id"] for l in lotes}
            lote_sel = st.selectbox("Lote", list(lote_map.keys()))
        else:
            brincos_input = st.text_area("Brincos (um por linha)")

        custo_unitario = op["custo_base_rs"] or 0
        custo_total    = round(custo_unitario * qtd_animais, 2)
        st.info(f"Custo estimado: R$ {custo_unitario:.2f}/cab × {qtd_animais} = **R$ {custo_total:.2f}**")
        obs = st.text_area("Observações", height=60)

        if st.form_submit_button("Registrar campanha", type="primary"):
            brincos = []
            if modo == "Animais específicos (brincos)" and brincos_input.strip():
                brincos = [b.strip().upper() for b in brincos_input.strip().splitlines() if b.strip()]
            elif modo == "Lote inteiro" and lote_sel:
                lote_id = lote_map[lote_sel]
                rows = fetch_all(
                    "SELECT id, brinco FROM dim_animal WHERE id_lote_origem = %s AND ativo",
                    (lote_id,)
                )
                brincos = [r["brinco"] for r in rows]

            if not brincos:
                st.error("Informe os brincos ou selecione um lote com animais.")
            else:
                ok, falhas = 0, []
                for br in brincos:
                    animal = buscar_animal_por_brinco(br)
                    if not animal:
                        falhas.append(f"{br}: não encontrado")
                        continue
                    try:
                        inserir_manejo(animal["id"], op["id"], dt_aplicacao,
                                       "campanha", custo_unitario,
                                       None, responsavel, obs)
                        ok += 1
                    except Exception as ex:
                        falhas.append(f"{br}: {ex}")
                st.success(f"Campanha registrada em {ok} animais.")
                if falhas:
                    for f in falhas:
                        st.caption(f"⚠️ {f}")

# ── CURATIVO ───────────────────────────────────────────────────────────────
with tab_curativo:
    st.subheader("Tratamento curativo individual")
    c1, _ = st.columns([2, 3])
    brinco_c = c1.text_input("Brinco do animal").strip().upper()
    animal_c = None

    if brinco_c:
        animal_c = buscar_animal_por_brinco(brinco_c)
        if not animal_c:
            st.warning("Animal não encontrado.")
        else:
            st.info(f"**{animal_c['brinco']}** · {animal_c['raca_descricao']} · {animal_c['etapa_atual']}")

    if animal_c:
        with st.form("form_curativo"):
            c1, c2 = st.columns(2)
            dt_aplic    = c1.date_input("Data tratamento*", value=date.today())
            responsavel = c2.text_input("Responsável (médico vet.)")
            receituario = st.text_area("Receituário / Diagnóstico*", height=100)
            c3, c4      = st.columns(2)
            custo_rs    = c3.number_input("Custo R$/cabeça", min_value=0.0, value=12.0, step=0.5)
            obs         = c4.text_area("Observações", height=68)

            # Op.16 = Tratamento Curativo
            op_curativo = next((o for o in listar_operacoes() if o["numero"] == 16), None)

            if st.form_submit_button("Registrar tratamento", type="primary"):
                if not receituario.strip():
                    st.error("Receituário obrigatório para tratamento curativo.")
                elif not op_curativo:
                    st.error("Operação 16 (Tratamento Curativo) não encontrada no banco.")
                else:
                    try:
                        inserir_manejo(animal_c["id"], op_curativo["id"], dt_aplic,
                                       "curativo", custo_rs, receituario, responsavel, obs)
                        st.success("Tratamento registrado.")
                    except Exception as e:
                        st.error(f"Erro: {e}")

# ── HISTÓRICO ──────────────────────────────────────────────────────────────
with tab_hist:
    st.subheader("Histórico de manejo")
    c1, c2 = st.columns([2, 2])
    brinco_h = c1.text_input("Brinco (opcional)", key="hist_man_brinco").strip().upper()

    if brinco_h:
        animal_h = buscar_animal_por_brinco(brinco_h)
        if not animal_h:
            st.warning("Animal não encontrado.")
        else:
            manejos = historico_manejo_animal(animal_h["id"])
            if manejos:
                df_m = pd.DataFrame(manejos)
                total = df_m["custo_total_rs"].sum()
                st.metric("Custo sanitário acumulado", f"R$ {total:.2f}")
                st.dataframe(df_m, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum manejo registrado para este animal.")
