# EarthScope · Sprint 0 — Análise estatística da precipitação

Arquivo analisado: `dados_pontos` · nível de significância α = 0.05 · 27 estados · 2006–2025 (anos completos).

## 1. Qualidade dos dados

| verificação | ocorrências | tratamento | detalhe |
|---|---|---|---|
| registros_recebidos | 207090 | informativo |  |
| datas_invalidas | 0 | registros removidos |  |
| datas_futuras | 27 | registros removidos |  |
| estados_nao_reconhecidos | 0 | registros removidos |  |
| estados_com_grafia_normalizada | 0 | convertidos para sigla UF |  |
| valores_nao_numericos | 0 | convertidos para ausente |  |
| valores_ausentes_na_origem | 0 | mantidos como ausentes |  |
| negativos_por_arredondamento | 0 | ajustados para 0 |  |
| valores_negativos | 0 | convertidos para ausente |  |
| valores_acima_do_limite_fisico | 0 | convertidos para ausente | limite = 700 mm/dia |
| identificadores_ponto_ausentes | 0 | substituídos pela sigla da UF |  |
| duplicatas_exatas | 0 | removidas (mantido o 1º registro) |  |
| duplicatas_conflitantes | 0 | média dos valores do mesmo estado/dia (ponto) |  |
| pontos_de_referencia_preservados | 27 | séries mantidas separadas por UF e identificador do ponto |  |
| estados_sem_nenhum_dado | 0 | informativo |  |
| sequencias_valores_identicos_suspeitas | 0 | apenas sinalizado | >= 5 dias consecutivos > 0 com o mesmo valor |
| meses_incompletos | 27 | excluídos das estatísticas (precip_mm = NaN) | de 6804 estado-meses |
| anos_incompletos | 27 | excluídos das estatísticas anuais e de tendência | de 567 estado-anos |

Regra de completude: um mês só entra nas estatísticas se **todos** os dias têm valor válido (ausência nunca é tratada como zero); um ano só entra se os 12 meses estão completos. Foram identificados **27 meses** e **27 anos** incompletos (lista completa em `incomplete_periods.csv`).

Anos incompletos por estado: **AC**: 2005; **AL**: 2005; **AM**: 2005; **AP**: 2005; **BA**: 2005; **CE**: 2005; **DF**: 2005; **ES**: 2005; **GO**: 2005; **MA**: 2005; **MG**: 2005; **MS**: 2005; **MT**: 2005; **PA**: 2005; **PB**: 2005; **PE**: 2005; **PI**: 2005; **PR**: 2005; **RJ**: 2005; **RN**: 2005; **RO**: 2005; **RR**: 2005; **RS**: 2005; **SC**: 2005; **SE**: 2005; **SP**: 2005; **TO**: 2005.

## 2. Estatística descritiva

| UF | ponto | anos | média anual (mm) | desvio (mm) | CV (%) | média mensal (mm) | ano + chuvoso | mm | ano + seco | mm  |
|---|---|---|---|---|---|---|---|---|---|---|
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

Maiores médias anuais: AM (3227 mm), RR (2657 mm), AP (2450 mm). Menores: PE (504 mm), PB (524 mm), AL (547 mm). Maior variabilidade relativa (CV): RN (86%).

Detalhes por mês do ano em `monthly_climatology.csv`; os 5 maiores/menores meses e anos de cada estado em `extreme_periods.csv`. Gráficos: `figures/evolution_annual_all_states.png`, `figures/climatology_monthly_heatmap.png` e um perfil por estado em `figures/states/`.

## 3. Categorias de precipitação

Cada mês é comparado com o mesmo mês do calendário nos demais anos do mesmo estado (P10/P30/P70/P90, referência: full_history). Frequência observada (todos os estados e meses) vs. esperada:

| categoria | esperada (%) | observada (%) |
|---|---|---|
| muito_seco | 10 | 8.3 |
| seco | 20 | 18.9 |
| normal | 40 | 44.2 |
| chuvoso | 20 | 19.0 |
| muito_chuvoso | 10 | 9.6 |

