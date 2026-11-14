# EarthScope · Sprint 0 — Statistical analysis of precipitation

Analyzed file: `dados_pontos` · significance level α = 0.05 · 27 states · 2006–2025 (complete years).

## 1. Data quality

| check | occurrences | treatment | detail |
| --- | ---: | --- | --- |
| records_received | 207090 | informational |  |
| invalid_dates | 0 | removed records |  |
| future_dates | 27 | removed records |  |
| unrecognized_states | 0 | removed records |  |
| normalized_state_spelling | 0 | converted to UF abbreviation |  |
| non_numeric_values | 0 | converted to missing |  |
| missing_values_in_source | 0 | kept as missing |  |
| rounding_negative_values | 0 | adjusted to 0 |  |
| negative_values | 0 | converted to missing |  |
| values_above_physical_limit | 0 | converted to missing | limit = 700 mm/day |
| missing_point_identifiers | 0 | replaced with UF abbreviation |  |
| exact_duplicates | 0 | removed (first record kept) |  |
| conflicting_duplicates | 0 | average of same state/day (point) values |  |
| preserved_reference_points | 27 | series kept separate by UF and point identifier |  |
| states_with_no_data | 0 | informational |  |
| suspicious_identical_value_sequences | 0 | flagged only | >= 5 consecutive days > 0 with same value |
| incomplete_months | 27 | excluded from statistics (precip_mm = NaN) | of 6804 state-months |
| incomplete_years | 27 | excluded from annual and trend statistics | of 567 state-years |

Completeness rule: a month is included in the statistics only if **all** days have valid values (absence is never treated as zero); a year is included only if all 12 months are complete. **27 incomplete months** and **27 incomplete years** were identified (full list in `incomplete_periods.csv`).

Incomplete years by state: **AC**: 2005; **AL**: 2005; **AM**: 2005; **AP**: 2005; **BA**: 2005; **CE**: 2005; **DF**: 2005; **ES**: 2005; **GO**: 2005; **MA**: 2005; **MG**: 2005; **MS**: 2005; **MT**: 2005; **PA**: 2005; **PB**: 2005; **PE**: 2005; **PI**: 2005; **PR**: 2005; **RJ**: 2005; **RN**: 2005; **RO**: 2005; **RR**: 2005; **RS**: 2005; **SC**: 2005; **SE**: 2005; **SP**: 2005; **TO**: 2005.

## 2. Descriptive statistics

