from datetime import date
from typing import Optional
import math


def calcular_gmd(peso_inicial: float, peso_final: float, dias: int) -> Optional[float]:
    if dias <= 0:
        return None
    return round((peso_final - peso_inicial) / dias, 3)


def projetar_abate(peso_atual: float, gmd_atual: float,
                   dt_ultimo_peso: date, peso_meta: float = 590) -> Optional[date]:
    if gmd_atual <= 0 or peso_atual >= peso_meta:
        return None
    dias = math.ceil((peso_meta - peso_atual) / gmd_atual)
    from datetime import timedelta
    return dt_ultimo_peso + timedelta(days=dias)


def calcular_rendimento(peso_carcaca: float, peso_vivo: float) -> float:
    if peso_vivo <= 0:
        return 0.0
    return round((peso_carcaca / peso_vivo) * 100, 2)


def calcular_gmp(peso_entrada_tip: float, peso_final: float) -> float:
    return round(peso_final - peso_entrada_tip, 2)


def status_gmd(gmd: Optional[float], etapa: str) -> str:
    minimos = {"cria": 0.4, "recria": 0.5, "engorda": 0.7}
    minimo = minimos.get(etapa, 0.5)
    if gmd is None:
        return "sem_dado"
    if gmd < minimo:
        return "critico"
    if gmd < minimo * 1.2:
        return "atencao"
    return "ok"
