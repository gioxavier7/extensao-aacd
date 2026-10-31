# Estrutura e auditoria de qualidade

## Escopo e método

Exploração da planilha `dados/base_quedas_AACD_anonimizada.xlsx` e do CSV
consolidado. A planilha tem abas `60+` e `60-`; o CSV contém 282 registros e
27 colunas. As contagens abaixo descrevem os dados atuais e não alteram a base.

Cada cadastro ocupa até duas linhas na planilha. Aplicando o agrupamento de
duas em duas linhas usado no notebook, resultam 166 registros na aba `60+` e
116 na aba `60-`. Os IDs do CSV vão de 1 a 282, sem repetição.

## Distribuição por aba e idade

| Aba de origem | Registros | Idade >= 60 | Idade < 60 | Idade não interpretável |
|---|---:|---:|---:|---:|
| `60+` | 166 | 159 | 7 | 0 |
| `60-` | 116 | 0 | 115 | 1 |
| **Total** | **282** | **159** | **122** | **1** |

As idades com `?` foram consideradas números após remover a marca (por exemplo,
`59?` passa a 59). A idade `k` não é interpretável. Assim, há 159 pessoas com
60 anos ou mais, 122 com menos de 60 anos e 1 idade sem classificação. A aba
`60+` contém 7 idades abaixo de 60; a aba `60-` contém 1 idade inválida.
Confirmar se a análise deve seguir a aba de origem ou a idade registrada.

Na base consolidada há 179 registros com `Sexo = M` e 103 com `Sexo = F`.

## Quedas por aba

`Nº quedas ao chão` foi convertido para número somente para esta contagem. Os
valores ausentes e a única representação não numérica foram excluídos; não
houve imputação.

| Aba de origem | Registros | Contagens numéricas | Ausentes | Não numéricas | Soma válida | Média válida | Mediana |
|---|---:|---:|---:|---:|---:|---:|---:|
| `60+` | 166 | 160 | 5 | 1 | 242 | 1,51 | 1 |
| `60-` | 116 | 114 | 2 | 0 | 122 | 1,07 | 1 |
| **Total** | **282** | **274** | **7** | **1** | **364** | — | — |

Uma resposta não numérica na aba `60+` contém um caractere antes do número
`2`; precisa ser conferida na origem antes de incluí-la em totais. As médias
são descritivas e não substituem a validação do significado/período da coluna.

## Status funcional e menções a cadeira de rodas

`Status funcional` não é uma variável binária: contém descrições de marcha,
aditamentos e situações combinadas. Após retirar espaços externos, reduzir
espaços repetidos e ignorar diferenças entre maiúsculas/minúsculas:

- 54 registros têm o status exatamente `cadeirante`.
- 71 registros contêm `cadeir`, `cadeira`, `rodas` ou a abreviação `CR`.
  Destes, 49 estão na aba `60+` e 22 na aba `60-`.
- A busca textual inclui descrições de uso em distâncias/contextos específicos
  e a abreviação `CR`; não significa que os 71 sejam cadeirantes em tempo
  integral. Não criar uma classificação clínica sem regra validada.

## Verificações e pendências

- No CSV original, `Suporte social (terapêutico)` tem 5 células vazias e 4
  valores `.`; após o tratamento, são 9 ausentes.
- No CSV original, `Suporte social (domiciliar)` tem 18 células vazias e 3
  valores `.`; após o tratamento, são 21 ausentes.
- `Status funcional`: 18 ausentes. Há 130 valores distintos não ausentes antes
  da normalização de caixa/espaços.
- Os campos de suporte são texto livre com combinações de pessoas/papéis.
  Normalizar caixa/espaços reduz duplicidade de escrita sem fundir papéis ou
  combinações. O tratamento agora converte células vazias e `.` em valores
  ausentes nas três colunas, sem substituí-los por uma categoria.
- `Custo dupla tarefa` está ausente nos 282 registros.
- `Queda último mês` tem 7 valores `0` e 1 valor `2`, além de respostas
  `sim`/`não` e 7 ausentes. Confirmar o significado dos valores numéricos.
- `Panturrilha D` tem duas entradas textuais `AMP` em uma coluna majoritariamente
  numérica; `CIF equilíbrio` tem uma entrada textual `o`.
- A auditoria é descritiva. Valores incomuns não foram corrigidos nem imputados.

## Decisões que dependem da origem

1. Confirmar se valores `.` também devem ser tratados como ausentes nas demais
   colunas da base.
2. Confirmar a regra de contagem de cadeirantes (status exato ou outra regra).
3. Confirmar a idade `k`, a queda escrita com caractere antes de `2` e os
   valores de `Queda último mês`.
4. Confirmar unidades e protocolos das medidas antes de análises clínicas.
