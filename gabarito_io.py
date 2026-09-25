"""
FotoMac Lab — leitura e escrita do gabarito.

O gabarito v1 tinha só `aparece_em`: tudo que não estivesse na lista era tratado
como "a pessoa não está". Isso só vale se alguém tiver olhado o acervo inteiro.

**O gabarito é POR MODELO.** Cada tecnologia tem o seu conjunto de marcações,
em `pessoas[nome]["por_modelo"][chave]`. Sem isso, o que foi marcado testando o
SFace aparecia pré-marcado ao testar o Facenet512 — contaminando exatamente o que
o teste deveria isolar. Um modelo nunca pode ser avaliado com as respostas de
outro.

(Nota: "a pessoa está na foto" é um fato do mundo, igual para todos os modelos.
Já "o modelo casou o rosto errado" depende do modelo, e cada um mostra fotos
diferentes no topo do ranking. Por isso a separação é por modelo, e não uma
verdade única. Juntar os "está" de vários modelos daria um gabarito mais forte —
mas isso é decisão do Thiago, não automatismo meu.)

O v3 separa quatro estados, porque a diferença importa:

  aparece_em       a pessoa ESTÁ na foto e o modelo casou o rosto DELA
  rosto_errado     a pessoa ESTÁ na foto, mas o modelo casou o rosto de OUTRA
  nao_aparece_em   a pessoa NÃO está na foto
  (ausente)        ninguém olhou

O `rosto_errado` existe porque os dois primeiros casos parecem iguais na
contagem e são muito diferentes na prática. Para o visitante, receber uma foto
em que ele realmente aparece é acerto — ele não sabe nem liga por qual rosto o
sistema chegou lá. Para medir o MODELO, é erro: a similaridade veio de outra
pessoa, e o acerto foi coincidência. Guardar os dois separados permite calcular
as duas leituras e dizer qual está sendo usada, em vez de escolher uma calada.

Com isso dá para calcular a métrica de dois jeitos e dizer qual foi usado:
  - só sobre o que foi conferido (rigoroso, e é o padrão);
  - tratando o não-conferido como negativo (otimista, precisa ser declarado).

Um gabarito v1 continua sendo lido: `nao_aparece_em` vira lista vazia e a marca
`acervo_completo` diz se o resto pode ser contado como negativo.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

CAMINHO = Path("gabarito.json")


VAZIO = {"aparece_em": [], "rosto_errado": [], "nao_aparece_em": [], "revisao": {}}


def _conjunto_vazio() -> dict:
    return {"aparece_em": [], "rosto_errado": [], "nao_aparece_em": [], "revisao": {}}


def carregar(caminho: Path = CAMINHO, migrar_para: str = "sface") -> dict:
    """Lê o gabarito, migrando o formato antigo (sem modelo) se preciso.

    O formato antigo guardava as marcações soltas na pessoa. Como todo o trabalho
    feito até agora foi com o YuNet+SFace, ele migra para lá — jogar fora seria
    descartar horas de conferência manual.
    """
    if not caminho.exists():
        return {"acervo": "fotos", "acervo_completo": False, "pessoas": {}}
    d = json.loads(caminho.read_text(encoding="utf-8"))
    d.setdefault("pessoas", {})
    for pessoa in d["pessoas"].values():
        pessoa.setdefault("consultas", [])
        pessoa.setdefault("por_modelo", {})
        antigas = (pessoa.pop("aparece_em", None), pessoa.pop("rosto_errado", None),
                   pessoa.pop("nao_aparece_em", None), pessoa.pop("revisao", None))
        if any(x for x in antigas[:3]):
            alvo = pessoa["por_modelo"].setdefault(migrar_para, _conjunto_vazio())
            alvo["aparece_em"] = sorted(set(alvo["aparece_em"]) | set(antigas[0] or []))
            alvo["rosto_errado"] = sorted(set(alvo["rosto_errado"]) | set(antigas[1] or []))
            alvo["nao_aparece_em"] = sorted(set(alvo["nao_aparece_em"]) | set(antigas[2] or []))
            alvo["revisao"] = antigas[3] or alvo["revisao"]
        for conj in pessoa["por_modelo"].values():
            for campo in ("aparece_em", "rosto_errado", "nao_aparece_em"):
                conj.setdefault(campo, [])
            conj.setdefault("revisao", {})
    return d


def marcacoes(d: dict, pessoa: str, modelo: str) -> dict:
    """As marcações de UMA pessoa com UM modelo. Vazio se ainda não testou."""
    p = d["pessoas"].get(pessoa)
    if not p:
        return _conjunto_vazio()
    return p.get("por_modelo", {}).get(modelo) or _conjunto_vazio()


def salvar(d: dict, caminho: Path = CAMINHO) -> Path:
    """Grava com backup do anterior.

    Marcar 80 fotos leva meia hora de trabalho humano; sobrescrever sem cópia
    seria jogar isso fora num erro de digitação.
    """
    if caminho.exists():
        backup = caminho.with_suffix(f".{datetime.now():%Y%m%d_%H%M%S}.bak.json")
        shutil.copy2(caminho, backup)
    caminho.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho


def registrar_marcacao(d: dict, pessoa: str, descricao: str, consulta: str,
                       sim: list[str], nao: list[str],
                       menor_sim_revisada: float | None,
                       rosto_errado: list[str] | None = None,
                       aceitas_em_bloco: int = 0,
                       modelo: str = "sface") -> dict:
    """Aplica o que a pessoa marcou na tela, sem perder o que já havia.

    Marcação nova ganha da antiga para a MESMA foto (é uma correção), mas foto
    que não apareceu nesta rodada continua como estava.
    """
    p = d["pessoas"].setdefault(pessoa, {
        "descricao": descricao, "consultas": [], "por_modelo": {}})
    p.setdefault("por_modelo", {})
    if descricao:
        p["descricao"] = descricao
    if consulta and consulta not in p["consultas"]:
        p["consultas"].append(consulta)
    p = p["por_modelo"].setdefault(modelo, _conjunto_vazio())

    novos_sim, novos_nao = set(sim), set(nao)
    novos_err = set(rosto_errado or [])
    # cada foto vive em exatamente UMA das três listas; a marcação nova manda
    outros = novos_nao | novos_err
    p["aparece_em"] = sorted((set(p["aparece_em"]) - outros) | novos_sim)
    p["rosto_errado"] = sorted(
        (set(p["rosto_errado"]) - novos_sim - novos_nao) | novos_err)
    p["nao_aparece_em"] = sorted(
        (set(p["nao_aparece_em"]) - novos_sim - novos_err) | novos_nao)

    rev = p["revisao"]
    rev["fotos_revisadas"] = len(set(p["aparece_em"]) | set(p["rosto_errado"])
                                 | set(p["nao_aparece_em"]))
    rev["atualizado_em"] = datetime.now().isoformat(timespec="minutes")
    # Quantas marcações vieram de "aceitar as propostas do modelo" em vez de
    # conferência foto a foto. Guardado porque muda o que o número significa:
    # gabarito construído aceitando o modelo em bloco mede o modelo contra ele
    # mesmo. O relatório precisa poder dizer isso.
    rev["aceitas_em_bloco"] = rev.get("aceitas_em_bloco", 0) + int(aceitas_em_bloco)
    if menor_sim_revisada is not None:
        anterior = rev.get("menor_similaridade_revisada")
        rev["menor_similaridade_revisada"] = (
            menor_sim_revisada if anterior is None
            else min(anterior, menor_sim_revisada))
    return d


def resumo(d: dict, modelo: str | None = None) -> list[dict]:
    """Uma linha por pessoa+modelo. Sem `modelo`, lista todos os testados."""
    saida = []
    for nome, p in sorted(d["pessoas"].items()):
        chaves = [modelo] if modelo else sorted(p.get("por_modelo", {}))
        if not chaves:
            chaves = [None]
        for chave in chaves:
            c = marcacoes(d, nome, chave) if chave else _conjunto_vazio()
            rev = c.get("revisao", {})
            saida.append({
                "pessoa": nome,
                "modelo": chave,
                "descricao": p.get("descricao", ""),
                "consultas": p["consultas"],
                "aparece_em": len(c["aparece_em"]),
                "rosto_errado": len(c["rosto_errado"]),
                "nao_aparece_em": len(c["nao_aparece_em"]),
                "revisadas": rev.get("fotos_revisadas", 0),
                "aceitas_em_bloco": rev.get("aceitas_em_bloco", 0),
                "menor_sim_revisada": rev.get("menor_similaridade_revisada"),
                "atualizado_em": rev.get("atualizado_em", ""),
            })
    return saida
