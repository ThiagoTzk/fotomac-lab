"""
FotoMac Lab — índice do acervo, construído uma vez e reaproveitado.

No totem a indexação roda de madrugada e a busca roda com o visitante esperando.
Para o servidor web simular isso, o acervo é indexado ao iniciar e guardado em
cache no disco: reiniciar o servidor não paga os 40 segundos de novo.

O cache é invalidado sozinho quando o acervo muda (nome, tamanho ou data de
qualquer arquivo) ou quando os parâmetros do modelo mudam — senão ele devolveria
resultado calibrado com ajuste velho, que é pior do que não ter cache.
"""

from __future__ import annotations

import hashlib
import pickle
import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

import fotomac_face as fm

CACHE_DIR = Path("cache")
THUMBS_DIR = CACHE_DIR / "thumbs"
THUMB_SIDE = 420


@dataclass
class FotoIndexada:
    nome: str
    caminho: Path
    largura: int
    altura: int
    status: str                      # ok | sem_rosto | ilegivel
    faces: list = field(default_factory=list)   # list[fm.Face]
    segundos: float = 0.0


@dataclass
class Indice:
    fotos: list[FotoIndexada]
    matriz: np.ndarray               # (N, 128) todos os vetores
    origem: list[tuple[int, int]]    # (indice_da_foto, indice_do_rosto)
    segundos_indexacao: float
    assinatura: str

    @property
    def total_rostos(self) -> int:
        return self.matriz.shape[0]

    @property
    def fotos_com_rosto(self) -> int:
        return sum(1 for f in self.fotos if f.status == "ok")


def _assinatura(acervo: Path, arquivos: list[Path], modelo: str = "sface") -> str:
    """Impressão digital do acervo + dos parâmetros do modelo.

    Inclui os parâmetros de propósito: mudar MIN_DET_SCORE muda quais rostos
    existem, então o cache anterior deixa de valer.
    """
    h = hashlib.sha256()
    # o modelo entra na assinatura: cada tecnologia tem o seu índice, e trocar
    # de modelo não pode reaproveitar vetores de outro
    h.update(f"{modelo}|{fm.MAX_SIDE}|{fm.MIN_DET_SCORE}|{fm.MIN_FACE_SIDE}".encode())
    for p in arquivos:
        st = p.stat()
        h.update(f"{p.name}|{st.st_size}|{int(st.st_mtime)}".encode())
    return h.hexdigest()[:16]