| UF | point | years | mean annual (mm) | std. dev. (mm) | CV (%) | mean monthly (mm) | wettest year | mm | driest year | mm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AC | AC_m9.047868_m70.526498 | 20 | 1954 | 326 | 17 | 162 | 2014 | 2674 | 2020 | 1554 |
| AL | AL_m9.661166_m36.650243 | 20 | 547 | 219 | 40 | 46 | 2020 | 1170 | 2015 | 276 |
| AM | AM_m3.131633_m59.982504 | 20 | 3227 | 1043 | 32 | 268 | 2025 | 6449 | 2018 | 1982 |
| AP | AP_p1.354544_m51.916198 | 20 | 2450 | 1040 | 42 | 202 | 2021 | 4337 | 2012 | 1418 |
| BA | BA_m12.285251_m41.929478 | 20 | 597 | 289 | 48 | 50 | 2020 | 1529 | 2015 | 274 |
| CE | CE_m5.326470_m39.715607 | 20 | 715 | 218 | 30 | 58 | 2024 | 1164 | 2012 | 290 |
| DF | DF_m15.775446_m47.797089 | 20 | 1366 | 400 | 29 | 113 | 2020 | 2275 | 2015 | 827 |
| ES | ES_m19.568768_m40.172199 | 20 | 1054 | 313 | 30 | 89 | 2020 | 1734 | 2015 | 625 |
| GO | GO_m15.932366_m50.139293 | 20 | 1501 | 396 | 26 | 124 | 2024 | 2278 | 2017 | 935 |
| MA | MA_m5.208550_m45.393026 | 20 | 1574 | 474 | 30 | 129 | 2020 | 3169 | 2012 | 997 |
| MG | MG_m18.526484_m44.158865 | 20 | 1148 | 491 | 43 | 95 | 2020 | 2204 | 2014 | 576 |
| MS | MS_m19.585256_m54.479473 | 20 | 1833 | 560 | 31 | 150 | 2023 | 3383 | 2018 | 1332 |
| MT | MT_m12.211501_m55.571655 | 20 | 2027 | 663 | 33 | 167 | 2020 | 3335 | 2017 | 1159 |
| PA | PA_m4.749393_m52.897301 | 20 | 2141 | 319 | 15 | 178 | 2020 | 3077 | 2012 | 1671 |
| PB | PB_m7.121937_m36.724685 | 20 | 524 | 401 | 77 | 43 | 2020 | 1538 | 2012 | 79 |
| PE | PE_m8.411632_m37.591970 | 20 | 504 | 358 | 71 | 41 | 2024 | 1329 | 2012 | 55 |
| PI | PI_m7.699278_m42.504379 | 20 | 872 | 304 | 35 | 72 | 2020 | 1800 | 2012 | 379 |
| PR | PR_m24.484219_m51.814887 | 20 | 2025 | 594 | 29 | 167 | 2023 | 4013 | 2006 | 1247 |
| RJ | RJ_m22.911014_m43.209373 | 20 | 1349 | 329 | 24 | 113 | 2023 | 2182 | 2014 | 752 |
| RN | RN_m5.678117_m36.478178 | 20 | 785 | 678 | 86 | 63 | 2024 | 2097 | 2013 | 142 |
| RO | RO_m10.943145_m62.827786 | 20 | 2091 | 459 | 22 | 172 | 2025 | 3290 | 2010 | 1489 |
| RR | RR_p2.135138_m61.363192 | 20 | 2657 | 589 | 22 | 222 | 2025 | 4497 | 2015 | 1579 |
| RS | RS_m29.842528_m53.768058 | 20 | 2237 | 1022 | 46 | 183 | 2023 | 4770 | 2012 | 1336 |
| SC | SC_m27.062837_m51.114965 | 20 | 2042 | 766 | 37 | 169 | 2023 | 4783 | 2006 | 1201 |
| SE | SE_m10.674391_m37.377352 | 20 | 679 | 178 | 26 | 57 | 2010 | 1036 | 2019 | 434 |
| SP | SP_m23.550651_m46.633382 | 20 | 1601 | 454 | 28 | 131 | 2023 | 2999 | 2014 | 900 |
| TO | TO_m10.885513_m48.371691 | 20 | 2122 | 822 | 39 | 175 | 2020 | 4382 | 2017 | 1186 |

Highest annual means: AM (3227 mm), RR (2657 mm), AP (2450 mm). Lowest: PE (504 mm), PB (524 mm), AL (547 mm). Highest relative variability (CV): RN (86%).

Details by month of the year in `monthly_climatology.csv`; the 5 wettest/driest months and years for each state in `extreme_periods.csv`. Graphs: `figures/evolution_annual_all_states.png`, `figures/climatology_monthly_heatmap.png`, and a state profile in `figures/states/`.

## 3. Precipitation categories

Each month is compared with the same calendar month in other years of the same state (P10/P30/P70/P90, reference: `full_history`). Observed frequency (all states and months) vs. expected:

| category   | expected (%) | observed (%) |
| ---------- | ------------ | ------------ |
| very_dry   | 10           | 8.3          |
| dry        | 20           | 18.9         |
| normal     | 40           | 44.2         |
| wet        | 20           | 19.0         |
| very_wet   | 10           | 9.6          |

**Limitation — ties:** in 336 state-months (5.0%) the thresholds coincide (typical of dry months with several values equal to 0 mm). In these cases the `very_dry` category may be empty or rare and the frequencies depart from 10/20/40/20/10; the `thresholds_degenerate` column in the CSV flags these cases.

