# Decadal comparison — descriptive interpretation

The comparison between decades in EarthScope is descriptive, not inferential.
For each UF and `point_id`, the number of complete years, mean,
median, standard deviation, minimum, and maximum of the annual total are
calculated. Differences in millimeters and percentages between consecutive
decades and between the first and last available decade are also computed.

No Mann–Whitney tests or other hypothesis tests are performed between
decades, no p-values are calculated, and no significance labels are assigned.
This avoids treating samples with different sizes and distinct time periods as
comparable by default.

A partial decade may contain fewer years because it falls at the beginning or
end of the record or because incomplete years are excluded. The CSV reports
`n_years` for each decade and `partial_decade`; the first-to-last comparison
also reports `n_years_first`, `n_years_last`, `first_decade_partial`,
`last_decade_partial`, and `sample_size_unequal`.

The percentage differences reflect only the relative magnitude observed
between the means of the selected periods. They do not show that precipitation
changed in a statistically significant way, do not control for interannual
variability, and do not isolate possible effects of climate cycles or changes
in the data source. For inference about monotonic trend over the full series,
refer to the Mann–Kendall + Sen's Slope analysis, which is a separate analysis
with its own assumptions and corrections.
