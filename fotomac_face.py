"""
FotoMac — motor de reconhecimento facial (YuNet + SFace / OpenCV).

Duas responsabilidades separadas, como o documento de requisitos exige:
  - detectar rostos numa imagem e gerar um vetor por rosto  (indexação, RF010)
  - gerar UM vetor a partir do autorretrato do visitante     (busca, RF016/RF017)

Modelos necessários (baixar do opencv_zoo, ver README no fim do arquivo):
  face_detection_yunet_2023mar.onnx
  face_recognition_sface_2021dec.onnx

Uso rápido:
  python fotomac_face.py selfie.jpg foto_evento.jpg
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

# ---------------------------------------------------------------- parâmetros

MODELS_DIR = Path(__file__).parent / "models"
YUNET = MODELS_DIR / "face_detection_yunet_2023mar.onnx"
SFACE = MODELS_DIR / "face_recognition_sface_2021dec.onnx"

# Reduz o lado maior da imagem antes de detectar. Fotos de evento vêm com
# 20+ megapixels; detectar no tamanho original é lento e não melhora o
# resultado para rostos de tamanho normal.
MAX_SIDE = 1920

# Confiança mínima do detector. Abaixo disso o rosto é descartado e NÃO gera
# vetor (RF010, regra 5).
#
# CALIBRADO em 23/09/2026 contra gabarito.json, no acervo de 204 fotos:
#   0.60 -> 1004 rostos em 197 fotos | pior acerto 0.5202 | melhor erro 0.3728
#   0.50 -> 3583 rostos em 204 fotos | pior acerto 0.5202 | melhor erro 0.3809
#   0.40 -> 3999 rostos em 204 fotos | pior acerto 0.5202 | melhor erro 0.3809
#   0.30 -> QUEBRA: pior acerto despenca para 0.0546
#
# 0.50 captura 3.6x mais rostos sem custo mensurável de separação.
#
# NÃO baixe para 0.30: nesse nível o detector inventa uma caixa grande e espúria
# no autorretrato (em IMG_1128, área 356206 com score 0.346, maior que o rosto
# real de área 319414). Como query_face escolhe pela MAIOR ÁREA, a caixa falsa
# vence e o vetor da consulta vira lixo. O problema é do lado da consulta, não
# do acervo.
MIN_DET_SCORE = 0.50

# Lado mínimo da caixa do rosto, em pixels, medido na imagem redimensionada.
# Filtro de qualidade do RF017.
#
# CALIBRADO em 23/09/2026. Baixado de 40 para 10 para levar TODOS os rostos à
# comparação — num acervo de formatura o visitante aparece pequeno e ao fundo, e
# descartar rosto pequeno é descartar foto que era dele.
#
# Conferido antes de baixar: rostos de 10-19 px NÃO produzem vetor degenerado
# (similaridade média entre eles +0.16, contra +0.12 dos rostos grandes). E o
# gabarito confirma: o melhor erro só subiu de 0.3728 para 0.3809, bem longe do
# limiar 0.45.
MIN_FACE_SIDE = 10

# Limiar de similaridade de cosseno.
#
# CALIBRADO em 23/09/2026 contra gabarito.json (204 fotos reais de evento,
# 1004 rostos, 3 fotos positivas de uma pessoa). Medido:
#   pior acerto  = 0.5202  (a foto correta de menor similaridade)
#   melhor erro  = 0.3728  (a foto errada de maior similaridade — IMG_3011)
# Qualquer valor entre os dois acerta 100% e erra 0%. 0.45 é o ponto médio:
# o mais distante das duas bordas, ~0.07 de folga de cada lado.
#
# O padrão do SFace é 0.363 e ele DEMONSTRAVELMENTE erra neste acervo
# (IMG_3011 passa por 0.363). Não volte para 0.363 sem novos dados.
#
# Ressalva: a calibração vem de UMA pessoa com 3 fotos. Acrescentar pessoas ao
# gabarito e recalibrar é o próximo passo — ver SISTEMA-DE-PONTUACAO.md.
COSINE_THRESHOLD = 0.45

EMBEDDING_DIM = 128


@dataclass
class Face:
    """Um rosto detectado e o seu vetor de características."""
    bbox: tuple[int, int, int, int]   # x, y, w, h na imagem ORIGINAL
    det_score: float
    embedding: np.ndarray             # (128,) float32, normalizado (norma 1)

    @property
    def area(self) -> int:
        return self.bbox[2] * self.bbox[3]


class FaceEngine:
    def __init__(self, yunet: Path = YUNET, sface: Path = SFACE):
        for p in (yunet, sface):
            if not p.exists():
                raise FileNotFoundError(f"Modelo não encontrado: {p}")

        self.detector = cv2.FaceDetectorYN.create(
            model=str(yunet),
            config="",
            input_size=(320, 320),      # redefinido a cada imagem
            score_threshold=MIN_DET_SCORE,
            nms_threshold=0.3,
            top_k=5000,
        )
        self.recognizer = cv2.FaceRecognizerSF.create(model=str(sface), config="")

    # ------------------------------------------------------------- interno

    @staticmethod
    def _load_and_resize(image_path: str | Path) -> tuple[np.ndarray, float]:
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Não foi possível ler a imagem: {image_path}")

        h, w = img.shape[:2]
        scale = min(1.0, MAX_SIDE / max(h, w))
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)),
                             interpolation=cv2.INTER_AREA)
        return img, scale

    def _detect_raw(self, img: np.ndarray) -> np.ndarray:
        """Devolve array Nx15 do YuNet (vazio se não houver rosto)."""
        h, w = img.shape[:2]
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(img)
        return faces if faces is not None else np.empty((0, 15), dtype=np.float32)

    def _embed(self, img: np.ndarray, row: np.ndarray) -> np.ndarray:
        """Alinha o rosto pelos 5 pontos do detector e extrai o vetor."""
        aligned = self.recognizer.alignCrop(img, row)
        feat = self.recognizer.feature(aligned).flatten().astype(np.float32)
        # Normaliza para norma 1 — assim a similaridade de cosseno vira
        # produto interno, e o pgvector compara direto.
        norm = np.linalg.norm(feat)
        return feat / norm if norm > 0 else feat

    @staticmethod
    def _passes_quality(row: np.ndarray) -> bool:
        _, _, bw, bh = row[:4]
        return min(bw, bh) >= MIN_FACE_SIDE and float(row[14]) >= MIN_DET_SCORE

    # ------------------------------------------------------------- público

    def index_image(self, image_path: str | Path) -> list[Face]:
        """
        INDEXAÇÃO (RF010). Devolve um Face por rosto aprovado nos filtros.
        Uma imagem pode gerar vários vetores — todos vinculados ao mesmo evento.
        """
        img, scale = self._load_and_resize(image_path)
        faces: list[Face] = []

        for row in self._detect_raw(img):
            if not self._passes_quality(row):
                continue
            x, y, bw, bh = row[:4]
            faces.append(Face(
                bbox=(int(x / scale), int(y / scale),
                      int(bw / scale), int(bh / scale)),
                det_score=float(row[14]),
                embedding=self._embed(img, row),
            ))
        return faces

    def query_face(self, image_path: str | Path) -> Face:
        """
        BUSCA (RF016/RF017). Devolve exatamente UM vetor, escolhido por
        política determinística: maior área da caixa após os filtros de
        qualidade; empate resolvido por (i) maior confiança do detector,
        (ii) menor distância ao centro do quadro, (iii) menor índice.

        Levanta NoFaceDetected ou LowQualityFace — os dois erros de negócio
        distintos previstos no RF017.
        """
        img, scale = self._load_and_resize(image_path)
        h, w = img.shape[:2]
        cx, cy = w / 2, h / 2

        rows = self._detect_raw(img)
        if len(rows) == 0:
            raise NoFaceDetected("Nenhum rosto detectado na imagem enviada.")

        approved = [(i, r) for i, r in enumerate(rows) if self._passes_quality(r)]
        if not approved:
            raise LowQualityFace(
                "Nenhum rosto com qualidade suficiente. Tente com mais luz, "
                "mais perto da câmera ou com o rosto mais enquadrado."
            )

        def sort_key(item):
            i, r = item
            x, y, bw, bh = r[:4]
            fx, fy = x + bw / 2, y + bh / 2
            dist = ((fx - cx) ** 2 + (fy - cy) ** 2) ** 0.5 / max(w, h)
            # área desc, score desc, distância asc, índice asc
            return (-(bw * bh), -float(r[14]), dist, i)

        _, row = min(approved, key=sort_key)
        x, y, bw, bh = row[:4]
        return Face(
            bbox=(int(x / scale), int(y / scale),
                  int(bw / scale), int(bh / scale)),
            det_score=float(row[14]),
            embedding=self._embed(img, row),
        )


class NoFaceDetected(ValueError):
    """RF017 — nenhuma face detectada no autorretrato."""


class LowQualityFace(ValueError):
    """RF017 — nenhuma face aprovada nos filtros de qualidade."""


def similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Similaridade de cosseno. Como os vetores já estão normalizados,
    é o produto interno. Quanto maior, mais parecidos."""
    return float(np.dot(a, b))


# ------------------------------------------------------------------- teste

def _main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 1

    engine = FaceEngine()

    try:
        query = engine.query_face(sys.argv[1])
    except (NoFaceDetected, LowQualityFace) as exc:
        print(f"Autorretrato recusado: {exc}")
        return 1

    print(f"Autorretrato: 1 rosto escolhido "
          f"(confiança {query.det_score:.3f}, caixa {query.bbox})")

    gallery = engine.index_image(sys.argv[2])
    print(f"Foto do evento: {len(gallery)} rosto(s) indexado(s)\n")

    if not gallery:
        print("Nenhum rosto aprovado na foto do evento.")
        return 0

    for n, face in enumerate(gallery, 1):
        score = similarity(query.embedding, face.embedding)
        veredito = "CORRESPONDE" if score >= COSINE_THRESHOLD else "não corresponde"
        print(f"  rosto {n}: similaridade {score:+.4f}  ->  {veredito}")

    melhor = max(similarity(query.embedding, f.embedding) for f in gallery)
    print(f"\nMelhor similaridade: {melhor:+.4f} (limiar {COSINE_THRESHOLD})")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
