# NASA_Project_FOR_Data
Statistical study and machine learning applied to NASA precipitation data for Brazil.

## Interactive dashboard

The English-language EarthScope dashboard in `dashboard/` combines the precipitation statistics, categories, anomalies, trend analysis, quality summaries, and machine-learning evaluation. It includes the general-indicator cards, historical charts, seasonal climatology, monthly category heatmap, anomaly and trend panels, model backtests, methodology, data inspection, and CSV export.

### Run the dashboard

From this project directory, start a local web server:

```bash
python -m http.server 8000
```

Open [http://localhost:8000/dashboard/](http://localhost:8000/dashboard/). The daily observations are loaded only when the daily time resolution is selected.

### Open a dashboard section from the terminal

Run one of these commands from the project directory. The launcher starts a local server on port 8000 if needed and opens the requested section in your browser:

```powershell
python dashboard\open_section.py overview
python dashboard\open_section.py indicators
python dashboard\open_section.py history
python dashboard\open_section.py seasonality
python dashboard\open_section.py anomalies
python dashboard\open_section.py ml-evaluation
python dashboard\open_section.py methods
```

Use `python dashboard\open_section.py --help` to see all available sections. If port 8000 is already used by another application, choose another port with `--port`, for example `python dashboard\open_section.py history --port 8001`.

### Refresh the dashboard analysis data

After recalculating the statistics or machine-learning reports, regenerate `dashboard/data.json`:

```bash
python dashboard/build_dashboard.py
```

The exporter reads the existing statistical tables and machine-learning reports under `data/`. The chart distinguishes a selected state from an optional comparison state, and can independently overlay a second period. Select one time resolution at a time—days, months, or years—because precipitation totals at different resolutions are not directly comparable. State and period comparisons use yellow and purple, respectively.

Historical monthly averages, wettest/driest months, categories, and trend statistics use the fixed reference and do not change with the displayed range. The selected-period anomaly compares the selected total with its matching daily, calendar-month, or annual historical climatology. Monthly totals must be complete; annual totals require all 12 months. Results describe one reference point per federal unit, not state-wide spatial averages. Machine-learning metrics describe held-out and recursive backtests, not guaranteed future performance.

The interface uses reusable CSS color tokens and semantic HTML/SVG elements to support recreating the design in Figma.
