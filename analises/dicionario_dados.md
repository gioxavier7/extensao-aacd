# Dicionário de dados

## Escopo

Inventário da base `dados/base_quedas_AACD_anonimizada.csv` em 30/10/2026:
282 registros e 27 colunas. As descrições abaixo foram inferidas dos nomes das
colunas e dos valores observados; confirmar definições, protocolos e unidades
com o formulário/origem antes de interpretar clinicamente.

`Ausentes` nesta tabela conta células vazias no CSV original; o valor literal
`.` aparece como texto e não entra na contagem bruta. No tratamento do notebook,
células vazias e `.` passam a nulos nas três colunas de suporte/status.

| Coluna no CSV | Tipo lido | Ausentes | Valores distintos* | Descrição preliminar |
|---|---:|---:|---:|---|
| `ID` | inteiro | 0 | 282 | Identificador sequencial anonimizado no CSV. |
| `Sexo` | texto | 0 | 2 | Código registrado (`F`/`M`); significado conforme cadastro de origem. |
| `Idade ` | texto | 0 | 72 | Idade registrada; unidade presumida em anos, a confirmar. O espaço final faz parte do nome original. |
| `Clínica/Dx` | texto | 0 | 19 | Clínica ou diagnóstico registrado, incluindo siglas não decodificadas na base. |
| `Diagnóstico Funcional` | texto | 213 | 16 | Descrição textual do diagnóstico funcional. |
| `Polifarmácia?` | texto | 33 | 3 | Resposta registrada sobre polifarmácia; predominam `sim` e `não`. |
| `Suporte social (terapêutico)` | texto | 5 | 62 | Pessoa/arranjo de suporte no contexto terapêutico; critério exato não documentado. |
| `Suporte social (domiciliar)` | texto | 18 | 79 | Pessoa/arranjo de suporte no domicílio; critério exato não documentado. |
| `Status funcional` | texto | 18 | 130 | Descrição livre de mobilidade, deslocamento ou assistência funcional. |
| `Cognição (MOCA)` | decimal | 206 | 21 | Resultado associado ao instrumento MOCA; escala/protocolo não informados. |
| `Cognição         (10-CS)` | decimal | 216 | 11 | Resultado associado ao instrumento 10-CS; espaços internos fazem parte do nome original. |
| `Nº quedas ao chão` | texto | 7 | 18 | Quantidade registrada de quedas ao chão; há uma representação não numérica a revisar. |
| `Queda último mês` | texto | 7 | 4 | Registro de queda no último mês; há valores além de `sim`/`não` a revisar. |
| `Sentar/levantar 30s` | decimal | 170 | 18 | Resultado do teste sentar/levantar em 30 segundos; protocolo a confirmar. |
| `Ponte` | decimal | 126 | 28 | Resultado registrado para ponte; definição/unidade não informada. |
| `Dinamômetro` | decimal | 5 | 50 | Medida registrada com dinamômetro; unidade e protocolo não informados. |
| `Panturrilha D` | texto | 107 | 61 | Valor registrado para panturrilha direita; medida e unidade a confirmar. |
| `Panturrilha E` | decimal | 120 | 41 | Valor registrado para panturrilha esquerda; medida e unidade a confirmar. |
| `Braço D` | decimal | 249 | 18 | Valor registrado para braço direito; medida e unidade a confirmar. |
| `Braço E` | decimal | 257 | 15 | Valor registrado para braço esquerdo; medida e unidade a confirmar. |
| `10 metros` | decimal | 46 | 90 | Resultado associado ao teste de 10 metros; unidade/protocolo não informados. |
| `Aditamento 10m` | texto | 52 | 26 | Aditamento/auxílio registrado para o teste de 10 metros. |
| `CIF equilíbrio` | texto | 6 | 11 | Registro relacionado a equilíbrio pela CIF; código/escala precisa confirmação. |
| `Posição equilíbrio` | texto | 6 | 4 | Posição registrada na avaliação de equilíbrio. |
| `Reação (blazepod)` | decimal | 7 | 48 | Resultado da tarefa de reação BlazePod; unidade não informada. |
| `Reação (blazepod) DT` | decimal | 15 | 43 | Resultado da tarefa de reação BlazePod em dupla tarefa; unidade não informada. |
| `Custo dupla tarefa` | decimal | 282 | 0 | Campo sem valores preenchidos nesta versão da base. |

\* Valores distintos não contam ausentes. Diferenças de caixa/espaços ainda
contam como valores distintos nesta contagem bruta.

## Observações sobre os nomes

- O notebook remove o espaço final de `Idade ` e o ponto de interrogação de
  `Polifarmácia?`.
- Idades sem conversão numérica permanecem ausentes; não há preenchimento pela
  média.
- `Cognição         (10-CS)` tem espaços repetidos no nome. O notebook renomeia
  essa coluna, mas a grafia do novo nome deve ser revisada antes de exportar.
- Esta tabela descreve os nomes originais do CSV, sem alterar a base.
