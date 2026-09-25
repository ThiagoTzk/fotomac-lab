"""
FotoMac Lab — servidor local de teste.

Abre uma página no navegador onde você:
  - tira a foto pela WEBCAM e ele procura você no acervo;
  - ou ENVIA uma imagem do disco e ele procura aquela pessoa no acervo.

O envio de arquivo é ferramenta de teste: no produto final o visitante só tira a
foto no totem. Está aqui para você comparar modelos sem depender de estar na
frente da câmera.

Só biblioteca padrão do Python — nenhuma dependência nova. Escuta apenas em
127.0.0.1: as fotos do fotógrafo são privadas e não podem ficar expostas na rede.

Uso:
  .venv/bin/python server.py
  .venv/bin/python server.py --porta 8000 --acervo fotos
"""

from __future__ import annotations

import argparse
import errno
import json
import time
import unicodedata
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import cv2
import numpy as np

import fotomac_face as fm
import indice as idx_mod
import painel
import gabarito_io
import modelos as cat
import estado_modelos
from painel_page import PAGINA_PAINEL
from marcar_page import PAGINA_MARCAR
import ui_comum

# Tamanho máximo aceito num envio. Uma foto de 20 MP em JPEG não passa de ~15 MB;
# acima disso é engano ou arquivo errado.
MAX_UPLOAD = 25 * 1024 * 1024

ESTADO: dict = {}


