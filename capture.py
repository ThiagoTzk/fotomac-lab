"""
FotoMac Lab — captura do autorretrato pela webcam.

Simula o que o visitante faz no totem: olha para a câmera, o sistema confere se o
rosto está bom o bastante, e só então tira a foto. É o RF016/RF017 rodando de
verdade, em vez de apontar para um arquivo que já estava no disco.

Dois modos:

  python capture.py                 janela com prévia ao vivo; ESPAÇO tira, ESC sai
  python capture.py --sem-janela    sem janela: conta 3, 2, 1 e escolhe o melhor quadro

Depois de capturar, com --buscar ele já roda o benchmark contra o acervo:

  python capture.py --buscar

A foto vai para consultas/autorretrato_<data-hora>.jpg.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

import fotomac_face as fm

SAIDA = Path("consultas")

# Quantos quadros o modo sem janela avalia antes de escolher. ~2 segundos de vídeo.
QUADROS_AVALIADOS = 60

COR_OK = (80, 220, 80)
COR_RUIM = (60, 170, 240)


def _mensagem_qualidade(rows: np.ndarray, frame_shape) -> tuple[str, bool, np.ndarray | None]:
    """Traduz o estado da detecção em instrução para a pessoa.

    Devolve (mensagem, pode_capturar, melhor_linha). As mensagens são as mesmas
    situações que o RF017 prevê, mas ditas como orientação e não como erro.
    """
    if len(rows) == 0:
        return "Nenhum rosto: chegue mais perto e olhe para a camera", False, None

    melhor = max(rows, key=lambda r: r[2] * r[3])
    lado = min(float(melhor[2]), float(melhor[3]))
    score = float(melhor[14])

    if score < fm.MIN_DET_SCORE:
        return f"Rosto pouco nitido ({score:.2f}): procure mais luz", False, melhor
    if lado < 80:
        # Exigência maior que MIN_FACE_SIDE de propósito: no acervo aceitamos
        # rosto pequeno porque a foto é o que é; aqui a pessoa pode se aproximar.
        return f"Rosto pequeno ({int(lado)}px): chegue mais perto", False, melhor
    if len(rows) > 1:
        return "Mais de um rosto no quadro: fique sozinho", False, melhor
    return "PRONTO", True, melhor


def _desenha(frame, rows, msg: str, pode: bool, melhor) -> np.ndarray:
    vis = frame.copy()
    cor = COR_OK if pode else COR_RUIM
    for r in rows:
        x, y, w, h = map(int, r[:4])
        c = cor if (melhor is not None and r is melhor) else (150, 150, 150)
        cv2.rectangle(vis, (x, y), (x + w, y + h), c, 3 if c == cor else 1)

    h_img = vis.shape[0]
    cv2.rectangle(vis, (0, h_img - 54), (vis.shape[1], h_img), (25, 25, 25), -1)
    cv2.putText(vis, msg, (14, h_img - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                cor, 2, cv2.LINE_AA)
    dica = "ESPACO tira a foto  |  ESC cancela" if pode else "ESC cancela"
    cv2.putText(vis, dica, (14, h_img - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                (190, 190, 190), 1, cv2.LINE_AA)
    return vis


def abrir_camera(indice: int) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(indice)
    if not cap.isOpened():
        print("\nNão consegui abrir a câmera.\n")
        print("No macOS isto quase sempre é permissão. Abra:")
        print("  Ajustes do Sistema > Privacidade e Segurança > Câmera")
        print("e ligue o aplicativo de onde você está rodando (Terminal, iTerm,")
        print("VS Code). Depois FECHE e reabra esse aplicativo — a permissão só")
        print("vale a partir do próximo início.\n")
        raise SystemExit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return cap


def capturar_com_janela(engine: fm.FaceEngine, cap) -> np.ndarray | None:
    print("Janela aberta. ESPAÇO tira a foto, ESC cancela.")
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Falha ao ler da câmera.")
            return None
        frame = cv2.flip(frame, 1)   # espelhado: a pessoa se vê como num espelho
        rows = engine._detect_raw(frame)
        msg, pode, melhor = _mensagem_qualidade(rows, frame.shape)
        cv2.imshow("FotoMac — autorretrato", _desenha(frame, rows, msg, pode, melhor))

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == 27:              # ESC
            return None
        if tecla == 32 and pode:     # ESPAÇO, só quando o rosto está bom
            return frame


def capturar_sem_janela(engine: fm.FaceEngine, cap) -> np.ndarray | None:
    """Conta 3, 2, 1 e fica com o melhor quadro dos QUADROS_AVALIADOS seguintes.

    'Melhor' = maior área de rosto entre os que passam na qualidade. Escolher
    automaticamente evita o quadro tremido que sai quando a pessoa aperta a tecla.
    """
    for n in (3, 2, 1):
        print(f"  {n}...", flush=True)
        fim = time.time() + 1.0
        while time.time() < fim:
            cap.read()

    print("  capturando...", flush=True)
    melhor_frame, melhor_area = None, -1.0
    for _ in range(QUADROS_AVALIADOS):
        ok, frame = cap.read()
        if not ok:
            continue
        frame = cv2.flip(frame, 1)
        rows = engine._detect_raw(frame)
        _, pode, melhor = _mensagem_qualidade(rows, frame.shape)
        if pode and melhor is not None:
            area = float(melhor[2]) * float(melhor[3])
            if area > melhor_area:
                melhor_frame, melhor_area = frame, area

    if melhor_frame is None:
        print("\nNenhum quadro com rosto aprovado. Mais luz, mais perto, sozinho no quadro.")
    return melhor_frame


def main() -> int:
    ap = argparse.ArgumentParser(description="Captura o autorretrato pela webcam.")
    ap.add_argument("--camera", type=int, default=0, help="índice da câmera (padrão: 0)")
    ap.add_argument("--sem-janela", action="store_true",
                    help="não abre janela; conta 3,2,1 e escolhe o melhor quadro")
    ap.add_argument("--buscar", action="store_true",
                    help="depois de capturar, roda o benchmark com esta foto")
    ap.add_argument("--acervo", type=Path, default=Path("fotos"))
    args = ap.parse_args()

    engine = fm.FaceEngine()
    cap = abrir_camera(args.camera)
    try:
        frame = (capturar_sem_janela(engine, cap) if args.sem_janela
                 else capturar_com_janela(engine, cap))
    finally:
        cap.release()
        cv2.destroyAllWindows()

    if frame is None:
        print("Cancelado. Nada foi salvo.")
        return 1

    SAIDA.mkdir(exist_ok=True)
    destino = SAIDA / f"autorretrato_{time.strftime('%Y-%m-%d_%H%M%S')}.jpg"
    cv2.imwrite(str(destino), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"\nFoto salva: {destino}")

    # Confirma que o motor de busca aceita a foto ANTES de prometer resultado.
    try:
        face = engine.query_face(destino)
        print(f"Rosto aprovado para busca: confiança {face.det_score:.3f}, caixa {face.bbox}")
    except (fm.NoFaceDetected, fm.LowQualityFace) as exc:
        print(f"A foto foi salva, mas não serve para busca: {exc}")
        return 1

    if args.buscar:
        print("\nRodando a busca contra o acervo...\n")
        return subprocess.call([sys.executable, "benchmark.py",
                                "--acervo", str(args.acervo),
                                "--consulta", str(destino)])
    print("\nPara buscar com ela:")
    print(f"  .venv/bin/python benchmark.py --consulta {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
