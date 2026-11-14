"""Configuração central do módulo estatístico EarthScope (Sprint 0).

Todos os parâmetros metodológicos ficam aqui para que possam ser auditados e
alterados em um único lugar.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
FIG_DIR = OUTPUT_DIR / "figures"
STATE_FIG_DIR = FIG_DIR / "states"
INTERIM_DIR = OUTPUT_DIR / "intermediate"

UF_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal",
    "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco",
    "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima",
    "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe",
    "TO": "Tocantins",
}
MONTH_NAMES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                  "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

# --- Qualidade dos dados -----------------------------------------------------
MAX_DAILY_MM = 700.0      # acima disso o valor diário é tratado como erro físico
ROUNDING_NOISE_MM = 0.05  # negativos entre -0.05 e 0 são ruído de arredondamento -> 0
WET_DAY_MM = 1.0          # limiar de "dia chuvoso"
FLATLINE_DAYS = 5         # sequência de dias > 0 com valor idêntico é suspeita (só sinaliza)

# --- Estatística ---------------------------------------------------------------
ALPHA = 0.05
CATEGORY_PCTS = (10, 30, 70, 90)
CATEGORY_LABELS = ["muito_seco", "seco", "normal", "chuvoso", "muito_chuvoso"]
MIN_REF_YEARS = 10        # mínimo de anos de referência p/ percentis, climatologia e Z
Z_MODERATE = 1.0
Z_SIGNIFICANT = 2.0
EPISODE_Z = 1.0           # episódio = meses consecutivos com |Z| >= EPISODE_Z
EPISODE_MIN_MONTHS = 3

MIN_YEARS_TREND = 10      # mínimo de anos completos para testar tendência
MIN_YEARS_DECADE = 5      # mínimo de anos completos para usar uma década
FULL_DECADE_YEARS = 8     # a partir daqui a década é considerada "cheia"

# Cores (paleta de referência do skill dataviz; azul = dados, laranja = tendência)
C_DATA = "#2a78d6"
C_TREND = "#eb6834"
C_NEUTRAL = "#8a8a86"
C_GRID = "#dcdcd8"
CATEGORY_COLORS = {
    "muito_seco": "#c2501f", "seco": "#eb9a72", "normal": "#c8c8c4",
    "chuvoso": "#86b6ef", "muito_chuvoso": "#1c5cab",
}
