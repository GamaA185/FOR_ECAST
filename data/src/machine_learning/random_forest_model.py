
import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error



PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
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


# Model configuration
RANDOM_STATE = 42

TRAIN_END_YEAR = 2021
TEST_START_YEAR = 2022
TEST_END_YEAR = 2025


def load_data():
    

    df = pd.read_csv(
        DATA_PATH,
        parse_dates=["data_inicio"]
    )

    return df


def prepare_model_data(df):
    

    # Identify UF one-hot encoded columns
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

    target_column = "precipitacao_mm"

    # Remove missing rows
    df = df.dropna(
        subset=feature_columns + [target_column]
    ).copy()

    X = df[feature_columns]
    y = df[target_column]

    return df, X, y, feature_columns


def split_data(df, X, y):
    

    train_mask = df["year"] <= TRAIN_END_YEAR

    test_mask = (
        (df["year"] >= TEST_START_YEAR) &
        (df["year"] <= TEST_END_YEAR)
    )

    X_train = X.loc[train_mask]
    y_train = y.loc[train_mask]

    X_test = X.loc[test_mask]
    y_test = y.loc[test_mask]

    test_data = df.loc[test_mask].copy()

    if X_train.empty or X_test.empty:
        raise ValueError(
            "Training or test dataset is empty. Check the date range."
        )

    if df.loc[train_mask, "year"].max() >= df.loc[test_mask, "year"].min():
        raise ValueError(
            "Temporal data leakage detected in the train/test split."
        )

    return X_train, X_test, y_train, y_test, test_data

# Train Random Forest model
def train_model(X_train, y_train):
    

    model = RandomForestRegressor(
        n_estimators=400,
        max_features=0.8,
        min_samples_leaf=3,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    return model


def calculate_feature_importance(model, feature_columns):
    """Calculate and save Random Forest feature importance."""

    importance_df = pd.DataFrame({
        "feature": feature_columns,
        "importance": model.feature_importances_
    })

    importance_df = importance_df.sort_values(
        by="importance",
        ascending=False
    )

    importance_dir = OUTPUT_DIR / "feature_importance"

    importance_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        importance_dir / "random_forest_feature_importance.csv"
    )

    importance_df.to_csv(
        output_path,
        index=False
    )

    print("\n--- FEATURE IMPORTANCE ---")

    print(
        importance_df.head(15).to_string(index=False)
    )

    print("\nFeature importance saved to:", output_path)

    return importance_df

def generate_predictions(model, X_test, test_data):
    

    predictions = model.predict(X_test)

    results = test_data[
        ["ponto_id", "uf", "data_inicio"]
    ].copy()

    results["actual_precipitation_mm"] = (
        test_data["precipitacao_mm"].values
    )

    results["predicted_precipitation_mm"] = predictions

    results["error_mm"] = (
        results["actual_precipitation_mm"]
        - results["predicted_precipitation_mm"]
    )

    return results


# RMSE and MAE calculations
def calculate_metrics(predictions):
    

    results = []

    for point_id, group in predictions.groupby("ponto_id"):

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
            "ponto_id": point_id,
            "uf": group["uf"].iloc[0],
            "model": "Random Forest",
            "mae_mm": mae,
            "rmse_mm": rmse,
            "samples": len(group)
        })

    metrics_df = pd.DataFrame(results)

    # Overall metrics across all reference points
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

    overall = pd.DataFrame([{
        "ponto_id": "ALL",
        "uf": "ALL",
        "model": "Random Forest",
        "mae_mm": overall_mae,
        "rmse_mm": overall_rmse,
        "samples": len(predictions)
    }])

    metrics_df = pd.concat(
        [metrics_df, overall],
        ignore_index=True
    )

    return metrics_df


def save_results(predictions, metrics):
    

    PREDICTIONS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    METRICS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    predictions.to_csv(
        PREDICTIONS_DIR / "random_forest_predictions.csv",
        index=False
    )

    metrics.to_csv(
        METRICS_DIR / "random_forest_metrics.csv",
        index=False
    )


def main():

    df = load_data()

    df, X, y, feature_columns = prepare_model_data(df)

    X_train, X_test, y_train, y_test, test_data = (
        split_data(df, X, y)
    )

    print("\n--- RANDOM FOREST TRAINING ---")

    print("Training samples:", len(X_train))
    print("Test samples:", len(X_test))

    print(
        "Training period:",
        df.loc[X_train.index, "year"].min(),
        "-",
        df.loc[X_train.index, "year"].max()
    )

    print(
        "Test period:",
        df.loc[X_test.index, "year"].min(),
        "-",
        df.loc[X_test.index, "year"].max()
    )

    print("\nTraining model...")

    model = train_model(X_train, y_train)
    feature_importance = calculate_feature_importance(
    model,
    feature_columns
)

    predictions = generate_predictions(
        model,
        X_test,
        test_data
    )

    metrics = calculate_metrics(predictions)

    save_results(predictions, metrics)

    print("\n--- RANDOM FOREST RESULTS ---")

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

    print("\nRandom Forest training completed.")


if __name__ == "__main__":
    main()
