"""
FotoMac Lab — registro das tecnologias candidatas, TODAS na configuração de fábrica.

Regra desta bancada, decidida em 24/09/2026: **a nota de referência de uma
tecnologia é medida com os parâmetros padrão da biblioteca dela, sem nenhum
pré-processamento nosso.**

O motivo é a defesa do resultado. Se eu recorto, alinho e redimensiono do meu
jeito, a nota passa a ser do meu código, e a pergunta "esse número é do modelo ou
do seu adaptador?" fica sem resposta. Ajuste é etapa posterior e entra como
variante separada, com rótulo próprio — nunca no lugar do padrão.

Cada motor aqui expõe a mesma interface de `fotomac_face.FaceEngine`
(`index_image` e `query_face`) porque é isso que o resto da bancada consome —
mas por DENTRO chama apenas a API oficial da biblioteca.
"""

from __future__ import annotations

import os
import warnings

# Precisa vir ANTES de qualquer import que puxe TensorFlow.
#
# O DeepFace roda sobre `tf-keras` (a API antiga do Keras). Ele liga essa
# compatibilidade sozinho ao ser importado — mas se o TensorFlow já tiver sido
# carregado antes, é tarde: o Keras 3 assume e os modelos quebram com
# "A KerasTensor cannot be used as input to a TensorFlow function".
# Custou um diagnóstico falso no verificador de instalação, que acusou os três
# modelos do DeepFace como quebrados quando o ambiente estava são.
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
warnings.filterwarnings("ignore")

from pathlib import Path

import cv2
import numpy as np

import fotomac_face as fm


def _normaliza(v: np.ndarray) -> np.ndarray:
    """L2. O resto do sistema trata produto interno como cosseno."""
    v = np.asarray(v, dtype=np.float32)
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


# ====================================================================
# DeepFace — API oficial, parâmetros padrão
# ====================================================================

class MotorDeepFacePadrao:
    """`DeepFace.represent(caminho, model_name=...)` e nada mais.

    Sem detector escolhido por nós, sem recorte nosso, sem alinhamento nosso.
    `enforce_detection=False` é a única concessão, e ela NÃO muda o resultado:
    apenas evita que a biblioteca levante exceção numa foto sem rosto, o que
    interromperia a varredura. Sem isso, uma foto sem rosto derruba o teste
    inteiro em vez de virar uma linha do relatório.
    """

    def __init__(self, rede: str, detector: str | None = None):
        from deepface import DeepFace
        self._df = DeepFace
        self.rede = rede
        self.detector = detector
        DeepFace.build_model(rede)
        self.rotulo = f"{rede} (DeepFace" + (f", {detector}" if detector else ", padrão") + ")"

    def _representa(self, caminho: Path) -> list[dict]:
        """Entrega a imagem JÁ DECODIFICADA, não o caminho.

        O DeepFace recusa nome de arquivo com acento — ele levanta
        "Input image must not have non-english characters". A foto de consulta
        do coordenador chama "Captura de Tela ... às ...png" e derrubava a
        requisição inteira.
        
        Passar o array não é alteração do modelo: o `detector_backend` continua
        rodando, com o alinhamento e o pré-processamento da própria biblioteca.
        Só o transporte da imagem muda.
        """
        img = cv2.imread(str(caminho))
        if img is None:
            raise ValueError(f"Não foi possível ler a imagem: {caminho}")
        kw = {"model_name": self.rede, "enforce_detection": False}
        if self.detector:
            kw["detector_backend"] = self.detector
        return self._df.represent(img, **kw)

    @staticmethod
    def _e_imagem_inteira(area: dict, caminho: Path) -> bool:
        """DeepFace devolve a imagem toda como 'rosto' quando não detecta nada.

        Medido: numa foto de 6240x4160 ele entrega x=0,y=0,w=6239,h=4159 com
        confiança 0.0. Contar isso como rosto encheria o índice de lixo, então
        vira 'sem rosto' — que é a verdade.
        """
        img = cv2.imread(str(caminho), cv2.IMREAD_REDUCED_COLOR_8)
        if img is None:
            return False
        h, w = img.shape[0] * 8, img.shape[1] * 8
        return area.get("w", 0) >= w - 16 and area.get("h", 0) >= h - 16

    def index_image(self, caminho: str | Path) -> list[fm.Face]:
        caminho = Path(caminho)
        faces = []
        for item in self._representa(caminho):
            area = item["facial_area"]
            if self._e_imagem_inteira(area, caminho):
                continue
            faces.append(fm.Face(
                bbox=(int(area["x"]), int(area["y"]), int(area["w"]), int(area["h"])),
                det_score=float(item.get("face_confidence") or 0.0),
                embedding=_normaliza(item["embedding"])))
        return faces

    def query_face(self, caminho: str | Path) -> fm.Face:
        faces = self.index_image(caminho)
        if not faces:
            raise fm.NoFaceDetected("Nenhum rosto detectado na imagem enviada.")
        # mesma política do motor original: maior área, empate por confiança
        return max(faces, key=lambda f: (f.bbox[2] * f.bbox[3], f.det_score))


# ====================================================================
# InsightFace — API oficial, parâmetros padrão
# ====================================================================

