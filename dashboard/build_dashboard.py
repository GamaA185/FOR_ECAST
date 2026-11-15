"""Build the static dashboard data from the project analysis outputs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "src" / "statistics"))
import config as stats_config

TABLES = ROOT / "data" / "src" / "reports" / "statistics" / "tables"
ML_REPORTS = ROOT / "data" / "reports" / "machine_learning"
OUTPUT = Path(__file__).resolve().parent / "data.json"


def records(frame: pd.DataFrame) -> list[dict]:
    return json.loads(frame.to_json(orient="records", double_precision=8))


def read_table(name: str) -> pd.DataFrame:
    path = TABLES / f"{name}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Required statistical output is missing: {path}")
    return pd.read_csv(path)


def read_ml_report(relative_path: str) -> pd.DataFrame:
    path = ML_REPORTS / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Required model report is missing: {path}")
    return pd.read_csv(path)


def main() -> None:
    monthly_source = read_table("monthly_precipitation")
    annual_source = read_table("annual_precipitation")
    climatology = read_table("monthly_climatology")
    categories = read_table("precipitation_categories")
    anomalies = read_table("anomalies")
    trends = read_table("trend_analysis")
    quality = read_table("data_quality_by_state")

    if not categories["reference"].eq("full_history").all():
        raise ValueError("The dashboard requires full-history category thresholds.")
    if monthly_source.groupby("state")["point_id"].nunique().max() != 1:
        raise ValueError("The dashboard requires exactly one precipitation point per state.")
    if monthly_source["state"].nunique() != 27:
        raise ValueError("The dashboard requires data for all 27 Brazilian federal units.")

    registry_path = ROOT / "data" / "precipitation" / "processed" / "pontos.csv"
    registry = pd.read_csv(registry_path).set_index("uf")

    states = []
    for (state, point_id), monthly_group in monthly_source.groupby(["state", "point_id"]):
        def subset(frame: pd.DataFrame) -> pd.DataFrame:
            return frame.loc[frame["state"].eq(state) & frame["point_id"].eq(point_id)].copy()

        monthly = monthly_group.merge(
            subset(categories).query("period_type == 'monthly'")[
                ["year", "month", "category", "p10_mm", "p30_mm", "p70_mm", "p90_mm",
                 "n_ref_years", "thresholds_degenerate"]
            ],
            on=["year", "month"],
            how="left",
            validate="one_to_one",
        )
        monthly = monthly.merge(
            subset(anomalies).query("period_type == 'monthly'")[
                ["year", "month", "anomaly_mm", "anomaly_pct", "zscore"]
            ],
            on=["year", "month"],
            how="left",
            validate="one_to_one",
        )

        annual = subset(annual_source).merge(
            subset(anomalies).query("period_type == 'annual'")[
                ["year", "anomaly_mm", "anomaly_pct", "zscore"]
            ],
            on="year",
            how="left",
            validate="one_to_one",
        )
        point = registry.loc[state]
        trend_rows = subset(trends)
        quality_rows = subset(quality)
        if len(trend_rows) != 1 or len(quality_rows) != 1:
            raise ValueError(f"Expected one trend and one data-quality summary for {state}.")

        states.append(
            {
                "uf": state,
                "name": stats_config.UF_NAMES[state],
                "point_id": point_id,
                "latitude": float(point["latitude"]),
                "longitude": float(point["longitude"]),
                "climate": records(subset(climatology).sort_values("month")),
                "monthly": records(monthly.sort_values(["year", "month"])),
                "annual": records(annual.sort_values("year")),
                "trend": records(trend_rows)[0],
                "quality": records(quality_rows)[0],
            }
        )

    base_model = read_ml_report("metrics/model_comparison.csv")
    recursive_state = read_ml_report("recursive_backtesting/recursive_metrics_by_uf.csv")
    recursive_horizons = read_ml_report("recursive_backtesting/recursive_metrics_comparison.csv")

    model_summary = base_model.loc[base_model["uf"].eq("ALL")]
    base_model = base_model.loc[base_model["uf"].isin(stats_config.UF_NAMES)]
    if base_model["uf"].nunique() != 27 or len(model_summary) != 1:
        raise ValueError("Model comparison results must include all 27 federal units.")

    first_year = int(monthly_source.loc[monthly_source["complete"], "year"].min())
    last_year = int(monthly_source.loc[monthly_source["complete"], "year"].max())
    payload = {
        "reference": {"start_year": first_year, "end_year": last_year},
        "source": "Meteomatics API (source=mix)",
        "states": states,
        "machine_learning": {
            "overall": records(model_summary)[0],
            "by_state": records(base_model.sort_values("uf")),
            "recursive_by_state": records(recursive_state.sort_values("uf")),
            "recursive_by_horizon": records(recursive_horizons.sort_values("horizon")),
        },
    }

    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Dashboard data: {len(states)} federal units; {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
