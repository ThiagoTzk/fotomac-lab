"""
FotoMac Lab — dados do painel de comparação.

Lê o ranking produzido por `avaliar_todos.py`, que por sua vez lê o que o Thiago
marcou foto a foto em `/marcar`. Nada aqui é digitado à mão: modelo que não foi
conferido não aparece no gráfico.

A nota principal é a da leitura **MODELO** (rosto errado conta como erro), porque
é ela que compara tecnologias. A leitura PRODUTO aparece ao lado.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

RESULTADOS = Path("resultados")

# Fatias da nota de acerto, na ordem fixa em que aparecem. Ordem fixa porque
# trocá-la trocaria as cores de lugar entre uma apresentação e outra.
COMPONENTES = [
    ("f1", "F1 (acerto)", 1.0),
    ("mAP", "Ordenação (mAP)", 1.0),
    ("auc", "Separação (AUC)", 1.0),
]


def _ranking_mais_recente() -> dict | None:
    arquivos = sorted(RESULTADOS.glob("*_ranking.json"))
    if not arquivos:
        return None
    try:
        return json.loads(arquivos[-1].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def montar() -> dict:
    r = _ranking_mais_recente()
    if not r:
        return {"gerado_em": datetime.now().isoformat(timespec="minutes"),
                "modelos": [], "componentes": [], "avisos": [
                    "Nenhum ranking encontrado. Marque as fotos em /marcar e rode "
                    "`python avaliar_todos.py`."]}

    modelos = []
    # A cor segue o MODELO, fixada pela ordem alfabética: um candidato novo
    # passando na frente no ranking não pode repintar os outros.
    cores = {m["chave"]: i for i, m in enumerate(sorted(r["modelos"], key=lambda x: x["chave"]))}

    for m in r["modelos"]:
        modelos.append({
            "chave": m["chave"],
            "modelo": m["rotulo"],
            "posicao": m["posicao"],
            "nota": m["nota_acerto"],
            "nota_produto": m["nota_acerto_produto"],
            "de_fabrica": m["de_fabrica"],
            "cor": cores[m["chave"]],
            "f1": round(m["modelo"]["f1"], 4),
            "mAP": round(m["modelo"]["mAP"], 4),
            "auc": round(m["modelo"]["auc"], 4),
            "separacao": round(m["modelo"]["separacao"], 4),
            "intrusos": m["modelo"]["intrusos"],
            "rosto_errado": m["rosto_errado_total"],
            "presentes": m["presentes_total"],
            "busca_ms": m["tempo"]["busca_ms"],
            "index_s": m["tempo"]["index_s_por_foto"],
            "fotos": m["acervo"]["fotos"],
            "rostos": m["acervo"]["rostos"],
            "fotos_com_rosto": m["acervo"]["com_rosto"],
            "conferidas": sum(c["conferidas"] for c in m["por_consulta"]),
        })

    melhor = r["modelos"][0] if r["modelos"] else None
    dist = melhor.get("distribuicao") if melhor else None

    avisos = []
    if melhor:
        n = sum(c["presentes"] for c in melhor["por_consulta"])
        if n < 30:
            avisos.append(f"AMOSTRA PEQUENA: {n} foto(s) com a pessoa. Uma a mais ou "
                          "a menos move a métrica vários pontos percentuais.")
        pessoas = {c["pessoa"] for c in melhor["por_consulta"]}
        if len(pessoas) < 3:
            avisos.append(f"O gabarito cobre {len(pessoas)} pessoa(s). A ordem do "
                          "ranking é confiável; os valores exatos, menos.")
    avisos.append("A nota é o melhor F1 que cada tecnologia alcança — o limiar é "
                  "escolhido olhando as respostas. Isso iguala a régua entre elas, "
                  "mas é otimista: não diz como cada uma se sai com uma pessoa nova.")

    return {
        "gerado_em": r.get("gerado_em", ""),
        "rotulo": r.get("rotulo", "Teste 1"),
        "componentes": [{"chave": k, "rotulo": ro, "maximo": mx}
                        for k, ro, mx in COMPONENTES],
        "modelos": modelos,
        "distribuicao": dist,
        "modelo_da_distribuicao": melhor["rotulo"] if melhor else None,
        "avisos": avisos,
    }


if __name__ == "__main__":
    print(json.dumps(montar(), ensure_ascii=False, indent=2)[:1800])
