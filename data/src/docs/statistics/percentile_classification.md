# Percentile classification: `full` and `expanding` modes

This document describes how EarthScope calculates the P10, P30, P70, and P90
thresholds and how the choice of reference mode changes the historical
classification.

## What the two modes have in common

The classification is calculated separately for each UF. For monthly totals,
each month is compared only with the same calendar month in other years for the
same UF (for example, January compared with January). This preserves
seasonality. For annual totals, the comparison is made across years.

The four thresholds are calculated with `numpy.percentile` and linear
interpolation (method 7). The classification uses the following ranges:

| Category | Rule applied |
|---|---|
| Very dry | value < P10 |
| Dry | P10 ≤ value < P30 |
| Normal | P30 ≤ value ≤ P70 |
| Wet | P70 < value ≤ P90 |
| Very wet | value > P90 |

EarthScope requires at least `MIN_REF_YEARS = 10` reference observations.
Below this minimum, the category is `referencia_insuficiente` and the
thresholds remain undefined (`NaN`). Incomplete months and years do not enter
the classification.

## Mode `full` — complete historical reference

In `full` mode, thresholds are calculated once using all complete years
available for that UF and group (calendar month or annual series). Each year
being evaluated is then classified against that same full historical
distribution.

**Consequence:** the reference includes both years before and after the
assessment year and also includes the assessed value itself. Therefore, it is a
retrospective classification: suitable for describing the position of each
period within the full historical series, but it does not represent a
classification that could have been known in real time for that year.

If the group has at least 10 complete years, all years in that group use the
same P10/P30/P70/P90. If it has fewer than 10, all receive
`referencia_insuficiente`.

## Mode `expanding` — historical reference accumulated up to the previous year

In `expanding` mode, to classify a year, the program computes thresholds using
only observations from previous years. The year being classified never
participates in the calculation of its own thresholds, and future years are not
used.

**Consequence:** thresholds can change every year as the historical series
grows. This provides a temporally coherent reference for simulating what would
have been possible to classify at that moment without using future information.

Because the minimum is 10 previous years (`MIN_REF_YEARS = 10`), the first 10
complete years of each group remain `referencia_insuficiente`. Starting from
the 11th available year, classification is calculated. For example, with a full
annual series starting in 2006, 2006–2015 have no 10 previous years; 2016 can
be classified using 2006–2015. For monthly data, this count is computed
separately for each UF-month combination.

## Direct comparison

| Aspect | `full` | `expanding` |
|---|---|---|
| Data used for thresholds | All complete years available | Only years prior to the evaluated year |
| Uses future years relative to the period evaluated? | Yes, when available | No |
| Uses the assessed period itself? | Yes | No |
| Do thresholds change by evaluated year? | No; they are fixed within each UF/group | Yes; they tend to update with new years |
| Early years in the series | Classifiable if there are 10 years in the full group | No reference until 10 previous years are accumulated |
| Interpretation | Retrospective / climatology of the full series | Progressive / evaluation without future information |
| Best use | Consolidated historical reports and whole-series comparison | Operational simulations and time-based assessment without future leakage |

## How to run

The default mode is `full`:

```bash
python run_pipeline.py --input DATA_PATH --today 2025-12-31
```

To use `expanding`:

```bash
python run_pipeline.py --input DATA_PATH --today 2025-12-31 --category-mode expanding
```

The standalone script also accepts `--mode`:

```bash
python precipitation_categories.py --mode full
python precipitation_categories.py --mode expanding
```

## How to identify the mode in the results

The file `precipitation_categories.csv` records the selected mode in the
`reference` column:

- `full_history`: classification in `full` mode.
- `previous_years`: classification in `expanding` mode.

The `n_ref_years` column shows how many years were used as reference for each
row. In `full`, this value corresponds to the total number of complete years
available in the group; in `expanding`, it corresponds to the number of years
prior to the evaluated year. The `percentile_rank` column records the
percentile position of the value in the reference distribution; ties receive
half-weight.

## Interpretation cautions

- Categories are relative to the historical distribution of each UF and, in the
  monthly case, to the same calendar month. “Very wet” does not necessarily mean
  a higher absolute volume than another UF.
- The results of the two modes may legitimately differ because they use
  different reference sets. The two outputs should not be mixed as if they were
  a single homogeneous series.
- In `expanding` mode, thresholds can vary over time; a category change can
  reflect either the observed precipitation or the change in the accumulated
  reference.
- In `full` mode, information from years after the analyzed period is incorporated
  into the reference. This is appropriate for retrospective reading, but not for
  evaluating what would have been known in real time.
- The current configuration requires 10 years of reference. Changing
  `MIN_REF_YEARS` modifies the start of the classifiable series in `expanding`
  mode and should be documented alongside the results.
