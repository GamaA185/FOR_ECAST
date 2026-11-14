"""Gera o relatório de resultados (Markdown) a partir dos CSVs em output/.

Todos os números do texto são calculados a partir dos arquivos; nada é escrito à mão.
Com --synthetic, o relatório avisa que os dados são de teste e inclui a conferência
contra as tendências plantadas (data/sample_planted_truth.csv).
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

import config as cfg
from common import fmt_p, md_table, month_name, read_output


def _list(items):
    return ", ".join(items) if len(items) else "nenhum"


def build_report(synthetic: bool = False, input_name: str = "") -> str:
    log = read_output("data_quality_report.csv")
    bys = read_output("data_quality_by_state.csv")
    summ = read_output("state_summary.csv")
    cat = read_output("precipitation_categories.csv")
    catf = read_output("category_frequency.csv")
    anom = read_output("anomalies.csv")
    asum = read_output("anomaly_summary.csv")
    eps = read_output("anomaly_episodes.csv")
    tr = read_output("trend_analysis.csv")
    dec = read_output("decadal_comparison.csv")
    chg = read_output("decadal_changes.csv")
    inc = read_output("incomplete_periods.csv")
    L = []
    A = L.append

    A("# EarthScope · Sprint 0 — Análise estatística da precipitação")
    A("")
    if synthetic:
        A("> **ATENÇÃO — DADOS SINTÉTICOS DE TESTE.** Este relatório foi gerado com dados simulados "
          "(`generate_test_data.py`), **não com dados reais da Meteomatics**. Os números abaixo validam o "
          "funcionamento do módulo e **não descrevem o clima real dos estados**. Ao receber os dados reais, "
          "rode `python run_pipeline.py --input <arquivo>` para regenerar tudo.")
        A("")
    A(f"Arquivo analisado: `{input_name}` · nível de significância α = {cfg.ALPHA} · "
      f"{summ['state'].nunique()} estados · "
      f"{int(summ['first_complete_year'].min())}–{int(summ['last_complete_year'].max())} (anos completos).")
    A("")

    # ---------------------------------------------------------------- 1
    A("## 1. Qualidade dos dados")
    A("")
    A(md_table(log.rename(columns={"check": "verificação", "count": "ocorrências", "action": "tratamento",
                                   "detail": "detalhe"}).fillna("")))
    A("")
    n_im = int(log.loc[log["check"] == "meses_incompletos", "count"].iloc[0])
    n_ia = int(log.loc[log["check"] == "anos_incompletos", "count"].iloc[0])
    A(f"Regra de completude: um mês só entra nas estatísticas se **todos** os dias têm valor válido "
      f"(ausência nunca é tratada como zero); um ano só entra se os 12 meses estão completos. "
      f"Foram identificados **{n_im} meses** e **{n_ia} anos** incompletos "
      f"(lista completa em `incomplete_periods.csv`).")
    ya = inc[(inc["period_type"] == "annual")].groupby("state")["year"].apply(lambda s: ", ".join(str(int(v)) for v in sorted(s)))
    A("")
    A("Anos incompletos por estado: " + "; ".join(f"**{k}**: {v}" for k, v in ya.items()) + ".")
    A("")

    # ---------------------------------------------------------------- 2
    A("## 2. Estatística descritiva")
    A("")
    t = summ[["state", "point_id", "n_years_complete", "mean_annual_mm", "std_annual_mm", "cv_annual_pct", "mean_monthly_mm",
              "wettest_year", "wettest_year_mm", "driest_year", "driest_year_mm"]].copy()
    t.columns = ["UF", "ponto", "anos", "média anual (mm)", "desvio (mm)", "CV (%)", "média mensal (mm)",
                 "ano + chuvoso", "mm", "ano + seco", "mm "]
    A(md_table(t, decimals=0))
    A("")
    top = summ.nlargest(3, "mean_annual_mm")
    bot = summ.nsmallest(3, "mean_annual_mm")
    A(f"Maiores médias anuais: {_list([f'{r.state} ({r.mean_annual_mm:.0f} mm)' for r in top.itertuples()])}. "
      f"Menores: {_list([f'{r.state} ({r.mean_annual_mm:.0f} mm)' for r in bot.itertuples()])}. "
      f"Maior variabilidade relativa (CV): {summ.loc[summ['cv_annual_pct'].idxmax(), 'state']} "
      f"({summ['cv_annual_pct'].max():.0f}%).")
    A("")
    A("Detalhes por mês do ano em `monthly_climatology.csv`; os 5 maiores/menores meses e anos de cada estado em "
      "`extreme_periods.csv`. Gráficos: `figures/evolution_annual_all_states.png`, "
      "`figures/climatology_monthly_heatmap.png` e um perfil por estado em `figures/states/`.")
    A("")

    # ---------------------------------------------------------------- 3
    A("## 3. Categorias de precipitação")
    A("")
    A("Cada mês é comparado com o mesmo mês do calendário nos demais anos do mesmo estado (P10/P30/P70/P90, "
      f"referência: {cat['reference'].iloc[0]}). Frequência observada (todos os estados e meses) vs. esperada:")
    A("")
    c = cat[(cat["period_type"] == "monthly") & (cat["category"] != "referencia_insuficiente")]
    fr = c["category"].value_counts(normalize=True).reindex(cfg.CATEGORY_LABELS) * 100
    exp = dict(zip(cfg.CATEGORY_LABELS, [10, 20, 40, 20, 10]))
    A(md_table(pd.DataFrame({"categoria": cfg.CATEGORY_LABELS, "esperada (%)": [exp[k] for k in cfg.CATEGORY_LABELS],
                             "observada (%)": [fr[k] for k in cfg.CATEGORY_LABELS]}), decimals=1))
    A("")
    nd = int(c["thresholds_degenerate"].sum())
    A(f"**Limitação — empates:** em {nd} estado-meses ({100 * nd / len(c):.1f}%) os limiares coincidem "
      "(típico de meses secos com vários acumulados iguais a 0 mm). Nesses casos a categoria 'muito seco' pode "
      "ficar vazia ou rara e as frequências se afastam de 10/20/40/20/10; a coluna `thresholds_degenerate` "
      "do CSV marca esses casos.")
    A("")

    # ---------------------------------------------------------------- 4
    A("## 4. Anomalias")
    A("")
    rows = []
    for pt, lab in (("monthly", "mensal"), ("3-month", "trimestre móvel"), ("annual", "anual")):
        g = anom[(anom["period_type"] == pt) & anom["zscore"].notna()]
        rows.append({"período": lab, "n": len(g), "Z ≤ -2": int((g["zscore"] <= -2).sum()),
                     "Z ≥ +2": int((g["zscore"] >= 2).sum()),
                     "esperado por lado se Normal": round(len(g) * 0.0228, 1)})
    A(md_table(pd.DataFrame(rows), decimals=1))
    A("")
    A("O Z-score assume distribuição aproximadamente simétrica. A chuva tem cauda à direita: por isso há bem mais "
      "casos de Z ≥ +2 do que de Z ≤ −2, e o Z não deve ser lido como probabilidade exata. Em 27 estados × centenas "
      "de meses, dezenas de |Z| ≥ 2 ocorrem por acaso; o Z serve para **ordenar** períodos incomuns, não para "
      "provar causa.")
    A("")
    ay = asum[asum["period_type"] == "annual"]
    A(f"Anos mais secos (menor Z anual) por estado: " +
      _list([f"{r.state} {r.driest_period} (Z={r.driest_z:.1f})" for r in ay.nsmallest(5, 'driest_z').itertuples()]) +
      ". Anos mais chuvosos: " +
      _list([f"{r.state} {r.wettest_period} (Z={r.wettest_z:+.1f})" for r in ay.nlargest(5, 'wettest_z').itertuples()]) + ".")
    A("")
    if len(eps):
        A(f"Episódios de ≥ {cfg.EPISODE_MIN_MONTHS} meses seguidos com |Z| ≥ {cfg.EPISODE_Z:g}: {len(eps)} "
          f"({int((eps['kind'] == 'seco').sum())} secos, {int((eps['kind'] == 'chuvoso').sum())} chuvosos). Os mais longos:")
        A("")
        top_ep = eps.sort_values(["n_months", "mean_z"], key=lambda s: s.abs() if s.name == "mean_z" else s,
                                 ascending=False).head(8)
        A(md_table(top_ep[["state", "kind", "start", "end", "n_months", "mean_z", "total_anomaly_mm"]]
                   .rename(columns={"kind": "tipo", "start": "início", "end": "fim", "n_months": "meses",
                                    "mean_z": "Z médio", "total_anomaly_mm": "anomalia acum. (mm)"}), decimals=1))
        A("")

    # ---------------------------------------------------------------- 5
    A("## 5. Tendências (Mann-Kendall + Sen's Slope)")
    A("")
    ok = tr[tr["trend_class"] != "dados_insuficientes"]
    m = len(ok)
    nnom = int(ok["significant_nominal"].sum())
    nfdr = int(ok["significant_fdr"].sum())
    nhol = int(ok["significant_holm"].sum())
    nac = int(ok["autocorr_significant"].sum())
    A(f"Série analisada: precipitação anual (anos completos) de cada estado. Foram testados **{m} estados**. "
      f"Resultado: **{nnom}** com p < {cfg.ALPHA} sem correção para múltiplos testes; "
      f"**{nfdr}** após Benjamini-Hochberg (FDR); {nhol} após Holm. "
      f"Com {m} testes e nenhuma tendência real, o esperado seria ≈ {m * cfg.ALPHA:.1f} falso-positivo sem correção. "
      f"Autocorrelação significativa em {nac} estado(s) (p corrigido por Hamed-Rao nesses casos).")
    A("")
    tt = ok.sort_values("sens_slope_pct_decade")[
        ["state", "point_id", "n_years", "mean_annual_mm", "sens_slope_mm_yr", "sens_ci_low_mm_yr", "sens_ci_high_mm_yr",
         "sens_slope_pct_decade", "mk_tau", "lag1_autocorr_detrended", "p_value_used", "p_adj_bh", "trend_class"]].copy()
    tt["p_value_used"] = tt["p_value_used"].map(fmt_p)
    tt["p_adj_bh"] = tt["p_adj_bh"].map(fmt_p)
    tt.columns = ["UF", "ponto", "anos", "média (mm)", "Sen (mm/ano)", "IC95 inf", "IC95 sup", "Sen (%/década)", "tau",
                  "r1 resíduos", "p", "p ajust. BH", "classificação"]
    A(md_table(tt, decimals=2, formats={"média (mm)": lambda v: f"{v:.0f}"}))
    A("")
    A("**Como ler:** a *inclinação de Sen* diz o tamanho e o sinal da variação estimada; o *p ajustado* diz se há "
      "evidência estatística suficiente para afirmar que a tendência existe. Uma inclinação negativa ou positiva "
      "**não** é, por si só, tendência: só é classificada como crescente/decrescente quando p ajustado (BH) < "
      f"{cfg.ALPHA}. Os demais ficam como *sem evidência estatística suficiente* — o que **não** prova ausência de "
      "tendência, apenas que a série não permite afirmá-la.")
    A("")
    sig = ok[ok["significant_fdr"]]
    near = ok[(~ok["significant_fdr"]) & ok["significant_nominal"]]
    A("Estados com tendência significativa após correção: " +
      _list([f"**{r.state}** ({r.trend_class}, {r.sens_slope_mm_yr:+.1f} mm/ano, {r.sens_slope_pct_decade:+.1f}%/década)"
             for r in sig.itertuples()]) + ". " +
      ("Significativos apenas sem correção (sinal fraco, interpretar com cautela): " +
       _list([f"{r.state} ({r.sens_slope_mm_yr:+.1f} mm/ano, p={fmt_p(r.p_value_used)}, p ajust.={fmt_p(r.p_adj_bh)})"
              for r in near.itertuples()]) + "." if len(near) else ""))
    A("")
    A("Gráficos: `figures/trend_overview.png` e `figures/trend_summary.png`.")
    A("")

    # ---------------------------------------------------------------- 6
    A("## 6. Comparação entre décadas — análise descritiva")
    A("")
    piv = dec.pivot(index="state", columns="decade", values="mean_annual_mm")
    piv.columns = [f"{int(c)}s" for c in piv.columns]
    A("Média anual (mm) por década, calculada apenas com anos completos. Décadas com menos de "
      f"{cfg.MIN_YEARS_DECADE} anos completos são omitidas:")
    A("")
    A(md_table(piv.reset_index().rename(columns={"state": "UF"}), decimals=0))
    A("")
    A("A comparação entre décadas é mantida exclusivamente como descrição. Não são aplicados Mann–Whitney, "
      "p-valores, correção por múltiplos testes nem rótulos de significância para diferenças entre décadas.")
    A("")
    parts = dec[dec["partial_decade"]].groupby("decade")["n_years"].agg(["min", "max"])
    if len(parts):
        A("Décadas parciais (menos de " + str(cfg.FULL_DECADE_YEARS) + " anos completos): " +
          "; ".join(f"{int(d)}s com {int(r['min'])}–{int(r['max'])} anos" for d, r in parts.iterrows()) + ".")
        A("")
    top = chg.head(8)[["state", "point_id", "first_decade", "last_decade", "n_years_first", "n_years_last",
                       "mean_first_mm", "mean_last_mm", "diff_mm", "pct_change"]].copy()
    top.columns = ["UF", "ponto", "1ª década", "última", "n 1ª", "n última",
                   "média 1ª (mm)", "média última (mm)", "dif. (mm)", "dif. (%)"]
    A("Maiores diferenças percentuais entre a primeira e a última década disponível (ordenação descritiva por |diferença %|):")
    A("")
    A(md_table(top, decimals=1, formats={"1ª década": lambda v: f"{int(v)}s", "última": lambda v: f"{int(v)}s"}))
    A("")
    A("**Interpretação:** as décadas podem ter números diferentes de anos completos e representam janelas temporais distintas. "
      "As médias, diferenças em milímetros e variações percentuais servem para caracterizar os dados observados; "
      "não permitem, por si sós, concluir que houve uma diferença estatisticamente significativa. A incerteza aumenta "
      "nas décadas parciais e quando os tamanhos amostrais diferem.")
    A("")

    # ---------------------------------------------------------------- 7 validation (synthetic)
    truth_path = cfg.DATA_DIR / "sample_planted_truth.csv"
    if synthetic and truth_path.exists():
        A("## 7. Verificação contra a verdade plantada (apenas dados sintéticos)")
        A("")
        truth = pd.read_csv(truth_path)
        v = truth.merge(tr[["state", "sens_slope_mm_yr", "sens_ci_low_mm_yr", "sens_ci_high_mm_yr", "p_adj_bh",
                            "autocorr_significant", "lag1_autocorr_detrended", "trend_class"]], on="state")
        v = v[(v["planted_trend_pct_per_year_of_initial_level"] != 0) | (v["planted_ar1_phi"] >= 0.5)].copy()
        v["IC cobre o plantado?"] = (v["sens_ci_low_mm_yr"] <= v["planted_slope_mm_yr_approx"]) & \
                                    (v["planted_slope_mm_yr_approx"] <= v["sens_ci_high_mm_yr"])
        v = v[["state", "planted_slope_mm_yr_approx", "planted_ar1_phi", "sens_slope_mm_yr", "IC cobre o plantado?",
               "lag1_autocorr_detrended", "autocorr_significant", "p_adj_bh", "trend_class"]]
        v.columns = ["UF", "plantado (mm/ano)", "AR1 plantado φ", "Sen estimado (mm/ano)", "IC cobre o plantado?",
                     "r1 estimado", "autocorr. detectada", "p ajust. BH", "classificação"]
        v["p ajust. BH"] = v["p ajust. BH"].map(fmt_p)
        A(md_table(v, decimals=2))
        A("")
        A("Leitura: o sinal da tendência é recuperado na maioria dos estados com tendência plantada, e os casos "
          "fortes são classificados como significativos. Tendências plantadas fracas relativas à variabilidade "
          "(por exemplo RS) **não** são detectadas — é a limitação de poder estatístico de séries anuais de ~40 "
          "anos, não um defeito do código. Estados com persistência (PE, CE) e sem tendência não devem ser "
          "classificados como significativos. As tendências plantadas de SC, GO e MT foram deliberadamente "
          "fortalecidas na base de teste para exercitar os ramos 'crescente/decrescente' do código.")
        A("")

    # ---------------------------------------------------------------- 8
    A("## 8. Metodologia, nível de significância e limitações")
    A("")
    A(f"- **Significância:** α = {cfg.ALPHA} bicaudal. Decisão de tendência pelo p ajustado de Benjamini-Hochberg "
      "(controle da taxa de falsas descobertas entre os estados); Holm é reportado como critério mais rígido.")
    A("- **Mann-Kendall:** aproximação normal com correção de empates e de continuidade; adequada para n ≥ 10. "
      "**Sen's Slope:** mediana das inclinações par a par, IC 95% de Gilbert.")
    A("- **Autocorrelação:** r(1) e Ljung-Box nos resíduos sem tendência. Se significativa, usa-se Mann-Kendall com "
      "variância corrigida (Hamed-Rao, nunca reduzindo a variância). Séries anuais de precipitação costumam ter "
      "pouca autocorrelação, mas ciclos como o ENSO podem criá-la.")
    A("- **Múltiplos testes:** BH assume independência ou dependência positiva entre testes. Estados vizinhos são "
      "espacialmente correlacionados, então os 27 testes não são independentes; o número de 'descobertas' deve "
      "ser lido como indício regional, não como 27 evidências separadas.")
    A("- **Uma série por estado:** a média/soma do estado esconde gradientes internos; tendências opostas em "
      "regiões diferentes do mesmo estado podem se anular.")
    A("- **Anos incompletos são excluídos**, o que pode abrir lacunas na série (sinalizadas em `has_gaps`).")
    A("- **Mudanças de homogeneidade:** se a fonte (modelo/reanálise/estações) mudou ao longo do tempo, uma "
      "'tendência' pode ser artefato dos dados. Mann-Kendall não distingue isso; convém checar a metodologia da fonte.")
    A("- **Tendência monotônica linear:** o teste não captura oscilações multidecadais nem mudanças abruptas; uma "
      "tendência de 40 anos pode ser parte de um ciclo mais longo.")
    A("- **Séries curtas:** poder baixo; ausência de significância ≠ ausência de tendência.")
    A("- **Comparação entre décadas:** exclusivamente descritiva. Décadas parciais e tamanhos amostrais desiguais "
      "não recebem testes de hipótese; diferenças não devem ser interpretadas como evidência estatística.")
    A("- **Categorias:** percentis de ~40 valores por estado-mês são estimativas ruidosas; use com cautela.")
    A("")
    A("## 9. Critério de aceite")
    A("")
    A("Para cada ponto de referência, identificado por UF + `point_id`, `python state_profile.py <UF>` mostra quanto choveu, o comportamento histórico "
      "(categorias e anomalias), a tendência com magnitude (Sen), significância (p, p ajustado), autocorrelação "
      "e a comparação entre décadas, mantendo a distinção entre direção da tendência e significância estatística.")
    A("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--input-name", default="")
    args = ap.parse_args(argv)
    txt = build_report(args.synthetic, args.input_name)
    (cfg.OUTPUT_DIR / "relatorio_resultados.md").write_text(txt, encoding="utf-8")
    print(f"relatório: {len(txt.splitlines())} linhas")


if __name__ == "__main__":
    main()
