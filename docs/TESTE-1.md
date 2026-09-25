---
title: "Teste 1 — comparação de cinco tecnologias de reconhecimento facial"
subtitle: "Metodologia, instalação e resultados — bancada FotoMac"
author: "Thiago José Nunes"
date: "24 de setembro de 2026"
lang: pt-BR
---

# 1. O que foi testado e por quê

O sistema FOTOMAC precisa de uma tecnologia de reconhecimento facial: o visitante
tira uma foto no totem e o sistema devolve as fotos do evento em que ele aparece.

Este documento relata o **Teste 1**, que comparou cinco tecnologias sobre o mesmo
acervo, com o mesmo procedimento e as mesmas métricas. Outras rodadas virão para
confirmar os resultados.

## O acervo

**388 fotografias** de duas colações de grau, cedidas pelo fotógrafo, em resolução
original (até 6240×4160 pixels). São fotos reais de evento: plateia cheia, muitas
pessoas por quadro, iluminação variada, rostos de perfil e ao fundo.

As imagens não são divulgadas; o uso é exclusivamente a comparação interna descrita
aqui.

## A pessoa procurada

A busca foi feita pelo **coordenador do curso**, a partir de uma fotografia dele
isolada (arquivo `Captura de Tela 2026-09-23 às 15.46.57.png`).

A escolha tem um motivo metodológico. O acervo contém **três fotografias do autor**,
mas elas são autorretratos: ele aparece sozinho, com o rosto ocupando quase todo o
quadro. Encontrá-las é trivial — qualquer tecnologia acerta —, e um teste em que todos
acertam não ordena ninguém.

O coordenador é o oposto: aparece em **dezenas de fotos de evento**, em situações
variadas — de frente, de perfil, ao fundo, a vários metros da câmera, parcialmente
encoberto por outras pessoas. É exatamente a dificuldade que o sistema real enfrenta,
e é onde as tecnologias se separam.

Vale registrar o contraste porque ele é, em si, um resultado: a mesma tecnologia que
acerta 100% num autorretrato isolado cai para 60% quando a pessoa está numa plateia.

# 2. As cinco tecnologias

| Tecnologia | Detector | Reconhecedor | Configuração |
|---|---|---|---|
| InsightFace buffalo_l | SCRFD | ArcFace (R50) | de fábrica |
| YuNet + SFace | YuNet | SFace | calibrada nesta bancada |
| ArcFace (DeepFace) | RetinaFace | ArcFace | de fábrica |
| Facenet512 (DeepFace) | RetinaFace | Facenet512 | de fábrica |
| VGG-Face (DeepFace) | RetinaFace | VGG-Face | de fábrica |

**Regra adotada: cada tecnologia foi medida na configuração de fábrica da biblioteca**,
sem pré-processamento próprio. Isso torna o resultado defensável — a pergunta "este
número é do modelo ou do código de quem testou?" tem resposta. A única exceção é o
YuNet + SFace, cujos parâmetros foram calibrados nesta bancada antes de as demais
entrarem, e isso está declarado em toda tabela.

## Uma limitação do DeepFace que precisou ser contornada

O detector padrão do DeepFace é a cascata de Haar do OpenCV. Na versão instalada
(opencv-python 5.0) esses arquivos não são mais distribuídos, e a biblioteca falha
com *"Confirm that opencv is installed on your environment"*. Os três modelos do
DeepFace falham igualmente.

Por isso eles declaram `detector_backend="retinaface"` — que continua sendo API
oficial com parâmetro da própria documentação, não código externo. A alternativa
seria não testá-los.

# 3. Como instalar

Ambiente: **Python 3.9**, macOS, ambiente virtual local.

```bash
# criar e ativar o ambiente
python3 -m venv .venv
source .venv/bin/activate

# base
pip install numpy opencv-python opencv-contrib-python

# DeepFace (traz TensorFlow; instala Facenet512, ArcFace, VGG-Face)
pip install deepface tf-keras

# RetinaFace — o detector usado pelos modelos do DeepFace
pip install retina-face

# InsightFace (traz onnxruntime)
pip install insightface onnxruntime
```

Os **pesos dos modelos são baixados no primeiro uso**, automaticamente:

| Tecnologia | Onde fica | Tamanho |
|---|---|---|
| Facenet512 | `~/.deepface/weights/` | 95 MB |
| RetinaFace | `~/.deepface/weights/` | 119 MB |
| ArcFace, VGG-Face | `~/.deepface/weights/` | 137 MB e 580 MB |
| InsightFace buffalo_l | `~/.insightface/models/` | 275 MB |

