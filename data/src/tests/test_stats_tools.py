"""Validação das implementações estatísticas e das regras de preparação de dados.

Execução:  python -m pytest tests -q      (ou: python tests/test_stats_tools.py)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import stats_tools as st
import data_preparation as prep
import precipitation_categories as pc
import trend_analysis as ta
import anomaly_analysis as an


# ----------------------------- Mann-Kendall ----------------------------------
def test_mk_hand_computed_monotonic():
    r = st.mann_kendall([1, 2, 3, 4, 5])
    assert r["s"] == 10
    assert abs(r["var_s"] - 5 * 4 * 15 / 18) < 1e-12
    assert abs(r["z"] - 9 / np.sqrt(5 * 4 * 15 / 18)) < 1e-12
    assert abs(r["p"] - 0.02752) < 1e-4 and r["tau"] == 1.0


def test_mk_ties_variance():
    # x = [1,1,2,2,3]: S=8 (pares empatados contam 0); correção de empates na variância
    r = st.mann_kendall([1, 1, 2, 2, 3])
    assert r["s"] == 8
    expected = (5 * 4 * 15 - 2 * (2 * 1 * 9)) / 18
    assert abs(r["var_s"] - expected) < 1e-12


def test_mk_matches_scipy_kendall():
    rng = np.random.default_rng(0)
    t = np.arange(40)
    x = 0.05 * t + rng.normal(size=40)
    mk = st.mann_kendall(x)
    tau, p = stats.kendalltau(t, x, method="asymptotic")
    assert abs(mk["tau"] - tau) < 1e-12
    assert abs(mk["p"] - p) < 0.01  # diferença = correção de continuidade


def test_mk_constant_series():
    r = st.mann_kendall([3.0] * 10)
    assert r["s"] == 0 and r["p"] == 1.0


# ----------------------------- Sen's slope -----------------------------------
def test_sen_matches_scipy_theilslopes():
    rng = np.random.default_rng(1)
    t = np.arange(1980, 2020, dtype=float)
    x = 3.0 * (t - 1980) + rng.normal(scale=20, size=len(t))
    sen = st.sens_slope(x, t)
    ref = stats.theilslopes(x, t)
    assert abs(sen["slope"] - ref.slope) < 1e-9
    assert abs(sen["intercept"] - (np.median(x) - sen["slope"] * np.median(t))) < 1e-9
    assert sen["ci_low"] < 3.0 < sen["ci_high"]


def test_sen_handles_gaps_in_time():
    t = np.array([1, 2, 3, 6, 7, 8], dtype=float)
    x = 2.0 * t
    assert abs(st.sens_slope(x, t)["slope"] - 2.0) < 1e-12


def test_sen_ci_coverage():
    rng = np.random.default_rng(2)
    t, hits, B = np.arange(40.0), 0, 400
    for _ in range(B):
        x = 1.5 * t + rng.normal(scale=15, size=40)
        s = st.sens_slope(x, t)
        hits += s["ci_low"] <= 1.5 <= s["ci_high"]
    assert 0.90 <= hits / B <= 0.99


# ----------------------------- autocorrelação --------------------------------
def test_acf_and_ljung_box():
    rng = np.random.default_rng(3)
    white = rng.normal(size=300)
    assert st.ljung_box(white, 10)[1] > 0.01
    ar = np.zeros(300)
    for i in range(1, 300):
        ar[i] = 0.7 * ar[i - 1] + rng.normal()
    assert st.acf(ar, 1)[1] > 0.5
    assert st.ljung_box(ar, 10)[1] < 1e-6
    assert st.acf(np.ones(10), 3)[1] == 0.0


def test_type1_error_and_hamed_rao_under_autocorrelation():
    rng = np.random.default_rng(4)
    n, B, phi = 43, 400, 0.6
    raw_rej = hr_rej = white_rej = 0
    t = np.arange(n, dtype=float)
    for _ in range(B):
        e = rng.normal(size=n)
        x = np.zeros(n)
        for i in range(1, n):
            x[i] = phi * x[i - 1] + e[i]
        raw_rej += st.mann_kendall(x)["p"] < 0.05
        hr_rej += st.hamed_rao(x, t)["p"] < 0.05
        white_rej += st.mann_kendall(rng.normal(size=n))["p"] < 0.05
    assert 0.02 <= white_rej / B <= 0.09          # ruído branco: ~5%
    assert raw_rej / B > 0.15                     # AR(1) sem correção: falso-positivo inflado
    assert hr_rej / B < raw_rej / B               # a correção reduz o excesso


def test_power_with_clear_trend():
    rng = np.random.default_rng(5)
    t = np.arange(40.0)
    det = sum(st.mann_kendall(0.8 * t + rng.normal(scale=8, size=40))["p"] < 0.05 for _ in range(200))
    assert det / 200 > 0.85


# ----------------------------- múltiplos testes ------------------------------
def test_benjamini_hochberg():
    np.testing.assert_allclose(st.benjamini_hochberg([0.01, 0.02, 0.03, 0.04, 0.05]), [0.05] * 5)
    np.testing.assert_allclose(st.benjamini_hochberg([0.001, 0.04, 0.03]), [0.003, 0.04, 0.04])
    out = st.benjamini_hochberg([0.01, np.nan, 0.5])
    assert np.isnan(out[1]) and abs(out[0] - 0.02) < 1e-12


def test_holm():
    np.testing.assert_allclose(st.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    assert (st.holm([0.2, 0.3]) <= 1).all()


# ----------------------------- preparação de dados ---------------------------
def _daily(state, start, end, value=1.0):
    d = pd.date_range(start, end, freq="D")
    return pd.DataFrame({"date": d.strftime("%Y-%m-%d"), "state": state, "precipitation_mm": value})


def test_cleaning_rules():
    df = _daily("SP", "2020-01-01", "2020-01-31")
    bad = pd.DataFrame({"date": ["2020-01-05", "2020-01-06", "2020-01-07", "2020-01-08", "bad", "2020-01-09"],
                        "state": ["sp", "São Paulo", "SP", "SP", "SP", "ZZ"],
                        "precipitation_mm": ["2,5", "-3", "9999", "abc", "1", "1"]})
    raw = pd.concat([df, df.iloc[:3], bad], ignore_index=True)
    clean, log = prep.clean_daily(raw)
    L = {r["check"]: r["count"] for r in log}
    assert L["datas_invalidas"] == 1 and L["estados_nao_reconhecidos"] == 1
    assert L["valores_negativos"] == 1 and L["valores_acima_do_limite_fisico"] == 1
    assert L["valores_nao_numericos"] == 1
    assert L["duplicatas_exatas"] >= 3
    assert set(clean["state"]) == {"SP"}
    assert clean.duplicated(["state", "date"]).sum() == 0


def test_monthly_completeness_and_leap_year():
    feb = _daily("SP", "2020-02-01", "2020-02-29")         # bissexto: 29 dias
    grid, _, _ = prep.build_daily_grid(prep.clean_daily(feb)[0])
    m = prep.aggregate_monthly(grid)
    assert m.loc[0, "n_days_expected"] == 29 and bool(m.loc[0, "complete"])
    assert m.loc[0, "precip_mm"] == 29.0
    # um dia ausente => mês incompleto e precip_mm NaN (nunca soma parcial como se fosse total)
    feb2 = feb.drop(index=10)
    res = prep.prepare(feb2)
    assert not res["monthly"].loc[0, "complete"] and np.isnan(res["monthly"].loc[0, "precip_mm"])
    assert res["monthly"].loc[0, "precip_partial_mm"] == 28.0


def test_annual_completeness():
    y = pd.concat([_daily("SP", "2019-01-01", "2020-12-31")])
    y = y[~((y["date"] >= "2020-07-01") & (y["date"] <= "2020-07-03"))]
    res = prep.prepare(y)
    a = res["annual"].set_index("year")
    assert bool(a.loc[2019, "complete"]) and a.loc[2019, "annual_total_mm"] == 365.0
    assert not bool(a.loc[2020, "complete"]) and np.isnan(a.loc[2020, "annual_total_mm"])
    assert a.loc[2020, "n_months_complete"] == 11


# ----------------------------- categorias e anomalias ------------------------
def _monthly_frame(n_years=40, seed=0):
    rng = np.random.default_rng(seed)
    rows = [(s, y, m, rng.gamma(2.0, 60.0)) for s in ("AA", "BB") for y in range(1980, 1980 + n_years)
            for m in range(1, 13)]
    df = pd.DataFrame(rows, columns=["state", "year", "month", "precip_mm"])
    df["complete"] = True
    ann = df.groupby(["state", "year"], as_index=False)["precip_mm"].sum().rename(columns={"precip_mm": "annual_total_mm"})
    ann["complete"] = True
    return df, ann


def test_category_boundaries_and_frequencies():
    assert pc.classify(5, 10, 20, 30, 40) == "muito_seco"
    assert pc.classify(10, 10, 20, 30, 40) == "seco"       # P10 ≤ x < P30
    assert pc.classify(20, 10, 20, 30, 40) == "normal"     # P30 ≤ x ≤ P70
    assert pc.classify(30, 10, 20, 30, 40) == "normal"
    assert pc.classify(40, 10, 20, 30, 40) == "chuvoso"    # P70 < x ≤ P90
    assert pc.classify(41, 10, 20, 30, 40) == "muito_chuvoso"
    m, a = _monthly_frame()
    cat = pc.build_categories(m, a)
    fr = cat[cat.period_type == "monthly"]["category"].value_counts(normalize=True) * 100
    for k, e in zip(["muito_seco", "seco", "normal", "chuvoso", "muito_chuvoso"], [10, 20, 40, 20, 10]):
        assert abs(fr[k] - e) < 4


def test_seasonality_respected_in_categories():
    m, a = _monthly_frame()
    m.loc[m.month == 7, "precip_mm"] = m.loc[m.month == 7, "precip_mm"] * 0.05   # julho muito seco
    cat = pc.build_categories(m, a)
    jul = cat[(cat.period_type == "monthly") & (cat.month == 7)]
    assert abs((jul["category"] == "muito_seco").mean() - 0.10) < 0.06  # ~10% muito seco DENTRO de julho


def test_expanding_mode_uses_only_previous_years():
    m, a = _monthly_frame(n_years=25)
    cat = pc.build_categories(m, a, mode="expanding", min_ref=10)
    mo = cat[(cat.period_type == "monthly") & (cat.state == "AA") & (cat.month == 1)].sort_values("year")
    assert (mo["n_ref_years"].to_numpy() == np.arange(25)).all()
    assert (mo.loc[mo.n_ref_years < 10, "category"] == "referencia_insuficiente").all()


def test_zscore_and_anomaly():
    m, a = _monthly_frame()
    out = an.build_anomalies(m, a)
    mo = out[(out.period_type == "monthly") & (out.state == "AA") & (out.month == 3)]
    assert abs(mo["zscore"].mean()) < 1e-9 and abs(mo["zscore"].std(ddof=1) - 1) < 1e-9
    assert abs(mo["anomaly_mm"].sum()) < 1e-6
    assert an.classify_z(-2.5) == "significativamente_seco" and an.classify_z(0.3) == "normal"


def test_trend_table_separates_direction_from_significance():
    rng = np.random.default_rng(7)
    yrs = np.arange(1980, 2021)
    rows = []
    for s, slope in (("UP", 12.0), ("FL", 0.0), ("NO", 2.0)):
        v = 1000 + slope * (yrs - 1980) + rng.normal(scale=150 if s == "NO" else 40, size=len(yrs))
        rows += [(s, y, x, True) for y, x in zip(yrs, v)]
    ann = pd.DataFrame(rows, columns=["state", "year", "annual_total_mm", "complete"])
    tr = ta.build_trend_table(ann).set_index("state")
    assert tr.loc["UP", "trend_class"] == "crescente"
    assert tr.loc["FL", "trend_class"] == "sem_evidencia_suficiente"
    assert tr.loc["NO", "trend_class"] == "sem_evidencia_suficiente" and tr.loc["NO", "sens_slope_mm_yr"] != 0


def test_short_series_flagged():
    ann = pd.DataFrame({"state": "XX", "year": range(2000, 2006), "annual_total_mm": range(6), "complete": True})
    assert ta.build_trend_table(ann).iloc[0]["trend_class"] == "dados_insuficientes"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
