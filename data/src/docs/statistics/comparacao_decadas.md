# Comparação entre décadas — interpretação descritiva

A comparação entre décadas no EarthScope é descritiva, não inferencial.
Para cada UF e `point_id`, são calculados o número de anos completos, média,
mediana, desvio-padrão, mínimo e máximo do acumulado anual. Também são
calculadas diferenças em milímetros e percentuais entre décadas consecutivas
e entre a primeira e a última década disponível.

Não são executados testes Mann–Whitney ou outros testes de hipótese entre
décadas, não são calculados p-valores e não são atribuídos rótulos de
significância. A decisão evita interpretar como comparáveis amostras com
tamanhos diferentes e períodos temporais distintos.

Uma década parcial pode conter menos anos por estar no início/fim da série ou
por ter anos incompletos excluídos. O CSV informa `n_years` em cada década e
`partial_decade`; a comparação primeira–última também informa
`n_years_first`, `n_years_last`, `first_decade_partial`,
`last_decade_partial` e `sample_size_unequal`.

As diferenças percentuais indicam somente a magnitude relativa observada
entre as médias dos períodos selecionados. Não demonstram que a precipitação
mudou de forma estatisticamente significativa, não controlam variabilidade
interanual e não isolam possíveis efeitos de ciclos climáticos ou mudanças
na fonte dos dados. Para inferência sobre tendência monotônica ao longo de
toda a série, consulte a análise Mann–Kendall + Sen's Slope, que é uma análise
separada e possui suas próprias hipóteses e correções.
