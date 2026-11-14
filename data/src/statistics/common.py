"""Utilitários compartilhados pelos scripts de análise."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config as cfg


def ensure_dirs() -> None:
    for d in (cfg.OUTPUT_DIR, cfg.FIG_DIR, cfg.STATE_FIG_DIR, cfg.INTERIM_DIR):
        d.mkdir(parents=True, exist_ok=True)


def apply_style() -> None:
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 130, "savefig.bbox": "tight",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#6b6b67", "axes.labelcolor": "#3a3a37",
        "axes.grid": True, "grid.color": cfg.C_GRID, "grid.linewidth": 0.6,
        "axes.axisbelow": True, "xtick.color": "#52514e", "ytick.color": "#52514e",
        "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
        "legend.frameon": False,
    })


def month_name(m: int) -> str:
    return cfg.MONTH_NAMES_PT[int(m) - 1]


def read_output(name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(cfg.OUTPUT_DIR / name, **kw)


def md_table(df: pd.DataFrame, decimals: int = 1, formats: dict | None = None) -> str:
    """DataFrame -> tabela markdown (sem depender de `tabulate`)."""
    formats = formats or {}
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |",
             "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if c in formats:
                cells.append(formats[c](v))
            elif pd.isna(v):
                cells.append("–")
            elif isinstance(v, (bool, np.bool_)):
                cells.append("sim" if v else "não")
            elif isinstance(v, (float, np.floating)):
                cells.append(f"{v:.{decimals}f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def fmt_p(p) -> str:
    if pd.isna(p):
        return "–"
    return "<0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def p_eq(p) -> str:
    """'p<0,001' ou 'p=0,123' (evita 'p=<0,001')."""
    f = fmt_p(p)
    return f"p{f}" if f.startswith("<") else f"p={f}"


def interpret_trend(row) -> str:
    """Frase em português que separa DIREÇÃO/MAGNITUDE de SIGNIFICÂNCIA."""
    if row["trend_class"] == "dados_insuficientes":
        return (f"Série com apenas {int(row['n_years'])} anos completos: "
                "insuficiente para testar tendência.")
    slope, pct = row["sens_slope_mm_yr"], row["sens_slope_pct_decade"]
    sinal = "positiva (aumento)" if slope > 0 else "negativa (redução)"
    base = (f"Inclinação de Sen {sinal}: {slope:+.1f} mm/ano ({pct:+.1f}% da média por década; "
            f"IC95% {row['sens_ci_low_mm_yr']:+.1f} a {row['sens_ci_high_mm_yr']:+.1f} mm/ano). ")
    ac = (" Houve autocorrelação significativa; o p-valor usado foi o corrigido (Hamed-Rao)."
          if row["autocorr_significant"] else "")
    if row["trend_class"] == "sem_evidencia_suficiente":
        nom = (" O p-valor nominal seria < 0,05, mas não sobrevive à correção para múltiplos testes."
               if row["significant_nominal"] else "")
        return (base + f"Sem evidência estatística suficiente de tendência "
                f"({p_eq(row['p_value_used'])}; p ajustado BH {('<0,001' if fmt_p(row['p_adj_bh']).startswith('<') else '=' + fmt_p(row['p_adj_bh']))})." + nom + ac)
    return (base + f"Tendência {row['trend_class']} estatisticamente significativa "
            f"({p_eq(row['p_value_used'])}; p ajustado BH {('<0,001' if fmt_p(row['p_adj_bh']).startswith('<') else '=' + fmt_p(row['p_adj_bh']))})." + ac)
