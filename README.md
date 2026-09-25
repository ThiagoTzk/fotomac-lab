# FotoMac Lab

Bancada de teste para escolher a tecnologia de reconhecimento facial do FOTOMAC.
Cada candidata é submetida ao mesmo acervo, conferida foto a foto à mão, e recebe
uma nota comparável.

**Resultado do Teste 1:** InsightFace 97,6 · YuNet+SFace 89,5 · ArcFace 64,0 ·
Facenet512 60,3 · VGG-Face 57,1 — ver [docs/TESTE-1.md](docs/TESTE-1.md).

## Começando

```bash
source .venv/bin/activate
python server.py            # abre http://127.0.0.1:8777/
```

Três telas:

| Tela | Para que serve |
|---|---|
| `/` | tirar foto na webcam ou enviar imagem e buscar no acervo |
| `/marcar` | conferir foto a foto e montar o gabarito de cada tecnologia |
| `/painel` | ranking e gráficos — é o que vai para a apresentação |

Depois de conferir uma tecnologia, gere a nota:

```bash
python avaliar_todos.py --rotulo "Teste 1"
```

## Os arquivos

### Motor e tecnologias
| Arquivo | O que faz |
|---|---|
| `fotomac_face.py` | motor YuNet + SFace: detecta, alinha, gera o vetor |
| `modelos.py` | catálogo das candidatas, todas na configuração de fábrica |
| `indice.py` | indexa o acervo e guarda em cache, um índice por tecnologia |

### Medição
| Arquivo | O que faz |
|---|---|
| `gabarito_io.py` | lê e grava o gabarito (por tecnologia, quatro estados) |
| `metricas.py` | AUC, mAP, intrusos — métricas que não dependem de limiar |
| `scoring.py` | notas e validação cruzada |
| `avaliar_todos.py` | calcula a nota de cada tecnologia e monta o ranking |
| `estado_modelos.py` | registra quais tecnologias já foram conferidas |

### Interface
| Arquivo | O que faz |
|---|---|
| `server.py` | servidor local (só 127.0.0.1) com as três telas |
| `marcar_page.py` | a tela de conferência |
| `painel.py` / `painel_page.py` | o painel de comparação |
| `capture.py` | captura pela webcam sem navegador |
| `diagnostico.py` | investiga por que um detector não achou rosto numa foto |
| `verificar_instalacao.py` | confere o ambiente e roda cada tecnologia numa imagem |

### Dados
| Pasta | Conteúdo |
|---|---|
| `fotos/` | o acervo (388 fotos, privado) |
| `consultas/` | fotos de consulta tiradas ou enviadas |
| `models/` | os `.onnx` do YuNet e do SFace |
| `gabarito.json` | a verdade conferida à mão, separada por tecnologia |
| `cache/` | índices e miniaturas — descartável, regenera sozinho |
| `resultados/` | rankings e CSVs de cada rodada |
| `backups/` | cópias do gabarito antes de cada limpeza |
| `docs/` | documentação; `entregaveis/` tem os PDFs |

---

# Manual de instalação

Escrito para quem vai rodar este projeto numa máquina nova, do zero. Nenhum passo
depende dos outros arquivos do repositório — só deste texto.

**Tempo estimado:** 15 a 40 minutos, quase tudo download.
**Espaço em disco:** cerca de **2,5 GB** (bibliotecas 1 GB + pesos dos modelos 1,5 GB).

## Passo 1 — Python 3.9

O projeto foi desenvolvido e medido no **Python 3.9**. Versões mais novas
provavelmente funcionam, mas as versões de biblioteca abaixo foram fixadas para o
3.9 e não há garantia fora dele.

```bash
python3 --version      # precisa mostrar 3.9.x
```

Se não tiver, no macOS: `brew install python@3.9`. No Windows e no Linux, baixe em
python.org ou use o gerenciador da distribuição.

## Passo 2 — ambiente virtual

Ambiente virtual é uma pasta com uma cópia isolada do Python e das bibliotecas. Serve
para este projeto não interferir em outros da mesma máquina.