**Limitação — empates:** em 336 estado-meses (5.0%) os limiares coincidem (típico de meses secos com vários acumulados iguais a 0 mm). Nesses casos a categoria 'muito seco' pode ficar vazia ou rara e as frequências se afastam de 10/20/40/20/10; a coluna `thresholds_degenerate` do CSV marca esses casos.

## 4. Anomalias

| período | n | Z ≤ -2 | Z ≥ +2 | esperado por lado se Normal |
|---|---|---|---|---|
| mensal | 6777 | 14 | 339 | 154.5 |
| trimestre móvel | 6723 | 15 | 313 | 153.3 |
| anual | 540 | 0 | 25 | 12.3 |

O Z-score assume distribuição aproximadamente simétrica. A chuva tem cauda à direita: por isso há bem mais casos de Z ≥ +2 do que de Z ≤ −2, e o Z não deve ser lido como probabilidade exata. Em 27 estados × centenas de meses, dezenas de |Z| ≥ 2 ocorrem por acaso; o Z serve para **ordenar** períodos incomuns, não para provar causa.

Anos mais secos (menor Z anual) por estado: CE 2012 (Z=-2.0), RR 2015 (Z=-1.8), RJ 2014 (Z=-1.8), PI 2012 (Z=-1.6), SP 2014 (Z=-1.5). Anos mais chuvosos: SC 2023 (Z=+3.6), MA 2020 (Z=+3.4), PR 2023 (Z=+3.3), BA 2020 (Z=+3.2), RR 2025 (Z=+3.1).

Episódios de ≥ 3 meses seguidos com |Z| ≥ 1: 82 (25 secos, 57 chuvosos). Os mais longos:

| state | tipo | início | fim | meses | Z médio | anomalia acum. (mm) |
|---|---|---|---|---|---|---|
| RS | chuvoso | 2023-09 | 2024-06 | 10 | 2.7 | 4465.1 |
| AM | chuvoso | 2025-05 | 2025-12 | 8 | 2.3 | 2718.3 |
| TO | chuvoso | 2019-10 | 2020-04 | 7 | 2.0 | 2195.0 |
| MG | chuvoso | 2019-12 | 2020-05 | 6 | 2.0 | 1093.4 |
| PR | chuvoso | 2023-08 | 2024-01 | 6 | 2.0 | 1753.9 |
| MT | chuvoso | 2020-10 | 2021-03 | 6 | 1.7 | 1233.3 |
| SE | seco | 2021-05 | 2021-10 | 6 | -1.3 | -337.5 |
| SC | chuvoso | 2023-07 | 2023-11 | 5 | 2.9 | 2415.2 |

## 5. Tendências (Mann-Kendall + Sen's Slope)

Série analisada: precipitação anual (anos completos) de cada estado. Foram testados **27 estados**. Resultado: **14** com p < 0.05 sem correção para múltiplos testes; **8** após Benjamini-Hochberg (FDR); 5 após Holm. Com 27 testes e nenhuma tendência real, o esperado seria ≈ 1.4 falso-positivo sem correção. Autocorrelação significativa em 4 estado(s) (p corrigido por Hamed-Rao nesses casos).