## 4. Anomalies

| period         | n    | Z ≤ -2 | Z ≥ +2 | expected per side if Normal |
| -------------- | ---- | ------ | ------ | -------------------------- |
| monthly        | 6777 | 14     | 339    | 154.5                      |
| moving quarter | 6723 | 15     | 313    | 153.3                      |
| annual         | 540  | 0      | 25     | 12.3                       |

The Z-score assumes an approximately symmetric distribution. Rainfall has a right-tail: therefore there are many more cases with Z ≥ +2 than Z ≤ −2, and Z should not be read as an exact probability. Across 27 states × hundreds of months, dozens of |Z| ≥ 2 occur by chance; Z serves to **rank** uncommon periods, not to prove causation.

Driest years (lowest annual Z) by state: CE 2012 (Z=-2.0), RR 2015 (Z=-1.8), RJ 2014 (Z=-1.8), PI 2012 (Z=-1.6), SP 2014 (Z=-1.5). Wettest years: SC 2023 (Z=+3.6), MA 2020 (Z=+3.4), PR 2023 (Z=+3.3), BA 2020 (Z=+3.2), RR 2025 (Z=+3.1).

Episodes of ≥ 3 consecutive months with |Z| ≥ 1: 82 (25 dry, 57 wet). Longest episodes:

| state | type | start     | end       | months | mean Z | cumulative anomaly (mm) |
| ----- | ---- | --------- | --------- | ------ | ------ | ----------------------- |
| RS    | wet  | 2023-09   | 2024-06   | 10     | 2.7    | 4465.1                  |
| AM    | wet  | 2025-05   | 2025-12   | 8      | 2.3    | 2718.3                  |
| TO    | wet  | 2019-10   | 2020-04   | 7      | 2.0    | 2195.0                  |
| MG    | wet  | 2019-12   | 2020-05   | 6      | 2.0    | 1093.4                  |
| PR    | wet  | 2023-08   | 2024-01   | 6      | 2.0    | 1753.9                  |
| MT    | wet  | 2020-10   | 2021-03   | 6      | 1.7    | 1233.3                  |
| SE    | dry  | 2021-05   | 2021-10   | 6      | -1.3   | -337.5                  |
| SC    | wet  | 2023-07   | 2023-11   | 5      | 2.9    | 2415.2                  |

## 5. Trends (Mann-Kendall + Sen's Slope)

Analyzed series: annual precipitation (complete years) for each state. **27 states** were tested. Result: **14** with p < 0.05 without multiple-testing correction; **8** after Benjamini-Hochberg (FDR); 5 after Holm. With 27 tests and no real trend, the expected number would be ≈ 1.4 false positives without correction. Significant autocorrelation was present in 4 states (p corrected by Hamed-Rao in those cases).