class Handler(BaseHTTPRequestHandler):
    # silencia o log de uma linha por requisição, que polui o terminal
    def log_message(self, fmt, *args):
        pass

    # ------------------------------------------------------------------ GET
    def do_GET(self):
        caminho = unquote(urlparse(self.path).path)

        if caminho in ("/", "/index.html"):
            return self._pagina(PAGINA, "/")

        if caminho == "/marcar":
            return self._pagina(PAGINA_MARCAR, "/marcar")

        if caminho == "/marcar/gabarito":
            d = gabarito_io.carregar()
            return self._json({"pessoas": gabarito_io.resumo(d),
                               "acervo_total": len(ESTADO["indice"].fotos)})

        if caminho == "/painel":
            return self._pagina(PAGINA_PAINEL, "/painel")

        if caminho == "/painel/dados":
            # Montado a cada requisição, de propósito: assim basta rodar o
            # benchmark com um modelo novo e recarregar a página.
            try:
                return self._json(painel.montar())
            except Exception as exc:
                return self._json({"erro": f"{type(exc).__name__}: {exc}"}, 500)

        if caminho == "/modelos":
            testados = estado_modelos.resumo()
            n = len(ESTADO["indice"].fotos)
            itens = []
            for m in cat.listar():
                t = testados.get(m["chave"], {})
                itens.append({**m,
                    "ativo": m["chave"] == ESTADO["modelo"],
                    "carregado": m["chave"] in ESTADO["motores"],
                    "verificado": bool(t.get("verificado")),
                    "marcadas": t.get("marcadas", 0),
                    "pessoas": t.get("pessoas", []),
                    "ultimo_uso": t.get("ultimo_uso", ""),
                    "estimativa_min": round(cat.estimativa_minutos(m["chave"], n), 1)})
            return self._json({"modelos": itens, "ativo": ESTADO["modelo"]})

        if caminho == "/estado":
            idx = ESTADO["indice"]
            return self._json({
                "acervo": str(ESTADO["acervo"]),
                "fotos": len(idx.fotos),
                "fotos_com_rosto": idx.fotos_com_rosto,
                "rostos": idx.total_rostos,
                "segundos_indexacao": round(idx.segundos_indexacao, 2),
                "limiar": fm.COSINE_THRESHOLD,
                "modelo": ESTADO["modelo"],
                "modelo_rotulo": cat.CATALOGO[ESTADO["modelo"]]["rotulo"],
                "parametros": {"max_side": fm.MAX_SIDE,
                               "min_det_score": fm.MIN_DET_SCORE,
                               "min_face_side": fm.MIN_FACE_SIDE},
            })

        if caminho.startswith("/thumb/"):
            return self._arquivo(idx_mod.THUMBS_DIR / (caminho[len("/thumb/"):] + ".jpg"))

        if caminho.startswith("/consulta/"):
            return self._arquivo(Path("consultas").resolve()
                                 / caminho[len("/consulta/"):])

        if caminho == "/consultas":
            pasta = Path("consultas")
            nomes = sorted((p.name for p in pasta.glob("*.jpg")), reverse=True) \
                if pasta.is_dir() else []
            return self._json({"consultas": nomes,
                               "acervo": sorted(f.nome for f in ESTADO["indice"].fotos)})

        if caminho.startswith("/foto/"):
            return self._arquivo(ESTADO["acervo"] / caminho[len("/foto/"):])

        self.send_error(404)

    # ----------------------------------------------------------------- POST
    def do_POST(self):
        rota = urlparse(self.path).path

        if rota == "/modelo/trocar":
            return self._trocar_modelo()
        if rota == "/marcar/ranking":
            return self._ranking_para_marcar()
        if rota == "/marcar/salvar":
            return self._salvar_marcacao()
        if rota != "/buscar":
            return self.send_error(404)

        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho <= 0 or tamanho > MAX_UPLOAD:
            return self._json({"ok": False,
                               "erro": "Arquivo vazio ou grande demais."}, 400)

        bruto = self.rfile.read(tamanho)
        origem = self.headers.get("X-Origem", "envio")   # "webcam" ou "envio"

        t0 = time.perf_counter()
        img = cv2.imdecode(np.frombuffer(bruto, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return self._json({"ok": False, "erro":
                               "Não consegui abrir esta imagem. HEIC do iPhone não "
                               "é lido pelo OpenCV — converta para JPEG."}, 400)

        # Grava a consulta para você poder conferir depois qual foto foi usada.
        pasta = Path("consultas"); pasta.mkdir(exist_ok=True)
        nome = f"{origem}_{time.strftime('%Y-%m-%d_%H%M%S')}.jpg"
        cv2.imwrite(str(pasta / nome), img, [cv2.IMWRITE_JPEG_QUALITY, 92])

        # A ordem importa: os dois erros de negócio primeiro, o pega-tudo por
        # último. Invertido, o pega-tudo engole os específicos e a pessoa recebe
        # um traceback no lugar de "chegue mais perto".
        try:
            face = ESTADO["engine"].query_face(pasta / nome)
        except fm.NoFaceDetected:
            return self._json({"ok": False, "erro":
                               "Nenhum rosto encontrado. Chegue mais perto e olhe "
                               "para a câmera."}, 200)
        except fm.LowQualityFace:
            return self._json({"ok": False, "erro":
                               "Rosto sem qualidade suficiente. Procure mais luz e "
                               "enquadre melhor o rosto."}, 200)
        except Exception as exc:
            # Falha do motor vira mensagem na tela. Antes subia até o handler e
            # o navegador só via a conexão cair, sem pista nenhuma.
            return self._json({"ok": False, "erro":
                               f"O modelo falhou nesta imagem — "
                               f"{type(exc).__name__}: {exc}"}, 200)

        ranking, busca_s = idx_mod.buscar(ESTADO["indice"], face.embedding)
        altura, largura = img.shape[:2]
        x, y, w, h = face.bbox

        return self._json({
            "ok": True,
            "consulta": {
                "arquivo": nome,
                "confianca": round(face.det_score, 3),
                "caixa": [round(x / largura, 5), round(y / altura, 5),
                          round(w / largura, 5), round(h / altura, 5)],
            },
            "busca_ms": round(busca_s * 1000, 2),
            "total_ms": round((time.perf_counter() - t0) * 1000, 1),
            "limiar": fm.COSINE_THRESHOLD,
            "resultados": ranking,
        })

    # ---------------------------------------------------------- modelos

    def _trocar_modelo(self):
        """Carrega (e indexa, se preciso) a tecnologia escolhida.

        A indexação de um modelo novo leva minutos. É feita aqui, de forma
        síncrona e com o custo avisado antes na tela, em vez de fingir que a
        troca é instantânea.
        """
        try:
            req = self._corpo_json()
        except (ValueError, json.JSONDecodeError) as exc:
            return self._json({"ok": False, "erro": str(exc)}, 400)

        chave = req.get("modelo", "")
        if chave not in cat.CATALOGO:
            return self._json({"ok": False, "erro": f"Modelo desconhecido: {chave}"}, 400)

        if chave not in ESTADO["motores"]:
            try:
                t0 = time.perf_counter()
                motor = cat.criar(chave)
                indice = idx_mod.construir(ESTADO["acervo"], motor, modelo=chave)
                ESTADO["motores"][chave] = motor
                ESTADO["indices"][chave] = indice
                estado_modelos.registrar(chave, "", 0, 0, indexado=True)
                print(f"Modelo '{chave}' pronto em {time.perf_counter()-t0:.0f}s "
                      f"({indice.total_rostos} rostos)", flush=True)
            except Exception as exc:
                return self._json({"ok": False,
                                   "erro": f"{type(exc).__name__}: {exc}"}, 500)

        ESTADO["modelo"] = chave
        ESTADO["engine"] = ESTADO["motores"][chave]
        ESTADO["indice"] = ESTADO["indices"][chave]
        idx = ESTADO["indice"]
        return self._json({"ok": True, "modelo": chave,
                           "rotulo": cat.CATALOGO[chave]["rotulo"],
                           "rostos": idx.total_rostos,
                           "fotos_com_rosto": idx.fotos_com_rosto,
                           "segundos_indexacao": round(idx.segundos_indexacao, 1)})

    # ------------------------------------------------------ marcação manual

    def _corpo_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > 8 * 1024 * 1024:
            raise ValueError("corpo vazio ou grande demais")
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def _ranking_para_marcar(self):
        """Devolve o ranking de uma consulta já conhecida, fundido com o que a
        pessoa já marcou antes — para ela continuar de onde parou."""
        try:
            req = self._corpo_json()
        except (ValueError, json.JSONDecodeError) as exc:
            return self._json({"ok": False, "erro": str(exc)}, 400)

        consulta = req.get("consulta", "")
        pessoa = req.get("pessoa", "")
        quantos = min(int(req.get("quantos", 80)), 400)

        alvo = self._resolver_consulta(consulta)
        if alvo is None:
            return self._json({"ok": False,
                               "erro": f"Não encontrei a foto de consulta: {consulta}"}, 400)
        try:
            face = ESTADO["engine"].query_face(alvo)
        except (fm.NoFaceDetected, fm.LowQualityFace) as exc:
            return self._json({"ok": False, "erro": str(exc)}, 200)
        except Exception as exc:
            # Qualquer falha do motor precisa virar mensagem na tela. Antes ela
            # subia até o handler e o navegador via a conexão cair, sem pista.
            return self._json({"ok": False, "erro":
                               f"O modelo falhou nesta imagem — "
                               f"{type(exc).__name__}: {exc}"}, 200)

        ranking, busca_s = idx_mod.buscar(ESTADO["indice"], face.embedding)

        # As marcações do MODELO ATIVO, só dele. Carregar as de outro modelo
        # pré-marcaria o ranking com as respostas de uma tecnologia diferente e
        # contaminaria justamente o que este teste isola.
        d = gabarito_io.carregar()
        c = gabarito_io.marcacoes(d, pessoa, ESTADO["modelo"])
        ja_sim, ja_err, ja_nao = (set(c["aparece_em"]), set(c["rosto_errado"]),
                                  set(c["nao_aparece_em"]))

        itens = []
        for r in ranking[:quantos]:
            nome = r["arquivo"]
            marca = ("sim" if nome in ja_sim else
                     "errado" if nome in ja_err else
                     "nao" if nome in ja_nao else None)
            # A PROPOSTA do modelo: o que ele responderia sozinho, no limiar em
            # uso. Vai junto para a tela poder mostrar a resposta dele e o
            # Thiago só confirmar ou corrigir — mas fica num campo separado de
            # `marca`, porque proposta não é gabarito. Só vira gabarito quando
            # alguém confirma.
            proposta = "sim" if r["similaridade"] >= fm.COSINE_THRESHOLD else "nao"
            itens.append({**r, "marca": marca, "proposta": proposta})
        return self._json({
            "ok": True,
            "consulta": consulta,
            "pessoa": pessoa,
            "modelo": ESTADO["modelo"],
            "modelo_rotulo": cat.CATALOGO[ESTADO["modelo"]]["rotulo"],
            "ja_marcadas": len(ja_sim | ja_err | ja_nao),
            "caixa_consulta": [round(v, 5) for v in self._caixa_fracao(alvo, face)],
            "consulta_url": self._url_da_consulta(consulta),
            "busca_ms": round(busca_s * 1000, 2),
            "limiar": fm.COSINE_THRESHOLD,
            "total_no_acervo": len(ESTADO["indice"].fotos),
            "itens": itens,
        })

    def _salvar_marcacao(self):
        try:
            req = self._corpo_json()
        except (ValueError, json.JSONDecodeError) as exc:
            return self._json({"ok": False, "erro": str(exc)}, 400)

        pessoa = (req.get("pessoa") or "").strip()
        if not pessoa:
            return self._json({"ok": False, "erro": "Dê um nome à pessoa."}, 400)

        d = gabarito_io.carregar()
        d = gabarito_io.registrar_marcacao(
            d, pessoa, req.get("descricao", ""), req.get("consulta", ""),
            req.get("sim", []), req.get("nao", []),
            req.get("menor_similaridade_revisada"),
            req.get("rosto_errado", []),
            int(req.get("aceitas_em_bloco", 0) or 0),
            ESTADO["modelo"])
        # o acervo deixa de ser "completo por declaração": agora há conferência
        # foto a foto, e é ela que vale.
        d["acervo_completo"] = False
        gabarito_io.salvar(d)
        # o selo de "verificado" do modelo ativo depende desta conferência
        estado_modelos.registrar(ESTADO["modelo"], pessoa,
                                 len(req.get("sim", [])) + len(req.get("nao", []))
                                 + len(req.get("rosto_errado", [])),
                                 int(req.get("ranking_visto", 0)))
        return self._json({"ok": True, "modelo": ESTADO["modelo"],
                           "rotulo": cat.CATALOGO[ESTADO["modelo"]]["rotulo"],
                           "pessoas": gabarito_io.resumo(d, ESTADO["modelo"]),
                           "modelos": estado_modelos.resumo()})

    def _resolver_consulta(self, nome: str) -> Path | None:
        """A consulta pode ser uma foto do acervo ou uma imagem em consultas/.

        Compara os nomes normalizados em NFC: o macOS grava acento em NFD e o
        navegador manda NFC, e sem isso um nome com acento nunca é encontrado.
        """
        alvo_nfc = unicodedata.normalize("NFC", nome)
        for base in (ESTADO["acervo"], Path("consultas").resolve()):
            if not base.is_dir():
                continue
            direto = (base / nome).resolve()
            if direto.is_file() and direto.parent == base:
                return direto
            for candidato in base.iterdir():
                if (candidato.is_file()
                        and unicodedata.normalize("NFC", candidato.name) == alvo_nfc):
                    return candidato
        return None

    def _url_da_consulta(self, nome: str) -> str:
        alvo = self._resolver_consulta(nome)
        if alvo is None:
            return ""
        return ("/foto/" if alvo.parent == ESTADO["acervo"]
                else "/consulta/") + nome

    @staticmethod
    def _caixa_fracao(caminho: Path, face) -> list[float]:
        img = cv2.imread(str(caminho), cv2.IMREAD_REDUCED_COLOR_8)
        if img is None:
            return [0, 0, 0, 0]
        h, w = img.shape[0] * 8, img.shape[1] * 8
        x, y, bw, bh = face.bbox
        return [x / w, y / h, bw / w, bh / h]

    def _pagina(self, modelo_html: str, rota: str):
        """Monta a página com o CSS e o menu compartilhados.

        Substituir na hora de servir, em vez de duplicar o CSS em cada arquivo,
        é o que garante que as três telas continuem iguais quando uma mudar.
        """
        direita = f"Modelo: {cat.CATALOGO[ESTADO['modelo']]['rotulo']}"
        html = (modelo_html
                .replace("/*__CSS_BASE__*/", ui_comum.CSS_BASE)
                .replace("<!--__TOPO__-->", ui_comum.topo(rota, direita)))
        return self._envia(html.encode("utf-8"), "text/html; charset=utf-8")

    # -------------------------------------------------------------- auxiliar
    def _envia(self, corpo: bytes, tipo: str, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, dados: dict, status: int = 200):
        self._envia(json.dumps(dados, ensure_ascii=False).encode("utf-8"),
                    "application/json; charset=utf-8", status)

    def _arquivo(self, caminho: Path):
        # Impede sair da pasta servida via "../" no caminho da URL.
        try:
            caminho = caminho.resolve()
            raiz = caminho.parent.resolve()
            if not caminho.is_file() or raiz != caminho.parent.resolve():
                raise FileNotFoundError
        except (OSError, FileNotFoundError):
            return self.send_error(404)
        tipos = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                 ".webp": "image/webp"}
        self._envia(caminho.read_bytes(),
                    tipos.get(caminho.suffix.lower(), "application/octet-stream"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Servidor local de teste do FotoMac.")
    ap.add_argument("--acervo", type=Path, default=Path("fotos"))
    ap.add_argument("--porta", type=int, default=8777)
    ap.add_argument("--sem-abrir", action="store_true",
                    help="não abrir o navegador automaticamente")
    args = ap.parse_args()

    engine = fm.FaceEngine()
    indice = idx_mod.construir(args.acervo, engine, modelo="sface")

    ESTADO.update(engine=engine, indice=indice, acervo=args.acervo.resolve(),
                  modelo="sface", motores={"sface": engine},
                  indices={"sface": indice})
    estado_modelos.registrar("sface", "", 0, 0, indexado=True)

    endereco = f"http://127.0.0.1:{args.porta}/"
    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", args.porta), Handler)
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE:
            raise
        print(f"\nA porta {args.porta} já está em uso.")
        print("Provavelmente há outro servidor do FotoMac rodando. Ou você abre o")
        print(f"que já está no ar em {endereco}, ou escolhe outra porta:")
        print(f"  .venv/bin/python server.py --porta {args.porta + 1}")
        print("\nPara descobrir e encerrar o que está usando a porta:")
        print(f"  lsof -ti tcp:{args.porta} | xargs kill")
        return 1
    print(f"\nServidor no ar: {endereco}")
    print(f"  {indice.total_rostos} rostos | {indice.fotos_com_rosto} de "
          f"{len(indice.fotos)} fotos | limiar {fm.COSINE_THRESHOLD}")
    print("  Ctrl+C para parar.\n")
    if not args.sem_abrir:
        webbrowser.open(endereco)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado.")
    return 0


PAGINA = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FotoMac — busca por rosto</title>
<style>
/*__CSS_BASE__*/
  /* ---------------- seletor de tecnologia, com selo de verificado -------- */
  .mods{display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));
    margin:10px 0 4px}
  .mod{border:2px solid var(--line);border-radius:11px;padding:11px 13px;cursor:pointer;
    background:var(--card);transition:border-color .12s,background .12s;position:relative}
  .mod:hover{border-color:var(--acc)}
  .mod.ativo{border-color:var(--acc);background:color-mix(in srgb,var(--acc) 9%,transparent)}
  .mod.ocupado{opacity:.55;cursor:wait}
  .mod .nome{font-weight:700;font-size:13.5px;padding-right:26px}
  .mod .desc{color:var(--muted);font-size:11.5px;margin-top:3px;line-height:1.4}
  .mod .pe{display:flex;gap:7px;margin-top:7px;flex-wrap:wrap;align-items:center}
  .selo{font-size:10px;font-weight:800;padding:2px 7px;border-radius:99px;
    border:1px solid var(--line);color:var(--muted)}
  .selo.ok{background:var(--ok-bg);color:var(--ok);border-color:var(--ok)}
  .selo.fab{background:transparent;color:var(--acc);border-color:var(--acc)}
  .mod .check{position:absolute;top:9px;right:10px;font-size:15px;line-height:1}
  .mod .check.on{color:var(--ok)}
  .mod .check.off{color:var(--line)}
  .spin{display:inline-block;width:15px;height:15px;border:2px solid var(--line);
    border-top-color:var(--acc);border-radius:50%;animation:g .7s linear infinite;vertical-align:-3px}
  @keyframes g{to{transform:rotate(360deg)}}
  dialog{border:none;border-radius:12px;padding:0;background:var(--card);max-width:94vw;color:var(--ink)}
  dialog::backdrop{background:rgba(0,0,0,.8)}
  dialog img{display:block;max-width:92vw;max-height:82vh}
  dialog .cap{padding:10px 14px;font-size:13px;font-family:ui-monospace,Menlo,monospace}
  @media (max-width:520px){.wrap{padding:14px}.grid{grid-template-columns:repeat(auto-fill,minmax(140px,1fr))}}
</style>
</head>
<body>
<!--__TOPO__-->
<div class="wrap">
  <h1>FotoMac — busca por rosto</h1>
  <p class="sub" id="sub">carregando o índice...</p>

  <div class="stats" id="estado"></div>

  <div class="panel">
    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap">
      <div><b>Tecnologia em teste</b>
        <div style="color:var(--muted);font-size:12.5px">O visto verde marca os que
          você já conferiu foto a foto, na tela de marcação.</div></div>
      <span id="mod-status" style="font-size:12.5px;color:var(--muted)"></span>
    </div>
    <div class="mods" id="mods"></div>
  </div>

  <h2>De onde vem a foto de consulta</h2>
  <div class="tabs" role="tablist">
    <button class="tab" id="tab-cam" role="tab" aria-selected="true">Webcam</button>
    <button class="tab" id="tab-env" role="tab" aria-selected="false">Enviar arquivo (teste)</button>
  </div>

  <div class="panel" id="pane-cam">
    <div class="camwrap"><video id="video" playsinline muted></video></div>
    <div class="row">
      <button class="btn" id="b-ligar">Ligar a câmera</button>
      <button class="btn" id="b-tirar" disabled>Tirar foto e buscar</button>
      <button class="btn sec" id="b-desligar" disabled>Desligar</button>
    </div>
    <p style="text-align:center;color:var(--muted);font-size:12.5px;margin:12px 0 0">
      O navegador vai pedir permissão da câmera. A imagem não sai da sua máquina:
      o servidor roda em 127.0.0.1.</p>
  </div>

  <div class="panel hide" id="pane-env">
    <div class="aviso"><b>Só para teste.</b> No produto final o visitante tira a foto
      no totem. O envio de arquivo existe para você comparar modelos sem precisar
      estar na frente da câmera.</div>
    <div class="drop" id="drop">
      Arraste uma imagem aqui, ou clique para escolher.<br>
      <span style="font-size:12.5px">JPG ou PNG. HEIC do iPhone não é lido.</span>
    </div>
    <input type="file" id="file" accept="image/*" class="hide">
  </div>

  <div id="saida"></div>
</div>

<dialog id="lb"><img id="lbimg" alt=""><div class="cap" id="lbcap"></div></dialog>

<script>
let LIMIAR = 0.45, ULTIMO = null, STREAM = null;

const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

// ------------------------------------------------------------------ estado
async function carregarEstado(){
  const e = await (await fetch('/estado')).json();
  LIMIAR = e.limiar;
  $('#sub').textContent = `${e.modelo_rotulo} · acervo ${e.acervo} · limiar ${e.limiar} · `
    + `MAX_SIDE=${e.parametros.max_side}, MIN_DET_SCORE=${e.parametros.min_det_score}, `
    + `MIN_FACE_SIDE=${e.parametros.min_face_side}`;
  $('#estado').innerHTML = `
    <div class="stat"><b>${e.fotos}</b><span>fotos no acervo</span></div>
    <div class="stat"><b>${e.rostos}</b><span>rostos indexados</span></div>
    <div class="stat"><b>${e.fotos_com_rosto}</b><span>fotos com rosto</span></div>
    <div class="stat"><b>${e.segundos_indexacao}s</b><span>indexação (uma vez)</span></div>`;
}

// -------------------------------------------------------------------- abas
function aba(qual){
  const cam = qual === 'cam';
  $('#tab-cam').setAttribute('aria-selected', cam);
  $('#tab-env').setAttribute('aria-selected', !cam);
  $('#pane-cam').classList.toggle('hide', !cam);
  $('#pane-env').classList.toggle('hide', cam);
}
$('#tab-cam').onclick = () => aba('cam');
$('#tab-env').onclick = () => aba('env');

// ------------------------------------------------------------------ webcam
$('#b-ligar').onclick = async () => {
  try{
    STREAM = await navigator.mediaDevices.getUserMedia(
      {video:{width:{ideal:1280}, height:{ideal:720}, facingMode:'user'}, audio:false});
    $('#video').srcObject = STREAM;
    await $('#video').play();
    $('#b-tirar').disabled = false; $('#b-desligar').disabled = false;
    $('#b-ligar').disabled = true;
  }catch(err){
    $('#saida').innerHTML = `<div class="panel erro">Não consegui abrir a câmera:
      ${esc(err.message)}<br><br>No Safari e no Chrome a permissão é pedida na
      primeira vez. Se você negou antes, libere nas preferências do site.</div>`;
  }
};
$('#b-desligar').onclick = () => {
  if (STREAM) STREAM.getTracks().forEach(t => t.stop());
  STREAM = null; $('#video').srcObject = null;
  $('#b-tirar').disabled = true; $('#b-desligar').disabled = true; $('#b-ligar').disabled = false;
};
$('#b-tirar').onclick = () => {
  const v = $('#video');
  const c = document.createElement('canvas');
  c.width = v.videoWidth; c.height = v.videoHeight;
  const ctx = c.getContext('2d');
  // Espelha na horizontal: a pessoa se vê como num espelho, que é o que o totem faz.
  ctx.translate(c.width, 0); ctx.scale(-1, 1);
  ctx.drawImage(v, 0, 0);
  c.toBlob(b => enviar(b, 'webcam'), 'image/jpeg', 0.92);
};

// ------------------------------------------------------------------- envio
$('#drop').onclick = () => $('#file').click();
$('#file').onchange = e => { if (e.target.files[0]) enviar(e.target.files[0], 'envio'); };
['dragenter','dragover'].forEach(n => $('#drop').addEventListener(n, e => {
  e.preventDefault(); $('#drop').classList.add('over'); }));
['dragleave','drop'].forEach(n => $('#drop').addEventListener(n, e => {
  e.preventDefault(); $('#drop').classList.remove('over'); }));
$('#drop').addEventListener('drop', e => {
  const f = e.dataTransfer.files[0]; if (f) enviar(f, 'envio'); });

// ------------------------------------------------------------------- busca
async function enviar(blob, origem){
  $('#saida').innerHTML = `<div class="panel"><span class="spin"></span>
    &nbsp;procurando no acervo...</div>`;
  const url = URL.createObjectURL(blob);
  let r;
  try{
    r = await (await fetch('/buscar', {method:'POST', headers:{'X-Origem':origem}, body:blob})).json();
  }catch(err){
    $('#saida').innerHTML = `<div class="panel erro">Falha ao falar com o servidor:
      ${esc(err.message)}</div>`; return;
  }
  if (!r.ok){
    $('#saida').innerHTML = `<div class="panel erro">${esc(r.erro)}</div>`; return;
  }
  ULTIMO = {r, url};
  render();
}

function render(){
  const {r, url} = ULTIMO;
  const [bx,by,bw,bh] = r.consulta.caixa;
  const n = r.resultados.filter(x => x.similaridade >= LIMIAR).length;

  $('#saida').innerHTML = `
    <h2>Resultado</h2>
    <div class="panel" style="display:flex;gap:18px;flex-wrap:wrap;align-items:flex-start">
      <div class="qprev">
        <img src="${url}" alt="consulta">
        <div class="box" style="left:${bx*100}%;top:${by*100}%;width:${bw*100}%;height:${bh*100}%"></div>
      </div>
      <div style="flex:1;min-width:250px">
        <p style="margin:0 0 8px"><b style="font-size:23px" id="cnt">${n}</b>
          foto(s) do acervo com esta pessoa, no limiar
          <span class="tval" id="tv">${LIMIAR.toFixed(3)}</span>.</p>
        <p style="margin:0 0 10px;color:var(--muted);font-size:13px">
          Busca em <b>${r.busca_ms} ms</b> · ida e volta completa ${r.total_ms} ms ·
          confiança do detector na consulta ${r.consulta.confianca}<br>
          A caixa verde é o rosto escolhido para representar você.</p>
        <div class="slider">
          <label for="t">Limiar:</label><br>
          <input type="range" id="t" min="0" max="1" step="0.001" value="${LIMIAR}">
        </div>
      </div>
    </div>
    <h2>Fotos encontradas</h2>
    <div class="grid" id="g">${r.resultados.map(card).join('')}</div>`;

  $('#t').oninput = e => { LIMIAR = parseFloat(e.target.value); repinta(); };
  repinta();
}

function card(x){
  const [bx,by,bw,bh] = x.caixa;
  return `<div class="card" data-sim="${x.similaridade}">
    <div class="ph">
      <img src="/thumb/${encodeURIComponent(x.arquivo)}"
           data-full="/foto/${encodeURIComponent(x.arquivo)}"
           data-cap="${esc(x.arquivo)} — ${x.similaridade}" alt="" loading="lazy">
      <div class="box" style="left:${bx*100}%;top:${by*100}%;width:${bw*100}%;height:${bh*100}%"></div>
    </div>
    <div class="meta">
      <div class="fname">${esc(x.arquivo)}</div>
      <div class="simrow"><span class="sim">${x.similaridade.toFixed(4)}</span>
        <span class="tag"></span></div>
      <div style="color:var(--muted);font-size:11px;margin-top:3px">${x.rostos} rosto(s) na foto</div>
    </div></div>`;
}

// Só repinta: as similaridades já vieram do servidor, o limiar não refaz busca.
function repinta(){
  const g = $('#g'); if (!g) return;
  let n = 0;
  for (const c of g.children){
    const s = parseFloat(c.dataset.sim), t = c.querySelector('.tag');
    const bate = s >= LIMIAR;
    c.classList.toggle('match', bate); c.classList.toggle('miss', !bate);
    t.textContent = bate ? 'é você' : '—';
    if (bate) n++;
  }
  $('#cnt').textContent = n;
  $('#tv').textContent = LIMIAR.toFixed(3);
}

// ---------------------------------------------------------------- lightbox
document.addEventListener('click', e => {
  const img = e.target.closest('img[data-full]'); if (!img) return;
  $('#lbimg').src = img.dataset.full; $('#lbcap').textContent = img.dataset.cap;
  $('#lb').showModal();
});
$('#lb').addEventListener('click', () => $('#lb').close());

carregarEstado();
carregaModelos();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
