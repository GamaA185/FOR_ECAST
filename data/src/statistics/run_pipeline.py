"""Executa todas as etapas do módulo estatístico, na ordem.

    python run_pipeline.py --input data/meteomatics_daily.csv
    python run_pipeline.py --generate-test-data            # base sintética de teste
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import config as cfg
import data_preparation as prep
import descriptive_stats, precipitation_categories, anomaly_analysis, trend_analysis
import decadal_comparison, report_generator, state_profile, generate_test_data
from common import ensure_dirs


def step(name, fn, *a, **kw):
    t0 = time.time()
    print(f"\n[{name}]", flush=True)
    r = fn(*a, **kw)
    print(f"  ok ({time.time() - t0:.1f}s)")
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--input")
    ap.add_argument("--today", default=None, help="AAAA-MM-DD; descarta datas posteriores")
    ap.add_argument("--generate-test-data", action="store_true")
    ap.add_argument("--category-mode", choices=["full", "expanding"], default="full")
    args = ap.parse_args(argv)
    ensure_dirs()
    synthetic = False
    if args.generate_test_data:
        path = cfg.DATA_DIR / "sample_meteomatics_daily.csv.gz"
        step("0. dados sintéticos de teste", generate_test_data.main, ["--out", str(path)])
        args.input, synthetic = str(path), True
    if not args.input:
        ap.error("informe --input ou --generate-test-data")

    def prepare():
        res = prep.prepare(prep.read_input(args.input), today=args.today)
        out = cfg.OUTPUT_DIR
        res["monthly"].to_csv(out / "monthly_precipitation.csv", index=False)
        res["annual"].to_csv(out / "annual_precipitation.csv", index=False)
        res["incomplete"].to_csv(out / "incomplete_periods.csv", index=False)
        res["log"].to_csv(out / "data_quality_report.csv", index=False)
        res["by_state"].to_csv(out / "data_quality_by_state.csv", index=False)
        res["clean"].to_csv(cfg.INTERIM_DIR / "daily_clean.csv.gz", index=False)

    step("1. preparação dos dados", prepare)
    step("2. estatística descritiva", descriptive_stats.main)
    step("3. categorias de precipitação", precipitation_categories.main, ["--mode", args.category_mode])
    step("4. anomalias", anomaly_analysis.main)
    step("5. tendências", trend_analysis.main)
    step("6. comparação entre décadas", decadal_comparison.main)
    step("7. perfis por estado", state_profile.main, ["--all", "--quiet"])
    rep = ["--input-name", Path(args.input).name] + (["--synthetic"] if synthetic else [])
    step("8. relatório", report_generator.main, rep)
    print("\nConcluído. Resultados em", cfg.OUTPUT_DIR)


if __name__ == "__main__":
    main()