| UF | point | years | mean (mm) | Sen (mm/year) | 95% CI low | 95% CI high | Sen (%/decade) | tau | lag-1 residual | p | adjusted p (BH) | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SE | SE_m10.674391_m37.377352 | 20 | 679 | -14.37 | -27.44 | -0.87 | -21.16 | -0.35 | -0.14 | 0.035 | 0.073 | no_sufficient_evidence |
| AL | AL_m9.661166_m36.650243 | 20 | 547 | -7.67 | -22.30 | 15.14 | -14.02 | -0.13 | -0.04 | 0.456 | 0.535 | no_sufficient_evidence |
| RR | RR_p2.135138_m61.363192 | 20 | 2657 | -20.04 | -43.82 | 33.65 | -7.54 | -0.16 | 0.10 | 0.347 | 0.426 | no_sufficient_evidence |
| AC | AC_m9.047868_m70.526498 | 20 | 1954 | -2.90 | -28.09 | 19.36 | -1.48 | -0.03 | 0.17 | 0.871 | 0.871 | no_sufficient_evidence |
| PA | PA_m4.749393_m52.897301 | 20 | 2141 | 15.68 | -7.59 | 41.14 | 7.32 | 0.23 | -0.01 | 0.163 | 0.232 | no_sufficient_evidence |
| BA | BA_m12.285251_m41.929478 | 20 | 597 | 5.11 | -15.13 | 24.60 | 8.57 | 0.07 | 0.15 | 0.673 | 0.699 | no_sufficient_evidence |
| RJ | RJ_m22.911014_m43.209373 | 20 | 1349 | 11.85 | -20.32 | 43.07 | 8.78 | 0.11 | 0.37 | 0.538 | 0.581 | no_sufficient_evidence |
| GO | GO_m15.932366_m50.139293 | 20 | 1501 | 20.42 | -21.47 | 57.54 | 13.60 | 0.17 | 0.43 | 0.315 | 0.404 | no_sufficient_evidence |
| ES | ES_m19.568768_m40.172199 | 20 | 1054 | 15.37 | -20.00 | 36.57 | 14.57 | 0.12 | -0.14 | 0.496 | 0.558 | no_sufficient_evidence |
| AM | AM_m3.131633_m59.982504 | 20 | 3227 | 60.52 | -45.58 | 140.48 | 18.76 | 0.24 | 0.27 | 0.144 | 0.216 | no_sufficient_evidence |
| PI | PI_m7.699278_m42.504379 | 20 | 872 | 16.45 | -1.36 | 37.83 | 18.86 | 0.29 | 0.03 | 0.074 | 0.125 | no_sufficient_evidence |
| SP | SP_m23.550651_m46.633382 | 20 | 1601 | 34.42 | 7.49 | 55.18 | 21.51 | 0.39 | 0.22 | 0.018 | 0.054 | no_sufficient_evidence |
| RO | RO_m10.943145_m62.827786 | 20 | 2091 | 50.49 | 17.90 | 81.08 | 24.15 | 0.51 | 0.08 | 0.002 | 0.011 | increasing |
| PR | PR_m24.484219_m51.814887 | 20 | 2025 | 50.01 | 23.34 | 79.78 | 24.69 | 0.52 | 0.03 | 0.002 | 0.011 | increasing |
| DF | DF_m15.775446_m47.797089 | 20 | 1366 | 33.74 | 0.22 | 67.36 | 24.71 | 0.33 | 0.34 | 0.048 | 0.092 | no_sufficient_evidence |
| MA | MA_m5.208550_m45.393026 | 20 | 1574 | 39.07 | 18.76 | 58.76 | 24.83 | 0.52 | -0.05 | 0.002 | 0.011 | increasing |
| SC | SC_m27.062837_m51.114965 | 20 | 2042 | 51.13 | 13.78 | 80.56 | 25.04 | 0.46 | 0.29 | 0.005 | 0.021 | increasing |
| CE | CE_m5.326470_m39.715607 | 20 | 715 | 21.29 | 7.12 | 37.65 | 29.77 | 0.45 | -0.11 | 0.006 | 0.022 | increasing |
| MS | MS_m19.585256_m54.479473 | 20 | 1833 | 56.75 | -2.65 | 82.17 | 30.96 | 0.32 | 0.45 | 0.193 | 0.261 | no_sufficient_evidence |
| TO | TO_m10.885513_m48.371691 | 20 | 2122 | 70.75 | 5.66 | 108.75 | 33.34 | 0.34 | 0.44 | 0.128 | 0.203 | no_sufficient_evidence |
| MT | MT_m12.211501_m55.571655 | 20 | 2027 | 69.76 | 5.41 | 108.47 | 34.42 | 0.37 | 0.42 | 0.025 | 0.062 | no_sufficient_evidence |
| RS | RS_m29.842528_m53.768058 | 20 | 2237 | 94.92 | 44.54 | 162.20 | 42.44 | 0.57 | 0.47 | <0.001 | 0.011 | increasing |
| MG | MG_m18.526484_m44.158865 | 20 | 1148 | 50.90 | 5.70 | 87.75 | 44.34 | 0.38 | 0.39 | 0.021 | 0.057 | no_sufficient_evidence |
| AP | AP_p1.354544_m51.916198 | 20 | 2450 | 126.42 | 29.12 | 177.39 | 51.59 | 0.46 | 0.53 | 0.066 | 0.118 | no_sufficient_evidence |
| PE | PE_m8.411632_m37.591970 | 20 | 504 | 35.38 | 1.72 | 58.36 | 70.13 | 0.36 | 0.18 | 0.030 | 0.067 | no_sufficient_evidence |
| PB | PB_m7.121937_m36.724685 | 20 | 524 | 42.05 | 13.76 | 64.35 | 80.29 | 0.44 | 0.33 | 0.007 | 0.024 | increasing |
| RN | RN_m5.678117_m36.478178 | 20 | 785 | 77.30 | 22.62 | 107.77 | 98.50 | 0.51 | 0.28 | 0.002 | 0.011 | increasing |

