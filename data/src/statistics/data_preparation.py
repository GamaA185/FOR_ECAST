"""Tarefa 1 — Preparação dos dados.

Entrada esperada (contrato com o desenvolvedor de integração), CSV/CSV.GZ/Parquet:

    date            data do acumulado diário (ISO 8601; ex.: 2020-03-15)
    state           sigla UF (SP) ou nome do estado (São Paulo)
    precipitation_mm  precipitação acumulada no dia, em mm
    point_id        (opcional) identificador do ponto de referência; as séries
                    de pontos diferentes são preservadas separadamente

Saídas (em output/): monthly_precipitation.csv, annual_precipitation.csv,
incomplete_periods.csv, data_quality_report.csv, data_quality_by_state.csv.
"""
from __future__ import annotations

import argparse
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg
from common import ensure_dirs

COLUMN_ALIASES = {
    "date": ["date", "data", "validdate", "valid_date", "time", "datetime", "dia"],
    "state": ["state", "uf", "estado", "sigla", "sigla_uf"],
    "precip_mm": ["precipitation_mm", "precip_mm", "precipitacao_mm", "precipitacao",
                  "precipitation", "precip", "precip_24h:mm", "precip_24h_mm", "value"],
    "point_id": ["point_id", "location_id", "ponto", "location"],
}


def _strip(s) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).strip().lower()


_STATE_LOOKUP = {}
for _uf, _name in cfg.UF_NAMES.items():
    _STATE_LOOKUP[_uf.lower()] = _uf
    _STATE_LOOKUP[_strip(_name)] = _uf


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    lowered = {_strip(c): c for c in df.columns}
    mapping = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for a in aliases:
            if a in lowered:
                mapping[lowered[a]] = canonical
                break
    missing = [c for c in ("date", "state", "precip_mm") if c not in mapping.values()]
    if missing:
        raise ValueError(f"Colunas obrigatórias não encontradas: {missing}. "
                         f"Colunas recebidas: {list(df.columns)}")
    return df.rename(columns=mapping)[list(mapping.values())].copy()


def _longest_run(mask: np.ndarray) -> int:
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def clean_daily(raw: pd.DataFrame, max_daily_mm: float = cfg.MAX_DAILY_MM,
                today=None) -> tuple[pd.DataFrame, list[dict]]:
    """Limpa os dados diários. Retorna (dados limpos, log de verificações)."""
    log: list[dict] = []

    def add(check, count, action, detail=""):
        log.append({"check": check, "count": int(count), "action": action, "detail": detail})

    df = _rename_columns(raw)
    add("registros_recebidos", len(df), "informativo")

    # --- datas --------------------------------------------------------------
    dates = pd.to_datetime(df["date"], errors="coerce", utc=True, format="ISO8601")
    n_bad = int(dates.isna().sum())
    if n_bad > 0.5 * len(df):
        raise ValueError("Mais de 50% das datas não puderam ser lidas; use o formato ISO 8601.")
    df["date"] = dates.dt.tz_localize(None).dt.normalize()
    add("datas_invalidas", n_bad, "registros removidos")
    df = df[df["date"].notna()]
    if today is not None:
        fut = df["date"] > pd.Timestamp(today)
        add("datas_futuras", fut.sum(), "registros removidos")
        df = df[~fut]

    # --- estados ------------------------------------------------------------
    uf = df["state"].astype(str).map(_strip).map(_STATE_LOOKUP)
    unknown = uf.isna()
    detail = ", ".join(sorted(df.loc[unknown, "state"].astype(str).unique())[:10])
    add("estados_nao_reconhecidos", unknown.sum(), "registros removidos", detail)
    renamed = (df["state"].astype(str).str.strip() != uf) & ~unknown
    add("estados_com_grafia_normalizada", renamed.sum(), "convertidos para sigla UF")
    df = df.assign(state=uf)[~unknown]

    # --- valores ------------------------------------------------------------
    s = df["precip_mm"]
    if pd.api.types.is_numeric_dtype(s):
        num = s.astype(float)
        non_numeric = pd.Series(False, index=df.index)
    else:
        txt = s.astype("string").str.strip().str.replace(",", ".", regex=False)
        num = pd.to_numeric(txt, errors="coerce").astype(float)
        blank = txt.str.lower().isin(["", "nan", "none", "na", "null", "n/a"]).fillna(True)
        non_numeric = num.isna() & s.notna() & ~blank.astype(bool)
    add("valores_nao_numericos", non_numeric.sum(), "convertidos para ausente")
    add("valores_ausentes_na_origem", num.isna().sum() - non_numeric.sum(), "mantidos como ausentes")

    noise = (num < 0) & (num >= -cfg.ROUNDING_NOISE_MM)
    add("negativos_por_arredondamento", noise.sum(), "ajustados para 0")
    num[noise] = 0.0
    neg = num < 0
    add("valores_negativos", neg.sum(), "convertidos para ausente")
    num[neg] = np.nan
    big = num > max_daily_mm
    add("valores_acima_do_limite_fisico", big.sum(), "convertidos para ausente",
        f"limite = {max_daily_mm:.0f} mm/dia")
    num[big] = np.nan
    df["precip_mm"] = num

    # --- identificador do ponto e duplicatas -------------------------------
    if "point_id" not in df.columns:
        # Contrato antigo sem identificador: mantém uma série por UF e deixa isso explícito.
        df["point_id"] = df["state"].astype(str)
    df["point_id"] = df["point_id"].astype("string").str.strip()
    missing_id = df["point_id"].isna() | df["point_id"].eq("")
    add("identificadores_ponto_ausentes", missing_id.sum(), "substituídos pela sigla da UF")
    df.loc[missing_id, "point_id"] = df.loc[missing_id, "state"]
    key = ["state", "point_id", "date"]
    exact = df.duplicated(subset=key + ["precip_mm"], keep="first")
    add("duplicatas_exatas", exact.sum(), "removidas (mantido o 1º registro)")
    df = df[~exact]
    conflict = df.duplicated(subset=key, keep=False)
    n_conf = df[conflict].groupby(key).ngroups if conflict.any() else 0
    add("duplicatas_conflitantes", n_conf, "média dos valores do mesmo estado/dia (ponto)")
    df = df.groupby(key, as_index=False)["precip_mm"].mean()
    add("pontos_de_referencia_preservados", df["point_id"].nunique(),
        "séries mantidas separadas por UF e identificador do ponto")

    df = df.sort_values(["state", "date"]).reset_index(drop=True)
    absent = sorted(set(cfg.UF_NAMES) - set(df["state"]))
    add("estados_sem_nenhum_dado", len(absent), "informativo", ", ".join(absent))
    return df, log


