"""
FotoMac Lab — calcula a nota de cada tecnologia a partir do que foi marcado na tela.

Faltava esta ponte: a conferência acontece em `/marcar` e grava no `gabarito.json`,
mas a nota só era produzida pelo `benchmark.py`, que reindexa tudo do zero. Aqui o
índice em cache de cada modelo é reaproveitado — segundos em vez de minutos.

Duas leituras do mesmo gabarito, e o relatório diz as duas:

  MODELO   `rosto_errado` é ERRO. A similaridade veio do rosto de outra pessoa;
           o acerto foi coincidência e não se repete. É a leitura que compara
           tecnologias, porque mede o que a tecnologia realmente fez.
  PRODUTO  `rosto_errado` é ACERTO. A foto entregue tem mesmo a pessoa e o
           visitante fica satisfeito, não importa por qual rosto o sistema
           chegou lá.

Uso:  python avaliar_todos.py
"""

from __future__ import annotations

import csv
import json
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import numpy as np

import gabarito_io
import indice as idx_mod
import metricas as mt
import modelos as cat

SAIDA = Path("resultados")
nfc = lambda s: unicodedata.normalize("NFC", s)


def _melhor_f1(ranking: list[tuple[str, float]], positivos: set[str],
               conferidas: set[str], consulta: str) -> tuple[float, float]:
    """Maior F1 alcançável e o limiar que o produz.

    É otimista de propósito e precisa ser lido assim: o limiar é escolhido
    olhando as respostas. Serve para comparar o POTENCIAL de cada tecnologia na
    mesma régua — nenhuma leva vantagem por ter um padrão de fábrica melhor
    calibrado. O que ele NÃO diz é como o modelo se sai com uma pessoa nova.
    """
    pares = [(n, s) for n, s in ranking if n != consulta and n in conferidas]
    esperados = {p for p in positivos if p != consulta}
    if not pares or not esperados:
        return 0.0, 0.0
    melhor = (0.0, 0.0)
    for _, corte in sorted(pares, key=lambda t: -t[1]):
        tp = sum(1 for n, s in pares if s >= corte and n in esperados)
        fp = sum(1 for n, s in pares if s >= corte and n not in esperados)
        fn = len(esperados) - tp
        if tp == 0:
            continue
        prec, rec = tp / (tp + fp), tp / (tp + fn)
        f1 = 2 * prec * rec / (prec + rec)
        if f1 > melhor[0]:
            melhor = (f1, corte)
    return melhor