```bash
cd fotomac-lab
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

Depois de ativar, o terminal mostra `(.venv)` no início da linha. **Todos os comandos
seguintes assumem o ambiente ativo.**

```bash
pip install --upgrade pip
```

## Passo 3 — bibliotecas base

```bash
pip install numpy==2.0.2 opencv-python==5.0.0.93 opencv-contrib-python==5.0.0.93
```

| Pacote | Para que serve |
|---|---|
| `numpy` | todas as contas com vetores |
| `opencv-python` | ler imagens e rodar o YuNet e o SFace |
| `opencv-contrib-python` | módulos extras do OpenCV usados no projeto |

## Passo 4 — os modelos

Cada bloco abaixo é independente. Instale **todos** para reproduzir o Teste 1, ou só
os que quiser avaliar.

### 4.1 YuNet + SFace (OpenCV) — já vem com o Passo 3

O código dos dois está no OpenCV, mas os **pesos** são dois arquivos `.onnx` que
precisam ser baixados à mão, do repositório oficial `opencv/opencv_zoo`:

```bash
mkdir -p models
curl -L -o models/face_detection_yunet_2023mar.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
curl -L -o models/face_recognition_sface_2021dec.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
```

São cerca de 39 MB somados. **É o único download manual do projeto** — os demais são
automáticos.

### 4.2 DeepFace — Facenet512, ArcFace e VGG-Face

```bash
pip install deepface==0.0.101 tf-keras==2.20.1
```

O DeepFace instala o TensorFlow junto (cerca de 600 MB). O `tf-keras` é obrigatório:
sem ele, o DeepFace quebra com as versões novas do Keras.

> **Atenção — limitação conhecida.** O detector padrão do DeepFace é a cascata de
> Haar do OpenCV, e o `opencv-python 5.0` não distribui mais esses arquivos. Os três
> modelos falham com *"Confirm that opencv is installed on your environment"*. Por
> isso o projeto declara `detector_backend="retinaface"` (Passo 4.3), que é
> parâmetro da própria documentação do DeepFace. **Instalar o RetinaFace não é
> opcional se você quiser usar os modelos do DeepFace.**

### 4.3 RetinaFace — o detector do DeepFace

```bash
pip install retina-face==0.0.18
```

### 4.4 InsightFace — o vencedor do Teste 1

```bash
pip install insightface==1.0.1 onnxruntime==1.19.2
```

O `onnxruntime` é o motor que executa os modelos do InsightFace. Sem ele a biblioteca
importa mas não roda.

> Em algumas máquinas o `insightface` precisa compilar uma parte em C++ e pede
> ferramentas de build. No macOS: `xcode-select --install`. No Ubuntu/Debian:
> `sudo apt install build-essential python3-dev`. No Windows: instale o
> *Build Tools for Visual Studio*.

## Passo 5 — tudo de uma vez (atalho)

```bash
pip install numpy==2.0.2 opencv-python==5.0.0.93 opencv-contrib-python==5.0.0.93 \
            deepface==0.0.101 tf-keras==2.20.1 retina-face==0.0.18 \
            insightface==1.0.1 onnxruntime==1.19.2