| UF | ponto | anos | média (mm) | Sen (mm/ano) | IC95 inf | IC95 sup | Sen (%/década) | tau | r1 resíduos | p | p ajust. BH | classificação |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SE | SE_m10.674391_m37.377352 | 20 | 679 | -14.37 | -27.44 | -0.87 | -21.16 | -0.35 | -0.14 | 0,035 | 0,073 | sem_evidencia_suficiente |
| AL | AL_m9.661166_m36.650243 | 20 | 547 | -7.67 | -22.30 | 15.14 | -14.02 | -0.13 | -0.04 | 0,456 | 0,535 | sem_evidencia_suficiente |
| RR | RR_p2.135138_m61.363192 | 20 | 2657 | -20.04 | -43.82 | 33.65 | -7.54 | -0.16 | 0.10 | 0,347 | 0,426 | sem_evidencia_suficiente |
| AC | AC_m9.047868_m70.526498 | 20 | 1954 | -2.90 | -28.09 | 19.36 | -1.48 | -0.03 | 0.17 | 0,871 | 0,871 | sem_evidencia_suficiente |
| PA | PA_m4.749393_m52.897301 | 20 | 2141 | 15.68 | -7.59 | 41.14 | 7.32 | 0.23 | -0.01 | 0,163 | 0,232 | sem_evidencia_suficiente |
| BA | BA_m12.285251_m41.929478 | 20 | 597 | 5.11 | -15.13 | 24.60 | 8.57 | 0.07 | 0.15 | 0,673 | 0,699 | sem_evidencia_suficiente |
| RJ | RJ_m22.911014_m43.209373 | 20 | 1349 | 11.85 | -20.32 | 43.07 | 8.78 | 0.11 | 0.37 | 0,538 | 0,581 | sem_evidencia_suficiente |
| GO | GO_m15.932366_m50.139293 | 20 | 1501 | 20.42 | -21.47 | 57.54 | 13.60 | 0.17 | 0.43 | 0,315 | 0,404 | sem_evidencia_suficiente |
| ES | ES_m19.568768_m40.172199 | 20 | 1054 | 15.37 | -20.00 | 36.57 | 14.57 | 0.12 | -0.14 | 0,496 | 0,558 | sem_evidencia_suficiente |
| AM | AM_m3.131633_m59.982504 | 20 | 3227 | 60.52 | -45.58 | 140.48 | 18.76 | 0.24 | 0.27 | 0,144 | 0,216 | sem_evidencia_suficiente |
| PI | PI_m7.699278_m42.504379 | 20 | 872 | 16.45 | -1.36 | 37.83 | 18.86 | 0.29 | 0.03 | 0,074 | 0,125 | sem_evidencia_suficiente |
| SP | SP_m23.550651_m46.633382 | 20 | 1601 | 34.42 | 7.49 | 55.18 | 21.51 | 0.39 | 0.22 | 0,018 | 0,054 | sem_evidencia_suficiente |
| RO | RO_m10.943145_m62.827786 | 20 | 2091 | 50.49 | 17.90 | 81.08 | 24.15 | 0.51 | 0.08 | 0,002 | 0,011 | crescente |
| PR | PR_m24.484219_m51.814887 | 20 | 2025 | 50.01 | 23.34 | 79.78 | 24.69 | 0.52 | 0.03 | 0,002 | 0,011 | crescente |
| DF | DF_m15.775446_m47.797089 | 20 | 1366 | 33.74 | 0.22 | 67.36 | 24.71 | 0.33 | 0.34 | 0,048 | 0,092 | sem_evidencia_suficiente |
| MA | MA_m5.208550_m45.393026 | 20 | 1574 | 39.07 | 18.76 | 58.76 | 24.83 | 0.52 | -0.05 | 0,002 | 0,011 | crescente |
| SC | SC_m27.062837_m51.114965 | 20 | 2042 | 51.13 | 13.78 | 80.56 | 25.04 | 0.46 | 0.29 | 0,005 | 0,021 | crescente |
| CE | CE_m5.326470_m39.715607 | 20 | 715 | 21.29 | 7.12 | 37.65 | 29.77 | 0.45 | -0.11 | 0,006 | 0,022 | crescente |
| MS | MS_m19.585256_m54.479473 | 20 | 1833 | 56.75 | -2.65 | 82.17 | 30.96 | 0.32 | 0.45 | 0,193 | 0,261 | sem_evidencia_suficiente |
| TO | TO_m10.885513_m48.371691 | 20 | 2122 | 70.75 | 5.66 | 108.75 | 33.34 | 0.34 | 0.44 | 0,128 | 0,203 | sem_evidencia_suficiente |
| MT | MT_m12.211501_m55.571655 | 20 | 2027 | 69.76 | 5.41 | 108.47 | 34.42 | 0.37 | 0.42 | 0,025 | 0,062 | sem_evidencia_suficiente |
| RS | RS_m29.842528_m53.768058 | 20 | 2237 | 94.92 | 44.54 | 162.20 | 42.44 | 0.57 | 0.47 | <0,001 | 0,011 | crescente |
| MG | MG_m18.526484_m44.158865 | 20 | 1148 | 50.90 | 5.70 | 87.75 | 44.34 | 0.38 | 0.39 | 0,021 | 0,057 | sem_evidencia_suficiente |
| AP | AP_p1.354544_m51.916198 | 20 | 2450 | 126.42 | 29.12 | 177.39 | 51.59 | 0.46 | 0.53 | 0,066 | 0,118 | sem_evidencia_suficiente |
| PE | PE_m8.411632_m37.591970 | 20 | 504 | 35.38 | 1.72 | 58.36 | 70.13 | 0.36 | 0.18 | 0,030 | 0,067 | sem_evidencia_suficiente |
| PB | PB_m7.121937_m36.724685 | 20 | 524 | 42.05 | 13.76 | 64.35 | 80.29 | 0.44 | 0.33 | 0,007 | 0,024 | crescente |
| RN | RN_m5.678117_m36.478178 | 20 | 785 | 77.30 | 22.62 | 107.77 | 98.50 | 0.51 | 0.28 | 0,002 | 0,011 | crescente |

