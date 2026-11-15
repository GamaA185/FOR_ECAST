# FOR_ECAST

Statistical analysis, machine learning, and visualization of historical
precipitation data in Brazil.

The project covers 27 federal units and one reference point per unit.
Therefore, the results represent those reference points; they are not
statewide spatial averages.

## Prototype:
LINK Figma Prototype: https://www.figma.com/proto/v1nLmA858CgxVrnf4iLuxT/NASA-Space-Apps?node-id=148-126&p=f&t=fHqQBSGjAnhZ4InG-1&scaling=scale-down&content-scaling=fixed&page-id=0%3A1&starting-point-node-id=148%3A126&show-proto-sidebar=1


## Project structure

```text
dashboard/                         Static dashboard
data/
  precipitation/
    raw/raw_files/                 Raw files by year
    processed/                     Processed data and ML features
    metadata/                      Audit and data dictionary
  reports/
    machine_learning/              ML model results
  src/
    extraction/                    Data collection and standardization
    statistics/                    Statistical pipeline
    machine_learning/              Models and evaluation
    reports/                       Statistical reports and figures
    tests/                         Automated tests
```

## Requirements

- Python 3
- pandas
- NumPy
- SciPy
- Matplotlib
- scikit-learn
- pytest (for running tests)
- requests (only for API collection)

Recommended installation in Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install pandas numpy scipy matplotlib scikit-learn pytest requests
```

## Available data

The checkout already contains processed data from **2005 to 2025**:

- `data/precipitation/processed/precipitacao_diaria_27_pontos_2005_2025.csv`
- `data/precipitation/processed/precipitacao_mensal_27_pontos_2005_2025.csv`
- `data/precipitation/processed/precipitacao_anual_27_pontos_2005_2025.csv`
- `data/precipitation/processed/monthly_precipitation_features.csv`
- `data/precipitation/processed/pontos.csv`

The first year starts on January 1 after the UTC date adjustment. Since
the original collection does not contain every day of 2005, analyses
requiring complete years use 2006--2025.

The main daily-data columns are `ponto_id`, `uf`, `latitude`,
`longitude`, `data_inicio`, `precipitacao_mm`, and `completo`. Values are
precipitation in millimeters, with one series per reference point.

## Data collection

The collection code is in `data/src/extraction/`. It accesses the
Meteomatics API and saves files under `data/src/extraction/dados/`.

Configure credentials locally and never commit them to Git:

```powershell
$env:METEOMATICS_USER = "your_username"
$env:METEOMATICS_PASSWORD = "your_password"
```

Run the collector from the repository root:

```powershell
python data\src\extraction\chuva.py
```

You can limit the federal units and select the source:

```powershell
python data\src\extraction\chuva.py --source mix --ufs RJ SP MG
```

For point-based collection, use:

```powershell
python data\src\extraction\pontos.py
```

The collection uses UTC days, assigns each validity timestamp to the
previous day, and never converts missing values to zero. The `mix`
source is exploratory; assess source homogeneity before interpreting
climate trends.

## Statistical pipeline

The pipeline is in `data/src/statistics/run_pipeline.py`. It accepts
CSV, CSV.GZ, or Parquet files with at least these columns:

```text
date,state,precipitation_mm
```

It also accepts aliases used by the current files, such as `data`, `uf`,
`precipitacao_mm`, `ponto_id`, and `location_id`.

### Run with repository data

The processed daily file uses Portuguese column names. The pipeline
recognizes these aliases:

```powershell
python data\src\statistics\run_pipeline.py `
  --input data\precipitation\processed\precipitacao_diaria_27_pontos_2005_2025.csv `
  --today 2025-12-31
