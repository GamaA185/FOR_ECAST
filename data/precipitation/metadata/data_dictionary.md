## Data dictionary

Run `pontos.py`. The three resulting files are
`precipitacao_diaria_27_pontos_2005_2025.csv`, `precipitacao_mensal_27_pontos_2005_2025.csv`,
and `precipitacao_anual_27_pontos_2005_2025.csv`. All share the same schema, use UTF-8
encoding, and use comma as the delimiter with a decimal point.

- `ponto_id`: stable identifier for the point (for example, `ponto_rj_01`).
- `uf`: the federative unit (state) associated with the point.
- `latitude`, `longitude`: coordinates in decimal degrees.
- `data_inicio`: first day included (YYYY-MM-DD, UTC).
- `data_fim_exclusiva`: first day not included in the interval.
- `frequencia`: daily, monthly, or annual.
- `precipitacao_mm`: accumulated precipitation for the interval (in mm), including monthly and annual totals.
- `dias_validos`, `dias_esperados`: time coverage in days.
- `cobertura`: proportion of valid days (0 to 1).
- `completo`: True/False; incomplete totals remain empty.
- `fonte`: `meteomatics_mix`.

Unique key: `ponto_id` + `data_inicio` + `frequencia`. For machine learning,
select a single frequency and perform a time-based train/test split. Mixing
several temporal aggregations for the same interval may lead to data leakage.
Raw files—preserving the original API response (including `precip_24h:mm`)—are
provided for audit purposes; please use the three standardized CSV files for
analysis. Repeated precipitation values across different dates are valid.