def build_daily_grid(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    """Reindexa para um calendário diário contínuo por estado e mede lacunas."""
    d0, d1 = df["date"].min(), df["date"].max()
    full_dates = pd.date_range(d0, d1, freq="D")
    point_keys = df[["state", "point_id"]].drop_duplicates()
    idx = pd.MultiIndex.from_tuples(
        [(r.state, r.point_id, dt) for r in point_keys.itertuples(index=False) for dt in full_dates],
        names=["state", "point_id", "date"])
    grid = df.set_index(["state", "point_id", "date"])["precip_mm"].reindex(idx).reset_index()

    rows = []
    for (st, pid), g in grid.groupby(["state", "point_id"]):
        present = df.loc[(df["state"] == st) & (df["point_id"] == pid), "date"]
        first, last = present.min(), present.max()
        in_range = g[(g["date"] >= first) & (g["date"] <= last)]
        rows.append({
            "state": st, "point_id": pid, "first_date": first.date(), "last_date": last.date(),
            "n_days_received": len(present),
            "n_leading_days_without_series": (first - d0).days,
            "n_trailing_days_without_series": (d1 - last).days,
            "n_internal_missing_dates": int((~in_range["date"].isin(present)).sum()),
            "n_nan_values_received": int(df.loc[df["state"] == st, "precip_mm"].isna().sum()),
            "longest_gap_days": _longest_run(in_range["precip_mm"].isna().to_numpy()),
        })
    by_state = pd.DataFrame(rows)

    v = grid["precip_mm"]
    change = ((v != v.shift()) | v.isna() | (grid["state"] != grid["state"].shift()) |
              (grid["point_id"] != grid["point_id"].shift()))
    run_id = change.cumsum()
    run_len = v.groupby(run_id).transform("size")
    flat = (run_len >= cfg.FLATLINE_DAYS) & (v > 0)
    extra = [{"check": "sequencias_valores_identicos_suspeitas",
              "count": int(run_id[flat].nunique()), "action": "apenas sinalizado",
              "detail": f">= {cfg.FLATLINE_DAYS} dias consecutivos > 0 com o mesmo valor"}]
    return grid, by_state, extra


def aggregate_monthly(grid: pd.DataFrame) -> pd.DataFrame:
    """Acumulados mensais. Mês só é 'completo' se TODOS os dias têm valor válido;
    mês incompleto fica com precip_mm = NaN (nunca se trata ausência como zero)."""
    d = grid.copy()
    d["year"] = d["date"].dt.year
    d["month"] = d["date"].dt.month
    d["wet"] = ((d["precip_mm"] >= cfg.WET_DAY_MM) & d["precip_mm"].notna()).astype(int)
    m = d.groupby(["state", "point_id", "year", "month"]).agg(
        n_valid_days=("precip_mm", "count"), precip_partial_mm=("precip_mm", "sum"),
        wet_days=("wet", "sum"), max_daily_mm=("precip_mm", "max")).reset_index()
    first = pd.to_datetime(dict(year=m["year"], month=m["month"], day=1))
    m["n_days_expected"] = first.dt.days_in_month
    m["complete"] = m["n_valid_days"] == m["n_days_expected"]
    m["precip_mm"] = m["precip_partial_mm"].where(m["complete"])
    m.loc[m["n_valid_days"] == 0, "precip_partial_mm"] = np.nan
    return m.sort_values(["state", "year", "month"]).reset_index(drop=True)


def aggregate_annual(monthly: pd.DataFrame) -> pd.DataFrame:
    """Acumulados anuais. Ano só é completo se os 12 meses estão completos."""
    comp = monthly["complete"]
    a = monthly.assign(_c=comp.astype(int),
                       _p=monthly["precip_mm"].where(comp, 0.0)
                       ).groupby(["state", "point_id", "year"]).agg(
        n_months_complete=("_c", "sum"), n_valid_days=("n_valid_days", "sum"),
        annual_partial_mm=("_p", "sum")).reset_index()
    a["complete"] = a["n_months_complete"] == 12
    a["annual_total_mm"] = a["annual_partial_mm"].where(a["complete"])
    return a


def incomplete_periods(monthly: pd.DataFrame, annual: pd.DataFrame) -> pd.DataFrame:
    mm = monthly[~monthly["complete"]].copy()
    mm["period_type"] = "monthly"
    mm["missing_days"] = mm["n_days_expected"] - mm["n_valid_days"]
    mm["reason"] = np.where(mm["n_valid_days"] == 0, "sem_dados", "parcial")
    aa = annual[~annual["complete"]].copy()
    aa["period_type"] = "annual"
    aa["month"] = np.nan
    aa["missing_days"] = np.nan
    aa["reason"] = np.where(aa["n_months_complete"] == 0, "sem_dados", "meses_incompletos")
    cols = ["state", "point_id", "period_type", "year", "month", "n_valid_days", "missing_days", "reason"]
    return pd.concat([mm[cols], aa[cols]]).sort_values(["state", "period_type", "year", "month"])


def prepare(raw: pd.DataFrame, today=None):
    clean, log = clean_daily(raw, today=today)
    grid, by_state, extra = build_daily_grid(clean)
    log += extra
    monthly = aggregate_monthly(grid)
    annual = aggregate_annual(monthly)
    inc = incomplete_periods(monthly, annual)
    log.append({"check": "meses_incompletos", "count": int((~monthly["complete"]).sum()),
                "action": "excluídos das estatísticas (precip_mm = NaN)",
                "detail": f"de {len(monthly)} estado-meses"})
    log.append({"check": "anos_incompletos", "count": int((~annual["complete"]).sum()),
                "action": "excluídos das estatísticas anuais e de tendência",
                "detail": f"de {len(annual)} estado-anos"})
    return {"clean": clean, "grid": grid, "monthly": monthly, "annual": annual,
            "incomplete": inc, "log": pd.DataFrame(log), "by_state": by_state}


def list_input_files(path) -> list[Path]:
    """Aceita arquivo, pasta ou padrão. Para a pasta NASA, prioriza bruto_*.csv
    para não misturar os arquivos derivados (diaria/mensal/anual) com os brutos."""
    import glob
    s = str(path)
    if Path(s).is_dir():
        folder = Path(s)
        raw_nasa = sorted(folder.glob("bruto_*.csv"))
        if raw_nasa:
            files = raw_nasa
        else:
            files = [f for f in sorted(folder.iterdir())
                     if f.suffix.lower() in (".csv", ".gz", ".tsv", ".txt", ".parquet")]
    elif any(c in s for c in "*?["):
        files = [Path(f) for f in sorted(glob.glob(s))]
    else:
        files = [Path(s)]
    if not files:
        raise FileNotFoundError(f"Nenhum arquivo de dados encontrado em: {s}")
    return files


def _read_nasa_points(folder: Path, files: list[Path]) -> pd.DataFrame:
    """Converte os CSVs brutos da NASA/Meteomatics (lat;lon;validdate;precip_24h:mm)
    para uma linha por UF/dia, associando cada ponto ao pontos.csv."""
    points_file = folder / "pontos.csv"
    if not points_file.exists():
        raise FileNotFoundError(
            f"Formato bruto NASA detectado, mas não encontrei {points_file}. "
            "Mantenha pontos.csv na pasta dados_pontos."
        )
    points = pd.read_csv(points_file)
    required = {"uf", "latitude", "longitude"}
    if not required.issubset(points.columns):
        raise ValueError(f"{points_file.name} deve conter {sorted(required)}")
    points = points.copy()
    point_coords = points[["latitude", "longitude"]].to_numpy(dtype=float)
    point_ufs = points["uf"].astype(str).to_numpy()
    if "point_id" in points.columns:
        point_ids = points["point_id"].astype(str).to_numpy()
    else:
        point_ids = np.array([
            f"{uf}_{lat:+.6f}_{lon:+.6f}".replace("+", "p").replace("-", "m")
            for uf, lat, lon in zip(points["uf"], points["latitude"], points["longitude"])
        ], dtype=object)

    frames = []
    for f in files:
        raw = pd.read_csv(f, sep=";", dtype=str)
        raw.columns = [str(c).strip().lstrip("\\ufeff") for c in raw.columns]
        needed = {"lat", "lon", "validdate", "precip_24h:mm"}
        if not needed.issubset(raw.columns):
            raise ValueError(f"{f.name}: esperado cabeçalho {sorted(needed)}; recebido {list(raw.columns)}")
        lat = pd.to_numeric(raw["lat"], errors="coerce").to_numpy(dtype=float)
        lon = pd.to_numeric(raw["lon"], errors="coerce").to_numpy(dtype=float)
        coords = np.column_stack([lat, lon])
        states = np.full(len(coords), None, dtype=object)
        ids = np.full(len(coords), None, dtype=object)
        valid_coords = np.isfinite(coords).all(axis=1)
        if valid_coords.any():
            distances = ((coords[valid_coords, None, :] - point_coords[None, :, :]) ** 2).sum(axis=2)
            nearest = distances.argmin(axis=1)
            min_distance = distances[np.arange(len(nearest)), nearest]
            matched = min_distance <= 1e-8
            valid_positions = np.flatnonzero(valid_coords)
            states[valid_positions[matched]] = point_ufs[nearest[matched]]
            ids[valid_positions[matched]] = point_ids[nearest[matched]]
        raw["state"] = states
        raw["point_id"] = ids
        raw["date"] = raw["validdate"]
        raw["precip_mm"] = raw["precip_24h:mm"].astype("string").str.replace(",", ".", regex=False)
        unknown = int(raw["state"].isna().sum())
        if unknown:
            raise ValueError(f"{f.name}: {unknown} linhas com coordenadas sem correspondência em pontos.csv")
        frames.append(raw[["date", "state", "point_id", "precip_mm"]])
        print(f"  lido NASA: {f.name} ({len(raw):,} linhas)")
    result = pd.concat(frames, ignore_index=True)
    return result


def read_input(path) -> pd.DataFrame:
    """Lê CSV/CSV.GZ/Parquet no contrato EarthScope ou os CSVs brutos NASA.
    Se a pasta contém bruto_*.csv, usa pontos.csv para converter coordenadas em UF."""
    files = list_input_files(path)
    if Path(path).is_dir() and files and files[0].name.startswith("bruto_"):
        return _read_nasa_points(Path(path), files)

    frames = []
    for f in files:
        if f.suffix == ".parquet":
            df = pd.read_parquet(f)
        else:
            df = pd.read_csv(f, dtype=str, sep=None, engine="python")
        frames.append(_rename_columns(df))
        print(f"  lido: {f.name} ({len(df):,} linhas)")
    return pd.concat(frames, ignore_index=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--input", required=True, help="arquivo de dados diários")
    ap.add_argument("--today", default=None, help="data de corte AAAA-MM-DD (descarta datas futuras)")
    args = ap.parse_args(argv)
    ensure_dirs()
    res = prepare(read_input(args.input), today=args.today)
    out = cfg.OUTPUT_DIR
    res["monthly"].to_csv(out / "monthly_precipitation.csv", index=False)
    res["annual"].to_csv(out / "annual_precipitation.csv", index=False)
    res["incomplete"].to_csv(out / "incomplete_periods.csv", index=False)
    res["log"].to_csv(out / "data_quality_report.csv", index=False)
    res["by_state"].to_csv(out / "data_quality_by_state.csv", index=False)
    res["clean"].to_csv(cfg.INTERIM_DIR / "daily_clean.csv.gz", index=False)
    print(res["log"].to_string(index=False))
    return res


if __name__ == "__main__":
    main()
