"""Tarefa 6 — Comparação descritiva entre décadas.

A comparação entre décadas é deliberadamente DESCRITIVA. As décadas podem
conter quantidades diferentes de anos completos (por início/fim da série e
lacunas); por isso não são executados testes de hipótese entre décadas e não
são atribuídos p-valores ou rótulos de significância a essas diferenças.

Cada série é identificada por UF + point_id. São reportados tamanho amostral,
média, mediana, desvio-padrão, diferenças absolutas e percentuais.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config as cfg
from common import apply_style, ensure_dirs, read_output


def build_decadal(annual: pd.DataFrame) -> pd.DataFrame:
    annual = annual.copy()
    if "point_id" not in annual.columns:
        annual["point_id"] = annual["state"].astype(str)
    a = annual[annual["complete"]].copy()
    a["decade"] = (a["year"] // 10) * 10
    g = a.groupby(["state", "point_id", "decade"])["annual_total_mm"]
    d = g.agg(n_years="count", mean_annual_mm="mean", median_annual_mm="median",
              std_annual_mm="std", min_annual_mm="min", max_annual_mm="max").reset_index()
    d = d[d["n_years"] >= cfg.MIN_YEARS_DECADE].copy()
    d["partial_decade"] = d["n_years"] < cfg.FULL_DECADE_YEARS
    d = d.sort_values(["state", "point_id", "decade"])
    keys = ["state", "point_id"]
    d["diff_mm_vs_prev_decade"] = d.groupby(keys)["mean_annual_mm"].diff()
    d["pct_change_vs_prev_decade"] = (
        100 * d["diff_mm_vs_prev_decade"] / d.groupby(keys)["mean_annual_mm"].shift()
    )
    d["comparison_type"] = "descritiva"
    return d.reset_index(drop=True)


def build_changes(annual: pd.DataFrame, dec: pd.DataFrame) -> pd.DataFrame:
    """Diferença da primeira para a última década disponível; sem teste inferencial."""
    annual = annual.copy()
    if "point_id" not in annual.columns:
        annual["point_id"] = annual["state"].astype(str)
    dec = dec.copy()
    if "point_id" not in dec.columns:
        dec["point_id"] = dec["state"].astype(str)
    rows = []
    for (state, point_id), g in dec.groupby(["state", "point_id"]):
        if len(g) < 2:
            continue
        f, l = g.iloc[0], g.iloc[-1]
        diff = l["mean_annual_mm"] - f["mean_annual_mm"]
        rows.append({
            "state": state, "point_id": point_id,
            "first_decade": int(f["decade"]), "last_decade": int(l["decade"]),
            "n_years_first": int(f["n_years"]), "n_years_last": int(l["n_years"]),
            "mean_first_mm": f["mean_annual_mm"], "mean_last_mm": l["mean_annual_mm"],
            "diff_mm": diff,
            "pct_change": 100 * diff / f["mean_annual_mm"] if f["mean_annual_mm"] else np.nan,
            "first_decade_partial": bool(f["partial_decade"]),
            "last_decade_partial": bool(l["partial_decade"]),
            "sample_size_unequal": bool(f["n_years"] != l["n_years"]),
            "comparison_type": "descritiva_sem_teste",
            "interpretation_note": "Diferença descritiva; tamanhos amostrais desiguais e períodos distintos impedem inferência direta."
        })
    c = pd.DataFrame(rows)
    if c.empty:
        return c
    c["rank_abs_pct_change"] = c["pct_change"].abs().rank(ascending=False, method="min").astype(int)
    return c.sort_values("rank_abs_pct_change").reset_index(drop=True)


def plot_decadal(dec: pd.DataFrame, ch: pd.DataFrame) -> None:
    apply_style()
    piv = dec.pivot(index="state", columns="decade", values="pct_change_vs_prev_decade")
    fig, ax = plt.subplots(figsize=(7, 9))
    ax.grid(False)
    im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="RdBu", vmin=-25, vmax=25)
    ax.set_xticks(range(piv.shape[1]), [f"{int(c)}s" for c in piv.columns])
    ax.set_yticks(range(len(piv)), piv.index)
    ax.set_title("Variação descritiva da média anual vs. década anterior")
    fig.colorbar(im, ax=ax, shrink=0.7, label="%")
    fig.savefig(cfg.FIG_DIR / "decadal_change_heatmap.png")
    plt.close(fig)

    d = ch.sort_values("pct_change")
    fig, ax = plt.subplots(figsize=(8, 9))
    y = np.arange(len(d))
    ax.barh(y, d["pct_change"], color=cfg.C_DATA, height=0.65)
    ax.axvline(0, color="#3a3a37", lw=0.8)
    ax.set_yticks(y, [f"{r.state} (n={r.n_years_first}/{r.n_years_last})"
                      for r in d.itertuples()])
    ax.set_xlabel("Variação descritiva da média anual: última vs. primeira década (%)")
    ax.set_title("Diferença entre décadas — sem teste de significância")
    fig.savefig(cfg.FIG_DIR / "decadal_change_first_vs_last.png")
    plt.close(fig)


def main():
    ensure_dirs()
    annual = read_output("annual_precipitation.csv")
    dec = build_decadal(annual)
    ch = build_changes(annual, dec)
    dec.to_csv(cfg.OUTPUT_DIR / "decadal_comparison.csv", index=False)
    ch.to_csv(cfg.OUTPUT_DIR / "decadal_changes.csv", index=False)
    plot_decadal(dec, ch)
    print(ch.round(2).head(10).to_string(index=False))


if __name__ == "__main__":
    main()