O YuNet e o SFace são arquivos `.onnx` do repositório *opencv_zoo*, colocados em
`models/` manualmente (cerca de 5 MB somados).

> Na primeira execução, contar alguns minutos de download. É uma vez só.

# 4. Como o teste foi feito

Esta é a parte que dá valor ao resultado, e é trabalhosa de propósito.

## 4.1 Indexação

Para cada tecnologia, o sistema percorreu as 388 fotos, detectou **todos** os rostos
de cada uma e converteu cada rosto num vetor numérico. Esse índice fica em cache: é
calculado uma vez por tecnologia.

## 4.2 Busca

A foto do coordenador virou um vetor, comparado com **todos** os rostos indexados.
Para cada foto do acervo guarda-se a maior similaridade encontrada — ou seja, numa
foto com 43 rostos, os 43 são comparados e vale o mais parecido.

## 4.3 Conferência manual — foto a foto

**Cada uma das 388 fotos foi aberta e classificada à mão, para cada tecnologia,
separadamente.** Três respostas possíveis:

| Resposta | Significa |
|---|---|
| **Está** | o coordenador aparece na foto E o sistema marcou o rosto dele |
| **Está, rosto errado** | ele aparece, mas o sistema marcou o rosto de outra pessoa |
| **Não está** | ele não aparece na foto |

A terceira categoria — **rosto errado** — é a contribuição metodológica deste teste.
Sem ela, "o sistema encontrou a foto" e "o sistema encontrou a foto pelo motivo
certo" ficam indistinguíveis. Com ela, dá para separar acerto de coincidência.

## 4.4 Gabarito separado por tecnologia

Cada tecnologia tem o **seu próprio** conjunto de marcações. Nenhuma herda as
respostas de outra. Sem essa separação, a segunda tecnologia testada já começaria
com as respostas da primeira na tela — e a comparação estaria contaminada.

Isso significa que a conferência manual foi repetida **cinco vezes**, uma por
tecnologia: aproximadamente 1900 classificações feitas à mão.

## 4.5 O que foi conferido

| Tecnologia | Está | Está, rosto errado | Não está | Total conferido |
|---|---|---|---|---|
| InsightFace | 62 | 2 | 324 | 388 |
| YuNet + SFace | 58 | 3 | 327 | 388 |
| Facenet512 | 47 | 9 | 324 | 380 |
| VGG-Face | 47 | 12 | 321 | 380 |
| ArcFace | 30 | 27 | 323 | 380 |

Os totais de 380 (em vez de 388) correspondem a fotos em que aquela tecnologia não
detectou rosto algum — não há o que conferir.

# 5. Como a nota é calculada

**Nota de acerto = 100 × o melhor F1 que a tecnologia alcança.**

- **Precisão** — das fotos que o sistema mostrou, quantas eram mesmo dele.
- **Recall** — das fotos em que ele aparece, quantas o sistema achou.
- **F1** — a média harmônica das duas. Só é alta quando as duas são altas.

O limiar de similaridade é escolhido, para cada tecnologia, no ponto que maximiza o
F1 **dela**. Isso iguala a régua: nenhuma leva vantagem por ter um valor padrão
melhor ajustado de fábrica. Em compensação, a nota é **otimista** — o limiar foi
escolhido olhando as respostas, então ela mede o potencial, não o desempenho com
uma pessoa nova.

Duas outras medidas, independentes de limiar, aparecem ao lado:

- **mAP** — os acertos foram para o topo do ranking?
- **AUC** — a chance de um acerto ficar acima de um erro. 0,5 é sorteio; 1,0 é
  separação total.

E duas leituras do mesmo gabarito:

- **Nota (modelo)** — "rosto errado" conta como **erro**. É a leitura que compara
  tecnologias, porque mede o que a tecnologia de fato fez.
- **Nota (produto)** — "rosto errado" conta como **acerto**, porque a foto entregue
  contém mesmo a pessoa e o visitante fica satisfeito.

# 6. Resultado

| # | Tecnologia | Nota | Nota produto | mAP | AUC | Intrusos | Rosto errado |
|---|---|---|---|---|---|---|---|
| **1** | **InsightFace buffalo_l** | **97,6** | 96,0 | 0,998 | **0,9995** | **7** | 2 |
| 2 | YuNet + SFace | 89,5 | 87,0 | 0,927 | 0,970 | 203 | 3 |
| 3 | ArcFace + RetinaFace | 64,0 | 43,0 | 0,627 | 0,823 | 311 | 27 |
| 4 | Facenet512 + RetinaFace | 60,3 | 53,9 | 0,669 | 0,886 | 314 | 9 |
| 5 | VGG-Face + RetinaFace | 57,1 | 51,5 | 0,563 | 0,806 | 261 | 12 |

