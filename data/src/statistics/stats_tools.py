"""Ferramentas estatísticas implementadas apenas com NumPy/SciPy.

Mann-Kendall, Sen's Slope (com IC de Gilbert), autocorrelação, Ljung-Box,
correção de Hamed-Rao e ajuste para múltiplos testes (Benjamini-Hochberg e Holm).
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def _z_to_p(z: float) -> float:
    return float(2.0 * stats.norm.sf(abs(z)))


def mann_kendall(x) -> dict:
    """Teste de Mann-Kendall (bicaudal, aproximação normal com correção de empates
    e de continuidade).  H0: não há tendência monotônica."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 3:
        raise ValueError("Mann-Kendall exige ao menos 3 observações")
    iu = np.triu_indices(n, k=1)
    s = int(np.sign((x[None, :] - x[:, None])[iu]).sum())
    _, counts = np.unique(x, return_counts=True)
    t = counts[counts > 1].astype(float)
    var_s = (n * (n - 1) * (2 * n + 5) - np.sum(t * (t - 1) * (2 * t + 5))) / 18.0
    if var_s <= 0 or s == 0:
        z = 0.0
    else:
        z = (s - 1) / np.sqrt(var_s) if s > 0 else (s + 1) / np.sqrt(var_s)
    return {"n": n, "s": s, "var_s": float(var_s), "z": float(z),
            "p": _z_to_p(z) if var_s > 0 else 1.0, "tau": s / (n * (n - 1) / 2.0)}


def _rank_value(sorted_vals: np.ndarray, r: float) -> float:
    """Valor na posição (1-based, real) r, com interpolação linear."""
    N = len(sorted_vals)
    r = min(max(r, 1.0), float(N))
    lo = int(np.floor(r))
    frac = r - lo
    i = lo - 1
    j = min(i + 1, N - 1)
    return float(sorted_vals[i] + frac * (sorted_vals[j] - sorted_vals[i]))


def sens_slope(x, t=None, alpha: float = 0.05) -> dict:
    """Inclinação de Sen (mediana das inclinações par a par) e IC (Gilbert, 1987)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    t = np.arange(n, dtype=float) if t is None else np.asarray(t, dtype=float)
    iu = np.triu_indices(n, k=1)
    dt = (t[None, :] - t[:, None])[iu]
    dx = (x[None, :] - x[:, None])[iu]
    ok = dt != 0
    slopes = np.sort(dx[ok] / dt[ok])
    slope = float(np.median(slopes))
    intercept = float(np.median(x) - slope * np.median(t))
    var_s = mann_kendall(x)["var_s"]
    c = stats.norm.ppf(1 - alpha / 2) * np.sqrt(var_s)
    N = len(slopes)
    lo = _rank_value(slopes, (N - c) / 2.0)
    hi = _rank_value(slopes, (N + c) / 2.0 + 1.0)
    return {"slope": slope, "intercept": intercept, "ci_low": lo, "ci_high": hi}


def acf(x, nlags: int) -> np.ndarray:
    """Autocorrelação amostral (estimador clássico, denominador comum)."""
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    denom = float(np.sum(x ** 2))
    out = np.zeros(nlags + 1)
    out[0] = 1.0
    if denom == 0:
        return out
    for k in range(1, nlags + 1):
        out[k] = np.sum(x[:-k] * x[k:]) / denom
    return out


def ljung_box(x, lags: int) -> tuple[float, float]:
    """Estatística Q de Ljung-Box e p-valor (H0: ausência de autocorrelação até `lags`)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    r = acf(x, lags)[1:]
    q = float(n * (n + 2) * np.sum(r ** 2 / (n - np.arange(1, lags + 1))))
    return q, float(stats.chi2.sf(q, lags))


def hamed_rao(x, t=None, alpha: float = 0.05) -> dict:
    """Mann-Kendall com variância corrigida por autocorrelação (Hamed & Rao, 1998).

    Os ranks da série sem tendência (retirada a reta de Sen) são testados lag a lag;
    só as autocorrelações significativas entram no fator de correção. O fator nunca
    reduz a variância (mínimo 1), escolha conservadora.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    t = np.arange(n, dtype=float) if t is None else np.asarray(t, dtype=float)
    mk = mann_kendall(x)
    slope = sens_slope(x, t, alpha)["slope"]
    ranks = stats.rankdata(x - slope * t)
    rho = acf(ranks, n - 1)
    bound = stats.norm.ppf(1 - alpha / 2) / np.sqrt(n)
    sni, nsig = 0.0, 0
    for k in range(1, n - 1):
        if abs(rho[k]) > bound:
            sni += (n - k) * (n - k - 1) * (n - k - 2) * rho[k]
            nsig += 1
    factor = 1.0 + 2.0 / (n * (n - 1) * (n - 2)) * sni
    factor_used = max(1.0, factor)
    var_adj = mk["var_s"] * factor_used
    s = mk["s"]
    if var_adj <= 0 or s == 0:
        z = 0.0
    else:
        z = (s - 1) / np.sqrt(var_adj) if s > 0 else (s + 1) / np.sqrt(var_adj)
    return {"factor_raw": float(factor), "factor_used": float(factor_used),
            "n_sig_lags": nsig, "z": float(z), "p": _z_to_p(z)}


def benjamini_hochberg(p) -> np.ndarray:
    """p-valores ajustados pelo procedimento de Benjamini-Hochberg (controle de FDR)."""
    p = np.asarray(p, dtype=float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    m = len(pv)
    if m == 0:
        return out
    order = np.argsort(pv)
    adj = pv[order] * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    res = np.empty(m)
    res[order] = np.clip(adj, 0, 1)
    out[ok] = res
    return out


def holm(p) -> np.ndarray:
    """p-valores ajustados por Holm-Bonferroni (controle de FWER)."""
    p = np.asarray(p, dtype=float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    m = len(pv)
    if m == 0:
        return out
    order = np.argsort(pv)
    adj = np.maximum.accumulate(pv[order] * (m - np.arange(m)))
    res = np.empty(m)
    res[order] = np.clip(adj, 0, 1)
    out[ok] = res
    return out