class MotorInsightFacePadrao:
    """`FaceAnalysis(name=...)` + `.prepare()` + `.get(img)`, como a documentação.

    O InsightFace já traz detector (SCRFD) e reconhecedor casados, e redimensiona
    internamente — por isso não precisa de nada nosso em volta.
    """

    def __init__(self, pacote: str = "buffalo_l"):
        from insightface.app import FaceAnalysis
        self._app = FaceAnalysis(name=pacote)
        self._app.prepare(ctx_id=-1)      # -1 = CPU; det_size padrão da biblioteca
        self.rotulo = f"InsightFace {pacote} (padrão)"

    def index_image(self, caminho: str | Path) -> list[fm.Face]:
        img = cv2.imread(str(caminho))
        if img is None:
            raise ValueError(f"Não foi possível ler a imagem: {caminho}")
        saida = []
        for f in self._app.get(img):
            x1, y1, x2, y2 = [int(v) for v in f.bbox]
            saida.append(fm.Face(
                bbox=(x1, y1, x2 - x1, y2 - y1),
                det_score=float(f.det_score),
                # normed_embedding já vem L2-normalizado pela biblioteca
                embedding=np.asarray(f.normed_embedding, dtype=np.float32)))
        return saida

    def query_face(self, caminho: str | Path) -> fm.Face:
        faces = self.index_image(caminho)
        if not faces:
            raise fm.NoFaceDetected("Nenhum rosto detectado na imagem enviada.")
        return max(faces, key=lambda f: (f.bbox[2] * f.bbox[3], f.det_score))


# ====================================================================
# O registro
# ====================================================================

# O detector PADRÃO do DeepFace ("opencv", cascata de Haar) NÃO funciona neste
# ambiente: o opencv-python 5.0 não distribui mais os arquivos
# `cv2/data/haarcascade_*.xml`, e a biblioteca levanta
# "Confirm that opencv is installed on your environment!".
# Medido em 24/09/2026 com Facenet512, ArcFace e VGG-Face — os três falham.
#
# Por isso os modelos do DeepFace aqui declaram `retinaface`, que é o detector
# recomendado pela própria biblioteca e roda em 1,3 s numa foto de 20 MP. Isso
# continua sendo configuração de fábrica: é a API oficial, com um parâmetro que
# a própria documentação oferece — nenhum pré-processamento nosso.
DETECTOR_DEEPFACE = "retinaface"

CATALOGO: dict[str, dict] = {
    "sface": {
        "rotulo": "YuNet + SFace (OpenCV)",
        "familia": "OpenCV",
        "descricao": "Detector YuNet e vetor SFace, ONNX locais. É o único que "
                     "está calibrado por nós — os outros rodam de fábrica.",
        "criar": lambda: fm.FaceEngine(),
        "de_fabrica": False,
        "custo_evento_s": 0.36,
    },
    "facenet512": {
        "rotulo": "Facenet512 + RetinaFace (DeepFace)",
        "familia": "DeepFace",
        "descricao": "Vetor de 512 dimensões, o de maior nota nas tabelas do "
                     "DeepFace. Detector RetinaFace porque o padrão da "
                     "biblioteca (Haar) não roda com OpenCV 5.",
        "criar": lambda: MotorDeepFacePadrao("Facenet512", DETECTOR_DEEPFACE),
        "de_fabrica": True,
        "custo_evento_s": 1.30,
    },
    "arcface": {
        "rotulo": "ArcFace + RetinaFace (DeepFace)",
        "familia": "DeepFace",
        "descricao": "Outro dos mais bem avaliados nas tabelas do DeepFace.",
        "criar": lambda: MotorDeepFacePadrao("ArcFace", DETECTOR_DEEPFACE),
        "de_fabrica": True,
        "custo_evento_s": 1.30,
    },
    "vggface": {
        "rotulo": "VGG-Face + RetinaFace (DeepFace)",
        "familia": "DeepFace",
        "descricao": "O modelo que o DeepFace usa quando nada é informado.",
        "criar": lambda: MotorDeepFacePadrao("VGG-Face", DETECTOR_DEEPFACE),
        "de_fabrica": True,
        "custo_evento_s": 1.60,
    },
    "insightface": {
        "rotulo": "InsightFace buffalo_l",
        "familia": "InsightFace",
        "descricao": "Detector SCRFD e vetor ArcFace casados de fábrica. "
                     "Redimensiona sozinho; nada em volta.",
        "criar": lambda: MotorInsightFacePadrao("buffalo_l"),
        "de_fabrica": True,
        "custo_evento_s": 1.67,
    },
}


def criar(chave: str):
    if chave not in CATALOGO:
        raise KeyError(f"Modelo desconhecido: {chave}. "
                       f"Disponíveis: {', '.join(CATALOGO)}")
    return CATALOGO[chave]["criar"]()


def listar() -> list[dict]:
    return [{"chave": k, **{i: v for i, v in d.items() if i != "criar"}}
            for k, d in CATALOGO.items()]


def estimativa_minutos(chave: str, n_fotos: int) -> float:
    """Quanto tempo a varredura deve levar, para avisar antes de começar."""
    return CATALOGO[chave].get("custo_evento_s", 1.0) * n_fotos / 60.0
