
import pandas as pd
from pathlib import Path


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "precipitation"
    / "processed"
    / "precipitacao_mensal_27_pontos_2005_2025_cleaned.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "precipitation"
    / "processed"
    / "monthly_precipitation_features.csv"
)


def load_data():
    

    return pd.read_csv(
        DATA_PATH,
        parse_dates=["data_inicio"]
    )

# Feature Engineering Functions

def create_features(df):
    

    df = df.copy()

    
    df = df.sort_values(
        ["ponto_id", "data_inicio"]
    ).reset_index(drop=True)

    
    df["year"] = df["data_inicio"].dt.year
    df["month"] = df["data_inicio"].dt.month

    # Previous precipitation values
    for lag in [1, 2, 3, 12]:
        df[f"lag_{lag}"] = (
            df.groupby("ponto_id")["precipitacao_mm"]
            .shift(lag)
        )

    # Rolling averages using only previous months
    for window in [3, 12]:
        df[f"rolling_{window}"] = (
            df.groupby("ponto_id")["precipitacao_mm"]
            .transform(
                lambda series: (
                    series.shift(1)
                    .rolling(window=window, min_periods=window)
                    .mean()
                )
            )
        )

    
    import numpy as np

    df["month_sin"] = np.sin(
        2 * np.pi * df["month"] / 12
    )

    df["month_cos"] = np.cos(
        2 * np.pi * df["month"] / 12
    )

    return df

# Encode reference points
def encode_reference_points(df):
    

    df = df.copy()

    uf_encoded = pd.get_dummies(
        df["uf"],
        prefix="uf",
        dtype=int
    )

    df = pd.concat(
        [df, uf_encoded],
        axis=1
    )

    return df


def prepare_features(df):
    

    df = create_features(df)

    df = encode_reference_points(df)

    # Remove records without sufficient historical information
    feature_columns = [
        "lag_1",
        "lag_2",
        "lag_3",
        "lag_12",
        "rolling_3",
        "rolling_12",
        "month_sin",
        "month_cos"
    ]

    df = df.dropna(
        subset=feature_columns
    ).reset_index(drop=True)

    return df


def main():

    df = load_data()

    df = prepare_features(df)

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n--- Feature Engineering Complete ---")

    print("Total records:", len(df))
    print("Reference points:", df["ponto_id"].nunique())

    print("\nCreated features:")
    print([
        "lag_1",
        "lag_2",
        "lag_3",
        "lag_12",
        "rolling_3",
        "rolling_12",
        "month_sin",
        "month_cos"
    ])

    print("\nDataset saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
