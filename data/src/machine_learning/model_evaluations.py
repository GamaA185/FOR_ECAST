
import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PREDICTIONS_DIR = (
    PROJECT_ROOT
    / "reports"
    / "machine_learning"
    / "predictions"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "machine_learning"
    / "metrics"
)


def load_predictions():

    baseline = pd.read_csv(
        PREDICTIONS_DIR / "baseline_predictions.csv",
        parse_dates=["data_inicio"]
    )

    random_forest = pd.read_csv(
        PREDICTIONS_DIR / "random_forest_predictions.csv",
        parse_dates=["data_inicio"]
    )

    return baseline, random_forest


def compare_predictions(baseline, random_forest):
    

    keys = ["ponto_id", "uf", "data_inicio"]

    baseline = baseline[
        keys + [
            "actual_precipitation_mm",
            "predicted_precipitation_mm"
        ]
    ].rename(columns={
        "predicted_precipitation_mm": "baseline_prediction"
    })

    random_forest = random_forest[
        keys + [
            "actual_precipitation_mm",
            "predicted_precipitation_mm"
        ]
    ].rename(columns={
        "actual_precipitation_mm": "rf_actual",
        "predicted_precipitation_mm": "rf_prediction"
    })

    # Ensure there are no duplicated observations
    if baseline.duplicated(subset=keys).any():
        raise ValueError("Duplicated observations in baseline predictions.")

    if random_forest.duplicated(subset=keys).any():
        raise ValueError("Duplicated observations in Random Forest predictions.")

    comparison = baseline.merge(
        random_forest,
        on=keys,
        how="inner",
        validate="one_to_one"
    )

    if len(comparison) != len(baseline) or len(comparison) != len(random_forest):
        raise ValueError(
            "The models were evaluated on different observations."
        )

    if not np.allclose(
        comparison["actual_precipitation_mm"],
        comparison["rf_actual"]
    ):
        raise ValueError("Actual precipitation values do not match.")

    comparison["actual"] = comparison["actual_precipitation_mm"]

    comparison["baseline_error"] = (
        comparison["actual"] - comparison["baseline_prediction"]
    )

    comparison["rf_error"] = (
        comparison["actual"] - comparison["rf_prediction"]
    )

    return comparison


def calculate_model_metrics(comparison):
    

    results = []

    groups = list(comparison.groupby("ponto_id"))

    # Add overall evaluation
    groups.append(("ALL", comparison))

    for point_id, group in groups:

        baseline_mae = mean_absolute_error(
            group["actual"],
            group["baseline_prediction"]
        )

        baseline_rmse = np.sqrt(
            mean_squared_error(
                group["actual"],
                group["baseline_prediction"]
            )
        )

        rf_mae = mean_absolute_error(
            group["actual"],
            group["rf_prediction"]
        )

        rf_rmse = np.sqrt(
            mean_squared_error(
                group["actual"],
                group["rf_prediction"]
            )
        )

        mae_improvement = (
            (baseline_mae - rf_mae) / baseline_mae * 100
            if baseline_mae != 0 else np.nan
        )

        rmse_improvement = (
            (baseline_rmse - rf_rmse) / baseline_rmse * 100
            if baseline_rmse != 0 else np.nan
        )

        if rf_mae < baseline_mae:
            winner = "Random Forest"
        elif baseline_mae < rf_mae:
            winner = "Seasonal Naive"
        else:
            winner = "Tie"

        results.append({
            "ponto_id": point_id,
            "uf": group["uf"].iloc[0] if point_id != "ALL" else "ALL",
            "baseline_mae_mm": baseline_mae,
            "random_forest_mae_mm": rf_mae,
            "mae_improvement_pct": mae_improvement,
            "baseline_rmse_mm": baseline_rmse,
            "random_forest_rmse_mm": rf_rmse,
            "rmse_improvement_pct": rmse_improvement,
            "winner_by_mae": winner,
            "samples": len(group)
        })

    return pd.DataFrame(results)


def save_results(metrics):
    

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = OUTPUT_DIR / "model_comparison.csv"

    metrics.to_csv(
        output_path,
        index=False
    )

    print("\nComparison saved to:", output_path)


def main():

    baseline, random_forest = load_predictions()

    comparison = compare_predictions(
        baseline,
        random_forest
    )

    metrics = calculate_model_metrics(comparison)

    save_results(metrics)

    print("\n--- MODEL COMPARISON ---")

    print(
        metrics[
            metrics["ponto_id"] == "ALL"
        ].to_string(index=False)
    )

    print("\n--- RESULTS BY REFERENCE POINT ---")

    print(
        metrics[
            metrics["ponto_id"] != "ALL"
        ].to_string(index=False)
    )

    print("\nModel evaluation completed.")


if __name__ == "__main__":
    main()
