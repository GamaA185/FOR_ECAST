"""Perfil individual de um estado: quanto choveu, como se comportou, tendência e magnitude.

Uso:  python state_profile.py SP            (imprime o perfil e salva a figura)
      python state_profile.py --all         (gera os 27 perfis)
Requer que o pipeline já tenha gerado os CSVs em output/.
"""
from __future__ import annotations

import argparse
import textwrap

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config as cfg
from common import apply_style, ensure_dirs, interpret_trend, month_name, read_output


def load_tables() -> dict:
    return {
        "annual": read_output("annual_statistics.csv"),
        "summary": read_output("state_summary.csv"),
        "clim": read_output("monthly_climatology.csv"),
        "cat": read_output("precipitation_categories.csv"),
        "anom": read_output("anomalies.csv"),
        "trend": read_output("trend_analysis.csv"),
        "dec": read_output("decadal_comparison.csv"),
        "chg": read_output("decadal_changes.csv"),
    }


def profile_text(uf: str, t: dict) -> str:
    s = t["summary"].query("state == @uf").iloc[0]
    tr = t["trend"].query("state == @uf").iloc[0]
    L = [f"=== {uf} · {cfg.UF_NAMES[uf]} ===",
         f"Ponto de referência: {s['point_id']}", "",
         "QUANTO CHOVEU",
         f"  Média anual: {s['mean_annual_mm']:.0f} mm (desvio-padrão {s['std_annual_mm']:.0f} mm; "
         f"CV {s['cv_annual_pct']:.0f}%) em {s['n_years_complete']} anos completos "
         f"({s['first_complete_year']}–{s['last_complete_year']}).",
         f"  Média mensal: {s['mean_monthly_mm']:.0f} mm. Mês climatologicamente mais chuvoso: "
         f"{month_name(s['wettest_calendar_month'])} ({s['wettest_calendar_month_mean_mm']:.0f} mm); "
         f"mais seco: {month_name(s['driest_calendar_month'])} ({s['driest_calendar_month_mean_mm']:.0f} mm).",
         f"  Ano mais chuvoso: {s['wettest_year']} ({s['wettest_year_mm']:.0f} mm); "
         f"mais seco: {s['driest_year']} ({s['driest_year_mm']:.0f} mm).",
         f"  Mês mais chuvoso da série: {s['wettest_month_ever']} ({s['wettest_month_ever_mm']:.0f} mm); "
         f"mais seco: {s['driest_month_ever']} ({s['driest_month_ever_mm']:.0f} mm).", ""]

    ca = t["cat"].query("state == @uf and period_type == 'annual'").sort_values("year").tail(5)
    aa = t["anom"].query("state == @uf and period_type == 'annual'").sort_values("year").tail(5)
    L.append("COMPORTAMENTO HISTÓRICO (últimos anos completos)")
    for (_, c), (_, a) in zip(ca.iterrows(), aa.iterrows()):
        z = f"{a['zscore']:+.2f}" if pd.notna(a["zscore"]) else "–"
        L.append(f"  {int(c['year'])}: {c['precip_mm']:.0f} mm · {c['category']} "
                 f"(percentil {c['percentile_rank']:.0f}) · anomalia {a['anomaly_mm']:+.0f} mm · Z={z}")
    sig = t["anom"].query("state == @uf and period_type == 'annual' and significant")
    L.append(f"  Anos com |Z| ≥ {cfg.Z_SIGNIFICANT:g}: " +
             (", ".join(f"{int(r.year)} (Z={r.zscore:+.1f})" for r in sig.itertuples()) or "nenhum"))
    L.append("")
    L.append("TENDÊNCIA (precipitação anual)")
    L.append(textwrap.fill("  " + interpret_trend(tr), 100, subsequent_indent="  "))
    if tr["trend_class"] != "dados_insuficientes":
        L.append(f"  Mann-Kendall: S={tr['mk_s']:.0f}, Z={tr['mk_z']:.2f}, tau={tr['mk_tau']:.2f}; "
                 f"r1 dos resíduos={tr['lag1_autocorr_detrended']:.2f} (limite ±{tr['lag1_autocorr_bound']:.2f}); "
                 f"Ljung-Box p={tr['ljung_box_p']:.3f}.")
        if isinstance(tr["notes"], str) and tr["notes"]:
            L.append(f"  Observações: {tr['notes']}.")
    L.append("")
    ch = t["chg"].query("state == @uf")
    L.append("COMPARAÇÃO ENTRE DÉCADAS (média anual, anos completos)")
    for r in t["dec"].query("state == @uf").itertuples():
        d = f" ({r.pct_change_vs_prev_decade:+.1f}% vs. anterior)" if pd.notna(r.pct_change_vs_prev_decade) else ""
        part = " [década parcial]" if r.partial_decade else ""
        L.append(f"  {int(r.decade)}s: {r.mean_annual_mm:.0f} mm em {r.n_years} anos{d}{part}")
    if len(ch):
        c = ch.iloc[0]
        L.append(f"  {int(c['first_decade'])}s → {int(c['last_decade'])}s: {c['pct_change']:+.1f}% "
                 f"(comparação descritiva; n={int(c['n_years_first'])} vs. {int(c['n_years_last'])} anos)")
        L.append("  Diferença entre décadas não foi submetida a teste de significância; tamanhos amostrais e janelas temporais são desiguais.")
    return "\n".join(L)


