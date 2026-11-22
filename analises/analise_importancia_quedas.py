"""Quais informações mais acompanham as quedas na base da AACD.

A comparação entre 60+ e 60-, por sexo, diagnóstico e medidas funcionais,
fica em ``analise_estatistica.py``. Aqui o recorte é outro: a força de cada
informação diante da queda, e o perfil da pessoa que mais caiu e da que
menos caiu. A leitura é exploratória: diferença de taxa não é causa.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import Markdown, display
from matplotlib.ticker import FuncFormatter


MINIMO_PESSOAS = 8
MINIMO_PERFIL = 15
CONTRASTE_MINIMO_PP = 3
COR_ALTA = "#DC2626"
COR_BAIXA = "#059669"
COR_NEUTRA = "#2563EB"
COR_CONTAGEM = "#7C3AED"
VALORES_FORA_DO_PERFIL = {
    "sem informação",
    "não informado",
    "não especificado",
    "outros",
    "outros diagnósticos",
}

PASTA_ANALISES = Path(__file__).resolve().parent


def localizar_base():
    nome = Path("dados") / "base_quedas_AACD_anonimizada.csv"
    candidatos = [Path.cwd(), PASTA_ANALISES, *Path.cwd().parents, *PASTA_ANALISES.parents]
    for pasta in candidatos:
        caminho = pasta / nome
        if caminho.is_file():
            return caminho
    raise FileNotFoundError(
        "Não foi possível localizar dados/base_quedas_AACD_anonimizada.csv "
        "a partir da pasta atual."
    )


def mostrar(obj):
    display(obj)


def estilo_eixo(eixo, grade="x"):
    eixo.grid(True, axis=grade, linestyle="--", alpha=0.45)
    eixo.spines["top"].set_visible(False)
    eixo.spines["right"].set_visible(False)


def formato_percentual(eixo, horizontal=True):
    formatador = FuncFormatter(lambda valor, _pos: f"{100 * valor:.0f}%")
    if horizontal:
        eixo.xaxis.set_major_formatter(formatador)
    else:
        eixo.yaxis.set_major_formatter(formatador)


def exibir(fig):
    fig.tight_layout()
    mostrar(fig)
    plt.close(fig)


def cramers_v(primeira, segunda):
    tabela = pd.crosstab(primeira, segunda)
    if tabela.shape[0] < 2 or tabela.shape[1] < 2:
        return np.nan
    observado = tabela.to_numpy(dtype=float)
    tamanho = observado.sum()
    if tamanho < 2:
        return np.nan
    esperado = np.outer(observado.sum(axis=1), observado.sum(axis=0)) / tamanho
    if np.any(esperado <= 0):
        return np.nan
    chi2 = ((observado - esperado) ** 2 / esperado).sum()
    phi2 = chi2 / tamanho
    linhas, colunas = observado.shape
    phi2_corrigido = max(0, phi2 - ((colunas - 1) * (linhas - 1)) / (tamanho - 1))
    linhas_corrigidas = linhas - ((linhas - 1) ** 2) / (tamanho - 1)
    colunas_corrigidas = colunas - ((colunas - 1) ** 2) / (tamanho - 1)
    denominador = min(colunas_corrigidas - 1, linhas_corrigidas - 1)
    if denominador <= 0:
        return np.nan
    return float(np.sqrt(phi2_corrigido / denominador))


def eta_squared(categorias, numeros):
    quadro = pd.DataFrame({"categoria": categorias, "numero": numeros}).dropna()
    if quadro["categoria"].nunique() < 2 or len(quadro) < 3:
        return np.nan
    media = quadro["numero"].mean()
    soma_total = ((quadro["numero"] - media) ** 2).sum()
    if soma_total == 0:
        return 0.0
    soma_entre = sum(
        len(grupo) * (grupo["numero"].mean() - media) ** 2
        for _, grupo in quadro.groupby("categoria")
    )
    return float(soma_entre / soma_total)


def texto_limpo(serie):
    return serie.astype("string").str.strip()


def marcar_sem_informacao(serie):
    texto = texto_limpo(serie)
    return texto.fillna("sem informação").replace({"": "sem informação", "<NA>": "sem informação"})


def descartar_grupos_pequenos(serie, minimo=MINIMO_PESSOAS):
    contagem = serie.dropna().value_counts()
    pequenos = set(contagem.loc[contagem.lt(minimo)].index)
    return serie.where(~serie.isin(pequenos))


def agrupar_frequentes(serie, rotulo_outros):
    texto = texto_limpo(serie)
    contagem = texto.dropna().value_counts()
    frequentes = set(contagem.loc[contagem.ge(MINIMO_PESSOAS)].index)
    agrupado = texto.where(texto.isna() | texto.isin(frequentes), rotulo_outros)
    return descartar_grupos_pequenos(agrupado)


def agrupar_auxilio(serie):
    texto = texto_limpo(serie).fillna("sem informação").str.lower()

    def classe(valor):
        if pd.isna(valor) or valor in {"", "nan", "não informado", "sem informação"}:
            return "sem informação"
        if "cadeira" in valor:
            return "cadeira de rodas"
        if "andador" in valor:
            return "andador"
        if "muleta" in valor:
            return "muleta"
        if "bengala" in valor or "bastão" in valor or "bastao" in valor:
            return "bengala ou bastão"
        if valor in {"nenhum", "comunitária independente", "comunitaria independente"}:
            return "nenhum"
        if any(termo in valor for termo in ("prótese", "protese", "órtese", "ortese")):
            return "prótese ou órtese"
        return "outros"

    return descartar_grupos_pequenos(texto.map(classe))


def agrupar_status(serie):
    texto = texto_limpo(serie).fillna("sem informação").str.lower()

    def classe(valor):
        if pd.isna(valor) or valor in {"", "nan", "não informado", "sem informação"}:
            return "sem informação"
        if "cadeir" in valor:
            return "cadeirante"
        if "comunit" in valor:
            return "marcha comunitária"
        if "domicil" in valor:
            return "marcha domiciliar"
        if "terap" in valor:
            return "marcha terapêutica"
        if valor in {"marcha", "deambulador"}:
            return "marcha sem detalhe de ambiente"
        return "outros"

    return descartar_grupos_pequenos(texto.map(classe))


def agrupar_nivel(serie):
    texto = texto_limpo(serie).fillna("sem informação").str.lower()

    def classe(valor):
        if pd.isna(valor) or valor in {"", "nan"}:
            return "sem informação"
        if "não espec" in valor or "nao espec" in valor:
            return "não especificado"
        if "não informado" in valor:
            return "sem informação"
        if "longa" in valor:
            return "longas distâncias"
        if "curta" in valor:
            return "curtas distâncias"
        return valor

    return descartar_grupos_pequenos(texto.map(classe))


def agrupar_posicao(serie):
    texto = texto_limpo(serie).fillna("sem informação").str.lower()

    def classe(valor):
        if pd.isna(valor) or valor in {"", "nan", "não informado", "sem informação"}:
            return "sem informação"
        if valor.startswith("sentad"):
            return "sentado"
        if "ortostat" in valor:
            return "ortostatismo"
        return valor

    return descartar_grupos_pequenos(texto.map(classe))


def agrupar_diagnostico_funcional(serie):
    texto = texto_limpo(serie)
    baixo = texto.str.lower()
    vazio = texto.isna() | baixo.isin(["", "nan", "não informado", "none"])
    hemiparesia = (
        baixo.str.contains("hemip", na=False)
        & ~baixo.str.contains("dupla|tetra", na=False)
    )
    agrupado = pd.Series(pd.NA, index=serie.index, dtype="string")
    agrupado.loc[~vazio & hemiparesia] = "hemiparesia"
    agrupado.loc[~vazio & ~hemiparesia] = "outro diagnóstico funcional"
    return descartar_grupos_pequenos(agrupado)


def agrupar_cif(serie):
    numero = pd.to_numeric(serie, errors="coerce")
    agrupado = pd.Series(pd.NA, index=serie.index, dtype="string")
    agrupado.loc[numero.eq(0)] = "0 sem deficiência"
    agrupado.loc[numero.eq(1)] = "1 deficiência leve"
    agrupado.loc[numero.eq(2)] = "2 deficiência moderada"
    agrupado.loc[numero.ge(3)] = "3 ou 4 deficiência grave"
    return descartar_grupos_pequenos(agrupado)


def resposta_sim_nao(serie):
    texto = texto_limpo(serie).str.lower()
    agrupado = pd.Series("sem informação", index=serie.index, dtype="string")
    agrupado.loc[texto.eq("sim")] = "sim"
    agrupado.loc[texto.eq("não")] = "não"
    agrupado.loc[texto.eq("nao")] = "não"
    return descartar_grupos_pequenos(agrupado)


def faixa_numerica(serie, casas):
    numeros = pd.to_numeric(serie, errors="coerce")
    validos = numeros.dropna()
    saida = pd.Series(pd.NA, index=serie.index, dtype="string")
    if validos.nunique() < 2 or len(validos) < MINIMO_PESSOAS * 2:
        return saida
    faixas = pd.qcut(validos, q=4, duplicates="drop")
    if getattr(faixas.dtype, "categories", None) is None or len(faixas.cat.categories) < 2:
        return saida
    usados = {}
    for categoria in faixas.cat.categories:
        membros = validos.loc[faixas.eq(categoria)]
        esquerda = float(membros.min())
        direita = float(membros.max())
        if round(esquerda, casas) == round(direita, casas):
            rotulo = f"{esquerda:.{casas}f}"
        else:
            rotulo = f"{esquerda:.{casas}f} até {direita:.{casas}f}"
        if rotulo in usados:
            usados[rotulo] += 1
            rotulo = f"{rotulo} ({usados[rotulo]})"
        else:
            usados[rotulo] = 1
        saida.loc[membros.index] = rotulo
    return saida


def preparar_dados(brutos):
    dados = brutos.copy()
    dados = dados.replace(
        to_replace=r"(?i)^\s*(não informado|\.)\s*$",
        value=np.nan,
        regex=True,
    )
    dados = dados.replace(to_replace=r"^\s*$", value=np.nan, regex=True)

    queda = texto_limpo(dados["Queda último mês"]).str.lower()
    dados["queda_recente"] = queda.map({"sim": 1, "não": 0})
    dados["n_quedas"] = pd.to_numeric(dados["Nº quedas ao chão"], errors="coerce")
    dados["idade"] = pd.to_numeric(dados["Idade"], errors="coerce")
    dados["faixa_idade"] = pd.cut(
        dados["idade"],
        bins=[0, 49, 59, 69, 79, 200],
        labels=[
            "até 49 anos",
            "50 a 59 anos",
            "60 a 69 anos",
            "70 a 79 anos",
            "80 anos ou mais",
        ],
    ).astype("string")

    sexo = texto_limpo(dados["Sexo"]).str.upper()
    dados["sexo"] = sexo.map({"F": "feminino", "M": "masculino"})
    dados["clinica"] = agrupar_frequentes(dados["Clínica/Dx"], "outros diagnósticos")
    dados["diagnostico_funcional"] = agrupar_diagnostico_funcional(
        dados["Diagnóstico Funcional"]
    )
    dados["polifarmacia"] = resposta_sim_nao(dados["Polifarmácia"])
    dados["suporte_terapeutico"] = marcar_sem_informacao(
        dados["Suporte social (terapêutico)"]
    ).str.lower()
    dados["suporte_domiciliar"] = marcar_sem_informacao(
        dados["Suporte social (domiciliar)"]
    ).str.lower()
    dados["status_funcional"] = agrupar_status(dados["Status funcional"])
    dados["cadeirante"] = resposta_sim_nao(dados["Cadeirante"])
    dados["supervisao"] = resposta_sim_nao(dados["Supervisão"])
    dados["auxilio"] = agrupar_auxilio(dados["Objetos de auxílio"])
    dados["nivel_locomocao"] = agrupar_nivel(dados["Nivel de locomoção"])
    dados["aditamento"] = agrupar_auxilio(dados["Aditamento 10m"])
    dados["cif"] = agrupar_cif(dados["CIF equilíbrio"])
    dados["posicao"] = agrupar_posicao(dados["Posição equilíbrio"])

    numericas = {
        "moca": "Cognição (MOCA)",
        "cs10": "Cogniçao (10-CS)",
        "sentar_levantar": "Sentar/levantar 30s",
        "ponte": "Ponte",
        "dinamometro": "Dinamômetro",
        "panturrilha_d": "Panturrilha D",
        "panturrilha_e": "Panturrilha E",
        "velocidade": "Velocidade (m/s)",
        "reacao": "Reação (blazepod)",
        "reacao_dt": "Reação (blazepod) DT",
        "dtc_pct": "dtc_pct",
    }
    casas = {
        "moca": 0,
        "cs10": 0,
        "sentar_levantar": 0,
        "ponte": 0,
        "dinamometro": 0,
        "panturrilha_d": 0,
        "panturrilha_e": 0,
        "velocidade": 2,
        "reacao": 0,
        "reacao_dt": 0,
        "dtc_pct": 0,
    }
    for chave, coluna in numericas.items():
        dados[chave] = pd.to_numeric(dados[coluna], errors="coerce")
    velocidades_implausiveis = int(dados["velocidade"].gt(3).sum())
    dados.loc[dados["velocidade"].gt(3), "velocidade"] = np.nan
    for chave in numericas:
        dados[f"{chave}_faixa"] = faixa_numerica(dados[chave], casas[chave])
    dados.attrs["velocidades_implausiveis"] = velocidades_implausiveis

    variaveis = [
        {"chave": "idade", "rotulo": "Idade (anos)", "tipo": "numerica", "associacao": True, "taxa": False},
        {"chave": "faixa_idade", "rotulo": "Faixa de idade", "tipo": "categorica", "associacao": False, "taxa": True},
        {"chave": "sexo", "rotulo": "Sexo", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "clinica", "rotulo": "Clínica ou diagnóstico", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "diagnostico_funcional", "rotulo": "Diagnóstico funcional", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "polifarmacia", "rotulo": "Polifarmácia", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "suporte_terapeutico", "rotulo": "Suporte social terapêutico", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "suporte_domiciliar", "rotulo": "Suporte social domiciliar", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "status_funcional", "rotulo": "Status funcional", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "cadeirante", "rotulo": "Cadeirante", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "supervisao", "rotulo": "Supervisão", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "auxilio", "rotulo": "Objeto de auxílio", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "nivel_locomocao", "rotulo": "Nível de locomoção", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "aditamento", "rotulo": "Aditamento no teste de 10 m", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "cif", "rotulo": "CIF de equilíbrio", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "posicao", "rotulo": "Posição na avaliação de equilíbrio", "tipo": "categorica", "associacao": True, "taxa": True},
        {"chave": "moca", "rotulo": "Cognição (MOCA)", "tipo": "numerica", "associacao": True, "taxa": False},
        {"chave": "moca_faixa", "rotulo": "Cognição (MOCA), faixa", "tipo": "categorica", "associacao": False, "taxa": True},
        {"chave": "cs10", "rotulo": "Cognição (10-CS)", "tipo": "numerica", "associacao": True, "taxa": False},
        {"chave": "cs10_faixa", "rotulo": "Cognição (10-CS), faixa", "tipo": "categorica", "associacao": False, "taxa": True},
        {"chave": "sentar_levantar", "rotulo": "Sentar e levantar em 30 s", "tipo": "numerica", "associacao": True, "taxa": False},
        {"chave": "sentar_levantar_faixa", "rotulo": "Sentar e levantar em 30 s, faixa", "tipo": "categorica", "associacao": False, "taxa": True},
        {"chave": "ponte", "rotulo": "Ponte", "tipo": "numerica", "associacao": True, "taxa": False},
        {"chave": "ponte_faixa", "rotulo": "Ponte, faixa", "tipo": "categorica", "associacao": False, "taxa": True},
        {"chave": "dinamometro", "rotulo": "Dinamômetro", "tipo": "numerica", "associacao": True, "taxa": False},
        {"chave": "dinamometro_faixa", "rotulo": "Dinamômetro, faixa", "tipo": "categorica", "associacao": False, "taxa": True},
        {"chave": "panturrilha_d", "rotulo": "Panturrilha direita", "tipo": "numerica", "associacao": True, "taxa": False},
        {"chave": "panturrilha_d_faixa", "rotulo": "Panturrilha direita, faixa", "tipo": "categorica", "associacao": False, "taxa": True},
        {"chave": "panturrilha_e", "rotulo": "Panturrilha esquerda", "tipo": "numerica", "associacao": True, "taxa": False},
        {"chave": "panturrilha_e_faixa", "rotulo": "Panturrilha esquerda, faixa", "tipo": "categorica", "associacao": False, "taxa": True},
        {"chave": "velocidade", "rotulo": "Velocidade de marcha (m/s)", "tipo": "numerica", "associacao": True, "taxa": False},
        {"chave": "velocidade_faixa", "rotulo": "Velocidade de marcha (m/s), faixa", "tipo": "categorica", "associacao": False, "taxa": True},
        {"chave": "reacao", "rotulo": "Reação (BlazePod)", "tipo": "numerica", "associacao": True, "taxa": False},
        {"chave": "reacao_faixa", "rotulo": "Reação (BlazePod), faixa", "tipo": "categorica", "associacao": False, "taxa": True},
        {"chave": "reacao_dt", "rotulo": "Reação em dupla tarefa (BlazePod)", "tipo": "numerica", "associacao": True, "taxa": False},
        {"chave": "reacao_dt_faixa", "rotulo": "Reação em dupla tarefa (BlazePod), faixa", "tipo": "categorica", "associacao": False, "taxa": True},
        {"chave": "dtc_pct", "rotulo": "Custo da dupla tarefa (%)", "tipo": "numerica", "associacao": True, "taxa": False},
        {"chave": "dtc_pct_faixa", "rotulo": "Custo da dupla tarefa (%), faixa", "tipo": "categorica", "associacao": False, "taxa": True},
    ]
    return dados, variaveis


def associar(dados, variaveis):
    linhas = []
    for variavel in variaveis:
        if not variavel["associacao"]:
            continue
        coluna = dados[variavel["chave"]]
        par_binario = pd.DataFrame({"valor": coluna, "alvo": dados["queda_recente"]}).dropna()
        par_contagem = pd.DataFrame({"valor": coluna, "alvo": dados["n_quedas"]}).dropna()
        metrica_binaria = "sem pares suficientes"
        forca_binaria = np.nan
        metrica_contagem = "sem pares suficientes"
        forca_contagem = np.nan

        if len(par_binario) > MINIMO_PESSOAS and par_binario["alvo"].nunique() == 2:
            if variavel["tipo"] == "numerica":
                coeficiente = par_binario["valor"].corr(par_binario["alvo"], method="pearson")
                metrica_binaria = f"r = {coeficiente:.3f}"
                forca_binaria = abs(coeficiente)
            else:
                coeficiente = cramers_v(par_binario["valor"], par_binario["alvo"])
                metrica_binaria = f"V = {coeficiente:.3f}"
                forca_binaria = coeficiente

        if len(par_contagem) > MINIMO_PESSOAS and par_contagem["alvo"].nunique() > 1:
            if variavel["tipo"] == "numerica":
                coeficiente = par_contagem["valor"].rank().corr(
                    par_contagem["alvo"].rank(), method="pearson"
                )
                metrica_contagem = f"rho = {coeficiente:.3f}"
                forca_contagem = abs(coeficiente)
            else:
                coeficiente = eta_squared(par_contagem["valor"], par_contagem["alvo"])
                metrica_contagem = f"eta2 = {coeficiente:.3f}"
                forca_contagem = coeficiente

        linhas.append(
            {
                "Informação": variavel["rotulo"],
                "Tipo": "Numérica" if variavel["tipo"] == "numerica" else "Categórica",
                "Relação com queda recente": metrica_binaria,
                "Força na queda recente": round(forca_binaria, 3) if pd.notna(forca_binaria) else np.nan,
                "N na queda recente": int(len(par_binario)),
                "Relação com nº de quedas": metrica_contagem,
                "Força no nº de quedas": round(forca_contagem, 3) if pd.notna(forca_contagem) else np.nan,
                "N no nº de quedas": int(len(par_contagem)),
            }
        )
    return pd.DataFrame(linhas).sort_values(
        "Força na queda recente", ascending=False, na_position="last"
    ).reset_index(drop=True)


def relacao_por_valor(dados, variaveis, taxa_geral):
    partes = []
    for variavel in variaveis:
        if not variavel["taxa"]:
            continue
        serie = dados[variavel["chave"]]
        mascara = serie.notna() & dados["queda_recente"].notna()
        if int(mascara.sum()) < MINIMO_PESSOAS:
            continue
        quadro = pd.DataFrame(
            {
                "valor": serie.loc[mascara].astype(str),
                "queda": dados.loc[mascara, "queda_recente"].astype(int),
            }
        )
        grupo = (
            quadro.groupby("valor", dropna=False)["queda"]
            .agg(pessoas="size", quedas="sum")
            .reset_index()
        )
        grupo = grupo.loc[grupo["pessoas"].ge(MINIMO_PESSOAS)].copy()
        if len(grupo) < 2:
            continue
        grupo["coluna"] = variavel["rotulo"]
        grupo["chave"] = variavel["chave"]
        partes.append(grupo)
    if not partes:
        return pd.DataFrame()
    relacao = pd.concat(partes, ignore_index=True)
    relacao["taxa_queda"] = relacao["quedas"] / relacao["pessoas"]
    relacao["diferenca_pp"] = (relacao["taxa_queda"] - taxa_geral) * 100
    relacao = relacao.rename(columns={"valor": "valor", "pessoas": "pessoas", "quedas": "quedas"})
    return relacao.sort_values(
        ["coluna", "diferenca_pp"], ascending=[True, False]
    ).reset_index(drop=True)


def recorte_interpretavel(relacao, minimo_pessoas):
    return relacao.loc[
        ~relacao["valor"].isin(VALORES_FORA_DO_PERFIL)
        & relacao["pessoas"].ge(minimo_pessoas)
    ].copy()


def impacto_das_colunas(relacao):
    linhas = []
    for coluna, recorte in recorte_interpretavel(relacao, MINIMO_PERFIL).groupby("coluna"):
        if len(recorte) < 2:
            continue
        maior = recorte.sort_values(["taxa_queda", "pessoas"], ascending=[False, False]).iloc[0]
        menor = recorte.sort_values(["taxa_queda", "pessoas"], ascending=[True, False]).iloc[0]
        linhas.append(
            {
                "coluna": coluna,
                "chave": maior["chave"],
                "taxa_mais_alta": maior["taxa_queda"],
                "n_taxa_alta": int(maior["pessoas"]),
                "taxa_mais_baixa": menor["taxa_queda"],
                "n_taxa_baixa": int(menor["pessoas"]),
                "impacto_pp": (maior["taxa_queda"] - menor["taxa_queda"]) * 100,
            }
        )
    return pd.DataFrame(linhas).sort_values("impacto_pp", ascending=False).reset_index(drop=True)


def barras_horizontais(eixo, rotulos, valores, titulo, xlabel, cor, formato="%.3f"):
    barras = eixo.barh(list(rotulos), list(valores), color=cor)
    eixo.bar_label(barras, fmt=formato, padding=3, fontsize=8)
    eixo.set_title(titulo)
    eixo.set_xlabel(xlabel)
    eixo.set_ylabel("")
    maior = max(valores) if len(valores) else 0
    eixo.set_xlim(0, maior * 1.22 if maior > 0 else 1)
    eixo.tick_params(axis="y", labelsize=8)
    estilo_eixo(eixo)


def desenhar_perfil(eixo, perfil, taxa_geral, titulo, cor):
    dados = perfil.sort_values("taxa_queda", ascending=True)
    rotulos = dados["coluna"] + ": " + dados["valor"].astype(str)
    barras = eixo.barh(rotulos, dados["taxa_queda"], color=cor)
    eixo.axvline(taxa_geral, color="#1E293B", linestyle="--", linewidth=1)
    eixo.bar_label(
        barras,
        labels=[f"{taxa:.0%}" for taxa in dados["taxa_queda"]],
        padding=3,
        fontsize=8,
    )
    eixo.set_title(titulo)
    eixo.set_xlabel("Quedas no último mês")
    teto = min(1, max(float(dados["taxa_queda"].max()), taxa_geral) + 0.12)
    eixo.set_xlim(0, teto)
    eixo.tick_params(axis="y", labelsize=8)
    formato_percentual(eixo)
    estilo_eixo(eixo)


def perfil_extremo(relacao, maior, taxa_geral):
    linhas = []
    base = recorte_interpretavel(relacao, MINIMO_PERFIL)
    for _, recorte in base.groupby("coluna"):
        ordenado = recorte.sort_values(
            ["taxa_queda", "pessoas"],
            ascending=[not maior, False],
        )
        linha = ordenado.iloc[0]
        if maior and linha["taxa_queda"] < taxa_geral + CONTRASTE_MINIMO_PP / 100:
            continue
        if not maior and linha["taxa_queda"] > taxa_geral - CONTRASTE_MINIMO_PP / 100:
            continue
        linhas.append(linha)
    if not linhas:
        return pd.DataFrame()
    perfil = pd.DataFrame(linhas)
    return perfil.sort_values("taxa_queda", ascending=not maior).reset_index(drop=True)


def tabela_legivel(perfil):
    visivel = perfil[["coluna", "valor", "pessoas", "quedas", "taxa_queda", "diferenca_pp"]].copy()
    visivel["taxa_queda"] = visivel["taxa_queda"].map(lambda valor: f"{valor:.1%}")
    visivel["diferenca_pp"] = visivel["diferenca_pp"].map(lambda valor: f"{valor:+.1f}")
    return visivel.rename(
        columns={
            "coluna": "Informação",
            "valor": "Valor",
            "pessoas": "Pessoas no grupo",
            "quedas": "Quedas recentes",
            "taxa_queda": "Taxa de queda recente",
            "diferenca_pp": "Diferença vs base (p.p.)",
        }
    )


def executar_analise():
    caminho = localizar_base()
    dados, variaveis = preparar_dados(pd.read_csv(caminho))
    respostas = dados["queda_recente"].dropna()
    taxa_geral = float(respostas.mean()) if len(respostas) else np.nan
    n_sim = int(respostas.eq(1).sum())
    n_validas = int(respostas.shape[0])

    mostrar(
        Markdown(
            "## 1. O que esta análise responde\n"
            "A pergunta é quais informações mais acompanham as quedas, "
            "e qual combinação descreve quem mais caiu e quem menos caiu. "
            "A comparação de 60+ com 60-, por sexo, diagnóstico e medidas "
            "funcionais, permanece na análise estatística anterior e não é refeita aqui. "
            "A queda recente usa só `sim` e `não`. "
            f"O ranking de impacto e os perfis usam grupos com pelo menos {MINIMO_PERFIL} pessoas "
            "e deixam de fora rótulos como sem informação, não especificado e outros. "
            "Braços e o custo de dupla tarefa sem preenchimento não entram. "
            "O tempo de 10 metros não entra separado: a velocidade de marcha "
            "já é essa mesma medida. Uma velocidade acima de 3 m/s fica de fora."
        )
    )
    print(f"Base: {caminho}")
    print(
        f"Queda no último mês: {n_sim} de {n_validas} "
        f"({taxa_geral:.1%}). Sem resposta de sim/não: "
        f"{int(dados['queda_recente'].isna().sum())}."
    )
    if dados.attrs.get("velocidades_implausiveis"):
        print(
            "Velocidade de marcha acima de 3 m/s retirada da análise de marcha: "
            f"{dados.attrs['velocidades_implausiveis']} registro."
        )
    bloco_sem_dado = dados[
        ["nivel_locomocao", "status_funcional", "cadeirante", "supervisao"]
    ].eq("sem informação").all(axis=1)
    respostas_bloco = dados.loc[bloco_sem_dado, "queda_recente"].dropna()
    if int(bloco_sem_dado.sum()):
        print(
            f"{int(bloco_sem_dado.sum())} pessoas estão sem nível de locomoção, "
            "status funcional, cadeirante e supervisão ao mesmo tempo. "
            f"Queda recente nesse bloco: {int(respostas_bloco.eq(1).sum())}/"
            f"{len(respostas_bloco)}. Esse vazio não entra no ranking de impacto, "
            "para não contar quatro vezes o mesmo buraco da ficha."
        )

    mostrar(
        Markdown(
            "## 2. Força de associação\n"
            "Numérica com queda recente: correlação de Pearson (`r`). "
            "Categórica com queda recente: V de Cramer. "
            "Numérica com o número de quedas: Spearman (`rho`). "
            "Categórica com o número de quedas: eta ao quadrado. "
            "O sinal de `r` e `rho` diz a direção. A força usada na ordenação "
            "é o valor absoluto. Essas medidas não são a mesma escala; "
            "a comparação mais direta entre colunas está na seção 3, em pontos percentuais."
        )
    )
    associacoes = associar(dados, variaveis)
    mostrar(associacoes)

    ranking_recente = associacoes.dropna(subset=["Força na queda recente"]).sort_values(
        "Força na queda recente", ascending=True
    )
    ranking_contagem = associacoes.dropna(subset=["Força no nº de quedas"]).sort_values(
        "Força no nº de quedas", ascending=True
    )
    fig, eixos = plt.subplots(1, 2, figsize=(16, 10))
    barras_horizontais(
        eixos[0],
        ranking_recente["Informação"],
        ranking_recente["Força na queda recente"],
        "Queda no último mês",
        "Força da relação (0 a 1)",
        COR_NEUTRA,
    )
    barras_horizontais(
        eixos[1],
        ranking_contagem["Informação"],
        ranking_contagem["Força no nº de quedas"],
        "Quantidade de quedas",
        "Força da relação (0 a 1)",
        COR_CONTAGEM,
    )
    fig.suptitle("O que mais se liga às quedas", fontsize=14)
    exibir(fig)
    print("Direção nas medidas numéricas com queda recente:")
    for _, linha in associacoes.iterrows():
        relacao = str(linha["Relação com queda recente"])
        if not relacao.startswith("r ="):
            continue
        coeficiente = float(relacao.replace("r =", "").strip())
        sentido = "valores mais altos" if coeficiente >= 0 else "valores mais baixos"
        print(
            f"  {linha['Informação']}: {sentido} acompanham mais queda recente ({relacao})."
        )

    mostrar(
        Markdown(
            "## 3. Quais informações mais separam quem cai\n"
            "Cada informação numérica entra em faixas. O impacto é a distância, "
            "em pontos percentuais, entre a maior e a menor taxa de queda recente, "
            f"só em valores com pelo menos {MINIMO_PERFIL} pessoas. "
            f"A taxa geral da base é {taxa_geral:.1%}."
        )
    )
    relacao = relacao_por_valor(dados, variaveis, taxa_geral)
    impacto = impacto_das_colunas(relacao)
    impacto_visivel = impacto.rename(columns={
        "coluna": "Informação",
        "taxa_mais_alta": "Maior taxa",
        "n_taxa_alta": "N da maior taxa",
        "taxa_mais_baixa": "Menor taxa",
        "n_taxa_baixa": "N da menor taxa",
        "impacto_pp": "Impacto (p.p.)",
    }).drop(columns=["chave"])
    mostrar(impacto_visivel)

    impacto_plot = impacto.sort_values("impacto_pp", ascending=True)
    fig, eixo = plt.subplots(figsize=(10, 9))
    barras_horizontais(
        eixo,
        impacto_plot["coluna"],
        impacto_plot["impacto_pp"],
        "O que mais muda a chance de queda",
        "Diferença, em pontos percentuais",
        COR_NEUTRA,
        formato="%.1f",
    )
    exibir(fig)

    mostrar(
        Markdown(
            "## 4. Pessoa mais fácil de cair e pessoa menos fácil\n"
            "O perfil mais fácil reúne, informação por informação, o valor conhecido "
            f"com maior taxa de queda recente, desde que o grupo tenha pelo menos {MINIMO_PERFIL} "
            f"pessoas e a taxa fique pelo menos {CONTRASTE_MINIMO_PP} pontos acima da base. "
            "O perfil menos fácil faz o mesmo com as taxas mais baixas. "
            "Essa combinação empilha o extremo de cada coluna. Ela pode não "
            "existir como uma única pessoa na base."
        )
    )
    mais_facil = perfil_extremo(relacao, maior=True, taxa_geral=taxa_geral)
    menos_facil = perfil_extremo(relacao, maior=False, taxa_geral=taxa_geral)
    print("Perfil com maior taxa de queda em cada informação:")
    for _, linha in mais_facil.iterrows():
        print(
            f"  {linha['coluna']}: {linha['valor']} "
            f"({linha['taxa_queda']:.1%}, {linha['diferenca_pp']:+.1f} p.p., "
            f"{int(linha['quedas'])}/{int(linha['pessoas'])})"
        )
    print("Perfil com menor taxa de queda em cada informação:")
    for _, linha in menos_facil.iterrows():
        print(
            f"  {linha['coluna']}: {linha['valor']} "
            f"({linha['taxa_queda']:.1%}, {linha['diferenca_pp']:+.1f} p.p., "
            f"{int(linha['quedas'])}/{int(linha['pessoas'])})"
        )
    mostrar(tabela_legivel(mais_facil))
    mostrar(tabela_legivel(menos_facil))
    fig, eixo = plt.subplots(figsize=(11, 8))
    desenhar_perfil(
        eixo,
        mais_facil,
        taxa_geral,
        "Quem cai com mais facilidade",
        COR_ALTA,
    )
    exibir(fig)
    fig, eixo = plt.subplots(figsize=(11, 8))
    desenhar_perfil(
        eixo,
        menos_facil,
        taxa_geral,
        "Quem cai com menos facilidade",
        COR_BAIXA,
    )
    exibir(fig)

    mostrar(
        Markdown(
            "## 5. Acima e abaixo da média de quedas\n"
            "Cada barra é um grupo com pelo menos "
            f"{MINIMO_PERFIL} pessoas. Vermelho fica acima da média da base "
            f"({taxa_geral:.1%}); verde fica abaixo. "
            "Nenhuma pessoa é identificada: o gráfico compara características, não prontuários."
        )
    )
    comparaveis = recorte_interpretavel(relacao, MINIMO_PERFIL).sort_values(
        "diferenca_pp", ascending=False
    )
    extremos = pd.concat(
        [comparaveis.head(8), comparaveis.tail(8)],
        ignore_index=True,
    ).drop_duplicates(subset=["coluna", "valor"])
    extremos = extremos.sort_values("diferenca_pp", ascending=True)
    rotulos = extremos["coluna"] + ": " + extremos["valor"].astype(str)
    cores = [COR_ALTA if valor >= 0 else COR_BAIXA for valor in extremos["diferenca_pp"]]
    fig, eixo = plt.subplots(figsize=(11, 8))
    barras = eixo.barh(rotulos, extremos["diferenca_pp"], color=cores)
    eixo.axvline(0, color="#1E293B", linewidth=1)
    eixo.bar_label(
        barras,
        labels=[f"{valor:+.0f}" for valor in extremos["diferenca_pp"]],
        padding=3,
        fontsize=8,
    )
    eixo.set_title("Acima e abaixo da média de quedas")
    eixo.set_xlabel("Pontos percentuais em relação à média")
    eixo.tick_params(axis="y", labelsize=8)
    estilo_eixo(eixo)
    exibir(fig)

    mostrar(
        Markdown(
            "## Leitura\n"
            "As informações do topo são as que mais mudam a taxa de queda "
            "entre um grupo e outro. O perfil de quem cai com mais facilidade "
            "junta essas características. Ele descreve um tipo de situação, "
            "não uma pessoa identificada. Medidas com muitos ausentes, como "
            "cognição, entram só com quem tem o dado preenchido."
        )
    )


if __name__ == "__main__":
    executar_analise()
