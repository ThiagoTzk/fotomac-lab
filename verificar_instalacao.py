"""
FotoMac Lab — confere se o ambiente está pronto.

Feito para quem acabou de instalar e quer saber se pode começar, sem precisar
ler o código. Roda cada tecnologia numa imagem real e diz, em português, o que
está de pé e o que falta.

    python verificar_instalacao.py

Não baixa nada de propósito: os pesos dos modelos são baixados no primeiro uso
real. Aqui ele só reporta o que já está no disco.
"""

from __future__ import annotations

import importlib
import os
import platform
import sys
import warnings
from pathlib import Path

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

OK, FALTA, AVISO = "  [ok]   ", "  [FALTA]", "  [aviso]"

# Cada linha: (nome, módulo a importar, pacote do pip, para que serve)
BIBLIOTECAS = [
    ("NumPy", "numpy", "numpy", "contas com vetores"),
    ("OpenCV", "cv2", "opencv-python", "ler imagem, YuNet e SFace"),
    ("DeepFace", "deepface", "deepface", "Facenet512, ArcFace, VGG-Face"),
    ("TensorFlow", "tensorflow", "tensorflow", "roda os modelos do DeepFace"),
    ("tf-keras", "tf_keras", "tf-keras", "compatibilidade do DeepFace com Keras 3"),
    ("RetinaFace", "retinaface", "retina-face", "detector usado pelo DeepFace"),
    ("InsightFace", "insightface", "insightface", "detector SCRFD + vetor ArcFace"),
    ("ONNX Runtime", "onnxruntime", "onnxruntime", "roda o InsightFace"),
]

PESOS = [
    ("Facenet512", Path.home() / ".deepface/weights/facenet512_weights.h5", "95 MB"),
    ("ArcFace", Path.home() / ".deepface/weights/arcface_weights.h5", "137 MB"),
    ("VGG-Face", Path.home() / ".deepface/weights/vgg_face_weights.h5", "580 MB"),
    ("RetinaFace", Path.home() / ".deepface/weights/retinaface.h5", "119 MB"),
    ("InsightFace buffalo_l", Path.home() / ".insightface/models/buffalo_l/w600k_r50.onnx", "275 MB"),
]

ONNX_LOCAIS = [
    ("YuNet (detector)", Path("models/face_detection_yunet_2023mar.onnx")),
    ("SFace (vetor)", Path("models/face_recognition_sface_2021dec.onnx")),
]


def secao(titulo: str) -> None:
    print(f"\n{titulo}\n" + "-" * len(titulo))


def main() -> int:
    problemas: list[str] = []

    secao("Ambiente")
    print(f"  Python {platform.python_version()}  ({sys.executable})")
    print(f"  Sistema {platform.system()} {platform.release()} · {platform.machine()}")
    if sys.version_info[:2] != (3, 9):
        print(f"{AVISO} este projeto foi testado no Python 3.9; você está no "
              f"{sys.version_info[0]}.{sys.version_info[1]}. Pode funcionar, "
              f"mas as versões abaixo foram fixadas para o 3.9.")
    if ".venv" not in sys.executable:
        print(f"{AVISO} você parece estar fora do ambiente virtual. "
              f"Rode 'source .venv/bin/activate' antes.")

    secao("Bibliotecas")
    for nome, modulo, pacote, para_que in BIBLIOTECAS:
        try:
            m = importlib.import_module(modulo)
            versao = getattr(m, "__version__", "?")
            print(f"{OK} {nome:<14} {versao:<12} {para_que}")
        except Exception as exc:
            print(f"{FALTA} {nome:<14} {'':<12} {para_que}")
            print(f"           instale com:  pip install {pacote}")
            print(f"           erro: {type(exc).__name__}: {str(exc)[:90]}")
            problemas.append(nome)

    secao("Modelos do YuNet e SFace (ficam em models/)")
    for nome, caminho in ONNX_LOCAIS:
        if caminho.exists():
            print(f"{OK} {nome:<20} {caminho.stat().st_size/1e6:.1f} MB")
        else:
            print(f"{FALTA} {nome:<20} baixe de github.com/opencv/opencv_zoo")
            print(f"           e salve em {caminho}")
            problemas.append(nome)

    secao("Pesos baixados automaticamente no primeiro uso")
    for nome, caminho, tamanho in PESOS:
        if caminho.exists():
            print(f"{OK} {nome:<24} já no disco ({caminho.stat().st_size/1e6:.0f} MB)")
        else:
            print(f"{AVISO} {nome:<24} ainda não baixado (~{tamanho}) — "
                  f"vem sozinho no primeiro uso")

    secao("Teste real: cada tecnologia numa imagem")
    amostra = _primeira_foto()
    if amostra is None:
        print(f"{AVISO} nenhuma imagem em fotos/ para testar. "
              f"Coloque ao menos uma e rode de novo.")
    else:
        print(f"  usando {amostra.name}\n")
        _testa_tecnologias(amostra, problemas)

    secao("Resumo")
    if problemas:
        print(f"  {len(problemas)} item(ns) faltando: {', '.join(problemas)}")
        print("  Veja as instruções de instalação no README.md")
        return 1
    print("  Tudo pronto. Rode:  python server.py")
    return 0


def _primeira_foto() -> Path | None:
    pasta = Path("fotos")
    if not pasta.is_dir():
        return None
    for p in sorted(pasta.iterdir()):
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            return p
    return None


def _testa_tecnologias(amostra: Path, problemas: list[str]) -> None:
    """Roda cada candidata de verdade. É o único jeito de saber se instalou."""
    try:
        import modelos as cat
    except Exception as exc:
        print(f"{FALTA} não consegui carregar modelos.py: {exc}")
        problemas.append("modelos.py")
        return

    for chave, dados in cat.CATALOGO.items():
        try:
            motor = cat.criar(chave)
            faces = motor.index_image(amostra)
            dim = faces[0].embedding.shape[0] if faces else 0
            print(f"{OK} {dados['rotulo']:<38} {len(faces):>3} rosto(s), vetor de {dim}")
        except Exception as exc:
            print(f"{FALTA} {dados['rotulo']:<38} {type(exc).__name__}: {str(exc)[:70]}")
            problemas.append(dados["rotulo"])


if __name__ == "__main__":
    raise SystemExit(main())