**Como ler:** a *inclinação de Sen* diz o tamanho e o sinal da variação estimada; o *p ajustado* diz se há evidência estatística suficiente para afirmar que a tendência existe. Uma inclinação negativa ou positiva **não** é, por si só, tendência: só é classificada como crescente/decrescente quando p ajustado (BH) < 0.05. Os demais ficam como *sem evidência estatística suficiente* — o que **não** prova ausência de tendência, apenas que a série não permite afirmá-la.

Estados com tendência significativa após correção: **CE** (crescente, +21.3 mm/ano, +29.8%/década), **MA** (crescente, +39.1 mm/ano, +24.8%/década), **PB** (crescente, +42.0 mm/ano, +80.3%/década), **PR** (crescente, +50.0 mm/ano, +24.7%/década), **RN** (crescente, +77.3 mm/ano, +98.5%/década), **RO** (crescente, +50.5 mm/ano, +24.1%/década), **RS** (crescente, +94.9 mm/ano, +42.4%/década), **SC** (crescente, +51.1 mm/ano, +25.0%/década). Significativos apenas sem correção (sinal fraco, interpretar com cautela): DF (+33.7 mm/ano, p=0,048, p ajust.=0,092), MG (+50.9 mm/ano, p=0,021, p ajust.=0,057), MT (+69.8 mm/ano, p=0,025, p ajust.=0,062), PE (+35.4 mm/ano, p=0,030, p ajust.=0,067), SE (-14.4 mm/ano, p=0,035, p ajust.=0,073), SP (+34.4 mm/ano, p=0,018, p ajust.=0,054).

Gráficos: `figures/trend_overview.png` e `figures/trend_summary.png`.

## 6. Comparação entre décadas — análise descritiva

Média anual (mm) por década, calculada apenas com anos completos. Décadas com menos de 5 anos completos são omitidas:

| UF | 2010s | 2020s |
|---|---|---|
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

A comparação entre décadas é mantida exclusivamente como descrição. Não são aplicados Mann–Whitney, p-valores, correção por múltiplos testes nem rótulos de significância para diferenças entre décadas.

Décadas parciais (menos de 8 anos completos): 2020s com 6–6 anos.

Maiores diferenças percentuais entre a primeira e a última década disponível (ordenação descritiva por |diferença %|):

