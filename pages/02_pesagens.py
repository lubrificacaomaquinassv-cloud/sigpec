import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from utils.auth import require_auth
from utils.queries import buscar_animal_por_brinco, inserir_pesagem, historico_pesagens

require_auth()
st.title("⚖️ Pesagens")

tab_individual, tab_lote, tab_historico = st.tabs(["Individual", "Em lote (CSV)", "Histórico"])

ETAPAS = ["nascimento", "cria", "recria", "desmama", "engorda", "abate"]

# ── INDIVIDUAL ─────────────────────────────────────────────────────────────
with tab_individual:
    c1, _ = st.columns([2, 3])
    brinco = c1.text_input("Brinco do animal").strip().upper()

    animal = None
    if brinco:
        animal = buscar_animal_por_brinco(brinco)
        if not animal:
            st.warning("Animal não encontrado.")
        else:
            st.info(f"**{animal['brinco']}** · {animal['raca_descricao']} · etapa: {animal['etapa_atual']}")

    if animal:
        with st.form("form_pesagem"):
            c1, c2, c3 = st.columns(3)
            dt_pesagem  = c1.date_input("Data pesagem*", value=date.today())
            peso_kg     = c2.number_input("Peso (kg)*", min_value=1.0, max_value=1000.0,
                                          value=float(animal.get("ultimo_peso") or 30), step=0.5)
            etapa       = c3.selectbox("Etapa*", ETAPAS,
                                       index=ETAPAS.index(animal["etapa_atual"])
                                       if animal["etapa_atual"] in ETAPAS else 0)
            responsavel = st.text_input("Responsável")
            obs         = st.text_area("Observações", height=60)

            # Alerta peso TIP
            if etapa == "engorda" and peso_kg < 350:
                st.warning(f"⚠️ Peso {peso_kg:.1f} kg abaixo do mínimo de entrada TIP (350 kg).")

            if st.form_submit_button("Registrar pesagem", type="primary"):
                try:
                    r = inserir_pesagem(animal["id"], dt_pesagem, peso_kg,
                                        etapa, responsavel, obs)
                    gmd = r.get("gmd_calculado")
                    dias = r.get("dias_periodo")
                    if gmd is not None:
                        st.success(f"Pesagem salva. GMD calculado: **{gmd:.3f} kg/dia** ({dias} dias)")
                    else:
                        st.success("Pesagem salva (primeira pesagem desta etapa — GMD será calculado na próxima).")
                except Exception as e:
                    st.error(f"Erro: {e}")

# ── LOTE (CSV) ─────────────────────────────────────────────────────────────
with tab_lote:
    st.markdown("""
    Faça upload de um CSV com as colunas:
    `brinco`, `dt_pesagem` (AAAA-MM-DD), `peso_kg`, `etapa`, `responsavel`
    """)
    arquivo = st.file_uploader("CSV de pesagens", type=["csv"])

    if arquivo:
        df = pd.read_csv(arquivo, sep=None, engine="python")
        df.columns = df.columns.str.strip().str.lower()
        st.dataframe(df.head(10), use_container_width=True)

        erros = []
        for col in ["brinco", "dt_pesagem", "peso_kg", "etapa"]:
            if col not in df.columns:
                erros.append(f"Coluna faltando: {col}")
        if erros:
            for e in erros:
                st.error(e)
        else:
            if st.button("Importar pesagens", type="primary"):
                ok, falhas = 0, []
                for _, row in df.iterrows():
                    try:
                        animal = buscar_animal_por_brinco(str(row["brinco"]).strip().upper())
                        if not animal:
                            falhas.append(f"{row['brinco']}: animal não encontrado")
                            continue
                        inserir_pesagem(
                            animal["id"],
                            pd.to_datetime(row["dt_pesagem"]).date(),
                            float(row["peso_kg"]),
                            str(row["etapa"]).strip(),
                            str(row.get("responsavel", "")) if pd.notna(row.get("responsavel")) else None,
                            None
                        )
                        ok += 1
                    except Exception as ex:
                        falhas.append(f"{row['brinco']}: {ex}")
                st.success(f"{ok} pesagens importadas.")
                if falhas:
                    st.warning("Falhas:")
                    for f in falhas:
                        st.caption(f)

# ── HISTÓRICO ──────────────────────────────────────────────────────────────
with tab_historico:
    c1, _ = st.columns([2, 3])
    brinco_h = c1.text_input("Brinco", key="hist_brinco").strip().upper()

    if brinco_h:
        animal_h = buscar_animal_por_brinco(brinco_h)
        if not animal_h:
            st.warning("Animal não encontrado.")
        else:
            pesagens = historico_pesagens(animal_h["id"])
            if not pesagens:
                st.info("Sem pesagens registradas para este animal.")
            else:
                df_h = pd.DataFrame(pesagens)
                st.dataframe(df_h, use_container_width=True, hide_index=True)

                # Gráfico evolução de peso
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_h["dt_pesagem"], y=df_h["peso_kg"],
                    mode="lines+markers", name="Peso real",
                    line=dict(color="#4caf50", width=2),
                    marker=dict(size=7)
                ))
                # Linha de referência TIP
                fig.add_hline(y=350, line_dash="dot", line_color="#ff9800",
                              annotation_text="Entrada TIP (350 kg)")
                fig.add_hline(y=590, line_dash="dot", line_color="#f44336",
                              annotation_text="Meta abate (590 kg)")
                fig.update_layout(
                    title=f"Curva de peso — {brinco_h}",
                    xaxis_title="Data", yaxis_title="Peso (kg)",
                    template="plotly_dark", height=380
                )
                st.plotly_chart(fig, use_container_width=True)
