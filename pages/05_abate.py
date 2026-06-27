import streamlit as st
import pandas as pd
from datetime import date
from utils.auth import require_auth
from utils.queries import (
    buscar_animal_por_brinco, inserir_abate,
    historico_pesagens,
)
from utils.db import fetch_one
from utils.calc import calcular_rendimento, calcular_gmp

require_auth()
st.title("🔪 Abate e Carcaça")

c1, _ = st.columns([2, 3])
brinco = c1.text_input("Brinco do animal (etapa: engorda)").strip().upper()

animal = None
if brinco:
    animal = buscar_animal_por_brinco(brinco)
    if not animal:
        st.warning("Animal não encontrado.")
    elif animal["etapa_atual"] != "engorda":
        st.warning(f"Animal está na etapa '{animal['etapa_atual']}', não na engorda.")
        animal = None
    else:
        st.info(f"**{animal['brinco']}** · {animal['raca_descricao']} · "
                f"Último peso: {animal.get('ultimo_peso') or '—'} kg")

if animal:
    # Busca custo sanitário acumulado
    custo_row = fetch_one(
        "SELECT custo_total_rs FROM pecuaria.vw_custo_acumulado_animal WHERE id_animal = %s",
        (animal["id"],)
    )
    custo_acumulado = float(custo_row["custo_total_rs"]) if custo_row and custo_row["custo_total_rs"] else 0.0

    # Busca pesagem de entrada na engorda para GMD e GMP
    pesagens = historico_pesagens(animal["id"])
    df_p = pd.DataFrame(pesagens) if pesagens else pd.DataFrame()
    peso_entrada_tip = 350.0
    dt_entrada_tip = None
    if not df_p.empty:
        tip_rows = df_p[df_p["etapa"] == "engorda"]
        if not tip_rows.empty:
            peso_entrada_tip = float(tip_rows.iloc[0]["peso_kg"])
            dt_entrada_tip   = tip_rows.iloc[0]["dt_pesagem"]

    with st.form("form_abate"):
        st.subheader("Dados de abate")
        c1, c2 = st.columns(2)
        dt_abate          = c1.date_input("Data do abate*", value=date.today())
        frigorifico       = c2.text_input("Frigorífico")

        c3, c4, c5 = st.columns(3)
        peso_vivo_final   = c3.number_input("Peso vivo final (kg)*",
                                             min_value=1.0, value=590.0, step=0.5)
        peso_carcaca      = c4.number_input("Peso carcaça (kg)*",
                                             min_value=1.0, value=330.0, step=0.5)
        receita_kg        = c5.number_input("Receita R$/kg carcaça*",
                                             min_value=0.0, value=12.0, step=0.10)

        obs = st.text_area("Observações", height=60)

        # Preview calculado
        rendimento     = calcular_rendimento(peso_carcaca, peso_vivo_final)
        receita_total  = round(peso_carcaca * receita_kg, 2)
        margem         = round(receita_total - custo_acumulado, 2)
        gmp            = calcular_gmp(peso_entrada_tip, peso_vivo_final)

        # GMD total
        gmd_total = None
        if dt_entrada_tip and not df_p.empty:
            primeira = df_p.iloc[0]
            dias_total = (dt_abate - pd.to_datetime(primeira["dt_pesagem"]).date()).days
            if dias_total > 0:
                gmd_total = round((peso_vivo_final - float(primeira["peso_kg"])) / dias_total, 3)

        st.markdown("---")
        st.markdown("**Preview — campos calculados**")
        pc1, pc2, pc3, pc4, pc5 = st.columns(5)
        pc1.metric("Rendimento",     f"{rendimento:.2f}%")
        pc2.metric("Receita total",  f"R$ {receita_total:.2f}")
        pc3.metric("Custo acumulado",f"R$ {custo_acumulado:.2f}")
        pc4.metric("Margem",         f"R$ {margem:.2f}",
                   delta=f"{'▲' if margem >= 0 else '▼'}")
        pc5.metric("GMP",            f"{gmp:.1f} kg")

        if st.form_submit_button("Registrar abate", type="primary"):
            try:
                r = inserir_abate(
                    animal["id"], dt_abate, peso_vivo_final, peso_carcaca,
                    gmd_total, gmp, receita_kg, receita_total,
                    custo_acumulado, margem, frigorifico, obs
                )
                st.success(
                    f"Abate registrado. Rendimento: {r['rendimento_pct']:.2f}% · "
                    f"Margem: R$ {margem:.2f}"
                )
            except Exception as e:
                st.error(f"Erro: {e}")