| UF | ponto | 1ª década | última | n 1ª | n última | média 1ª (mm) | média última (mm) | dif. (mm) | dif. (%) |
|---|---|---|---|---|---|---|---|---|---|
| RN | RN_m5.678117_m36.478178 | 2010s | 2020s | 10 | 6 | 362.8 | 1680.0 | 1317.1 | 363.0 |
| PB | PB_m7.121937_m36.724685 | 2010s | 2020s | 10 | 6 | 264.3 | 1036.2 | 771.8 | 292.0 |
| PE | PE_m8.411632_m37.591970 | 2010s | 2020s | 10 | 6 | 292.7 | 927.2 | 634.5 | 216.8 |
| MG | MG_m18.526484_m44.158865 | 2010s | 2020s | 10 | 6 | 837.7 | 1815.6 | 977.9 | 116.7 |
| AP | AP_p1.354544_m51.916198 | 2010s | 2020s | 10 | 6 | 1813.6 | 3926.1 | 2112.6 | 116.5 |
| RS | RS_m29.842528_m53.768058 | 2010s | 2020s | 10 | 6 | 1765.1 | 3442.1 | 1677.1 | 95.0 |
| TO | TO_m10.885513_m48.371691 | 2010s | 2020s | 10 | 6 | 1662.2 | 3181.7 | 1519.5 | 91.4 |
| BA | BA_m12.285251_m41.929478 | 2010s | 2020s | 10 | 6 | 453.4 | 838.5 | 385.1 | 84.9 |

**Interpretação:** as décadas podem ter números diferentes de anos completos e representam janelas temporais distintas. As médias, diferenças em milímetros e variações percentuais servem para caracterizar os dados observados; não permitem, por si sós, concluir que houve uma diferença estatisticamente significativa. A incerteza aumenta nas décadas parciais e quando os tamanhos amostrais diferem.

## 8. Metodologia, nível de significância e limitações

- **Significância:** α = 0.05 bicaudal. Decisão de tendência pelo p ajustado de Benjamini-Hochberg (controle da taxa de falsas descobertas entre os estados); Holm é reportado como critério mais rígido.
- **Mann-Kendall:** aproximação normal com correção de empates e de continuidade; adequada para n ≥ 10. **Sen's Slope:** mediana das inclinações par a par, IC 95% de Gilbert.
- **Autocorrelação:** r(1) e Ljung-Box nos resíduos sem tendência. Se significativa, usa-se Mann-Kendall com variância corrigida (Hamed-Rao, nunca reduzindo a variância). Séries anuais de precipitação costumam ter pouca autocorrelação, mas ciclos como o ENSO podem criá-la.
- **Múltiplos testes:** BH assume independência ou dependência positiva entre testes. Estados vizinhos são espacialmente correlacionados, então os 27 testes não são independentes; o número de 'descobertas' deve ser lido como indício regional, não como 27 evidências separadas.
- **Uma série por estado:** a média/soma do estado esconde gradientes internos; tendências opostas em regiões diferentes do mesmo estado podem se anular.
- **Anos incompletos são excluídos**, o que pode abrir lacunas na série (sinalizadas em `has_gaps`).
- **Mudanças de homogeneidade:** se a fonte (modelo/reanálise/estações) mudou ao longo do tempo, uma 'tendência' pode ser artefato dos dados. Mann-Kendall não distingue isso; convém checar a metodologia da fonte.
- **Tendência monotônica linear:** o teste não captura oscilações multidecadais nem mudanças abruptas; uma tendência de 40 anos pode ser parte de um ciclo mais longo.
- **Séries curtas:** poder baixo; ausência de significância ≠ ausência de tendência.
- **Comparação entre décadas:** exclusivamente descritiva. Décadas parciais e tamanhos amostrais desiguais não recebem testes de hipótese; diferenças não devem ser interpretadas como evidência estatística.
- **Categorias:** percentis de ~40 valores por estado-mês são estimativas ruidosas; use com cautela.

## 9. Critério de aceite

Para cada ponto de referência, identificado por UF + `point_id`, `python state_profile.py <UF>` mostra quanto choveu, o comportamento histórico (categorias e anomalias), a tendência com magnitude (Sen), significância (p, p ajustado), autocorrelação e a comparação entre décadas, mantendo a distinção entre direção da tendência e significância estatística.
