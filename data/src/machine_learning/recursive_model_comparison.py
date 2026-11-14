
import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PREDICTIONS_PATH = (
    PROJECT_ROOT
    / "reports"
    / "machine_learning"
    / "recursive_backtesting"
    / "recursive_predictions.csv"
)

HISTORY_PATH = (
    PROJECT_ROOT
    / "precipitation"
    / "processed"
    / "precipitacao_mensal_27_pontos_2005_2025_cleaned.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "machine_learning"
    / "recursive_backtesting"
)


def load_data():

    predictions = pd.read_csv(
        PREDICTIONS_PATH,
        parse_dates=["origin_date", "forecast_date"]
    )

    history = pd.read_csv(
        HISTORY_PATH,
        parse_dates=["data_inicio"]
    )

    return predictions, history


def add_baseline_predictions(predictions, history):

    baseline = history[
        ["ponto_id", "data_inicio", "precipitacao_mm"]
    ].copy()

    # The baseline uses precipitation from the same month one year earlier
    baseline["forecast_date"] = (
        baseline["data_inicio"] + pd.DateOffset(years=1)
    )

    baseline = baseline.rename(columns={
        "precipitacao_mm": "baseline_prediction"
    })

    baseline = baseline[
        ["ponto_id", "forecast_date", "baseline_prediction"]
    ]

    comparison = predictions.merge(
        baseline,
        on=["ponto_id", "forecast_date"],
        how="left",
        validate="many_to_one"
    )

    if comparison["baseline_prediction"].isna().any():
        raise ValueError(
            "Some baseline predictions could not be generated."
        )

    comparison["baseline_error"] = (
        comparison["actual_precipitation_mm"]
        - comparison["baseline_prediction"]
    )

    comparison["rf_error"] = (
        comparison["actual_precipitation_mm"]
        - comparison["predicted_precipitation_mm"]
    )

    return comparison


def calculate_metrics(group):

    baseline_mae = mean_absolute_error(
        group["actual_precipitation_mm"],
        group["baseline_prediction"]
    )

    rf_mae = mean_absolute_error(
        group["actual_precipitation_mm"],
        group["predicted_precipitation_mm"]
    )

    baseline_rmse = np.sqrt(
        mean_squared_error(
            group["actual_precipitation_mm"],
            group["baseline_prediction"]
        )
    )

    rf_rmse = np.sqrt(
        mean_squared_error(
            group["actual_precipitation_mm"],
            group["predicted_precipitation_mm"]
        )
    )

    improvement = (
        (baseline_mae - rf_mae) / baseline_mae * 100
        if baseline_mae != 0 else np.nan
    )

    return {
        "baseline_mae_mm": baseline_mae,
        "random_forest_mae_mm": rf_mae,
        "mae_improvement_pct": improvement,
        "baseline_rmse_mm": baseline_rmse,
        "random_forest_rmse_mm": rf_rmse,
        "samples": len(group)
    }


def evaluate_by_horizon(comparison):

    results = []

    for horizon, group in comparison.groupby("horizon"):

        metrics = calculate_metrics(group)

        metrics["horizon"] = horizon

        results.append(metrics)

    overall = calculate_metrics(comparison)
    overall["horizon"] = "ALL"

    results.append(overall)

    return pd.DataFrame(results)


def evaluate_by_uf(comparison):

    results = []

    for (point_id, uf), group in comparison.groupby(
        ["ponto_id", "uf"]
    ):

        metrics = calculate_metrics(group)

        metrics["ponto_id"] = point_id
        metrics["uf"] = uf

        results.append(metrics)

    return pd.DataFrame(results)


def main():

    predictions, history = load_data()

    comparison = add_baseline_predictions(
        predictions,
        history
    )

    horizon_metrics = evaluate_by_horizon(comparison)

    uf_metrics = evaluate_by_uf(comparison)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    comparison.to_csv(
        OUTPUT_DIR / "recursive_model_predictions_comparison.csv",
        index=False
    )

    horizon_metrics.to_csv(
        OUTPUT_DIR / "recursive_metrics_comparison.csv",
        index=False
    )

    uf_metrics.to_csv(
        OUTPUT_DIR / "recursive_metrics_by_uf.csv",
        index=False
    )

    print("\n--- RECURSIVE MODEL COMPARISON ---")

    print(
        horizon_metrics.to_string(index=False)
    )

    print("\n--- COMPARISON BY REFERENCE POINT ---")

    print(
        uf_metrics.to_string(index=False)
    )

    print("\nRecursive model comparison completed.")


if __name__ == "__main__":
    main()