*Intrusos = quantas fotos sem o coordenador pontuaram acima da pior foto com ele.*

## 6.1 O InsightFace vence com folga

AUC de **0,9995** significa separação praticamente total entre as duas populações. E
deixa **7 intrusos** contra 203 do segundo colocado — 29 vezes menos ruído.

## 6.2 O resultado contraria as tabelas publicadas

Nas tabelas de referência do DeepFace, o Facenet512 aparece entre os melhores. Aqui
ficou em quarto. Duas explicações prováveis:

1. **A tarefa é outra.** Aquelas tabelas medem verificação de pares em bases como a
   LFW: dois rostos já recortados e centralizados, pergunta-se se são a mesma pessoa.
   Aqui a tarefa é buscar uma pessoa em 388 fotos de plateia, com rostos pequenos, de
   perfil e ao fundo.
2. **O conjunto importa tanto quanto o modelo.** O InsightFace entrega detector e
   reconhecedor treinados e ajustados juntos. Nos modelos do DeepFace tivemos de
   escolher o detector, porque o padrão não funciona no ambiente instalado.

**Conclusão metodológica:** escolher tecnologia por tabela publicada é arriscado. A
tabela responde a pergunta dela, não necessariamente a sua.

## 6.3 O "rosto errado" mudou o ranking

O ArcFace tem **27 fotos** em que o coordenador aparece mas a similaridade veio do
rosto de outra pessoa — quase metade das fotos em que ele foi "encontrado".

Por isso a nota de produto dele (43,0) fica **abaixo** da nota de modelo (64,0):
quando essas fotos passam a ser tratadas como alvo, ele não consegue reencontrá-las.
Foram acertos por coincidência.

Sem a terceira categoria de resposta, o ArcFace apareceria bem melhor do que é. Essa
é a justificativa para o custo extra da conferência manual em três estados.

## 6.4 Os detectores enxergam quantidades muito diferentes de rostos

Todos os sistemas comparam **todos** os rostos que detectam — verificado: numa mesma
foto de plateia foram 43, 33 e 23 comparações. A diferença está em **quantos rostos
cada detector encontra**:

| Tecnologia | Rostos numa mesma foto | Média no acervo |
|---|---|---|
| YuNet + SFace | 43 | 18,2 por foto |
| InsightFace (SCRFD) | 33 | 9,8 por foto |
| DeepFace (RetinaFace) | 23 | 6,9 por foto |

O YuNet está calibrado nesta bancada para aceitar rostos pequenos; os outros usam os
limites de fábrica, que reduzem a imagem antes de detectar e perdem rostos ao fundo.

Isto é relevante: **um rosto não detectado é uma foto perdida**, e nenhuma qualidade
de reconhecimento compensa. O InsightFace venceu apesar de detectar quase metade dos
rostos que o YuNet — o que sugere margem de melhora se o detector dele for ajustado.
Fica para a próxima rodada.

# 7. Limitações — leia junto com os números

1. **O gabarito cobre uma pessoa.** A ordem do ranking é confiável — a distância
   entre o primeiro e o terceiro é grande demais para ser acaso. Os valores exatos
   merecem menos confiança.
2. **A nota é otimista.** O limiar foi escolhido olhando as respostas. Ela mede o
   potencial máximo de cada tecnologia, não o desempenho com uma pessoa nova.
3. **Uma configuração é privilegiada.** O YuNet + SFace teve os parâmetros calibrados
   nesta bancada; as outras quatro rodaram de fábrica. A comparação favorece o
   segundo colocado, não o primeiro — o que reforça a vitória do InsightFace.
4. **Fotos não conferidas não entram na conta.** Medido em outro momento deste
   trabalho: tratar fotos não verificadas como "não é a pessoa" elevou a AUC de 0,700
   para 0,9996 nos mesmos dados. Por isso só o que foi olhado é contado.

# 8. Próximas rodadas

- **Teste 2** — ampliar o gabarito para três ou quatro pessoas do evento, para que os
  valores absolutos ganhem a confiança que a ordem já tem.
- **Teste 3** — ajustar o detector do InsightFace para enxergar rostos menores, e
  medir quanto o recall melhora.
- **Teste 4** — incluir uma API paga como referência de mercado.
