"""
FotoMac Lab — quais modelos já foram testados, e até onde.

O Thiago vai conferir foto por foto, modelo por modelo. São dezenas de fotos por
modelo e vários modelos: sem um registro do que já passou, ele se perde e
retrabalha. Este arquivo é esse registro — é o que acende o "verificado" ao lado
de cada modelo na tela.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

CAMINHO = Path("modelos_testados.json")


def carregar() -> dict:
    if not CAMINHO.exists():
        return {"modelos": {}}
    try:
        d = json.loads(CAMINHO.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"modelos": {}}
    d.setdefault("modelos", {})
    return d


def salvar(d: dict) -> None:
    CAMINHO.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def registrar(chave: str, pessoa: str, marcadas: int, total: int,
              indexado: bool = False) -> dict:
    """Anota progresso. Um modelo só vira 'verificado' quando alguém marcou
    fotos com ele — indexar sozinho não prova nada."""
    d = carregar()
    m = d["modelos"].setdefault(chave, {
        "indexado": False, "pessoas": {}, "primeiro_uso": "", "ultimo_uso": ""})
    agora = datetime.now().isoformat(timespec="minutes")
    m["primeiro_uso"] = m["primeiro_uso"] or agora
    m["ultimo_uso"] = agora
    m["indexado"] = m["indexado"] or indexado
    if pessoa:
        p = m["pessoas"].setdefault(pessoa, {})
        p["marcadas"] = max(p.get("marcadas", 0), int(marcadas))
        p["ranking_visto"] = max(p.get("ranking_visto", 0), int(total))
        p["atualizado_em"] = agora
    salvar(d)
    return d


def resumo() -> dict:
    """Por modelo: indexado, quantas pessoas conferidas, quantas fotos marcadas."""
    d = carregar()
    saida = {}
    for chave, m in d["modelos"].items():
        total = sum(p.get("marcadas", 0) for p in m["pessoas"].values())
        saida[chave] = {
            "indexado": bool(m.get("indexado")),
            "pessoas": sorted(m["pessoas"]),
            "marcadas": total,
            # o critério do selo: houve conferência humana, não só indexação
            "verificado": total > 0,
            "ultimo_uso": m.get("ultimo_uso", ""),
        }
    return saida
