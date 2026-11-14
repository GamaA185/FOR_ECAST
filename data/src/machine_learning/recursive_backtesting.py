
import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


PROJECT_ROOT = Path(__file__).resolve().parents[2]

FEATURES_PATH = (
    PROJECT_ROOT
    / "precipitation"
    / "processed"
    / "monthly_precipitation_features.csv"
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

ORIGIN_YEARS = [2021, 2022, 2023, 2024]
FORECAST_HORIZON = 3

RANDOM_STATE = 42


def load_data():

    features = pd.read_csv(
        FEATURES_PATH,
        parse_dates=["data_inicio"]
    )

    history = pd.read_csv(
        HISTORY_PATH,
        parse_dates=["data_inicio"]
    )

    return features, history


def get_feature_columns(df):

    uf_columns = [
        column for column in df.columns
        if column.startswith("uf_")
    ]

    feature_columns = [
        "lag_1",
        "lag_2",
        "lag_3",
        "lag_12",
        "rolling_3",
        "rolling_12",
        "month_sin",
        "month_cos"
    ] + uf_columns

    return feature_columns


def train_model(train_data, feature_columns):

    X_train = train_data[feature_columns]
    y_train = train_data["precipitacao_mm"]

    model = RandomForestRegressor(
        n_estimators=400,
        max_features=0.8,
        min_samples_leaf=3,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    return model


def create_future_features(
    precipitation_history,
    forecast_date,
    uf,
    feature_columns
):

    values = np.asarray(
        precipitation_history,
        dtype=float
    )

    if len(values) < 12:
        raise ValueError(
            "At least 12 months of history are required."
        )

    month = forecast_date.month

    features = {
        "lag_1": values[-1],
        "lag_2": values[-2],
        "lag_3": values[-3],
        "lag_12": values[-12],
        "rolling_3": values[-3:].mean(),
        "rolling_12": values[-12:].mean(),
        "month_sin": np.sin(2 * np.pi * month / 12),
        "month_cos": np.cos(2 * np.pi * month / 12)
    }

    # Initialize all UF columns
    for column in feature_columns:
        if column.startswith("uf_"):
            features[column] = 0

    uf_column = f"uf_{uf}"

    if uf_column not in feature_columns:
        raise ValueError(
            f"UF column not found in training features: {uf_column}"
        )

    features[uf_column] = 1

    return pd.DataFrame(
        [features],
        columns=feature_columns
    )


def recursive_forecast(
    model,
    history,
    point_id,
    uf,
    origin_date,
    feature_columns
):
    

    point_history = (
        history[
            (history["ponto_id"] == point_id) &
            (history["data_inicio"] <= origin_date)
        ]
        .sort_values("data_inicio")
    )

    precipitation_history = (
        point_history["precipitacao_mm"]
        .astype(float)
        .tolist()
    )

    if len(precipitation_history) < 12:
        raise ValueError(
            f"Insufficient history for reference point {point_id}."
        )

    future_dates = pd.date_range(
        start=origin_date + pd.offsets.MonthBegin(1),
        periods=FORECAST_HORIZON,
        freq="MS"
    )

    results = []

    for horizon, forecast_date in enumerate(future_dates, start=1):

        X_future = create_future_features(
            precipitation_history,
            forecast_date,
            uf,
            feature_columns
        )

        prediction = model.predict(X_future)[0]

        # Precipitation cannot be negative
        prediction = max(0.0, float(prediction))

        results.append({
            "ponto_id": point_id,
            "uf": uf,
            "origin_date": origin_date,
            "forecast_date": forecast_date,
            "horizon": horizon,
            "predicted_precipitation_mm": prediction
        })

        # Use the prediction as input for the next month
        precipitation_history.append(prediction)

    return results


def run_backtesting(features, history):

    feature_columns = get_feature_columns(features)

    all_predictions = []

    for origin_year in ORIGIN_YEARS:

        origin_date = pd.Timestamp(
            year=origin_year,
            month=12,
            day=1
        )

        train_data = features[
            features["data_inicio"] <= origin_date
        ].copy()

        if train_data.empty:
            raise ValueError(
                f"No training data available for {origin_year}."
            )

        print(f"\nTraining through December {origin_year}...")
        print("Training samples:", len(train_data))

        model = train_model(
            train_data,
            feature_columns
        )

        points = (
            history[["ponto_id", "uf"]]
            .drop_duplicates()
            .sort_values("ponto_id")
        )

        for _, point in points.iterrows():

            predictions = recursive_forecast(
                model=model,
                history=history,
                point_id=point["ponto_id"],
                uf=point["uf"],
                origin_date=origin_date,
                feature_columns=feature_columns
            )

            all_predictions.extend(predictions)

    predictions_df = pd.DataFrame(all_predictions)

    # Attach actual observed precipitation only after predictions
    actuals = history[
        ["ponto_id", "data_inicio", "precipitacao_mm"]
    ].rename(columns={
        "data_inicio": "forecast_date",
        "precipitacao_mm": "actual_precipitation_mm"
    })

    predictions_df = predictions_df.merge(
        actuals,
        on=["ponto_id", "forecast_date"],
        how="left",
        validate="one_to_one"
    )

    if predictions_df["actual_precipitation_mm"].isna().any():
        raise ValueError(
            "Some forecast dates do not have actual observations."
        )

    predictions_df["error_mm"] = (
        predictions_df["actual_precipitation_mm"]
        - predictions_df["predicted_precipitation_mm"]
    )

    predictions_df["absolute_error_mm"] = (
        predictions_df["error_mm"].abs()
    )

    return predictions_df


def calculate_metrics(predictions):
    """Calculate metrics by forecast horizon."""

    results = []

    for horizon, group in predictions.groupby("horizon"):

        mae = mean_absolute_error(
            group["actual_precipitation_mm"],
            group["predicted_precipitation_mm"]
        )

        rmse = np.sqrt(
            mean_squared_error(
                group["actual_precipitation_mm"],
                group["predicted_precipitation_mm"]
            )
        )

        results.append({
            "horizon": horizon,
            "mae_mm": mae,
            "rmse_mm": rmse,
            "samples": len(group)
        })

    # Overall metrics
    overall_mae = mean_absolute_error(
        predictions["actual_precipitation_mm"],
        predictions["predicted_precipitation_mm"]
    )

    overall_rmse = np.sqrt(
        mean_squared_error(
            predictions["actual_precipitation_mm"],
            predictions["predicted_precipitation_mm"]
        )
    )

    results.append({
        "horizon": "ALL",
        "mae_mm": overall_mae,
        "rmse_mm": overall_rmse,
        "samples": len(predictions)
    })

    return pd.DataFrame(results)


def main():

    features, history = load_data()

    predictions = run_backtesting(
        features,
        history
    )

    metrics = calculate_metrics(predictions)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    predictions.to_csv(
        OUTPUT_DIR / "recursive_predictions.csv",
        index=False
    )

    metrics.to_csv(
        OUTPUT_DIR / "recursive_metrics.csv",
        index=False
    )

    print("\n--- RECURSIVE BACKTESTING RESULTS ---")

    print(metrics.to_string(index=False))

    print("\nTotal predictions:", len(predictions))

    print("\nRecursive backtesting completed.")


if __name__ == "__main__":
    main()
