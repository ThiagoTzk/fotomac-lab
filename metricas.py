"""
FotoMac Lab — métricas de ranking, independentes de limiar.

Por que este arquivo existe separado do scoring.py:

O `scoring.py` original media o modelo NO limiar. Isso tem dois problemas para
comparar modelos:

  1. o limiar é calibrado no mesmo gabarito onde a nota é medida — a nota sai
     boa por construção, não por qualidade (é o clássico "treinar no teste");
  2. cada modelo tem sua própria escala de similaridade, então comparar no mesmo
     número não compara nada.

As métricas aqui olham a ORDEM em que o modelo colocou as fotos, não os valores.
Ordem é comparável entre modelos sem calibrar nada.
"""

from __future__ import annotations

import numpy as np


def _separa(ranking: list[tuple[str, float]], positivos: set[str],
            consulta: str) -> tuple[list[float], list[float]]:
    """Divide o ranking em acertos e erros, tirando a própria consulta fora."""
    pos, neg = [], []
    for nome, sim in ranking:
        if nome == consulta:
            continue           # casar consigo mesma não prova nada
        (pos if nome in positivos else neg).append(float(sim))
    return pos, neg


def auc_roc(pos: list[float], neg: list[float]) -> float | None:
    """Probabilidade de um acerto sorteado ficar acima de um erro sorteado.

    1.0 = todo acerto está acima de todo erro. 0.5 = ordenação aleatória.
    Calculada pela estatística de Mann-Whitney (conta pares), que não assume
    distribuição nenhuma e não depende da escala das similaridades.
    """
    if not pos or not neg:
        return None
    p = np.asarray(pos, float)[:, None]
    n = np.asarray(neg, float)[None, :]
    # empate conta meio ponto, como manda a definição
    return float(((p > n).sum() + 0.5 * (p == n).sum()) / (len(pos) * len(neg)))


def average_precision(ranking: list[tuple[str, float]], positivos: set[str],
                      consulta: str) -> float | None:
    """Precisão média ao longo do ranking (a métrica de busca, não de classificação).

    Premia colocar TODOS os acertos no topo. Diferente do F1, ela não precisa de
    limiar: percorre o ranking de cima para baixo e mede a precisão em cada acerto.
    """
    ordenado = [(n, s) for n, s in sorted(ranking, key=lambda t: -t[1]) if n != consulta]
    esperados = {p for p in positivos if p != consulta}
    if not esperados:
        return None
    acertos = 0
    soma = 0.0
    for i, (nome, _) in enumerate(ordenado, 1):
        if nome in esperados:
            acertos += 1
            soma += acertos / i
    # divide pelo total esperado, não pelo encontrado: acerto que o detector nem
    # indexou entra como precisão zero, que é o que o visitante sente.
    return soma / len(esperados)


def intrusos(pos: list[float], neg: list[float]) -> int | None:
    """Quantos erros ficaram ACIMA do pior acerto.

    É o número mais direto de todos: zero significa que existe um limiar capaz de
    acertar tudo e não errar nada. Cinco significa que, para pegar todas as fotos
    da pessoa, você leva cinco fotos de estranhos junto.
    """
    if not pos or not neg:
        return None
    pior_acerto = min(pos)
    return int(sum(1 for s in neg if s >= pior_acerto))


def separacao_nao_parametrica(pos: list[float], neg: list[float]) -> float | None:
    """Fração dos erros que ficou abaixo do pior acerto.

    Substitui o d-prime (σ) do scoring.py original. O d-prime divide pelo
    desvio-padrão dos erros, o que pressupõe uma distribuição bem comportada —
    com 3500 rostos de estranhos ela não é. Esta versão só conta, sem supor nada,
    e continua adimensional (logo, comparável entre modelos).
    """
    if not pos or not neg:
        return None
    return float(np.mean(np.asarray(neg) < min(pos)))


def metricas_de_consulta(ranking: list[tuple[str, float]], positivos: set[str],
                         consulta: str, conferidas: set[str] | None = None) -> dict:
    """Se `conferidas` for dada, só as fotos que alguém olhou entram na conta.

    É a diferença entre "o modelo não errou" e "ninguém verificou se errou".
    Com 3583 rostos no acervo e 80 fotos revisadas, contar as 3503 restantes como
    acerto de rejeição infla toda métrica.
    """
    if conferidas is not None:
        ranking = [(n, s) for n, s in ranking if n in conferidas or n == consulta]
        positivos = {p for p in positivos if p in conferidas}

    pos, neg = _separa(ranking, positivos, consulta)
    esperados = {p for p in positivos if p != consulta}
    encontrados = {n for n, _ in ranking}
    perdidos_na_indexacao = len(esperados - encontrados)

    return {
        "consulta": consulta,
        "escopo": ("apenas fotos conferidas" if conferidas is not None
                   else "acervo inteiro (não conferido)"),
        "fotos_avaliadas": len(pos) + len(neg),
        "positivos_esperados": len(esperados),
        "positivos_indexados": len(pos),
        "perdidos_na_indexacao": perdidos_na_indexacao,
        "negativos": len(neg),
        "auc": auc_roc(pos, neg),
        "average_precision": average_precision(ranking, positivos, consulta),
        "intrusos": intrusos(pos, neg),
        "separacao": separacao_nao_parametrica(pos, neg),
        "pior_acerto": min(pos) if pos else None,
        "melhor_erro": max(neg) if neg else None,
    }


