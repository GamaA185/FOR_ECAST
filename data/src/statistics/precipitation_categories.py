"""Tarefa 3 — Categorias de precipitação (percentis históricos por estado).

Muito seco: < P10 · Seco: P10 ≤ x < P30 · Normal: P30 ≤ x ≤ P70
Chuvoso: P70 < x ≤ P90 · Muito chuvoso: > P90

Mensal: cada mês é comparado com o MESMO mês do calendário nos outros anos do
mesmo estado (sazonalidade respeitada). Anual: comparado com os demais anos.

Modos de referência:
  full      (padrão) — todos os anos completos da série, incluindo o ano
              avaliado e anos futuros (classificação retrospectiva);
  expanding — somente anos ANTERIORES ao avaliado (mín. MIN_REF_YEARS anos),
              sem informação futura (classificação progressiva).
Percentis: interpolação linear (numpy.percentile, método 7).
Documentação detalhada: docs/classificacao_percentis.md.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

import config as cfg
from common import ensure_dirs, read_output


def pct_rank(ref: np.ndarray, v: float) -> float:
    """Posição percentual de v em ref (empates contam metade)."""
    return 100.0 * ((ref < v).sum() + 0.5 * (ref == v).sum()) / len(ref)


def classify(v: float, p10: float, p30: float, p70: float, p90: float) -> str:
    if np.isnan([v, p10, p30, p70, p90]).any():
        return "referencia_insuficiente"
    if v < p10:
        return "muito_seco"
    if v < p30:
        return "seco"
    if v <= p70:
        return "normal"
    if v <= p90:
        return "chuvoso"
    return "muito_chuvoso"


def _group_rows(years, vals, mode: str, min_ref: int):
    out, th_full = [], None
    if mode == "full" and len(vals) >= min_ref:
        th_full = np.percentile(vals, cfg.CATEGORY_PCTS)
    for i, (y, v) in enumerate(zip(years, vals)):
        ref = vals if mode == "full" else vals[:i]
        if len(ref) < min_ref:
            th, rank = np.full(4, np.nan), np.nan
        else:
            th = th_full if mode == "full" else np.percentile(ref, cfg.CATEGORY_PCTS)
            rank = pct_rank(ref, v)
        out.append((y, v, *th, len(ref), classify(v, *th), rank))
    return out


def build_categories(monthly: pd.DataFrame, annual: pd.DataFrame, mode: str = "full",
                     min_ref: int = cfg.MIN_REF_YEARS) -> pd.DataFrame:
    monthly = monthly.copy()
    annual = annual.copy()
    if "point_id" not in monthly.columns:
        monthly["point_id"] = monthly["state"].astype(str)
    if "point_id" not in annual.columns:
        annual["point_id"] = annual["state"].astype(str)
    cols = ["year", "precip_mm", "p10_mm", "p30_mm", "p70_mm", "p90_mm",
            "n_ref_years", "category", "percentile_rank"]
    frames = []
    mc = monthly[monthly["complete"]].sort_values(["state", "month", "year"])
    for (st, pid, m), g in mc.groupby(["state", "point_id", "month"]):
        d = pd.DataFrame(_group_rows(g["year"].to_numpy(), g["precip_mm"].to_numpy(), mode, min_ref), columns=cols)
        d.insert(0, "month", m)
        d.insert(0, "period_type", "monthly")
        d.insert(0, "point_id", pid)
        d.insert(0, "state", st)
        frames.append(d)
    ac = annual[annual["complete"]].sort_values(["state", "point_id", "year"])
    for (st, pid), g in ac.groupby(["state", "point_id"]):
        d = pd.DataFrame(_group_rows(g["year"].to_numpy(), g["annual_total_mm"].to_numpy(), mode, min_ref), columns=cols)
        d.insert(0, "month", np.nan)
        d.insert(0, "period_type", "annual")
        d.insert(0, "point_id", pid)
        d.insert(0, "state", st)
        frames.append(d)
    out = pd.concat(frames, ignore_index=True)
    out["reference"] = "full_history" if mode == "full" else "previous_years"
    th = out[["p10_mm", "p30_mm", "p70_mm", "p90_mm"]].to_numpy()
    with np.errstate(invalid="ignore"):
        out["thresholds_degenerate"] = (np.diff(th, axis=1) <= 0).any(axis=1) & ~np.isnan(th).any(axis=1)
    return out.sort_values(["state", "point_id", "period_type", "year", "month"]).reset_index(drop=True)


def category_frequency(cat: pd.DataFrame) -> pd.DataFrame:
    c = cat[cat["category"] != "referencia_insuficiente"]
    ct = pd.crosstab([c["state"], c["point_id"], c["period_type"]], c["category"], normalize="index") * 100
    ct = ct.reindex(columns=cfg.CATEGORY_LABELS, fill_value=0).round(2).reset_index()
    ct.columns.name = None
    return ct


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["full", "expanding"], default="full")
    args = ap.parse_args(argv)
    ensure_dirs()
    cat = build_categories(read_output("monthly_precipitation.csv"),
                           read_output("annual_precipitation.csv"), mode=args.mode)
    cat.to_csv(cfg.OUTPUT_DIR / "precipitation_categories.csv", index=False)
    category_frequency(cat).to_csv(cfg.OUTPUT_DIR / "category_frequency.csv", index=False)
    print(cat["category"].value_counts())
    print("meses com limiares degenerados (empates em P10/P30/P70/P90):",
          int(cat["thresholds_degenerate"].sum()))


if __name__ == "__main__":
    main()