def avaliar(chave: str, gab: dict, progresso=print) -> dict | None:
    pessoas = [(n, p) for n, p in gab["pessoas"].items()
               if gabarito_io.marcacoes(gab, n, chave)["aparece_em"]
               or gabarito_io.marcacoes(gab, n, chave)["nao_aparece_em"]]
    if not pessoas:
        return None

    progresso(f"  carregando {chave}...")
    t0 = time.perf_counter()
    motor = cat.criar(chave)
    carga_s = time.perf_counter() - t0
    indice = idx_mod.construir(Path(gab.get("acervo", "fotos")), motor,
                               progresso=lambda m: None, modelo=chave)

    por_consulta, buscas, csvs = [], [], []
    for nome, dados in pessoas:
        c = gabarito_io.marcacoes(gab, nome, chave)
        sim_set = {nfc(x) for x in c["aparece_em"]}
        err_set = {nfc(x) for x in c["rosto_errado"]}
        nao_set = {nfc(x) for x in c["nao_aparece_em"]}
        conferidas = sim_set | err_set | nao_set

        for consulta in dados["consultas"]:
            alvo = Path(gab.get("acervo", "fotos")) / consulta
            if not alvo.exists():
                alvo = Path("consultas") / consulta
            if not alvo.exists():
                continue
            try:
                face = motor.query_face(alvo)
            except Exception as exc:
                progresso(f"    consulta recusada ({consulta}): {exc}")
                continue
            t = time.perf_counter()
            rank, _ = idx_mod.buscar(indice, face.embedding)
            buscas.append((time.perf_counter() - t) * 1000)
            ranking = [(nfc(r["arquivo"]), float(r["similaridade"])) for r in rank]
            alvo_nfc = nfc(consulta)

            # MODELO: rosto errado é negativo
            m_modelo = mt.metricas_de_consulta(ranking, sim_set, alvo_nfc, conferidas)
            f1_m, lim_m = _melhor_f1(ranking, sim_set, conferidas, alvo_nfc)
            # PRODUTO: rosto errado é positivo
            amplos = sim_set | err_set
            m_produto = mt.metricas_de_consulta(ranking, amplos, alvo_nfc, conferidas)
            f1_p, lim_p = _melhor_f1(ranking, amplos, conferidas, alvo_nfc)

            # guarda as similaridades separadas, para o gráfico do painel
            sims_pos = [v for n, v in ranking if n in sim_set and n != alvo_nfc]
            sims_err = [v for n, v in ranking if n in err_set and n != alvo_nfc]
            sims_neg = [v for n, v in ranking if n in nao_set and n != alvo_nfc]

            # CSV por foto: permite recalcular qualquer limiar no Excel sem
            # reprocessar nada. Era a única coisa útil do antigo benchmark.py.
            csvs.append((f"{chave}_{nome}", [
                (n, v, "esta" if n in sim_set else
                 "rosto_errado" if n in err_set else
                 "nao_esta" if n in nao_set else "nao_conferida")
                for n, v in ranking]))

            por_consulta.append({
                "similaridades": {"esta": sims_pos, "rosto_errado": sims_err,
                                  "nao_esta": sims_neg},
                "pessoa": nome, "consulta": consulta,
                "conferidas": len(conferidas),
                "presentes": len(sim_set | err_set),
                "rosto_errado": len(err_set),
                "modelo": {**m_modelo, "melhor_f1": f1_m, "limiar_do_melhor_f1": lim_m},
                "produto": {**m_produto, "melhor_f1": f1_p, "limiar_do_melhor_f1": lim_p},
            })

    if not por_consulta:
        return None

    med = lambda campo, leitura: float(np.mean(
        [c[leitura][campo] for c in por_consulta if c[leitura].get(campo) is not None]))

    # distribuição juntando todas as consultas deste modelo
    todos_pos = [v for c in por_consulta for v in c["similaridades"]["esta"]]
    todos_err = [v for c in por_consulta for v in c["similaridades"]["rosto_errado"]]
    todos_neg = [v for c in por_consulta for v in c["similaridades"]["nao_esta"]]
    bins = np.linspace(-0.3, 1.0, 66)
    dist = {
        "bins": [round(float(b), 4) for b in bins],
        "esta": [int(x) for x in np.histogram(todos_pos, bins=bins)[0]],
        "rosto_errado": [int(x) for x in np.histogram(todos_err, bins=bins)[0]],
        "nao_esta": [int(x) for x in np.histogram(todos_neg, bins=bins)[0]],
        "n_esta": len(todos_pos), "n_errado": len(todos_err), "n_nao": len(todos_neg),
        "pior_acerto": round(min(todos_pos), 4) if todos_pos else None,
        "melhor_erro": round(max(todos_neg), 4) if todos_neg else None,
    }

    return {
        "chave": chave,
        "csvs": csvs,
        "distribuicao": dist,
        "rotulo": cat.CATALOGO[chave]["rotulo"],
        "de_fabrica": cat.CATALOGO[chave]["de_fabrica"],
        "acervo": {"fotos": len(indice.fotos), "com_rosto": indice.fotos_com_rosto,
                   "rostos": indice.total_rostos},
        "tempo": {"carregar_s": round(carga_s, 2),
                  "index_s_por_foto": round(indice.segundos_indexacao / max(1, len(indice.fotos)), 4),
                  "busca_ms": round(float(np.mean(buscas)), 3) if buscas else None},
        "modelo": {"f1": med("melhor_f1", "modelo"), "mAP": med("average_precision", "modelo"),
                   "auc": med("auc", "modelo"), "separacao": med("separacao", "modelo"),
                   "intrusos": int(sum(c["modelo"]["intrusos"] or 0 for c in por_consulta))},
        "produto": {"f1": med("melhor_f1", "produto"), "mAP": med("average_precision", "produto"),
                    "auc": med("auc", "produto")},
        "rosto_errado_total": sum(c["rosto_errado"] for c in por_consulta),
        "presentes_total": sum(c["presentes"] for c in por_consulta),
        "por_consulta": por_consulta,
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Calcula a nota de cada tecnologia.")
    ap.add_argument("--rotulo", default="Teste 1",
                    help="nome desta rodada (aparece no painel e no relatório)")
    args = ap.parse_args()
    gab = gabarito_io.carregar()
    SAIDA.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    resultados = []

    for chave in cat.CATALOGO:
        print(f"\n### {chave}")
        r = avaliar(chave, gab)
        if r is None:
            print("  sem marcações para este modelo — pulado.")
            continue
        resultados.append(r)
        print(f"  F1 {r['modelo']['f1']:.4f} | mAP {r['modelo']['mAP']:.4f} | "
              f"AUC {r['modelo']['auc']:.4f} | rosto errado {r['rosto_errado_total']}")

    for r in resultados:
        for c in r["por_consulta"]:
            c.pop("similaridades", None)   # já viraram histograma
        for nome, linhas in r.pop("csvs", []):
            destino = SAIDA / f"{stamp}_{nome}.csv"
            with destino.open("w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["arquivo", "similaridade", "gabarito"])
                for arq, sim, marca in linhas:
                    w.writerow([arq, f"{sim:.6f}", marca])

    resultados.sort(key=lambda r: -r["modelo"]["f1"])
    for i, r in enumerate(resultados, 1):
        r["posicao"] = i
        r["nota_acerto"] = round(100 * r["modelo"]["f1"], 1)
        r["nota_acerto_produto"] = round(100 * r["produto"]["f1"], 1)

    destino = SAIDA / f"{stamp}_ranking.json"
    print(f"\nRodada: {args.rotulo}")
    destino.write_text(json.dumps(
        {"gerado_em": datetime.now().isoformat(timespec="minutes"),
         "rotulo": args.rotulo,
         "leitura_principal": "modelo",
         "modelos": resultados}, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{'#':>2} {'tecnologia':<38} {'NOTA':>6} {'F1':>7} {'mAP':>7} {'AUC':>7} "
          f"{'intrusos':>8} {'r.errado':>8} {'produto':>8}")
    for r in resultados:
        print(f"{r['posicao']:>2} {r['rotulo']:<38} {r['nota_acerto']:>6.1f} "
              f"{r['modelo']['f1']:>7.4f} {r['modelo']['mAP']:>7.4f} {r['modelo']['auc']:>7.4f} "
              f"{r['modelo']['intrusos']:>8} {r['rosto_errado_total']:>8} "
              f"{r['nota_acerto_produto']:>8.1f}")
    print(f"\nGravado: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