```

Results are written to:

```text
data/src/statistics/output/
```

Main generated files include:

- `monthly_precipitation.csv`
- `annual_precipitation.csv`
- `incomplete_periods.csv`
- `data_quality_report.csv`
- `data_quality_by_state.csv`
- `monthly_climatology.csv`
- `precipitation_categories.csv`
- `anomalies.csv`
- `trend_analysis.csv`
- `decadal_comparison.csv`
- `relatorio_resultados.md`
- `figures/`

The pipeline requires either `--input` or `--generate-test-data`:

```powershell
python data\src\statistics\run_pipeline.py --generate-test-data
```

To test classification with an expanding reference:

```powershell
python data\src\statistics\run_pipeline.py `
  --input data\precipitation\processed\precipitacao_diaria_27_pontos_2005_2025.csv `
  --today 2025-12-31 `
  --category-mode expanding
```

### Main statistical rules

- A month is complete only when all days have valid values.
- A year is complete only when all 12 months are complete.
- Missing values are never converted to zero.
- Categories use percentiles from the same calendar month.
- Anomalies use the monthly mean, standard deviation, and Z-score.
- Annual trends use the Mann--Kendall test and Sen's slope.
- When calculated by the module, significance across federal units uses
  the Benjamini--Hochberg adjustment.

## Machine learning

The ML scripts are in `data/src/machine_learning/` and use files from
`data/precipitation/processed/`. Run them from the repository root:

```powershell
python data\src\machine_learning\data_preparation.py
python data\src\machine_learning\feature_engineering.py
python data\src\machine_learning\baseline_model.py
python data\src\machine_learning\random_forest_model.py
python data\src\machine_learning\model_evaluations.py
python data\src\machine_learning\recursive_backtesting.py
python data\src\machine_learning\recursive_model_comparison.py
python data\src\machine_learning\error_analysis.py
```

Results are written to:

```text
data/reports/machine_learning/
  metrics/
  predictions/
  feature_importance/
  recursive_backtesting/
  error_analysis/
```

The Random Forest model uses data through 2021 for training and
2022--2025 for testing. These are historical backtests, not guaranteed
weather forecasts.

## Dashboard

The dashboard is a static application in `dashboard/`. It reads
`dashboard/data.json` and does not query the API from the browser.

Before opening the dashboard, rebuild the JSON from the existing reports:

```powershell
python dashboard\build_dashboard.py
```

This command reads:

- `data/src/reports/statistics/tables/`
- `data/reports/machine_learning/`
- `data/precipitation/processed/pontos.csv`

and writes `dashboard/data.json`. The statistical pipeline and ML
scripts do not automatically replace the versioned reports in
`data/src/reports` used by the builder. If you generate new output in
`data/src/statistics/output`, copy or configure that output before
rebuilding the dashboard.

To open the dashboard in a browser:

```powershell
python dashboard\open_section.py overview
```

Available sections:

```text
overview
indicators
history
seasonality
anomalies
ml-evaluation
methods
```

Example using another port:

```powershell
python dashboard\open_section.py ml-evaluation --port 8001
```

Alternatively, serve the repository root:

```powershell
python -m http.server 8000
```

Then open `http://127.0.0.1:8000/dashboard/`. Do not open
`index.html` directly with `file://`, because the browser may block JSON
loading.

## Tests

The tests import modules directly from the source directories. In
PowerShell, configure both directories in `PYTHONPATH` before running
the suite:

```powershell
$env:PYTHONPATH = "$(Resolve-Path data\src\statistics);$(Resolve-Path data\src\extraction)"
python -m pytest data\src\tests -q
```

## Limitations

1. One reference point per federal unit does not represent the full
   spatial variability of a state.
2. The daily series uses UTC accumulations, which may not match the
   local civil day.
3. 2005 is incomplete in the current collection and must not be treated
   as a complete year.
4. The `mix` source may combine products; source homogeneity and changes
   in origin must be assessed.
5. ML metrics describe the tested historical periods and do not guarantee
   future performance.

## Useful files

- [`data/metadata/data_dictionary.md`](data/metadata/data_dictionary.md)
- [`data/metadata/audit.json`](data/metadata/audit.json)
- [`data/src/reports/results_report.md`](data/src/reports/results_report.md)
- [`dashboard/index.html`](dashboard/index.html)
- [`dashboard/build_dashboard.py`](dashboard/build_dashboard.py)
- [`dashboard/open_section.py`](dashboard/open_section.py)
  
