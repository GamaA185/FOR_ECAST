"""Tarefa 5 — Análise de tendências (Mann-Kendall + Sen's Slope).

Série analisada: precipitação ANUAL (anos completos) de cada ponto de referência, identificado por UF + point_id.

Procedimento por estado:
 1. Mann-Kendall (S, Z, p, tau) e Sen's Slope com IC 95% (Gilbert).
 2. Autocorrelação: série sem tendência (reta de Sen removida) -> r(1) e teste
    de Ljung-Box. Autocorrelação positiva infla a significância do MK.
 3. Se há autocorrelação significativa (Ljung-Box p<α ou |r1|>1,96/√n), usa-se o
    p-valor de Mann-Kendall com variância corrigida (Hamed-Rao); senão, o p original.
 4. Múltiplos testes (27 estados): p ajustado por Benjamini-Hochberg (FDR, critério
    de decisão) e Holm (FWER, mais conservador, para referência).
 5. Classificação: crescente / decrescente SOMENTE se p_adj_BH < α; caso contrário
    "sem_evidencia_suficiente". A inclinação de Sen é sempre reportada, mas
    magnitude ≠ significância.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

import config as cfg
from common import apply_style, ensure_dirs, read_output
import stats_tools as st


def analyze_series(years, values, alpha: float = cfg.ALPHA) -> dict:
    years = np.asarray(years, dtype=float)
    x = np.asarray(values, dtype=float)
    n = len(x)
    mean = float(np.mean(x))
    mk = st.mann_kendall(x)
    sen = st.sens_slope(x, years, alpha)
    resid = x - (sen["slope"] * years + sen["intercept"])
    lags = max(1, min(10, n // 4))
    r = st.acf(resid, lags)
    lb_q, lb_p = st.ljung_box(resid, lags)
    bound = stats.norm.ppf(1 - alpha / 2) / np.sqrt(n)
    ac_sig = bool(lb_p < alpha or abs(r[1]) > bound)
    hr = st.hamed_rao(x, years, alpha)
    p_used = hr["p"] if ac_sig else mk["p"]
    to_pct = lambda v: 100.0 * v * 10.0 / mean if mean else np.nan
    return {
        "n_years": n, "first_year": int(years.min()), "last_year": int(years.max()),
        "has_gaps": bool(np.any(np.diff(years) > 1)), "mean_annual_mm": mean,
        "mk_s": mk["s"], "mk_tau": mk["tau"], "mk_z": mk["z"], "p_value_mk": mk["p"],
        "sens_slope_mm_yr": sen["slope"], "sens_ci_low_mm_yr": sen["ci_low"],
        "sens_ci_high_mm_yr": sen["ci_high"],
        "sens_slope_pct_decade": to_pct(sen["slope"]),
        "sens_ci_low_pct_decade": to_pct(sen["ci_low"]),
        "sens_ci_high_pct_decade": to_pct(sen["ci_high"]),
        "lag1_autocorr_detrended": float(r[1]), "lag1_autocorr_bound": float(bound),
        "ljung_box_lags": lags, "ljung_box_p": lb_p, "autocorr_significant": ac_sig,
        "hr_variance_factor": hr["factor_used"], "hr_n_significant_lags": hr["n_sig_lags"],
        "mk_z_corrected": hr["z"], "p_value_hamed_rao": hr["p"], "p_value_used": p_used,
        "p_value_method": "hamed_rao" if ac_sig else "mann_kendall",
    }


def build_trend_table(annual: pd.DataFrame, alpha: float = cfg.ALPHA,
                      min_years: int = cfg.MIN_YEARS_TREND) -> pd.DataFrame:
    annual = annual.copy()
    if "point_id" not in annual.columns:
        annual["point_id"] = annual["state"].astype(str)
    rows = []
    for (state, point_id), g in annual[annual["complete"]].sort_values("year").groupby(["state", "point_id"]):
        if len(g) < min_years:
            rows.append({"state": state, "point_id": point_id, "n_years": len(g)})
            continue
        rows.append({"state": state, "point_id": point_id,
                     **analyze_series(g["year"], g["annual_total_mm"], alpha)})
    template = list(analyze_series(np.arange(12.0), np.random.default_rng(0).normal(size=12)).keys())
    df = pd.DataFrame(rows).reindex(columns=["state", "point_id"] + template)  # esquema fixo mesmo se todas as séries forem curtas
    df["p_adj_bh"] = st.benjamini_hochberg(df["p_value_used"])
    df["p_adj_holm"] = st.holm(df["p_value_used"])
    df["significant_nominal"] = df["p_value_used"] < alpha
    df["significant_fdr"] = df["p_adj_bh"] < alpha
    df["significant_holm"] = df["p_adj_holm"] < alpha

    def klass(r):
        if pd.isna(r.get("p_value_used")):
            return "dados_insuficientes"
        if r["significant_fdr"]:
            return "crescente" if r["mk_z"] > 0 else "decrescente"
        return "sem_evidencia_suficiente"

    df["trend_class"] = df.apply(klass, axis=1)
    df["alpha"] = alpha
    notes = []
    for _, r in df.iterrows():
        n = []
        if r["trend_class"] == "dados_insuficientes":
            n.append(f"menos de {min_years} anos completos")
        else:
            if r["n_years"] < 20:
                n.append("série curta (<20 anos): baixo poder")
            if r["has_gaps"]:
                n.append("anos faltantes na série (autocorrelação aproximada)")
            if r["autocorr_significant"]:
                n.append("autocorrelação significativa: p corrigido (Hamed-Rao)")
            if r["significant_nominal"] and not r["significant_fdr"]:
                n.append("significativo só sem correção para múltiplos testes")
            if abs(np.sign(r["mk_z"]) - np.sign(r["sens_slope_mm_yr"])) > 0:
                n.append("sinais de Z e de Sen divergem")
        notes.append("; ".join(n))
    df["notes"] = notes
    first = ["state", "point_id", "trend_class", "n_years", "first_year", "last_year", "mean_annual_mm"]
    return df[first + [c for c in df.columns if c not in first]]


def plot_trend_overview(annual: pd.DataFrame, tr: pd.DataFrame) -> None:
    apply_style()
    states = sorted(tr["state"])
    fig, axes = plt.subplots(5, 6, figsize=(18, 11), sharex=True)
    for ax, s in zip(axes.ravel(), states):
        g = annual[(annual["state"] == s) & annual["complete"]]
        r = tr[tr["state"] == s].iloc[0]
        ax.plot(g["year"], g["annual_total_mm"], color=cfg.C_DATA, lw=1.1)
        if r["trend_class"] != "dados_insuficientes":
            xs = np.array([r["first_year"], r["last_year"]])
            sig = r["trend_class"] != "sem_evidencia_suficiente"
            med = g["annual_total_mm"].median()
            ymid = r["sens_slope_mm_yr"] * (xs - g["year"].median()) + med
            ax.plot(xs, ymid, color=cfg.C_TREND, lw=2.0 if sig else 1.2, ls="-" if sig else "--")
            tag = "signif." if sig else "n.s."
            ax.set_title(f"{s}: {r['sens_slope_mm_yr']:+.1f} mm/ano ({tag})", fontsize=9)
        ax.tick_params(labelsize=7)
    for ax in axes.ravel()[len(states):]:
        ax.axis("off")
    fig.suptitle("Tendência anual: reta de Sen (laranja contínua = significativa após correção BH; "
                 "tracejada = sem evidência suficiente)", fontsize=12, y=0.995)
    fig.tight_layout()
    fig.savefig(cfg.FIG_DIR / "trend_overview.png")
    plt.close(fig)


def plot_trend_summary(tr: pd.DataFrame) -> None:
    apply_style()
    d = tr[tr["trend_class"] != "dados_insuficientes"].sort_values("sens_slope_pct_decade")
    fig, ax = plt.subplots(figsize=(8, 9))
    y = np.arange(len(d))
    sig = d["significant_fdr"].to_numpy()
    xerr = np.vstack([d["sens_slope_pct_decade"] - d["sens_ci_low_pct_decade"],
                      d["sens_ci_high_pct_decade"] - d["sens_slope_pct_decade"]])
    ax.errorbar(d["sens_slope_pct_decade"], y, xerr=xerr, fmt="none", ecolor=cfg.C_NEUTRAL, lw=1, capsize=2)
    ax.scatter(d["sens_slope_pct_decade"][sig], y[sig], s=48, color=cfg.C_TREND, zorder=3,
               label="significativa (BH, α=0,05)")
    ax.scatter(d["sens_slope_pct_decade"][~sig], y[~sig], s=48, facecolor="white",
               edgecolor=cfg.C_TREND, zorder=3, label="sem evidência suficiente")
    ax.axvline(0, color="#3a3a37", lw=0.8)
    ax.set_yticks(y, d["state"])
    ax.set_xlabel("Inclinação de Sen (% da média anual por década) · barras = IC 95%")
    ax.set_title("Magnitude da tendência ≠ significância estatística")
    ax.legend(loc="lower right")
    fig.savefig(cfg.FIG_DIR / "trend_summary.png")
    plt.close(fig)


def main():
    ensure_dirs()
    annual = read_output("annual_precipitation.csv")
    tr = build_trend_table(annual)
    tr.to_csv(cfg.OUTPUT_DIR / "trend_analysis.csv", index=False)
    plot_trend_overview(annual, tr)
    plot_trend_summary(tr)
    print(tr[["state", "n_years", "sens_slope_mm_yr", "sens_slope_pct_decade", "p_value_mk", "p_value_used",
              "p_adj_bh", "autocorr_significant", "trend_class"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
