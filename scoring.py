"""
FotoMac Lab — sistema de pontuação para comparar modelos de reconhecimento facial.

A bancada existe para escolher UM modelo. Para escolher é preciso uma nota, e para
ter nota é preciso um gabarito (`gabarito.json`): quais fotos de fato contêm cada
pessoa. Sem ele só dá para medir velocidade.

O sistema é deliberadamente independente de modelo: só exige que o candidato produza,
para cada foto do acervo, um número de similaridade com a consulta. Não importa se é
cosseno de um vetor local ou o "confidence" de uma API paga — a nota é calculada em
cima do ranking, não da escala.

Ver SISTEMA-DE-PONTUACAO.md para a explicação completa dos pesos.
"""

from __future__ import annotations

import json
import math
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

# ------------------------------------------------------------------ pesos

# Somam 100. Mudar aqui muda a nota de TODOS os modelos igualmente — é só não
# mudar no meio de uma comparação.
PESO_ACERTO = 60      # o modelo acha quem tem que achar e só quem tem que achar
PESO_SEPARACAO = 20   # quanta folga o limiar tem antes de quebrar
PESO_BUSCA = 10       # o visitante espera por isto, na frente do totem
PESO_INDEXACAO = 10   # custo de processar o acervo, uma vez por evento

# Orçamentos de tempo. Nota cheia no "bom", zero no "inaceitável", interpolado
# em escala logarítmica entre os dois (tempo é percebido em ordem de grandeza,
# não em diferença absoluta: 50ms e 100ms são iguais para uma pessoa; 1s e 2s não).
BUSCA_BOA_MS = 100.0
BUSCA_RUIM_MS = 3000.0
INDEX_BOM_S = 0.10     # por foto
INDEX_RUIM_S = 2.00


@dataclass
class QueryScore:
    """Resultado do gabarito aplicado a UMA consulta, num limiar."""
    consulta: str
    limiar: float
    tp: int          # acertos: fotos que têm a pessoa e foram marcadas
    fp: int          # falsos positivos: não têm a pessoa mas foram marcadas
    fn: int          # perdidas: têm a pessoa e não foram marcadas
    tn: int          # rejeições corretas
    precisao: float  # dos que ele marcou, quantos estavam certos
    recall: float    # dos que existiam, quantos ele achou
    f1: float
    pior_verdadeiro: float | None   # menor similaridade entre as fotos corretas
    melhor_falso: float | None      # maior similaridade entre as fotos erradas
    margem: float | None            # pior_verdadeiro - melhor_falso
    separacao: float | None         # d-prime: folga em desvios-padrão dos falsos