def listar(acervo: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff", ".heic", ".heif"}
    return sorted(p for p in acervo.iterdir()
                  if p.is_file() and p.suffix.lower() in exts)


def gerar_thumb(foto: FotoIndexada) -> Path:
    """Miniatura limpa, SEM caixas desenhadas.

    As caixas dependem de qual rosto casou com a consulta da vez, e isso muda a
    cada busca. O navegador desenha por cima, com as coordenadas que a busca
    devolve — assim a mesma miniatura serve para todas as consultas.
    """
    destino = THUMBS_DIR / (foto.nome + ".jpg")
    if destino.exists():
        return destino
    img = cv2.imread(str(foto.caminho), cv2.IMREAD_REDUCED_COLOR_4)
    if img is None:
        return destino
    h, w = img.shape[:2]
    k = min(1.0, THUMB_SIDE / max(h, w))
    if k < 1.0:
        img = cv2.resize(img, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
    destino.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(destino), img, [cv2.IMWRITE_JPEG_QUALITY, 82])
    return destino


def _progresso_padrao(msg: str) -> None:
    # flush: sem isto o progresso da indexação fica preso no buffer quando a
    # saída vai para um arquivo, e parece que o servidor travou.
    print(msg, flush=True)


def construir(acervo: Path, engine, progresso=_progresso_padrao,
              modelo: str = "sface") -> Indice:
    arquivos = listar(acervo)
    assin = _assinatura(acervo, arquivos, modelo)
    cache = CACHE_DIR / f"indice_{modelo}_{assin}.pkl"

    if cache.exists():
        progresso(f"Índice de '{modelo}' em cache ({assin}) — nada a reindexar.")
        idx: Indice = pickle.loads(cache.read_bytes())
        for f in idx.fotos:
            gerar_thumb(f)
        return idx

    progresso(f"Indexando {len(arquivos)} foto(s) com '{modelo}'... "
              f"(uma vez só; fica em cache)")
    fotos: list[FotoIndexada] = []
    t0 = time.perf_counter()

    for n, caminho in enumerate(arquivos, 1):
        t = time.perf_counter()
        try:
            # Só preciso das DIMENSÕES aqui (as caixas viram fração da imagem no
            # navegador). Decodificar 20 MP inteiros para ler dois números custava
            # 0.08s por foto — o IMREAD_REDUCED_COLOR_8 devolve 1/8 e o erro de
            # até 7 px num original de milhares não muda fração nenhuma.
            pequena = cv2.imread(str(caminho), cv2.IMREAD_REDUCED_COLOR_8)
            if pequena is None:
                raise ValueError("OpenCV não conseguiu ler o arquivo")
            altura, largura = pequena.shape[0] * 8, pequena.shape[1] * 8
            faces = engine.index_image(caminho)
            fotos.append(FotoIndexada(caminho.name, caminho, largura, altura,
                                      "ok" if faces else "sem_rosto", faces,
                                      time.perf_counter() - t))
        except ValueError:
            fotos.append(FotoIndexada(caminho.name, caminho, 0, 0, "ilegivel",
                                      [], time.perf_counter() - t))
        if n % 25 == 0 or n == len(arquivos):
            progresso(f"  {n}/{len(arquivos)}")

    segundos = time.perf_counter() - t0

    vetores, origem = [], []
    for i, foto in enumerate(fotos):
        for j, face in enumerate(foto.faces):
            vetores.append(face.embedding)
            origem.append((i, j))
    matriz = (np.vstack(vetores).astype(np.float32) if vetores
              else np.empty((0, fm.EMBEDDING_DIM), np.float32))

    idx = Indice(fotos, matriz, origem, segundos, assin)
    CACHE_DIR.mkdir(exist_ok=True)
    cache.write_bytes(pickle.dumps(idx))
    progresso(f"Índice pronto: {idx.total_rostos} rostos em {segundos:.1f}s "
              f"({segundos/max(1,len(arquivos)):.3f}s por foto)")

    progresso("Gerando miniaturas...")
    for f in fotos:
        gerar_thumb(f)
    return idx


def buscar(idx: Indice, consulta_emb: np.ndarray) -> tuple[list[dict], float]:
    """Compara a consulta com todos os rostos. Devolve ranking por foto e tempo."""
    t0 = time.perf_counter()
    if idx.matriz.shape[0] == 0:
        return [], 0.0

    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        scores = idx.matriz @ consulta_emb
    if not np.isfinite(scores).all():
        raise RuntimeError("Similaridades inválidas no índice.")

    melhor: dict[int, tuple[float, int]] = {}
    for linha, (i_foto, i_rosto) in enumerate(idx.origem):
        s = float(scores[linha])
        if i_foto not in melhor or s > melhor[i_foto][0]:
            melhor[i_foto] = (s, i_rosto)
    decorrido = time.perf_counter() - t0

    ranking = []
    for i_foto, (s, i_rosto) in melhor.items():
        foto = idx.fotos[i_foto]
        x, y, w, h = foto.faces[i_rosto].bbox
        ranking.append({
            "arquivo": foto.nome,
            "similaridade": round(s, 4),
            "rostos": len(foto.faces),
            # caixa em fração da imagem: o navegador posiciona sem saber o tamanho
            "caixa": [round(x / foto.largura, 5), round(y / foto.altura, 5),
                      round(w / foto.largura, 5), round(h / foto.altura, 5)],
        })
    ranking.sort(key=lambda r: -r["similaridade"])
    return ranking, decorrido