# ------------------------------------------------- validação cruzada do limiar

def _f1_no_limiar(ranking, positivos, consulta, limiar) -> float:
    esperados = {p for p in positivos if p != consulta}
    tp = fp = 0
    for nome, sim in ranking:
        if nome == consulta:
            continue
        if sim >= limiar:
            if nome in esperados: tp += 1
            else: fp += 1
    fn = len(esperados) - tp
    if tp == 0:
        return 0.0
    prec, rec = tp / (tp + fp), tp / (tp + fn)
    return 2 * prec * rec / (prec + rec)


def limiar_de(conjunto: list[dict]) -> float | None:
    """Ponto médio entre o pior acerto e o melhor erro de um conjunto de consultas."""
    piores = [m["pior_acerto"] for m in conjunto if m["pior_acerto"] is not None]
    melhores = [m["melhor_erro"] for m in conjunto if m["melhor_erro"] is not None]
    if not piores or not melhores:
        return None
    pv, mf = min(piores), max(melhores)
    return (pv + mf) / 2 if pv > mf else None


def validacao_cruzada(rankings: dict[str, list[tuple[str, float]]],
                      positivos_por_consulta: dict[str, set[str]]) -> dict:
    """Calibra o limiar deixando UMA consulta de fora, e testa nela.

    É o remédio para o "treinar no teste": o limiar que julga a consulta X nunca
    viu a consulta X. O F1 que sai daqui é uma estimativa honesta de como o modelo
    se sai com uma pessoa nova, e não a garantia de 1.000 que o ajuste no próprio
    conjunto produzia.
    """
    nomes = list(rankings)
    if len(nomes) < 2:
        return {"possivel": False,
                "motivo": "precisa de pelo menos 2 consultas no gabarito"}

    todas = {n: metricas_de_consulta(rankings[n], positivos_por_consulta[n], n)
             for n in nomes}

    f1s, limiares = [], []
    for fora in nomes:
        treino = [todas[n] for n in nomes if n != fora]
        t = limiar_de(treino)
        if t is None:
            continue
        limiares.append(t)
        f1s.append(_f1_no_limiar(rankings[fora], positivos_por_consulta[fora], fora, t))

    if not f1s:
        return {"possivel": False,
                "motivo": "nenhum limiar separa as consultas de treino"}
    return {
        "possivel": True,
        "f1_medio": float(np.mean(f1s)),
        "f1_minimo": float(min(f1s)),
        "limiares_testados": [round(t, 4) for t in limiares],
        "por_consulta": dict(zip(nomes, [round(f, 4) for f in f1s])),
    }


# ----------------------------------------------- o conjunto consegue comparar?

def poder_de_discriminacao(metricas: list[dict]) -> dict:
    """O conjunto de teste consegue separar um modelo bom de um ótimo?

    Isto não mede o modelo: mede o TESTE. Se todo acerto está muito acima de todo
    erro e nenhum modelo erra, os dois candidatos empatam no teto e a nota deixa
    de decidir. Nesse caso o problema é o conjunto ser fácil demais, e nenhuma
    métrica mais esperta resolve — só um conjunto mais difícil.
    """
    aucs = [m["auc"] for m in metricas if m["auc"] is not None]
    intr = [m["intrusos"] for m in metricas if m["intrusos"] is not None]
    n_pos = sum(m["positivos_esperados"] for m in metricas)

    saturado = bool(aucs) and all(a >= 0.9999 for a in aucs) and all(i == 0 for i in intr)
    avisos = []
    if saturado:
        avisos.append(
            "CONJUNTO SATURADO: todos os acertos ficaram acima de todos os erros. "
            "Um modelo melhor vai empatar aqui — a nota passa a ser decidida só "
            "pela velocidade. Para comparar modelos de verdade o conjunto precisa "
            "conter casos difíceis.")
    if n_pos < 20:
        avisos.append(
            f"AMOSTRA PEQUENA: {n_pos} acerto(s) esperado(s) no total. Uma foto a "
            "mais ou a menos muda a métrica em dezenas de pontos percentuais.")
    return {"saturado": saturado, "positivos_totais": n_pos, "avisos": avisos}
