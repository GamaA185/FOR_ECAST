# Classificação por percentis: modos `full` e `expanding`

Este documento descreve como o EarthScope calcula os limiares P10, P30, P70 e
P90 e como a escolha do modo de referência altera a classificação histórica.

## O que os dois modos têm em comum

A classificação é calculada separadamente para cada UF. Para os acumulados
mensais, cada mês é comparado apenas com o mesmo mês do calendário nos outros
anos daquela UF (por exemplo, janeiro com janeiros). Isso preserva a
sazonalidade. Para os acumulados anuais, a comparação é feita entre anos.

Os quatro limiares são calculados com `numpy.percentile` e interpolação linear
(método 7). A classificação usa estas faixas:

| Categoria | Regra aplicada |
|---|---|
| Muito seco | valor < P10 |
| Seco | P10 ≤ valor < P30 |
| Normal | P30 ≤ valor ≤ P70 |
| Chuvoso | P70 < valor ≤ P90 |
| Muito chuvoso | valor > P90 |

O EarthScope exige pelo menos `MIN_REF_YEARS = 10` observações de referência.
Abaixo desse mínimo, a categoria é `referencia_insuficiente` e os limiares
ficam sem valor (`NaN`). Meses e anos incompletos não entram na classificação.

## Modo `full` — referência histórica completa

No modo `full`, os limiares são calculados uma única vez usando todos os anos
completos disponíveis para aquela UF e grupo (mês do calendário, ou série
anual). Cada ano avaliado é classificado contra essa mesma distribuição
histórica completa.

**Consequência:** a referência inclui tanto anos anteriores quanto posteriores
ao ano avaliado e inclui também o próprio valor avaliado. Portanto, é uma
classificação retrospectiva: adequada para descrever a posição de cada
período dentro de toda a série histórica disponível, mas não representa uma
classificação que poderia ter sido conhecida em tempo real naquele ano.

Se o grupo tiver pelo menos 10 anos completos, todos os anos desse grupo usam
os mesmos P10/P30/P70/P90. Se tiver menos de 10, todos recebem
`referencia_insuficiente`.

## Modo `expanding` — referência histórica acumulada até o ano anterior

No modo `expanding`, para classificar um ano, o programa calcula os limiares
usando somente as observações dos anos anteriores. O ano que está sendo
classificado nunca participa do cálculo dos seus próprios limiares, e anos
futuros também não são utilizados.

**Consequência:** os limiares podem mudar a cada ano, à medida que a série
histórica cresce. É uma referência temporalmente coerente para simular o que
seria possível classificar naquele momento, sem usar informação futura.

Como o mínimo é de 10 anos anteriores (`MIN_REF_YEARS = 10`), os primeiros
10 anos completos de cada grupo ficam como `referencia_insuficiente`. A partir
do 11º ano disponível, a classificação passa a ser calculada. Por exemplo,
com a série anual completa iniciando em 2006, 2006–2015 não têm 10 anos
anteriores; 2016 pode ser classificado usando 2006–2015. Para dados mensais,
essa contagem é feita separadamente para cada combinação UF-mês.

## Comparação direta

| Aspecto | `full` | `expanding` |
|---|---|---|
| Dados usados nos limiares | Todos os anos completos disponíveis | Somente anos anteriores ao ano avaliado |
| Usa anos futuros em relação ao período avaliado? | Sim, quando disponíveis | Não |
| Usa o próprio período avaliado? | Sim | Não |
| Os limiares mudam por ano avaliado? | Não; são fixos dentro de cada UF/grupo | Sim; tendem a se atualizar com novos anos |
| Primeiros anos da série | Classificáveis se houver 10 anos no grupo completo | Sem referência até acumular 10 anos anteriores |
| Interpretação | Retrospectiva / climatologia da série completa | Progressiva / avaliação sem informação futura |
| Uso mais indicado | Relatórios históricos consolidados e comparação da série inteira | Simulações operacionais e avaliação temporal sem vazamento de informação futura |

## Como executar

O modo padrão é `full`:

```bash
python run_pipeline.py --input CAMINHO_DOS_DADOS --today 2025-12-31
```

Para usar `expanding`:

```bash
python run_pipeline.py --input CAMINHO_DOS_DADOS --today 2025-12-31 --category-mode expanding
```

O script isolado também aceita `--mode`:

```bash
python precipitation_categories.py --mode full
python precipitation_categories.py --mode expanding
```

## Como identificar o modo nos resultados

O arquivo `precipitation_categories.csv` registra a escolha na coluna
`reference`:

- `full_history`: classificação no modo `full`.
- `previous_years`: classificação no modo `expanding`.

A coluna `n_ref_years` informa quantos anos foram usados como referência para
cada linha. Em `full`, esse número corresponde ao total de anos completos
disponíveis no grupo; em `expanding`, corresponde ao número de anos anteriores
ao ano avaliado. A coluna `percentile_rank` registra a posição percentual do
valor na distribuição de referência; empates recebem peso de metade.

## Cuidados de interpretação

- As categorias são relativas à distribuição histórica de cada UF e, no caso
  mensal, ao mesmo mês do calendário. “Muito chuvoso” não significa
  necessariamente um volume absoluto maior que o de outra UF.
- Os resultados dos dois modos podem divergir legitimamente, pois usam
  conjuntos de referência diferentes. Não se deve misturar as duas saídas
  como se fossem uma única série homogênea.
- No modo `expanding`, os limiares podem variar ao longo do tempo; uma mudança
  de categoria pode refletir tanto a precipitação observada quanto a mudança
  da referência acumulada.
- No modo `full`, a informação de anos futuros em relação ao período analisado
  é incorporada à referência. Isso é apropriado para uma leitura retrospectiva,
  mas não para avaliar o que teria sido conhecido em tempo real.
- A configuração atual exige 10 anos de referência. Alterar
  `MIN_REF_YEARS` modifica o início da série classificável no modo `expanding`
  e deve ser documentado junto aos resultados.
