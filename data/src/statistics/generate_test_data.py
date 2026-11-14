"""Gera dados diários SINTÉTICOS no formato esperado da integração Meteomatics.

ATENÇÃO: não são dados reais. Servem para testar o módulo estatístico:
  * sazonalidade distinta por estado;
  * tendências conhecidas (plantadas) em alguns estados, e persistência (AR1)
    em outros SEM tendência, para testar a correção de autocorrelação;
  * defeitos injetados: duplicatas, conflitos, negativos, outliers, lacunas,
    grafias de estado, datas inválidas, texto no lugar de número.
A verdade plantada fica em data/sample_planted_truth.csv.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

# annual_mm, mês de pico, intensidade da sazonalidade k, tendência (%/ano do nível inicial),
# phi (AR1 anual), desvio da variabilidade interanual
PARAMS = {
    "AC": (2000, 1, .6, 0.0, .1, .12), "AL": (1200, 6, .6, 0.0, .1, .18),
    "AP": (2300, 4, .7, 0.0, .1, .12), "AM": (2300, 2, .5, 0.0, .1, .10),
    "BA": (900, 12, .7, -0.3, .1, .18), "CE": (900, 3, 1.0, 0.0, .80, .30),
    "DF": (1400, 12, .9, -0.4, .1, .15), "ES": (1200, 12, .6, 0.0, .1, .15),
    "GO": (1500, 12, .9, -0.9, .1, .14), "MA": (1500, 3, .8, 0.0, .1, .15),
    "MT": (1500, 1, .85, -0.9, .1, .12), "MS": (1300, 1, .7, 0.0, .1, .15),
    "MG": (1300, 12, .9, 0.0, .1, .13), "PA": (2000, 3, .6, 0.0, .1, .10),
    "PB": (800, 6, .8, 0.0, .1, .22), "PR": (1600, 1, .3, 0.4, .1, .15),
    "PE": (1000, 6, .8, 0.0, .85, .28), "PI": (1000, 3, .9, 0.0, .1, .20),
    "RJ": (1300, 12, .6, 0.0, .1, .14), "RN": (800, 4, 1.0, 0.0, .1, .22),
    "RS": (1600, 9, .15, 0.6, .1, .18), "RO": (2000, 1, .6, 0.0, .1, .10),
    "RR": (1800, 7, .5, 0.0, .1, .12), "SC": (1700, 1, .2, 1.0, .1, .15),
    "SP": (1400, 1, .6, 0.0, .1, .13), "SE": (1200, 6, .6, 0.0, .1, .18),
    "TO": (1500, 1, .8, 0.0, .1, .13),
}


def simulate_state(rng, dates: pd.DatetimeIndex, p) -> np.ndarray:
    annual, peak, k, trend, phi, sd = p
    months = np.arange(1, 13)
    shape = np.clip(1 + k * np.cos(2 * np.pi * (months - peak) / 12), 0.02, None)
    clim = annual * shape / shape.sum()
    years = np.arange(dates.year.min(), dates.year.max() + 1)
    e = rng.normal(0, sd, len(years))
    a = np.zeros(len(years))
    a[0] = e[0]
    for i in range(1, len(years)):
        a[i] = phi * a[i - 1] + e[i] * np.sqrt(1 - phi ** 2)
    yf = np.exp(a - sd ** 2 / 2)
    tf = 1 + trend / 100 * (years - years[0])
    mf = np.exp(rng.normal(0, 0.3, (len(years), 12)) - 0.045)
    yi = dates.year.to_numpy() - years[0]
    mi = dates.month.to_numpy() - 1
    mu = clim[mi] * yf[yi] * tf[yi] * mf[yi, mi] / dates.days_in_month.to_numpy()
    f = np.clip(mu / 9.0, 0.02, 0.8)
    wet = rng.random(len(dates)) < f
    x = rng.gamma(0.7, (mu / f) / 0.7)
    return np.minimum(np.where(wet, x, 0.0), 250.0).round(1)


def generate(seed: int = 42, start="1980-01-01", end="2026-10-31") -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, end, freq="D")
    frames, truth = [], []
    for uf, p in PARAMS.items():
        frames.append(pd.DataFrame({"date": dates, "state": uf,
                                    "precipitation_mm": simulate_state(rng, dates, p)}))
        truth.append({"state": uf, "planted_trend_pct_per_year_of_initial_level": p[3],
                      "planted_slope_mm_yr_approx": p[0] * p[3] / 100,
                      "planted_ar1_phi": p[4]})
    df = pd.concat(frames, ignore_index=True)

    # ---------------- defeitos injetados ----------------
    df = df[~((df.state == "AP") & (df.date < "1986-01-01"))]                 # série começa em 1986
    df = df[~((df.state == "AM") & (df.date.dt.strftime("%Y-%m") == "2003-05"))]  # mês inteiro ausente
    df = df[~((df.state == "RR") & (df.date >= "1999-08-10") & (df.date <= "1999-08-29"))]
    df = df[~((df.state == "MT") & (df.date >= "2011-01-01") & (df.date <= "2011-03-31"))]
    df = df.reset_index(drop=True)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df["precipitation_mm"] = df["precipitation_mm"].astype(object)
    n = len(df)
    pick = lambda k: rng.choice(n, k, replace=False)
    df.loc[pick(int(n * 1e-4)), "precipitation_mm"] = np.nan
    df.loc[pick(25), "precipitation_mm"] = -1.0
    df.loc[pick(10), "precipitation_mm"] = -0.01
    df.loc[pick(8), "precipitation_mm"] = 9999.0
    df.loc[pick(5), "precipitation_mm"] = "sem_dado"
    df.loc[pick(3), "date"] = "not-a-date"
    sp = df.index[df.state == "SP"]
    df.loc[rng.choice(sp, int(len(sp) * .05), replace=False), "state"] = \
        rng.choice(["sp", " SP ", "São Paulo"], int(len(sp) * .05))
    df.loc[pick(2), "state"] = "XX"

    dup_exact = df.iloc[pick(400)]
    dup_conf = df.iloc[pick(40)].copy()
    dup_conf["precipitation_mm"] = pd.to_numeric(dup_conf["precipitation_mm"], errors="coerce") * 1.1 + 1
    df = pd.concat([df, dup_exact, dup_conf], ignore_index=True)
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df, pd.DataFrame(truth)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(cfg.DATA_DIR / "sample_meteomatics_daily.csv.gz"))
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)
    cfg.DATA_DIR.mkdir(parents=True, exist_ok=True)
    df, truth = generate(args.seed)
    df.to_csv(args.out, index=False)
    truth.to_csv(cfg.DATA_DIR / "sample_planted_truth.csv", index=False)
    print(f"{len(df):,} linhas gravadas em {args.out}")


if __name__ == "__main__":
    main()
