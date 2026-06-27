from utils.db import fetch_all, fetch_one, execute, execute_returning


# ── RAÇAS ──────────────────────────────────────────────────────────────────

def listar_racas() -> list[dict]:
    return fetch_all("SELECT id, codigo, descricao FROM dim_raca WHERE ativo ORDER BY descricao")


# ── LOTES ──────────────────────────────────────────────────────────────────

def listar_lotes(tipo: str = None) -> list[dict]:
    sql = "SELECT id, codigo, tipo, capacidade_max, dt_formacao, fazenda_setor, ativo FROM dim_lote"
    params = ()
    if tipo:
        sql += " WHERE tipo = %s AND ativo ORDER BY dt_formacao DESC"
        params = (tipo,)
    else:
        sql += " WHERE ativo ORDER BY dt_formacao DESC"
    return fetch_all(sql, params)


def inserir_lote(codigo, tipo, capacidade_max, dt_formacao, fazenda_setor, responsavel, observacoes) -> dict:
    sql = """
        INSERT INTO dim_lote (codigo, tipo, capacidade_max, dt_formacao, fazenda_setor, responsavel, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, codigo
    """
    return execute_returning(sql, (codigo, tipo, capacidade_max, dt_formacao, fazenda_setor, responsavel, observacoes))


# ── ANIMAIS ────────────────────────────────────────────────────────────────

def buscar_animal_por_brinco(brinco: str) -> dict | None:
    return fetch_one("""
        SELECT a.*, r.descricao AS raca_descricao, r.codigo AS raca_codigo,
               l.codigo AS lote_codigo
        FROM dim_animal a
        JOIN dim_raca r ON r.id = a.id_raca
        LEFT JOIN dim_lote l ON l.id = a.id_lote_origem
        WHERE a.brinco = %s
    """, (brinco,))


def inserir_animal(brinco, dt_nascimento, sexo, id_raca, id_lote_origem,
                   brinco_mae, peso_nasc_kg, observacoes) -> dict:
    sql = """
        INSERT INTO dim_animal
            (brinco, dt_nascimento, sexo, id_raca, id_lote_origem,
             brinco_mae, peso_nasc_kg, etapa_atual, dt_entrada_etapa, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'nascimento', CURRENT_DATE, %s)
        RETURNING id, brinco
    """
    return execute_returning(sql, (brinco, dt_nascimento, sexo, id_raca,
                                   id_lote_origem, brinco_mae, peso_nasc_kg, observacoes))


def listar_animais_por_etapa(etapa: str) -> list[dict]:
    return fetch_all("""
        SELECT a.id, a.brinco, a.sexo, a.etapa_atual, a.dt_nascimento,
               r.descricao AS raca, p.peso_kg AS ultimo_peso,
               p.dt_pesagem AS dt_ultimo_peso, p.gmd_calculado
        FROM dim_animal a
        JOIN dim_raca r ON r.id = a.id_raca
        LEFT JOIN vw_ultimo_peso p ON p.id_animal = a.id
        WHERE a.etapa_atual = %s AND a.ativo
        ORDER BY a.brinco
    """, (etapa,))


def ficha_animal(brinco: str) -> dict | None:
    return fetch_one("""
        SELECT a.*, r.descricao AS raca, r.codigo AS raca_codigo,
               l.codigo AS lote_codigo,
               p.peso_kg AS ultimo_peso, p.dt_pesagem AS dt_ultimo_peso,
               p.gmd_calculado,
               c.custo_total_rs AS custo_sanitario_total
        FROM dim_animal a
        JOIN dim_raca r ON r.id = a.id_raca
        LEFT JOIN dim_lote l ON l.id = a.id_lote_origem
        LEFT JOIN vw_ultimo_peso p ON p.id_animal = a.id
        LEFT JOIN vw_custo_acumulado_animal c ON c.id_animal = a.id
        WHERE a.brinco = %s
    """, (brinco,))


# ── PESAGENS ───────────────────────────────────────────────────────────────

def inserir_pesagem(id_animal, dt_pesagem, peso_kg, etapa, responsavel, observacoes) -> dict:
    sql = """
        INSERT INTO fato_pesagem (id_animal, dt_pesagem, peso_kg, etapa, responsavel, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, gmd_calculado, dias_periodo
    """
    return execute_returning(sql, (id_animal, dt_pesagem, peso_kg, etapa, responsavel, observacoes))


def historico_pesagens(id_animal: int) -> list[dict]:
    return fetch_all("""
        SELECT dt_pesagem, peso_kg, etapa, gmd_calculado, dias_periodo, responsavel
        FROM fato_pesagem
        WHERE id_animal = %s
        ORDER BY dt_pesagem
    """, (id_animal,))


# ── MANEJO SANITÁRIO ───────────────────────────────────────────────────────

