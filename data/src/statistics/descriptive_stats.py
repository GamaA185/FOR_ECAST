"""Tarefa 2 — Estatística descritiva.

Saídas: annual_statistics.csv (estado × ano), state_summary.csv (um por estado),
monthly_climatology.csv (estado × mês do ano), extreme_periods.csv e gráficos de
evolução histórica.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config as cfg
from common import apply_style, ensure_dirs, month_name, read_output


def build_annual_statistics(monthly: pd.DataFrame, annual: pd.DataFrame) -> pd.DataFrame:
    ann = annual.set_index(["state", "point_id", "year"]).copy()
    piv = monthly.set_index(["state", "point_id", "year", "month"])["precip_mm"].unstack("month")
    piv = piv.reindex(ann.index)
    comp = ann["complete"].to_numpy()
    arr = piv.to_numpy(dtype=float, copy=True)
    arr[~comp, :] = np.nan
    all_nan = np.isnan(arr).all(axis=1)
    wet_idx = np.where(np.isnan(arr), -np.inf, arr).argmax(axis=1) + 1
    dry_idx = np.where(np.isnan(arr), np.inf, arr).argmin(axis=1) + 1
    import warnings
    warnings.simplefilter("ignore", RuntimeWarning)
    with np.errstate(all="ignore"):
        ann["mean_monthly_mm"] = np.nanmean(arr, axis=1)
        ann["std_monthly_mm"] = np.nanstd(arr, axis=1, ddof=1)
        ann["wettest_month"] = np.where(all_nan, np.nan, wet_idx)
        ann["wettest_month_mm"] = np.nanmax(np.where(np.isnan(arr), -np.inf, arr), axis=1)
        ann["driest_month"] = np.where(all_nan, np.nan, dry_idx)
        ann["driest_month_mm"] = np.nanmin(np.where(np.isnan(arr), np.inf, arr), axis=1)
    ann.loc[all_nan, ["wettest_month_mm", "driest_month_mm"]] = np.nan

    extra = monthly.groupby(["state", "year"]).agg(
        wet_days=("wet_days", "sum"), max_daily_mm=("max_daily_mm", "max"))
    ann = ann.join(extra)
    ann.loc[~ann["complete"], ["wet_days", "max_daily_mm"]] = np.nan
    ann = ann.reset_index()
    ann["rank_wettest"] = ann.groupby("state")["annual_total_mm"].rank(ascending=False, method="min")
    mean_state = ann.groupby("state")["annual_total_mm"].transform("mean")
    ann["pct_of_state_mean"] = 100 * ann["annual_total_mm"] / mean_state
    cols = ["state", "point_id", "year", "complete", "n_months_complete", "n_valid_days", "annual_total_mm",
            "annual_partial_mm", "mean_monthly_mm", "std_monthly_mm", "wettest_month",
            "wettest_month_mm", "driest_month", "driest_month_mm", "wet_days", "max_daily_mm",
            "rank_wettest", "pct_of_state_mean"]
    return ann[cols]


def build_monthly_climatology(monthly: pd.DataFrame) -> pd.DataFrame:
    c = monthly[monthly["complete"]]
    g = c.groupby(["state", "point_id", "month"])["precip_mm"]
    out = g.agg(n_years="count", mean_mm="mean", std_mm="std", median_mm="median",
                min_mm="min", max_mm="max").reset_index()
    out["p10_mm"] = g.quantile(0.10).to_numpy()
    out["p90_mm"] = g.quantile(0.90).to_numpy()
    return out


def build_state_summary(ann_stats: pd.DataFrame, monthly: pd.DataFrame,
                        clim: pd.DataFrame) -> pd.DataFrame:
    ac = ann_stats[ann_stats["complete"]].reset_index(drop=True)
    g = ac.groupby(["state", "point_id"])["annual_total_mm"]
    s = pd.DataFrame({
        "n_years_complete": g.count(), "first_complete_year": ac.groupby(["state", "point_id"])["year"].min(),
        "last_complete_year": ac.groupby(["state", "point_id"])["year"].max(),
        "mean_annual_mm": g.mean(), "std_annual_mm": g.std(ddof=1),
        "median_annual_mm": g.median(), "skewness_annual": g.skew()})
    s["cv_annual_pct"] = 100 * s["std_annual_mm"] / s["mean_annual_mm"]
    wy, dy = ac.loc[g.idxmax()].set_index(["state", "point_id"]), ac.loc[g.idxmin()].set_index(["state", "point_id"])
    s["wettest_year"], s["wettest_year_mm"] = wy["year"], wy["annual_total_mm"]
    s["driest_year"], s["driest_year_mm"] = dy["year"], dy["annual_total_mm"]

    mc = monthly[monthly["complete"]].reset_index(drop=True)
    mg = mc.groupby(["state", "point_id"])["precip_mm"]
    s["mean_monthly_mm"], s["std_monthly_mm"] = mg.mean(), mg.std(ddof=1)
    wm, dm = mc.loc[mg.idxmax()].set_index(["state", "point_id"]), mc.loc[mg.idxmin()].set_index(["state", "point_id"])
    s["wettest_month_ever"] = wm["year"].astype(int).astype(str) + "-" + wm["month"].astype(int).astype(str).str.zfill(2)
    s["wettest_month_ever_mm"] = wm["precip_mm"]
    s["driest_month_ever"] = dm["year"].astype(int).astype(str) + "-" + dm["month"].astype(int).astype(str).str.zfill(2)
    s["driest_month_ever_mm"] = dm["precip_mm"]
    cw, cd = clim.loc[clim.groupby(["state", "point_id"])["mean_mm"].idxmax()].set_index(["state", "point_id"]), \
        clim.loc[clim.groupby(["state", "point_id"])["mean_mm"].idxmin()].set_index(["state", "point_id"])
    s["wettest_calendar_month"], s["wettest_calendar_month_mean_mm"] = cw["month"], cw["mean_mm"]
    s["driest_calendar_month"], s["driest_calendar_month_mean_mm"] = cd["month"], cd["mean_mm"]
    s["n_incomplete_months"] = (~monthly["complete"]).groupby([monthly["state"], monthly["point_id"]]).sum()
    s["n_incomplete_years"] = (~ann_stats["complete"]).groupby([ann_stats["state"], ann_stats["point_id"]]).sum()
    s = s.reset_index()
    for c in ("n_years_complete", "first_complete_year", "last_complete_year", "wettest_year",
              "driest_year", "wettest_calendar_month", "driest_calendar_month"):
        s[c] = s[c].astype(int)
    return s


def build_extremes(monthly: pd.DataFrame, ann_stats: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    rows = []
    ac = ann_stats[ann_stats["complete"]]
    mc = monthly[monthly["complete"]]
    for (st, pid), g in ac.groupby(["state", "point_id"]):
        for kind, sub in (("mais_chuvoso", g.nlargest(k, "annual_total_mm")),
                          ("mais_seco", g.nsmallest(k, "annual_total_mm"))):
            for r, (_, x) in enumerate(sub.iterrows(), 1):
                rows.append((st, pid, "year", kind, r, int(x["year"]), np.nan, x["annual_total_mm"]))
    for (st, pid), g in mc.groupby(["state", "point_id"]):
        for kind, sub in (("mais_chuvoso", g.nlargest(k, "precip_mm")),
                          ("mais_seco", g.nsmallest(k, "precip_mm"))):
            for r, (_, x) in enumerate(sub.iterrows(), 1):
                rows.append((st, pid, "month", kind, r, int(x["year"]), int(x["month"]), x["precip_mm"]))
    return pd.DataFrame(rows, columns=["state", "point_id", "period_type", "kind", "rank", "year", "month", "precip_mm"])


# ------------------------------- gráficos -------------------------------------
def plot_overview(ann_stats: pd.DataFrame) -> None:
    apply_style()
    states = sorted(ann_stats["state"].unique())
    fig, axes = plt.subplots(5, 6, figsize=(18, 11), sharex=True)
    for ax, st in zip(axes.ravel(), states):
        g = ann_stats[(ann_stats["state"] == st) & ann_stats["complete"]]
        ax.plot(g["year"], g["annual_total_mm"], color=cfg.C_DATA, lw=1.2)
        ax.axhline(g["annual_total_mm"].mean(), color=cfg.C_NEUTRAL, lw=0.8, ls="--")
        ax.set_title(f"{st} · média {g['annual_total_mm'].mean():.0f} mm", fontsize=9)
        ax.tick_params(labelsize=7)
    for ax in axes.ravel()[len(states):]:
        ax.axis("off")
    fig.suptitle("Precipitação anual por estado (anos completos; tracejado = média)", fontsize=12, y=0.995)
    fig.supylabel("mm/ano")
    fig.tight_layout()
    fig.savefig(cfg.FIG_DIR / "evolution_annual_all_states.png")
    plt.close(fig)


def plot_climatology_heatmap(clim: pd.DataFrame) -> None:
    apply_style()
    piv = clim.pivot(index="state", columns="month", values="mean_mm")
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.grid(False)
    im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="Blues")
    ax.set_xticks(range(12), cfg.MONTH_NAMES_PT)
    ax.set_yticks(range(len(piv)), piv.index)
    ax.set_title("Climatologia mensal: precipitação média (mm)")
    fig.colorbar(im, ax=ax, shrink=0.7, label="mm/mês")
    fig.savefig(cfg.FIG_DIR / "climatology_monthly_heatmap.png")
    plt.close(fig)


def main():
    ensure_dirs()
    monthly, annual = read_output("monthly_precipitation.csv"), read_output("annual_precipitation.csv")
    ann_stats = build_annual_statistics(monthly, annual)
    clim = build_monthly_climatology(monthly)
    summary = build_state_summary(ann_stats, monthly, clim)
    ext = build_extremes(monthly, ann_stats)
    ann_stats.to_csv(cfg.OUTPUT_DIR / "annual_statistics.csv", index=False)
    clim.to_csv(cfg.OUTPUT_DIR / "monthly_climatology.csv", index=False)
    summary.to_csv(cfg.OUTPUT_DIR / "state_summary.csv", index=False)
    ext.to_csv(cfg.OUTPUT_DIR / "extreme_periods.csv", index=False)
    plot_overview(ann_stats)
    plot_climatology_heatmap(clim)
    print(summary[["state", "n_years_complete", "mean_annual_mm", "std_annual_mm", "cv_annual_pct"]]
          .round(1).to_string(index=False))


if __name__ == "__main__":
    main()