def carregar_gabarito(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def nfc(nome: str) -> str:
    """Normaliza o nome do arquivo para comparação.

    O macOS grava acento decomposto (NFD) e o shell/navegador entregam composto
    (NFC). São a mesma letra para uma pessoa e strings diferentes para o Python,
    então TODA comparação de nome de arquivo passa por aqui. Esta armadilha já
    custou duas execuções: o gabarito existia e o teste dizia que não.
    """
    return unicodedata.normalize("NFC", nome)


def pessoa_da_consulta(gabarito: dict, consulta: str) -> tuple[str, dict] | None:
    """Descobre de quem é o autorretrato, pelo nome do arquivo."""
    alvo = nfc(consulta)
    for nome, dados in gabarito["pessoas"].items():
        if alvo in {nfc(c) for c in dados.get("consultas", [])}:
            return nome, dados
    return None


def avaliar(ranking: list[tuple[str, float]], positivos: set[str],
            limiar: float, consulta: str, incluir_consulta: bool = False) -> QueryScore:
    """Aplica o gabarito a um ranking (nome da foto -> similaridade).

    A própria foto de consulta é removida por padrão: ela casa consigo mesma com
    similaridade máxima e inflaria o acerto sem provar nada.
    """
    pares = [(n, s) for n, s in ranking if incluir_consulta or n != consulta]
    esperados = {p for p in positivos if incluir_consulta or p != consulta}

    tp = fp = fn = tn = 0
    sim_verdadeiros, sim_falsos = [], []

    for nome, sim in pares:
        eh_positivo = nome in esperados
        marcou = sim >= limiar
        (sim_verdadeiros if eh_positivo else sim_falsos).append(sim)
        if eh_positivo and marcou: tp += 1
        elif eh_positivo: fn += 1
        elif marcou: fp += 1
        else: tn += 1

    # Fotos esperadas que o detector nem chegou a indexar (sem rosto) contam
    # como perdidas: para o visitante, foto que não aparece é foto perdida.
    vistos = {n for n, _ in pares}
    fn += len(esperados - vistos)

    precisao = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precisao * recall / (precisao + recall) if (precisao + recall) else 0.0

    pior_v = min(sim_verdadeiros) if sim_verdadeiros else None
    melhor_f = max(sim_falsos) if sim_falsos else None
    margem = (pior_v - melhor_f) if (pior_v is not None and melhor_f is not None) else None

    separacao = None
    if pior_v is not None and len(sim_falsos) > 1:
        mu, sd = float(np.mean(sim_falsos)), float(np.std(sim_falsos))
        if sd > 1e-9:
            # Quantos desvios-padrão dos falsos o pior acerto está acima da
            # média dos falsos. É adimensional, então compara modelos cujas
            # similaridades vivem em escalas diferentes.
            separacao = (pior_v - mu) / sd

    return QueryScore(consulta, limiar, tp, fp, fn, tn, precisao, recall, f1,
                      pior_v, melhor_f, margem, separacao)


def melhor_limiar(ranking: list[tuple[str, float]], positivos: set[str],
                  consulta: str, passos: int = 400) -> tuple[float, QueryScore]:
    """Encontra o limiar que maximiza o F1 desta consulta.

    Cada modelo é avaliado no SEU melhor limiar. Comparar modelos num número
    fixo mediria a escala de similaridade de cada um, não a qualidade — o 0.363
    do SFace não quer dizer nada para uma API que devolve 0 a 100.
    """
    sims = [s for n, s in ranking if n != consulta]
    if not sims:
        return 0.0, avaliar(ranking, positivos, 0.0, consulta)
    lo, hi = min(sims), max(sims)
    melhor = (None, None)
    for i in range(passos + 1):
        t = lo + (hi - lo) * i / passos
        sc = avaliar(ranking, positivos, t, consulta)
        chave = (sc.f1, sc.margem if sc.margem is not None else 0.0)
        if melhor[0] is None or chave > melhor[0]:
            melhor = (chave, (t, sc))
    return melhor[1]


# --------------------------------------------------------------- nota final

def _nota_tempo(valor: float, bom: float, ruim: float, peso: int) -> float:
    """Interpolação logarítmica entre 'bom' (nota cheia) e 'ruim' (zero)."""
    if valor <= bom: return float(peso)
    if valor >= ruim: return 0.0
    frac = math.log(valor / bom) / math.log(ruim / bom)
    return peso * (1.0 - frac)


def _nota_separacao(separacao: float | None) -> float:
    """3 desvios-padrão de folga já é separação confortável -> nota cheia."""
    if separacao is None or separacao <= 0:
        return 0.0
    return PESO_SEPARACAO * min(1.0, separacao / 3.0)


def pontuar(scores: list[QueryScore], busca_ms: float,
            index_s_por_foto: float, modelo: str) -> dict:
    """Consolida as consultas numa nota de 0 a 100."""
    if not scores:
        raise ValueError("Sem consultas avaliadas — o gabarito cobre alguma delas?")

    f1 = float(np.mean([s.f1 for s in scores]))
    precisao = float(np.mean([s.precisao for s in scores]))
    recall = float(np.mean([s.recall for s in scores]))
    seps = [s.separacao for s in scores if s.separacao is not None]
    separacao = float(np.mean(seps)) if seps else None
    margens = [s.margem for s in scores if s.margem is not None]

    n_acerto = PESO_ACERTO * f1
    n_sep = _nota_separacao(separacao)
    n_busca = _nota_tempo(busca_ms, BUSCA_BOA_MS, BUSCA_RUIM_MS, PESO_BUSCA)
    n_index = _nota_tempo(index_s_por_foto, INDEX_BOM_S, INDEX_RUIM_S, PESO_INDEXACAO)

    return {
        "modelo": modelo,
        "nota_final": round(n_acerto + n_sep + n_busca + n_index, 1),
        "componentes": {
            "acerto": round(n_acerto, 1),
            "separacao": round(n_sep, 1),
            "busca": round(n_busca, 1),
            "indexacao": round(n_index, 1),
        },
        "metricas": {
            "f1_medio": round(f1, 4),
            "precisao_media": round(precisao, 4),
            "recall_medio": round(recall, 4),
            "separacao_sigmas": round(separacao, 2) if separacao is not None else None,
            "margem_minima": round(min(margens), 4) if margens else None,
            "busca_ms": round(busca_ms, 2),
            "index_s_por_foto": round(index_s_por_foto, 4),
        },
        "consultas": [asdict(s) for s in scores],
    }


def limiar_recomendado(scores: list[QueryScore]) -> float | None:
    """O ponto médio entre o pior acerto e o melhor erro, no conjunto todo.

    É o limiar mais distante das duas bordas — o que aguenta mais variação de
    foto nova antes de começar a errar.
    """
    piores = [s.pior_verdadeiro for s in scores if s.pior_verdadeiro is not None]
    melhores = [s.melhor_falso for s in scores if s.melhor_falso is not None]
    if not piores or not melhores:
        return None
    pv, mf = min(piores), max(melhores)
    if pv <= mf:
        return None   # não existe limiar que separe: as faixas se sobrepõem
    return round((pv + mf) / 2, 4)


# =====================================================================
# NOTA v2 — construída sobre metricas.py, independente de limiar.
#
# A v1 media F1 no limiar, e o limiar era calibrado no mesmo gabarito.
# A nota saía alta por construção. A v2 separa as duas coisas:
#   - a maior parte dos pontos vem da ORDEM em que o modelo colocou as fotos,
#     que não depende de calibrar nada;
#   - a parte que depende de limiar é medida por validação cruzada, com o
#     limiar calibrado SEM ver a consulta que está sendo julgada.
# =====================================================================

PESO_ORDENACAO = 40     # o modelo põe os acertos no topo? (mAP)
PESO_SEPARACAO = 25     # sobra espaço entre o pior acerto e os erros?
PESO_ROBUSTEZ = 15      # o limiar calibrado em outras pessoas funciona nesta?
PESO_BUSCA_V2 = 10
PESO_INDEX_V2 = 10


def pontuar_v2(metricas_consultas: list[dict], cruzada: dict, busca_ms: float,
               index_s_por_foto: float, modelo: str, diagnostico: dict) -> dict:
    """Nota 0-100 a partir das métricas de ranking."""
    import numpy as _np

    aps = [m["average_precision"] for m in metricas_consultas
           if m["average_precision"] is not None]
    seps = [m["separacao"] for m in metricas_consultas if m["separacao"] is not None]
    aucs = [m["auc"] for m in metricas_consultas if m["auc"] is not None]
    intr = [m["intrusos"] for m in metricas_consultas if m["intrusos"] is not None]

    mapk = float(_np.mean(aps)) if aps else 0.0
    sep = float(_np.mean(seps)) if seps else 0.0
    auc = float(_np.mean(aucs)) if aucs else 0.0

    n_ordem = PESO_ORDENACAO * mapk
    n_sep = PESO_SEPARACAO * sep
    # sem validação cruzada possível (1 consulta só), este componente é zerado e
    # dito em voz alta — não inventado.
    n_rob = PESO_ROBUSTEZ * cruzada["f1_medio"] if cruzada.get("possivel") else 0.0
    n_busca = _nota_tempo(busca_ms, BUSCA_BOA_MS, BUSCA_RUIM_MS, PESO_BUSCA_V2)
    n_index = _nota_tempo(index_s_por_foto, INDEX_BOM_S, INDEX_RUIM_S, PESO_INDEX_V2)

    return {
        "versao": 2,
        "modelo": modelo,
        "nota_final": round(n_ordem + n_sep + n_rob + n_busca + n_index, 1),
        "componentes": {
            "ordenacao": round(n_ordem, 1),
            "separacao": round(n_sep, 1),
            "robustez": round(n_rob, 1),
            "busca": round(n_busca, 1),
            "indexacao": round(n_index, 1),
        },
        "metricas": {
            "mAP": round(mapk, 4),
            "auc": round(auc, 4),
            "separacao_fracao": round(sep, 4),
            "intrusos_total": sum(intr) if intr else None,
            "f1_validacao_cruzada": (round(cruzada["f1_medio"], 4)
                                     if cruzada.get("possivel") else None),
            "busca_ms": round(busca_ms, 2),
            "index_s_por_foto": round(index_s_por_foto, 4),
        },
        "validacao_cruzada": cruzada,
        "diagnostico_do_conjunto": diagnostico,
        "consultas": metricas_consultas,
    }
