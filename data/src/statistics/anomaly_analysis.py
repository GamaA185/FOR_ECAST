"""Tarefa 4 — Análise de anomalias de precipitação.

Para cada estado e período (mensal, trimestral móvel de 3 meses e anual):
    anomalia_mm  = valor − média histórica do mesmo mês (ou do mesmo trimestre)
    anomalia_pct = 100 × anomalia / média histórica
    Z            = anomalia / desvio-padrão histórico (ddof=1)
A climatologia usa todos os períodos completos da série (inclui o próprio ano).

Limitação: a precipitação é assimétrica (cauda direita) e, em meses secos, tem
muitos zeros; o Z bruto assume simetria, então |Z| alto é mais frequente no lado
chuvoso e o desvio-padrão pode ser ~0 (Z indefinido) — esses casos ficam como NaN.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

import config as cfg
from common import apply_style, ensure_dirs, read_output


def classify_z(z: float) -> str:
    if np.isnan(z):
        return "indefinido"
    if z <= -cfg.Z_SIGNIFICANT:
        return "significativamente_seco"
    if z <= -cfg.Z_MODERATE:
        return "moderadamente_seco"
    if z < cfg.Z_MODERATE:
        return "normal"
    if z < cfg.Z_SIGNIFICANT:
        return "moderadamente_chuvoso"
    return "significativamente_chuvoso"


def _anomalies(df: pd.DataFrame, keys: list[str], period_type: str,
               min_ref: int = cfg.MIN_REF_YEARS) -> pd.DataFrame:
    d = df.dropna(subset=["precip_mm"]).copy()
    g = d.groupby(keys)["precip_mm"]
    d["clim_mean_mm"], d["clim_std_mm"], d["n_ref_years"] = g.transform("mean"), g.transform("std"), g.transform("count")
    bad = d["n_ref_years"] < min_ref
    d.loc[bad, ["clim_mean_mm", "clim_std_mm"]] = np.nan
    d["anomaly_mm"] = d["precip_mm"] - d["clim_mean_mm"]
    d["anomaly_pct"] = np.where(d["clim_mean_mm"] > 0.5, 100 * d["anomaly_mm"] / d["clim_mean_mm"], np.nan)
    d["zscore"] = np.where(d["clim_std_mm"] > 0, d["anomaly_mm"] / d["clim_std_mm"], np.nan)
    d["anomaly_class"] = d["zscore"].map(classify_z)
    d["significant"] = d["zscore"].abs() >= cfg.Z_SIGNIFICANT
    d["period_type"] = period_type
    return d


def build_anomalies(monthly: pd.DataFrame, annual: pd.DataFrame) -> pd.DataFrame:
    monthly = monthly.copy()
    annual = annual.copy()
    if "point_id" not in monthly.columns:
        monthly["point_id"] = monthly["state"].astype(str)
    if "point_id" not in annual.columns:
        annual["point_id"] = annual["state"].astype(str)
    m = monthly.sort_values(["state", "point_id", "year", "month"]).reset_index(drop=True)
    mo = _anomalies(m[["state", "point_id", "year", "month", "precip_mm"]],
                    ["state", "point_id", "month"], "monthly")

    # trimestre móvel (mês final = `month`); exige os 3 meses completos e consecutivos
    m["precip_mm"] = m["precip_mm"].astype(float)
    r3 = m.groupby(["state", "point_id"])["precip_mm"].rolling(3, min_periods=3).sum().reset_index(level=[0, 1], drop=True)
    m3 = m[["state", "point_id", "year", "month"]].assign(precip_mm=r3)
    tr = _anomalies(m3, ["state", "point_id", "month"], "3-month")

    a = annual.rename(columns={"annual_total_mm": "precip_mm"})[["state", "point_id", "year", "precip_mm"]].copy()
    a["month"] = np.nan
    an = _anomalies(a, ["state", "point_id"], "annual")

    out = pd.concat([mo, tr, an], ignore_index=True)
    out["period"] = np.where(out["period_type"] == "annual", out["year"].astype(int).astype(str),
                             out["year"].astype(int).astype(str) + "-" + out["month"].fillna(0).astype(int).astype(str).str.zfill(2))
    cols = ["state", "point_id", "period_type", "period", "year", "month", "precip_mm", "clim_mean_mm", "clim_std_mm",
            "n_ref_years", "anomaly_mm", "anomaly_pct", "zscore", "anomaly_class", "significant"]
    return out[cols].sort_values(["state", "period_type", "year", "month"]).reset_index(drop=True)


def find_episodes(anom: pd.DataFrame) -> pd.DataFrame:
    """Episódios: >= EPISODE_MIN_MONTHS meses consecutivos com Z <= -1 (seco) ou >= +1 (chuvoso).
    Meses incompletos (sem Z) interrompem o episódio."""
    mo = anom[anom["period_type"] == "monthly"].copy()
    rows = []
    for (st, pid), g in mo.groupby(["state", "point_id"]):
        g = g.sort_values(["year", "month"])
        idx = g["year"].to_numpy() * 12 + g["month"].to_numpy().astype(int)
        z, a = g["zscore"].to_numpy(), g["anomaly_mm"].to_numpy()
        yrs, mos = g["year"].to_numpy(), g["month"].to_numpy().astype(int)
        for kind, cond in (("seco", z <= -cfg.EPISODE_Z), ("chuvoso", z >= cfg.EPISODE_Z)):
            i, n = 0, len(z)
            while i < n:
                if cond[i]:
                    j = i
                    while j + 1 < n and cond[j + 1] and idx[j + 1] == idx[j] + 1:
                        j += 1
                    if j - i + 1 >= cfg.EPISODE_MIN_MONTHS:
                        rows.append({"state": st, "point_id": pid, "kind": kind,
                                     "start": f"{yrs[i]}-{mos[i]:02d}", "end": f"{yrs[j]}-{mos[j]:02d}",
                                     "n_months": j - i + 1, "mean_z": z[i:j + 1].mean(),
                                     "min_z_or_max_z": z[i:j + 1].min() if kind == "seco" else z[i:j + 1].max(),
                                     "total_anomaly_mm": a[i:j + 1].sum()})
                    i = j + 1
                else:
                    i += 1
    cols = ["state", "point_id", "kind", "start", "end", "n_months", "mean_z", "min_z_or_max_z", "total_anomaly_mm"]
    return pd.DataFrame(rows, columns=cols).sort_values(["state", "start"]).reset_index(drop=True)


def anomaly_summary(anom: pd.DataFrame) -> pd.DataFrame:
    p_two = 2 * stats.norm.sf(cfg.Z_SIGNIFICANT)
    rows = []
    for (st, pid, pt), g in anom.groupby(["state", "point_id", "period_type"]):
        g = g.dropna(subset=["zscore"])
        if g.empty:
            continue
        dry, wet = g.loc[g["zscore"].idxmin()], g.loc[g["zscore"].idxmax()]
        rows.append({"state": st, "point_id": pid, "period_type": pt, "n_periods": len(g),
                     "n_sig_dry": int((g["zscore"] <= -cfg.Z_SIGNIFICANT).sum()),
                     "n_sig_wet": int((g["zscore"] >= cfg.Z_SIGNIFICANT).sum()),
                     "expected_by_chance_normal": round(len(g) * p_two, 1),
                     "driest_period": dry["period"], "driest_z": dry["zscore"],
                     "wettest_period": wet["period"], "wettest_z": wet["zscore"]})
    return pd.DataFrame(rows)


def plot_annual_z_heatmap(anom: pd.DataFrame) -> None:
    apply_style()
    a = anom[anom["period_type"] == "annual"]
    piv = a.pivot(index="state", columns="year", values="zscore")
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.grid(False)
    im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="RdBu", vmin=-3, vmax=3)
    yrs = piv.columns.to_numpy()
    ax.set_xticks(range(0, len(yrs), 5), yrs[::5])
    ax.set_yticks(range(len(piv)), piv.index)
    ax.set_title("Anomalia anual padronizada (Z) · laranja = mais seco, azul = mais chuvoso · branco = sem dado/ano incompleto")
    fig.colorbar(im, ax=ax, shrink=0.7, label="Z-score")
    fig.savefig(cfg.FIG_DIR / "anomaly_annual_zscore_heatmap.png")
    plt.close(fig)


def main():
    ensure_dirs()
    anom = build_anomalies(read_output("monthly_precipitation.csv"), read_output("annual_precipitation.csv"))
    anom.to_csv(cfg.OUTPUT_DIR / "anomalies.csv", index=False)
    anomaly_summary(anom).to_csv(cfg.OUTPUT_DIR / "anomaly_summary.csv", index=False)
    ep = find_episodes(anom)
    ep.to_csv(cfg.OUTPUT_DIR / "anomaly_episodes.csv", index=False)
    plot_annual_z_heatmap(anom)
    print(anom.groupby("period_type")["anomaly_class"].value_counts().unstack().fillna(0).astype(int).to_string())
    print(len(ep), "episódios")


if __name__ == "__main__":
    main()
