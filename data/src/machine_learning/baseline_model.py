
import pandas as pd
import numpy as np
from pathlib import Path



PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "precipitation"
    / "processed"
    / "monthly_precipitation_features.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "machine_learning"
)

PREDICTIONS_DIR = OUTPUT_DIR / "predictions"
METRICS_DIR = OUTPUT_DIR / "metrics"


def load_data():
    

    df = pd.read_csv(
        DATA_PATH,
        parse_dates=["data_inicio"]
    )

    return df


def generate_baseline_predictions(df):


    df = df.copy()

    # Use the same month from the previous year
    df["predicted_precipitation_mm"] = df["lag_12"]

    
    df = df.dropna(
        subset=[
            "precipitacao_mm",
            "predicted_precipitation_mm"
        ]
    )

    
    df = df[
        (df["year"] >= 2022) &
        (df["year"] <= 2025)
    ].copy()

    # Calculate prediction errors
    df["actual_precipitation_mm"] = df["precipitacao_mm"]

    df["error_mm"] = (
        df["actual_precipitation_mm"]
        - df["predicted_precipitation_mm"]
    )

    df["absolute_error_mm"] = df["error_mm"].abs()

    df["squared_error_mm"] = df["error_mm"] ** 2

    return df

# RMSE and MAE calculations
def calculate_metrics(df):
    

    results = []

    # Metrics for each reference point
    for point_id, group in df.groupby("ponto_id"):

        mae = group["absolute_error_mm"].mean()

        rmse = np.sqrt(
            group["squared_error_mm"].mean()
        )

        results.append({
            "ponto_id": point_id,
            "uf": group["uf"].iloc[0],
            "model": "Seasonal Naive",
            "mae_mm": mae,
            "rmse_mm": rmse,
            "samples": len(group)
        })

    metrics_df = pd.DataFrame(results)

    # Overall metrics
    overall_mae = df["absolute_error_mm"].mean()

    overall_rmse = np.sqrt(
        df["squared_error_mm"].mean()
    )

    overall = pd.DataFrame([{
        "ponto_id": "ALL",
        "uf": "ALL",
        "model": "Seasonal Naive",
        "mae_mm": overall_mae,
        "rmse_mm": overall_rmse,
        "samples": len(df)
    }])

    metrics_df = pd.concat(
        [metrics_df, overall],
        ignore_index=True
    )

    return metrics_df

# Save predictions and metrics to CSV files
def save_results(predictions, metrics):
    

    PREDICTIONS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    METRICS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    prediction_columns = [
        "ponto_id",
        "uf",
        "data_inicio",
        "actual_precipitation_mm",
        "predicted_precipitation_mm",
        "error_mm"
    ]

    predictions[prediction_columns].to_csv(
        PREDICTIONS_DIR / "baseline_predictions.csv",
        index=False
    )

    metrics.to_csv(
        METRICS_DIR / "baseline_metrics.csv",
        index=False
    )


def main():

    df = load_data()

    predictions = generate_baseline_predictions(df)

    metrics = calculate_metrics(predictions)

    save_results(predictions, metrics)

    print("\n--- BASELINE MODEL RESULTS ---")

    print("\nOverall metrics:")

    print(
        metrics[
            metrics["ponto_id"] == "ALL"
        ].to_string(index=False)
    )

    print("\nMetrics by reference point:")

    print(
        metrics[
            metrics["ponto_id"] != "ALL"
        ].to_string(index=False)
    )

    print("\nBaseline evaluation completed.")


if __name__ == "__main__":
    main()