**How to read:** the *Sen slope* indicates the size and sign of the estimated change; the *adjusted p* indicates whether there is sufficient statistical evidence to say the trend exists. A negative or positive slope **by itself** is not a trend: it is classified as increasing/decreasing only when the adjusted p (BH) < 0.05. The others remain *no sufficient statistical evidence* — which **does not** prove the absence of a trend, only that the series does not allow asserting it.

States with statistically significant trends after correction: **CE** (increasing, +21.3 mm/year, +29.8%/decade), **MA** (increasing, +39.1 mm/year, +24.8%/decade), **PB** (increasing, +42.0 mm/year, +80.3%/decade), **PR** (increasing, +50.0 mm/year, +24.7%/decade), **RN** (increasing, +77.3 mm/year, +98.5%/decade), **RO** (increasing, +50.5 mm/year, +24.1%/decade), **RS** (increasing, +94.9 mm/year, +42.4%/decade), **SC** (increasing, +51.1 mm/year, +25.0%/decade). Significant only without correction (weak signal; interpret with caution): DF (+33.7 mm/year, p=0.048, adjusted p=0.092), MG (+50.9 mm/year, p=0.021, adjusted p=0.057), MT (+69.8 mm/year, p=0.025, adjusted p=0.062), PE (+35.4 mm/year, p=0.030, adjusted p=0.067), SE (-14.4 mm/year, p=0.035, adjusted p=0.073), SP (+34.4 mm/year, p=0.018, adjusted p=0.054).

Graphs: `figures/trend_overview.png` and `figures/trend_summary.png`.

## 6. Decadal comparison — descriptive analysis

Annual mean (mm) by decade, calculated only for complete years. Decades with fewer than 5 complete years are omitted:

| UF | 2010s | 2020s |
| --- | --- | --- |
| AC | 2031 | 1867 |
| AL | 477 | 607 |
| AM | 2565 | 4424 |
| AP | 1814 | 3926 |
| BA | 453 | 839 |
| CE | 640 | 906 |
| DF | 1131 | 1846 |
| ES | 882 | 1331 |
| GO | 1256 | 1924 |
| MA | 1399 | 2063 |
| MG | 838 | 1816 |
| MS | 1500 | 2577 |
| MT | 1637 | 2897 |
| PA | 1965 | 2462 |
| PB | 264 | 1036 |
| PE | 293 | 927 |
| PI | 707 | 1180 |
| PR | 1809 | 2619 |
| RJ | 1145 | 1594 |
| RN | 363 | 1680 |
| RO | 2006 | 2478 |
| RR | 2655 | 2685 |
| RS | 1765 | 3442 |
| SC | 1751 | 2794 |
| SE | 654 | 651 |
| SP | 1365 | 2099 |
| TO | 1662 | 3182 |

The comparison between decades is retained purely as description. No Mann–Whitney tests, p-values, multiple-testing correction, or significance labels are applied to differences between decades.

