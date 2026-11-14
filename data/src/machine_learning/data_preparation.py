import pandas as pd
from pathlib import Path


from pathlib import Path
import pandas as pd

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "precipitation"
    / "processed"
    / "precipitacao_mensal_27_pontos_2005_2025.csv"
)

print("Project root:", PROJECT_ROOT)
print("Data path:", DATA_PATH)
print("File exists:", DATA_PATH.exists())


def load_data():
    df = pd.read_csv(DATA_PATH)
    return df


def prepare_data(df):
    # Cleaning of "Cria"

    df["data_inicio"] = pd.to_datetime(df["data_inicio"])
    df["data_fim_exclusiva"] = pd.to_datetime(df["data_fim_exclusiva"])

    # Precipitation data

    df["precitacao_mm"] = pd.to_numeric(
        df["precipitacao_mm"], errors = "coerce"
    )

    # Temporal Features
    df["year"] = df["data_inicio"].dt.year
    df["month"] = df["data_inicio"].dt.month

    df = df.sort_values(
        ["ponto_id", "data_inicio"]
    ). reset_index(drop=True)

    return df

def validade_data(df):
    # Intergrity verification

    print("\n--- DATA VALIDATION ---")

    print("Reference points:", df["ponto_id"].nunique())

    print("Total records;", len(df))

    print("Missing values:")
    print(df.isnull().sum())

    #Duplicates
    duplicates = df.duplicated(
        subset= ["ponto_id", "data_inicio"]
    ).sum()

    print("Duplicates:", duplicates)

    months_per_point = df.groupby("ponto_id").size()

    print("Months per point:")
    print(months_per_point.describe())


    # Expected temporal coverage

    expected_months = pd.date_range(
        start= "2005-01-01",
        end="2025-12-01",
        freq= "MS"
    )

    for point_id, group in df.groupby("ponto_id"):
        actual_months = pd.DatetimeIndex(
            group["data_inicio"]
        )

        missing_months = expected_months.difference(
            actual_months
        )

        if len(missing_months) > 0:
            print(
                f"WARNING: {point_id} has"
                f"{len(missing_months)} missing months."
            )

    print("\n--- Data Validation Complete ---\n")

def main():
    df = load_data()
    df = prepare_data(df)
    validade_data(df)

    # PRESAVE

    output_path = (
        PROJECT_ROOT
        / "precipitation"
        / "processed"
        / "precipitacao_mensal_27_pontos_2005_2025_cleaned.csv"
    )

    df.to_csv(output_path, index=False)

    print("\n Prepared data saved to:", output_path
          )
if __name__ == "__main__":
    main()