def listar_operacoes(etapa: str = None) -> list[dict]:
    if etapa:
        return fetch_all("""
            SELECT id, numero, descricao, etapa_ciclo, raca_alvo, custo_base_rs
            FROM dim_operacao WHERE ativo AND etapa_ciclo = %s ORDER BY numero
        """, (etapa,))
    return fetch_all("""
        SELECT id, numero, descricao, etapa_ciclo, raca_alvo, custo_base_rs
        FROM dim_operacao WHERE ativo ORDER BY numero
    """)


def componentes_operacao(id_operacao: int) -> list[dict]:
    return fetch_all("""
        SELECT i.nome, oc.dose_padrao, oc.unidade, oc.custo_unitario, oc.custo_total
        FROM dim_operacao_componente oc
        JOIN dim_insumo i ON i.id = oc.id_insumo
        WHERE oc.id_operacao = %s
    """, (id_operacao,))


def inserir_manejo(id_animal, id_operacao, dt_aplicacao, tipo,
                   custo_total_rs, receituario, responsavel, observacoes) -> dict:
    sql = """
        INSERT INTO fato_manejo_sanitario
            (id_animal, id_operacao, dt_aplicacao, tipo,
             custo_total_rs, receituario, responsavel, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    return execute_returning(sql, (id_animal, id_operacao, dt_aplicacao, tipo,
                                   custo_total_rs, receituario, responsavel, observacoes))


def historico_manejo_animal(id_animal: int) -> list[dict]:
    return fetch_all("""
        SELECT m.dt_aplicacao, m.tipo, o.numero, o.descricao AS operacao,
               m.custo_total_rs, m.receituario, m.responsavel
        FROM fato_manejo_sanitario m
        JOIN dim_operacao o ON o.id = m.id_operacao
        WHERE m.id_animal = %s
        ORDER BY m.dt_aplicacao DESC
    """, (id_animal,))


# ── INSUMOS ────────────────────────────────────────────────────────────────

def listar_insumos() -> list[dict]:
    return fetch_all("""
        SELECT id, nome, unidade, valor_atual, indice_correcao,
               valor_corrigido, dt_revisao, ativo
        FROM dim_insumo ORDER BY nome
    """)


def atualizar_insumo(id_insumo: int, valor_atual: float, indice_correcao: float):
    execute("""
        UPDATE dim_insumo
        SET valor_atual = %s, indice_correcao = %s, dt_revisao = CURRENT_DATE
        WHERE id = %s
    """, (valor_atual, indice_correcao, id_insumo))


# ── ABATE ──────────────────────────────────────────────────────────────────

def inserir_abate(id_animal, dt_abate, peso_vivo_final_kg, peso_carcaca_kg,
                  gmd_total, gmp_kg, receita_rs_kg, receita_total_rs,
                  custo_total_rs, margem_rs, frigorifico, observacoes) -> dict:
    sql = """
        INSERT INTO fato_abate
            (id_animal, dt_abate, peso_vivo_final_kg, peso_carcaca_kg,
             gmd_total, gmp_kg, receita_rs_kg, receita_total_rs,
             custo_total_rs, margem_rs, frigorifico, observacoes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id, rendimento_pct
    """
    result = execute_returning(sql, (id_animal, dt_abate, peso_vivo_final_kg,
                                     peso_carcaca_kg, gmd_total, gmp_kg,
                                     receita_rs_kg, receita_total_rs,
                                     custo_total_rs, margem_rs, frigorifico, observacoes))
    execute("""
        UPDATE dim_animal SET etapa_atual = 'abate', atualizado_em = NOW() WHERE id = %s
    """, (id_animal,))
    return result


# ── PAINEL ─────────────────────────────────────────────────────────────────

def resumo_rebanho() -> list[dict]:
    return fetch_all("SELECT * FROM vw_resumo_rebanho")


def projecao_abate() -> list[dict]:
    return fetch_all("""
        SELECT brinco, raca, peso_atual_kg, dt_ultimo_peso,
               gmd_atual, kg_faltando, dt_projecao_abate, dias_restantes
        FROM vw_projecao_abate
        ORDER BY dias_restantes NULLS LAST
    """)


def indicadores_abate() -> list[dict]:
    return fetch_all("SELECT * FROM vw_indicadores_abate ORDER BY mes_abate DESC LIMIT 24")


def orcamento_realizado(ano: int) -> list[dict]:
    return fetch_all("""
        SELECT * FROM vw_orcamento_realizado WHERE ano = %s ORDER BY mes, num_operacao
    """, (ano,))


def gargalos_engorda(gmd_minimo: float = 0.7) -> list[dict]:
    return fetch_all("""
        SELECT a.brinco, r.descricao AS raca, p.peso_kg AS peso_atual,
               p.gmd_calculado, p.dt_pesagem,
               ROUND(590 - p.peso_kg, 1) AS kg_faltando
        FROM dim_animal a
        JOIN dim_raca r ON r.id = a.id_raca
        JOIN vw_ultimo_peso p ON p.id_animal = a.id
        WHERE a.etapa_atual = 'engorda'
          AND a.ativo
          AND (p.gmd_calculado IS NULL OR p.gmd_calculado < %s)
        ORDER BY p.gmd_calculado NULLS FIRST
    """, (gmd_minimo,))
