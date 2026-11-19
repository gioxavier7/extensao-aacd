from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import Markdown, display


GRUPOS = ["60+", "60-"]
CORES = ["#2563EB", "#F97316"]


def localizar_planilha():
    for pasta in (Path.cwd(), *Path.cwd().parents):
        caminho = pasta / "dados" / "base_quedas_AACD_anonimizada.xlsx"
        if caminho.is_file():
            return caminho
    raise FileNotFoundError(
        "Não foi possível localizar dados/base_quedas_AACD_anonimizada.xlsx "
        "a partir da pasta atual."
    )


def respostas_binarias(serie):
    respostas = serie.astype("string").str.strip().str.lower()
    return respostas.where(respostas.isin(["sim", "não"]))


def resumo_contexto(dados, coluna_contexto):
    linhas = []
    for contexto in dados[coluna_contexto].dropna().unique():
        for grupo in GRUPOS:
            recorte = dados.loc[
                dados[coluna_contexto].eq(contexto)
                & dados["Faixa etária"].eq(grupo)
            ]
            respostas = respostas_binarias(recorte["Queda último mês"])
            validas = respostas.notna()
            n_validas = int(validas.sum())
            n_sim = int(respostas.eq("sim").sum())
            linhas.append(
                {
                    "Contexto": contexto,
                    "Faixa etária": grupo,
                    "N do recorte": len(recorte),
                    "Quedas recentes (n/N)": f"{n_sim}/{n_validas}",
                    "N respostas válidas": n_validas,
                    "Taxa de queda recente (%)": (
                        round(100 * n_sim / n_validas, 1)
                        if n_validas
                        else float("nan")
                    ),
                }
            )
    return pd.DataFrame(linhas)


def quartis_validos(serie):
    valores = pd.to_numeric(serie, errors="coerce").dropna()
    if valores.empty:
        return valores, (float("nan"),) * 3
    q1, mediana, q3 = valores.quantile([0.25, 0.5, 0.75])
    return valores, (q1, mediana, q3)


