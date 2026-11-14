
import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PREDICTIONS_PATH = (
    PROJECT_ROOT
    / "reports"
    / "machine_learning"
    / "predictions"
    / "random_forest_predictions.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "machine_learning"
    / "error_analysis"
)


def load_predictions():

    df = pd.read_csv(
        PREDICTIONS_PATH,
        parse_dates=["data_inicio"]
    )

    return df


def prepare_errors(df):

    df = df.copy()

    df["month"] = df["data_inicio"].dt.month
    df["year"] = df["data_inicio"].dt.year

    df["error_mm"] = (
        df["actual_precipitation_mm"]
        - df["predicted_precipitation_mm"]
    )

    df["absolute_error_mm"] = df["error_mm"].abs()

    df["squared_error_mm"] = df["error_mm"] ** 2

    df["bias_mm"] = (
    df["predicted_precipitation_mm"]
    - df["actual_precipitation_mm"]
)

    return df


def analyze_bias_by_uf(df):
    """Analyze systematic prediction bias by reference point."""

    return (
        df.groupby(["ponto_id", "uf"])
        .agg(
            mean_bias_mm=("bias_mm", "mean"),
            overprediction_pct=(
                "bias_mm",
                lambda values: (values > 0).mean() * 100
            ),
            underprediction_pct=(
                "bias_mm",
                lambda values: (values < 0).mean() * 100
            ),
            samples=("bias_mm", "count")
        )
        .reset_index()
        .sort_values("mean_bias_mm")
    )


def analyze_bias_by_month(df):
    """Analyze systematic prediction bias by month."""

    return (
        df.groupby("month")
        .agg(
            mean_bias_mm=("bias_mm", "mean"),
            overprediction_pct=(
                "bias_mm",
                lambda values: (values > 0).mean() * 100
            ),
            underprediction_pct=(
                "bias_mm",
                lambda values: (values < 0).mean() * 100
            ),
            samples=("bias_mm", "count")
        )
        .reset_index()
        .sort_values("month")
    )


def calculate_metrics(group):

    mae = group["absolute_error_mm"].mean()

    rmse = np.sqrt(
        group["squared_error_mm"].mean()
    )

    return pd.Series({
        "mae_mm": mae,
        "rmse_mm": rmse,
        "samples": len(group)
    })


def analyze_by_uf(df):

    return (
        df.groupby(["ponto_id", "uf"])
        .apply(calculate_metrics, include_groups=False)
        .reset_index()
        .sort_values("mae_mm", ascending=False)
    )


def analyze_by_month(df):

    return (
        df.groupby("month")
        .apply(calculate_metrics, include_groups=False)
        .reset_index()
        .sort_values("month")
    )


def analyze_by_year(df):

    return (
        df.groupby("year")
        .apply(calculate_metrics, include_groups=False)
        .reset_index()
        .sort_values("year")
    )


def analyze_largest_errors(df):

    return (
        df.sort_values(
            "absolute_error_mm",
            ascending=False
        )
        [[
            "ponto_id",
            "uf",
            "data_inicio",
            "actual_precipitation_mm",
            "predicted_precipitation_mm",
            "error_mm",
            "absolute_error_mm"
        ]]
        .head(30)
    )


def save_results(results):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for name, table in results.items():

        table.to_csv(
            OUTPUT_DIR / f"{name}.csv",
            index=False
        )


def main():

    df = load_predictions()

    df = prepare_errors(df)

    results = {
        "errors_by_uf": analyze_by_uf(df),
        "errors_by_month": analyze_by_month(df),
        "errors_by_year": analyze_by_year(df),
        "largest_errors": analyze_largest_errors(df),
        "bias_by_uf": analyze_bias_by_uf(df),
        "bias_by_month": analyze_bias_by_month(df)
    }

    save_results(results)

    print("\n--- ERROR ANALYSIS ---")

    print("\nErrors by reference point:")

    print(
        results["errors_by_uf"].to_string(index=False)
    )

    print("\nErrors by month:")

    print(
        results["errors_by_month"].to_string(index=False)
    )

    print("\nErrors by year:")

    print(
        results["errors_by_year"].to_string(index=False)
    )
    print("\n--- BIAS BY REFERENCE POINT ---")
    print(results["bias_by_uf"].to_string(index=False))

    print("\n--- BIAS BY MONTH ---")
    print(results["bias_by_month"].to_string(index=False))
    print("\nError analysis completed.")


if __name__ == "__main__":
    main()
