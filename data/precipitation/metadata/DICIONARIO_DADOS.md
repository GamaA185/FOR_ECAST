## Standard for analytical files
Run `pontos.py`. The three resulting files are `precipitacao_diaria_27_pontos_2005_2025.csv`, `precipitacao_mensal_27_pontos_2005_2025.csv`, and `precipitacao_anual_27_pontos_2005_2025.csv`. All share the same schema, use UTF-8 encoding, and employ commas as delimiters with a decimal point.

- `ponto_id`: stable identifier for the point (e.g., `ponto_rj_01`).
- `uf`: the federative unit (state) associated with the point.
- `latitude`, `longitude`: coordinates in decimal degrees.
- `data_inicio`: the first day included (YYYY-MM-DD, UTC).
- `data_fim_exclusiva`: the first day not included in the interval.
- `frequencia`: daily, monthly, or annual.
- `precipitacao_mm`: the accumulated precipitation for the interval (in mm), including monthly and annual totals.
- `dias_validos`, `dias_esperados`: temporal coverage in days.
- `cobertura`: the proportion of valid days (0 to 1).
- `completo`: True/False; incomplete totals are left empty.
- `fonte`: ​​`meteomatics_mix`.

Unique key: `ponto_id` + `data_inicio` + `frequencia`. For machine learning, select a single frequency and perform a train/test split based on time. Mixing different temporal aggregations for the same interval may lead to data leakage. Raw files—which preserve the original API response (including `precip_24h:mm`)—are provided for auditing purposes; please use the three standardized CSV files for your analysis. Repeated precipitation values ​​across different dates are valid.