def profile_figure(uf: str, t: dict, path) -> None:
    apply_style()
    ann = t["annual"].query("state == @uf and complete")
    tr = t["trend"].query("state == @uf").iloc[0]
    clim = t["clim"].query("state == @uf")
    az = t["anom"].query("state == @uf and period_type == 'annual'").sort_values("year")
    mz = t["anom"].query("state == @uf and period_type == 'monthly'")
    dec = t["dec"].query("state == @uf")

    fig, axes = plt.subplots(2, 3, figsize=(16, 8.5))
    ax = axes[0, 0]
    ax.plot(ann["year"], ann["annual_total_mm"], color=cfg.C_DATA, lw=1.3, marker="o", ms=3)
    ax.axhline(ann["annual_total_mm"].mean(), color=cfg.C_NEUTRAL, ls="--", lw=0.9, label="média")
    if tr["trend_class"] != "dados_insuficientes":
        xs = np.array([tr["first_year"], tr["last_year"]])
        sig = tr["trend_class"] != "sem_evidencia_suficiente"
        ax.plot(xs, tr["sens_slope_mm_yr"] * (xs - ann["year"].median()) + ann["annual_total_mm"].median(),
                color=cfg.C_TREND, lw=2 if sig else 1.3, ls="-" if sig else "--",
                label=f"Sen {tr['sens_slope_mm_yr']:+.1f} mm/ano ({'signif.' if sig else 'n.s.'})")
    ax.set(title="Precipitação anual", ylabel="mm"); ax.legend()

    ax = axes[0, 1]
    ax.bar(clim["month"], clim["mean_mm"], color=cfg.C_DATA, width=0.65)
    # Em amostras pequenas/empates, a média pode ficar fora do intervalo P10–P90.
    # Barras de erro precisam ser não negativas para o Matplotlib.
    lower = np.maximum(0, clim["mean_mm"] - clim["p10_mm"])
    upper = np.maximum(0, clim["p90_mm"] - clim["mean_mm"])
    ax.errorbar(clim["month"], clim["mean_mm"], yerr=[lower, upper],
                fmt="none", ecolor="#3a3a37", lw=0.9, capsize=2)
    ax.set_xticks(range(1, 13), cfg.MONTH_NAMES_PT, fontsize=8)
    ax.set(title="Climatologia mensal (média; barras = P10–P90)", ylabel="mm")

    ax = axes[0, 2]
    colors = np.where(az["zscore"] >= 0, "#2a78d6", "#eb6834")
    ax.bar(az["year"], az["zscore"], color=colors, width=0.8)
    for v in (-2, -1, 1, 2):
        ax.axhline(v, color=cfg.C_NEUTRAL, lw=0.6, ls=":" if abs(v) == 1 else "--")
    ax.set(title="Anomalia anual padronizada (Z) · laranja = seco", ylabel="Z")

    ax = axes[1, 0]
    piv = mz.pivot(index="year", columns="month", values="zscore")
    ax.grid(False)
    im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="RdBu", vmin=-3, vmax=3)
    ax.set_xticks(range(12), cfg.MONTH_NAMES_PT, fontsize=7)
    yrs = piv.index.to_numpy()
    ax.set_yticks(range(0, len(yrs), 5), yrs[::5], fontsize=7)
    ax.set_title("Z mensal (ano × mês)")
    fig.colorbar(im, ax=ax, shrink=0.8)

    ax = axes[1, 1]
    ax.bar([f"{int(d)}s" for d in dec["decade"]], dec["mean_annual_mm"], color=cfg.C_DATA, width=0.6)
    for i, r in enumerate(dec.itertuples()):
        ax.text(i, r.mean_annual_mm, f"n={r.n_years}", ha="center", va="bottom", fontsize=8)
    ax.set(title="Média anual por década", ylabel="mm")

    ax = axes[1, 2]
    ax.axis("off")
    ax.text(0, 1, "Interpretação da tendência\n\n" + "\n".join(textwrap.wrap(interpret_trend(tr), 62)),
            va="top", fontsize=9.5, transform=ax.transAxes)
    fig.suptitle(f"{uf} · {cfg.UF_NAMES[uf]}", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("state", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    ensure_dirs()
    t = load_tables()
    ufs = sorted(t["summary"]["state"]) if args.all else [args.state.upper()]
    texts = []
    for uf in ufs:
        txt = profile_text(uf, t)
        texts.append(txt)
        profile_figure(uf, t, cfg.STATE_FIG_DIR / f"state_{uf}.png")
        if not args.quiet:
            print(txt, "\n")
    if args.all:
        (cfg.OUTPUT_DIR / "state_profiles.txt").write_text("\n\n".join(texts), encoding="utf-8")


if __name__ == "__main__":
    main()