def executar_analise():
    caminho = localizar_planilha()
    planilha = pd.ExcelFile(caminho)
    dados = pd.concat(
        [
            pd.read_excel(planilha, sheet_name=aba).groupby(
                lambda indice: indice // 2
            ).first()
            for aba in GRUPOS
        ],
        ignore_index=True,
    )

    coluna_idade = next(
        (coluna for coluna in dados.columns if str(coluna).strip() == "Idade"),
        None,
    )
    if coluna_idade is None:
        raise KeyError("A coluna de idade não foi encontrada na planilha original.")

    dados["Idade análise"] = pd.to_numeric(
        dados[coluna_idade]
        .astype("string")
        .str.replace("?", "", regex=False)
        .str.strip(),
        errors="coerce",
    )
    dados["Faixa etária"] = pd.Series(
        pd.NA, index=dados.index, dtype="string"
    )
    dados.loc[
        dados["Idade análise"].ge(60).fillna(False), "Faixa etária"
    ] = "60+"
    dados.loc[
        dados["Idade análise"].lt(60).fillna(False), "Faixa etária"
    ] = "60-"
    dados["Velocidade (m/s)"] = 10 / pd.to_numeric(
        dados["10 metros"], errors="coerce"
    ).where(pd.to_numeric(dados["10 metros"], errors="coerce") > 0)

    comparacao = dados.loc[dados["Faixa etária"].notna()].copy()
    comparacao["Queda último mês"] = (
        comparacao["Queda último mês"]
        .astype("string")
        .str.strip()
        .str.lower()
    )
    comparacao["Sexo análise"] = (
        comparacao["Sexo"].astype("string").str.strip().str.upper()
    )
    comparacao["Diagnóstico análise"] = (
        comparacao["Clínica/Dx"].astype("string").str.strip().str.upper()
    )
    comparacao["Diagnóstico análise"] = comparacao[
        "Diagnóstico análise"
    ].replace({"PARKISON": "PARKINSON", "POLIO?": "POLIO"})

    display(
        Markdown(
            "## 1. Panorama geral: 60+ versus 60-\n"
            "As taxas de queda recente usam somente respostas explícitas "
            "`sim`/`não`; códigos numéricos e vazios não entram no denominador."
        )
    )

    linhas_gerais = []
    for grupo in GRUPOS:
        recorte = comparacao.loc[comparacao["Faixa etária"].eq(grupo)]
        idades, (q1_idade, mediana_idade, q3_idade) = quartis_validos(
            recorte["Idade análise"]
        )
        respostas = respostas_binarias(recorte["Queda último mês"])
        n_respostas = int(respostas.notna().sum())
        n_quedas_recentes = int(respostas.eq("sim").sum())
        quedas, (q1_quedas, mediana_quedas, q3_quedas) = quartis_validos(
            recorte["Nº quedas ao chão"]
        )
        sexo_feminino = int(recorte["Sexo análise"].eq("F").sum())
        linhas_gerais.append(
            {
                "Faixa etária": grupo,
                "Pessoas (N)": len(recorte),
                "Idade mediana [Q1–Q3]": (
                    f"{mediana_idade:.0f} [{q1_idade:.0f}–{q3_idade:.0f}]"
                ),
                "Sexo F, n (%)": (
                    f"{sexo_feminino} ({100 * sexo_feminino / len(recorte):.1f}%)"
                ),
                "Queda último mês, sim (n/N, %)": (
                    f"{n_quedas_recentes}/{n_respostas} "
                    f"({100 * n_quedas_recentes / n_respostas:.1f}%)"
                    if n_respostas
                    else "sem respostas válidas"
                ),
                "Nº quedas mediana [Q1–Q3]": (
                    f"{mediana_quedas:.1f} [{q1_quedas:.1f}–{q3_quedas:.1f}] "
                    f"(n={len(quedas)})"
                    if len(quedas)
                    else "sem valores válidos"
                ),
            }
        )
    resumo_geral = pd.DataFrame(linhas_gerais).set_index("Faixa etária")
    display(resumo_geral)

    respostas_brutas = (
        comparacao["Queda último mês"].astype("string").str.strip().str.lower()
    )
    nao_classificadas = respostas_brutas.loc[
        respostas_brutas.notna() & ~respostas_brutas.isin(["sim", "não"])
    ].value_counts(dropna=False)
    print(
        "Respostas de queda recente não classificadas (fora das taxas):",
        nao_classificadas.to_dict(),
    )
    print(
        "Idades sem classificação etária excluídas:",
        int(dados["Faixa etária"].isna().sum()),
    )

    fig, eixos = plt.subplots(1, 3, figsize=(15, 4.5))
    ns = [int(resumo_geral.loc[grupo, "Pessoas (N)"]) for grupo in GRUPOS]
    barras = eixos[0].bar(GRUPOS, ns, color=CORES)
    eixos[0].bar_label(barras, fmt="%d")
    eixos[0].set_title("Tamanho dos grupos")
    eixos[0].set_ylabel("Pessoas")

    taxas = []
    denominadores = []
    for grupo in GRUPOS:
        recorte = comparacao.loc[comparacao["Faixa etária"].eq(grupo)]
        respostas = respostas_binarias(recorte["Queda último mês"])
        n = int(respostas.notna().sum())
        denominadores.append(n)
        taxas.append(
            100 * int(respostas.eq("sim").sum()) / n if n else float("nan")
        )
    barras = eixos[1].bar(GRUPOS, taxas, color=CORES)
    for barra, taxa, denominador in zip(barras, taxas, denominadores):
        if pd.notna(taxa):
            eixos[1].text(
                barra.get_x() + barra.get_width() / 2,
                barra.get_height(),
                f"{taxa:.1f}% (n={denominador})",
                ha="center",
                va="bottom",
            )
    eixos[1].set_title("Queda no último mês")
    eixos[1].set_ylabel("Respostas sim (%)")
    eixos[1].set_ylim(bottom=0)

    dados_boxplot = []
    rotulos_boxplot = []
    for grupo in GRUPOS:
        valores, _ = quartis_validos(
            comparacao.loc[
                comparacao["Faixa etária"].eq(grupo), "Nº quedas ao chão"
            ]
        )
        if len(valores):
            dados_boxplot.append(valores)
            rotulos_boxplot.append(f"{grupo} (n={len(valores)})")
    eixos[2].boxplot(dados_boxplot, tick_labels=rotulos_boxplot, showfliers=True)
    eixos[2].set_title("Número de quedas ao chão")
    eixos[2].set_ylabel("Contagem registrada")
    fig.tight_layout()
    display(fig)
    plt.close(fig)

    taxas_gerais = dict(zip(GRUPOS, taxas))
    if all(pd.notna(taxas_gerais[grupo]) for grupo in GRUPOS):
        diferenca = taxas_gerais["60+"] - taxas_gerais["60-"]
        print(
            "Leitura descritiva: a diferença na taxa de queda recente "
            f"(60+ menos 60-) é {diferenca:+.1f} pontos percentuais."
        )

    display(
        Markdown(
            "## 2. Contextos sociodemográfico e clínico\n"
            "A comparação agora é estratificada por sexo e pelos diagnósticos "
            "com pelo menos 10 registros no conjunto. O corte reduz a leitura "
            "de percentuais muito instáveis em categorias raras."
        )
    )
    tabela_sexo = resumo_contexto(comparacao, "Sexo análise")
    display(tabela_sexo)
    print("Diferença descritiva de taxa por sexo (60+ menos 60-, em p.p.):")
    for sexo, recorte in tabela_sexo.groupby("Contexto"):
        taxas_sexo = recorte.set_index("Faixa etária")[
            "Taxa de queda recente (%)"
        ]
        denominadores_sexo = recorte.set_index("Faixa etária")[
            "N respostas válidas"
        ]
        if (
            all(grupo in taxas_sexo.index for grupo in GRUPOS)
            and taxas_sexo.loc[GRUPOS].notna().all()
        ):
            diferenca_sexo = taxas_sexo.loc["60+"] - taxas_sexo.loc["60-"]
            n_mais = denominadores_sexo.loc["60+"]
            n_menos = denominadores_sexo.loc["60-"]
            print(
                f"  {sexo}: {diferenca_sexo:+.1f} p.p. "
                f"(N válido: 60+={n_mais}; 60-={n_menos})"
            )

    frequencias_dx = comparacao["Diagnóstico análise"].value_counts()
    diagnosticos_frequentes = frequencias_dx.loc[
        frequencias_dx.ge(10)
    ].index
    comparacao_dx = comparacao.loc[
        comparacao["Diagnóstico análise"].isin(diagnosticos_frequentes)
    ]
    tabela_dx = resumo_contexto(comparacao_dx, "Diagnóstico análise")
    display(tabela_dx)
    print(
        "Diferenças descritivas por diagnóstico (somente quando há pelo "
        "menos 5 respostas válidas em cada faixa; em p.p.):"
    )
    for diagnostico, recorte in tabela_dx.groupby("Contexto"):
        taxas_dx = recorte.set_index("Faixa etária")[
            "Taxa de queda recente (%)"
        ]
        denominadores_dx = recorte.set_index("Faixa etária")[
            "N respostas válidas"
        ]
        if (
            all(grupo in taxas_dx.index for grupo in GRUPOS)
            and denominadores_dx.loc[GRUPOS].ge(5).all()
            and taxas_dx.loc[GRUPOS].notna().all()
        ):
            diferenca_dx = taxas_dx.loc["60+"] - taxas_dx.loc["60-"]
            print(
                f"  {diagnostico}: {diferenca_dx:+.1f} p.p. "
                f"(N válido: 60+={denominadores_dx.loc['60+']}; "
                f"60-={denominadores_dx.loc['60-']})"
            )

    fig, eixos = plt.subplots(1, 2, figsize=(15, 6))
    for eixo, tabela, titulo in [
        (eixos[0], tabela_sexo, "Por sexo"),
        (eixos[1], tabela_dx, "Por diagnóstico (N ≥ 10)"),
    ]:
        if tabela.empty:
            eixo.text(0.5, 0.5, "Sem dados para exibir", ha="center", va="center")
            eixo.set_axis_off()
            continue
        matriz = tabela.pivot(
            index="Contexto",
            columns="Faixa etária",
            values="Taxa de queda recente (%)",
        ).reindex(columns=GRUPOS)
        matriz.plot(kind="barh", ax=eixo, color=CORES)
        eixo.set_title(titulo)
        eixo.set_xlabel("Queda no último mês (%)")
        eixo.set_ylabel("")
        eixo.legend(title="Faixa etária")
        eixo.invert_yaxis()
    fig.tight_layout()
    display(fig)
    plt.close(fig)

    display(
        Markdown(
            "## 3. Foco funcional e cognitivo\n"
            "Medianas e intervalos interquartis são apresentados por faixa "
            "etária, com cobertura explícita. O último recorte compara "
            "velocidade de marcha e sentar/levantar entre quem respondeu "
            "`sim` ou `não` para queda no último mês."
        )
    )
    medidas = [
        ("Cognição (MOCA)", "Cognição (MOCA)"),
        ("Cognição (10-CS)", "Cognição         (10-CS)"),
        ("Sentar/levantar 30s", "Sentar/levantar 30s"),
        ("Velocidade (m/s)", "Velocidade (m/s)"),
        ("Dinamômetro", "Dinamômetro"),
    ]
    linhas_medidas = []
    for rotulo, coluna in medidas:
        for grupo in GRUPOS:
            recorte = comparacao.loc[comparacao["Faixa etária"].eq(grupo)]
            valores, (q1, mediana, q3) = quartis_validos(recorte[coluna])
            linhas_medidas.append(
                {
                    "Medida": rotulo,
                    "Faixa etária": grupo,
                    "N válido": len(valores),
                    "Cobertura no grupo (%)": round(
                        100 * len(valores) / len(recorte), 1
                    ),
                    "Mediana": round(mediana, 2),
                    "Q1": round(q1, 2),
                    "Q3": round(q3, 2),
                }
            )
    tabela_medidas = pd.DataFrame(linhas_medidas)
    display(tabela_medidas)

    fig, eixos = plt.subplots(2, 3, figsize=(15, 9))
    for eixo, (rotulo, coluna) in zip(eixos.flat, medidas):
        valores_por_grupo = []
        rotulos = []
        for grupo in GRUPOS:
            recorte = comparacao.loc[comparacao["Faixa etária"].eq(grupo)]
            valores, _ = quartis_validos(recorte[coluna])
            if len(valores):
                valores_por_grupo.append(valores)
                rotulos.append(f"{grupo} (n={len(valores)})")
        if valores_por_grupo:
            eixo.boxplot(valores_por_grupo, tick_labels=rotulos, showfliers=True)
        else:
            eixo.text(0.5, 0.5, "Sem valores válidos", ha="center", va="center")
        eixo.set_title(rotulo)
        eixo.set_ylabel("Valor registrado")
    eixos.flat[-1].set_visible(False)
    fig.tight_layout()
    display(fig)
    plt.close(fig)

    medidas_foco = [
        ("Velocidade (m/s)", "Velocidade (m/s)"),
        ("Sentar/levantar 30s", "Sentar/levantar 30s"),
    ]
    linhas_foco = []
    fig, eixos = plt.subplots(1, 2, figsize=(13, 5))
    for eixo, (rotulo, coluna) in zip(eixos, medidas_foco):
        valores_por_recorte = []
        rotulos = []
        for grupo in GRUPOS:
            for resposta in ["sim", "não"]:
                recorte = comparacao.loc[
                    comparacao["Faixa etária"].eq(grupo)
                    & comparacao["Queda último mês"].eq(resposta)
                ]
                valores, (q1, mediana, q3) = quartis_validos(recorte[coluna])
                linhas_foco.append(
                    {
                        "Medida": rotulo,
                        "Faixa etária": grupo,
                        "Queda último mês": resposta,
                        "N válido": len(valores),
                        "Mediana [Q1–Q3]": (
                            f"{mediana:.2f} [{q1:.2f}–{q3:.2f}]"
                            if len(valores)
                            else "sem valores válidos"
                        ),
                    }
                )
                if len(valores):
                    valores_por_recorte.append(valores)
                    rotulos.append(f"{grupo}, {resposta}\n(n={len(valores)})")
        if valores_por_recorte:
            eixo.boxplot(
                valores_por_recorte, tick_labels=rotulos, showfliers=True
            )
        else:
            eixo.text(0.5, 0.5, "Sem valores válidos", ha="center", va="center")
        eixo.set_title(rotulo)
        eixo.set_ylabel("Valor registrado")
        eixo.tick_params(axis="x", labelrotation=15)
    fig.tight_layout()
    display(pd.DataFrame(linhas_foco))
    display(fig)
    plt.close(fig)

    print(
        "Interpretação: estes recortes são exploratórios e não ajustam por "
        "confundidores. Diferenças descritivas não demonstram efeito da idade "
        "nem causalidade; medidas com baixa cobertura devem ser lidas com cautela."
    )


if __name__ == "__main__":
    executar_analise()