```

E depois os dois `.onnx` do Passo 4.1.

## Passo 6 — conferir a instalação

```bash
python verificar_instalacao.py
```

Ele testa cada biblioteca, confere os arquivos `.onnx`, e **roda cada tecnologia numa
imagem real**, dizendo quantos rostos cada uma encontrou. A saída termina em
"Tudo pronto" ou lista o que falta, com o comando de instalação de cada item.

## Passo 7 — os pesos dos modelos

**Não precisa fazer nada:** cada modelo baixa os pesos sozinho, na primeira vez que é
usado. O que você precisa saber é que a primeira execução de cada um demora.

| Tecnologia | Onde fica | Tamanho |
|---|---|---|
| Facenet512 | `~/.deepface/weights/` | 95 MB |
| RetinaFace | `~/.deepface/weights/` | 119 MB |
| ArcFace | `~/.deepface/weights/` | 137 MB |
| VGG-Face | `~/.deepface/weights/` | 580 MB |
| InsightFace buffalo_l | `~/.insightface/models/` | 275 MB |

Para baixar tudo de antemão, em vez de esperar no meio de um teste:

```bash
python -c "
from deepface import DeepFace
for m in ('Facenet512','ArcFace','VGG-Face'): DeepFace.build_model(m)
from retinaface import RetinaFace; RetinaFace.build_model()
from insightface.app import FaceAnalysis; FaceAnalysis(name='buffalo_l').prepare(ctx_id=-1)
print('pesos baixados')
"
```

## Passo 8 — as fotos

O acervo **não acompanha este repositório**: são fotografias de pessoas reais, e
distribuí-las seria tratamento de dado pessoal sem base legal.

Para rodar, coloque imagens em `fotos/` e uma foto de consulta em `consultas/` ou em
`fotos/`. Qualquer conjunto serve — JPG ou PNG. Os resultados do Teste 1 só se
reproduzem com o mesmo acervo.

## Passo 9 — rodar

```bash
python server.py              # abre http://127.0.0.1:8777/
```

Indexar um acervo de 388 fotos leva de 2 a 11 minutos, dependendo da tecnologia. É
feito **uma vez por tecnologia** e fica em cache; as trocas seguintes são imediatas.

---

## Quando der errado

| Sintoma | Causa e solução |
|---|---|
| `Confirm that opencv is installed on your environment` | detector padrão do DeepFace não existe no OpenCV 5. Instale o `retina-face` (Passo 4.3). |
| `Input image must not have non-english characters` | o DeepFace recusa caminho com acento. O projeto já contorna entregando a imagem decodificada; se aparecer, renomeie o arquivo. |
| `cv2.imread` devolve `None` num arquivo que existe | nome com acento em outra normalização Unicode (comum no macOS). O projeto trata isso em `resolver_caminho()`. |
| Primeira execução parece travada | é o download dos pesos. Rode o comando do Passo 7 e acompanhe a barra de progresso. |
| `ModuleNotFoundError` depois de instalar | o ambiente virtual não está ativo. Rode `source .venv/bin/activate`. |
| InsightFace falha ao instalar | faltam ferramentas de compilação — ver a nota do Passo 4.4. |
| Fotos HEIC do iPhone não são lidas | o OpenCV não abre HEIC. Converta para JPEG antes. |
| `A KerasTensor cannot be used as input to a TensorFlow function` | TensorFlow foi carregado antes do DeepFace, e o Keras 3 assumiu no lugar do `tf-keras`. Defina `TF_USE_LEGACY_KERAS=1` **antes** de qualquer import, como fazem `modelos.py` e `verificar_instalacao.py`. |

## Versões exatas usadas no Teste 1

Registrar as versões é o que permite alguém repetir a medição e chegar ao mesmo número.

```
Python            3.9.6          macOS 27.0 (Apple M5 Pro)
numpy             2.0.2          opencv-python      5.0.0.93
deepface          0.0.101        opencv-contrib     5.0.0.93
tensorflow        2.20.0         tf-keras           2.20.1
retina-face       0.0.18         insightface        1.0.1
onnxruntime       1.19.2
```

---

## Privacidade e LGPD

Fotografia de rosto e vetor facial são **dado pessoal sensível** (LGPD, art. 5º, II —
dado biométrico). O projeto foi construído com isso em mente:

- o servidor escuta **apenas em `127.0.0.1`**, nunca na rede;
- nenhuma imagem é enviada a serviço externo — todos os modelos rodam localmente;
- o acervo **não acompanha o repositório**;
- os vetores ficam em `cache/`, que pode ser apagado a qualquer momento sem perda
  do que importa (o gabarito e os resultados).

Esta é uma bancada de avaliação técnica, de uso interno. O tratamento de dados do
sistema final — base legal, consentimento, retenção e eliminação — é tema do projeto
do FOTOMAC, não deste laboratório.