Partial decades (fewer than 8 complete years): 2020s with 6–6 years.

Largest percentage differences between the first and last available decade (descriptive ordering by |difference %|):

| UF | point | 1st decade | last | n 1st | n last | mean 1st (mm) | mean last (mm) | diff. (mm) | diff. (%) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RN | RN_m5.678117_m36.478178 | 2010s | 2020s | 10 | 6 | 362.8 | 1680.0 | 1317.1 | 363.0 |
| PB | PB_m7.121937_m36.724685 | 2010s | 2020s | 10 | 6 | 264.3 | 1036.2 | 771.8 | 292.0 |
| PE | PE_m8.411632_m37.591970 | 2010s | 2020s | 10 | 6 | 292.7 | 927.2 | 634.5 | 216.8 |
| MG | MG_m18.526484_m44.158865 | 2010s | 2020s | 10 | 6 | 837.7 | 1815.6 | 977.9 | 116.7 |
| AP | AP_p1.354544_m51.916198 | 2010s | 2020s | 10 | 6 | 1813.6 | 3926.1 | 2112.6 | 116.5 |
| RS | RS_m29.842528_m53.768058 | 2010s | 2020s | 10 | 6 | 1765.1 | 3442.1 | 1677.1 | 95.0 |
| TO | TO_m10.885513_m48.371691 | 2010s | 2020s | 10 | 6 | 1662.2 | 3181.7 | 1519.5 | 91.4 |
| BA | BA_m12.285251_m41.929478 | 2010s | 2020s | 10 | 6 | 453.4 | 838.5 | 385.1 | 84.9 |

**Interpretation:** decades can have different numbers of complete years and represent distinct temporal windows. The means, differences in millimeters, and percentage changes help characterize observed data; they do not, by themselves, allow concluding that there was a statistically significant difference. Uncertainty increases in partial decades and when sample sizes differ.

## 8. Methodology, significance level, and limitations

- **Significance:** α = 0.05 two-sided. Trend decisions use the adjusted p-value from Benjamini-Hochberg (control of the false discovery rate across states); Holm is reported as a stricter criterion.
- **Mann-Kendall:** normal approximation with tie and continuity correction; appropriate for n ≥ 10. **Sen's Slope:** median of all pairwise slopes, 95% CI from Gilbert.
- **Autocorrelation:** r(1) and Ljung-Box on the residuals after removing trend. If significant, Mann-Kendall is applied with corrected variance (Hamed-Rao, never reducing variance). Annual precipitation series usually show little autocorrelation, but cycles such as ENSO may create it.
- **Multiple tests:** BH assumes independence or positive dependence between tests. Neighboring states are spatially correlated, so the 27 tests are not independent; the number of “discoveries” should be read as regional evidence, not as 27 separate proofs.
- **One series per state:** the state mean/sum hides internal gradients; opposite trends in different regions of the same state can cancel out.
- **Incomplete years are excluded**, which can create gaps in the series (flagged in `has_gaps`).
- **Homogeneity changes:** if the source (model/reanalysis/stations) changed over time, a “trend” may be an artifact of the data. Mann-Kendall does not distinguish this; it is worth checking the source methodology.
- **Monotonic linear trend:** the test does not capture multidecadal oscillations or abrupt shifts; a trend over 40 years may be part of a longer cycle.
- **Short series:** low power; lack of significance ≠ absence of trend.
- **Decadal comparison:** strictly descriptive. Partial decades and unequal sample sizes do not receive hypothesis tests; differences should not be interpreted as statistical evidence.
- **Categories:** percentiles based on ~40 values per state-month are noisy estimates; use with caution.

## 9. Acceptance criteria

For each reference point, identified by UF + `point_id`, `python state_profile.py <UF>` shows how much rain fell, the historical behavior (categories and anomalies), the trend with magnitude (Sen), significance (p, adjusted p), autocorrelation, and the decadal comparison, while keeping the distinction between trend direction and statistical significance.
