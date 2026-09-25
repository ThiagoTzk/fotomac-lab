"""
FotoMac — diagnóstico da detecção facial.

Descobre por que o YuNet não encontra rosto numa imagem: testa vários
limiares de confiança, as quatro rotações e vários tamanhos de entrada,
e grava uma cópia com as caixas desenhadas para conferência visual.

Uso:
  python diagnostico.py fotos/IMG_1128.JPG
  python diagnostico.py fotos/*.JPG
"""

import sys
from pathlib import Path

import cv2
import numpy as np

MODELO = Path(__file__).parent / "models" / "face_detection_yunet_2023mar.onnx"
ROTACOES = {
    0:   None,
    90:  cv2.ROTATE_90_CLOCKWISE,
    180: cv2.ROTATE_180,
    270: cv2.ROTATE_90_COUNTERCLOCKWISE,
}


def detectar(img, score=0.5):
    det = cv2.FaceDetectorYN.create(str(MODELO), "", (320, 320),
                                    score_threshold=score, nms_threshold=0.3, top_k=5000)
    h, w = img.shape[:2]
    det.setInputSize((w, h))
    _, faces = det.detect(img)
    return faces if faces is not None else np.empty((0, 15), dtype=np.float32)


def redimensiona(img, lado):
    h, w = img.shape[:2]
    s = min(1.0, lado / max(h, w))
    if s == 1.0:
        return img
    return cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)


def analisa(caminho):
    print("=" * 68)
    print(caminho)

    img = cv2.imread(caminho)
    if img is None:
        print("  ERRO: o OpenCV não conseguiu ler este arquivo.")
        print("  Provavelmente não é um JPEG de verdade (HEIC ou DNG renomeado).")
        return

    h, w = img.shape[:2]
    print(f"  Dimensões: {w} x {h}  ({w*h/1_000_000:.1f} MP)"
          f"  |  orientação: {'retrato' if h > w else 'paisagem'}")

    melhor = None
    for lado in (1920, 2560, 1280):
        base = redimensiona(img, lado)
        for graus, op in ROTACOES.items():
            alvo = base if op is None else cv2.rotate(base, op)
            for score in (0.85, 0.6, 0.3):
                faces = detectar(alvo, score)
                if len(faces):
                    maior = max(faces, key=lambda r: r[2] * r[3])
                    info = (len(faces), float(maior[14]), int(maior[2]), int(maior[3]),
                            graus, score, lado, alvo)
                    if melhor is None or info[1] > melhor[1]:
                        melhor = info
                    break
            if melhor and melhor[4] == graus and melhor[6] == lado:
                break
        if melhor:
            break

    if melhor is None:
        print("  NENHUM rosto encontrado em nenhuma combinação testada.")
        print("  A imagem provavelmente não contém um rosto nítido e de frente.")
        return

    n, conf, bw, bh, graus, score, lado, alvo = melhor
    print(f"  ENCONTROU {n} rosto(s)")
    print(f"    confiança do maior : {conf:.3f}")
    print(f"    tamanho do rosto   : {bw} x {bh} px")
    print(f"    rotação necessária : {graus}°")
    print(f"    limiar necessário  : {score}")
    print(f"    lado usado         : {lado}px")

    if graus != 0:
        print("  >> CAUSA: a imagem está girada. Corrija a rotação do arquivo.")
    if score < 0.85:
        print(f"  >> CAUSA: confiança abaixo de 0.85. Baixe MIN_DET_SCORE para {score}.")
    if min(bw, bh) < 40:
        print(f"  >> CAUSA: rosto menor que 40px. Baixe MIN_FACE_SIDE para {min(bw,bh)-5}.")

    faces = detectar(alvo, score)
    marcada = alvo.copy()
    for f in faces:
        x, y, fw, fh = map(int, f[:4])
        cv2.rectangle(marcada, (x, y), (x + fw, y + fh), (0, 255, 0), 3)
        cv2.putText(marcada, f"{f[14]:.2f}", (x, max(0, y - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    saida = Path("diagnostico") / (Path(caminho).stem + "_detectado.jpg")
    saida.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(saida), marcada)
    print(f"  Imagem marcada salva em: {saida}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    if not MODELO.exists():
        print(f"Modelo não encontrado: {MODELO}")
        raise SystemExit(1)
    for c in sys.argv[1:]:
        analisa(c)
    print("=" * 68)
