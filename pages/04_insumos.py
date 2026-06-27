import streamlit as st
import pandas as pd
from utils.auth import require_auth
from utils.queries import listar_insumos, atualizar_insumo
from utils.db import execute

require_auth()
st.title("🧪 Insumos")

insumos = listar_insumos()
df = pd.DataFrame(insumos)

st.subheader("Tabela de insumos")
st.caption("Edite valor_atual ou índice_correcao e clique em Salvar alterações.")

if not df.empty:
    df_edit = st.data_editor(
        df[["id", "nome", "unidade", "valor_atual", "indice_correcao",
            "valor_corrigido", "dt_revisao"]],
        use_container_width=True,
        hide_index=True,
        disabled=["id", "nome", "unidade", "valor_corrigido", "dt_revisao"],
        column_config={
            "valor_atual":     st.column_config.NumberColumn("Valor atual (R$)", format="%.4f"),
            "indice_correcao": st.column_config.NumberColumn("Índice correção", format="%.4f"),
            "valor_corrigido": st.column_config.NumberColumn("Valor corrigido (R$)", format="%.4f"),
        }
    )

    if st.button("Salvar alterações", type="primary"):
        erros = []
        for _, row in df_edit.iterrows():
            try:
                atualizar_insumo(int(row["id"]), float(row["valor_atual"]),
                                 float(row["indice_correcao"]))
            except Exception as e:
                erros.append(f"ID {row['id']}: {e}")
        if erros:
            for e in erros:
                st.error(e)
        else:
            st.success("Insumos atualizados. Os custos das operações foram recalculados automaticamente.")
            st.rerun()

st.markdown("---")
st.subheader("Correção global de índice")
st.caption("Aplica o mesmo índice de correção para todos os insumos de uma vez.")

with st.form("form_correcao_global"):
    novo_indice = st.number_input("Novo índice (ex: 0.17 = 17%)", min_value=0.0,
                                   max_value=2.0, value=0.17, step=0.01, format="%.4f")
    confirmacao = st.checkbox("Confirmo que quero atualizar o índice de TODOS os insumos")
    if st.form_submit_button("Aplicar correção global"):
        if not confirmacao:
            st.warning("Marque a confirmação para prosseguir.")
        else:
            try:
                execute("""
                    UPDATE pecuaria.dim_insumo
                    SET indice_correcao = %s, dt_revisao = CURRENT_DATE
                    WHERE ativo
                """, (novo_indice,))
                st.success(f"Índice {novo_indice:.2%} aplicado a todos os insumos ativos.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
