# FotoMac Lab — bancada de teste de reconhecimento facial

## 1. O que é este projeto

Laboratório isolado, ligado ao TCC (FOTOMAC). O objetivo é **comparar soluções de
reconhecimento facial e decidir com número na mão qual vai para o sistema final**.

Isto **não é o produto**. É a bancada onde os candidatos são medidos. Código aqui é
descartável; o que sobrevive é o *resultado da medição*.

Candidato em teste hoje: **YuNet** (detecção de rosto) + **SFace** (vetor de
características), via OpenCV, com os `.onnx` do opencv_zoo em `models/`.
A bancada precisa aceitar outros candidatos depois (InsightFace, DeepFace, API paga)
**sem reescrever o resto**. Trate o modelo como peça trocável, não como o programa.

## 2. O que o teste precisa responder

Dada uma foto de consulta (o autorretrato do visitante) e um acervo de fotos de evento,
o relatório tem que entregar:

1. **Quantas correspondências** — em quantas fotos o modelo achou aquela pessoa.
2. **Quais arquivos** — o nome de cada foto correspondente, com a similaridade de cada uma.
3. **Quanto tempo** — o tempo total para varrer o acervo inteiro, separando:
   - carregar o modelo (custo único),
   - indexar o acervo (detectar + gerar vetor de cada foto),
   - comparar a consulta contra o acervo já indexado.

Por que separar o tempo: no sistema real a indexação acontece uma vez, de madrugada; a
busca acontece com o visitante esperando na frente do totem. Um número só, somado,
esconde qual das duas etapas é o gargalo — e é a busca que o usuário sente.

Saída **em arquivo** (CSV e/ou JSON), além do que aparece no terminal. Esse resultado
vira tabela e gráfico no TCC; não pode morrer no scrollback do terminal.

## 3. Estado dos dados — leia antes de mexer

- `fotos/` tem **388 imagens** (24/09/2026): fotos reais de duas colações de grau,
  em resolução original (até 6240x4160), mais 3 autorretratos do Thiago.
- Medido nelas: **7046 rostos** com YuNet, 3799 com InsightFace, 2639 com RetinaFace.
  São fotos de formatura com plateia — muitas têm 20 a 40 rostos, a maioria pequenos
  e ao fundo. TODOS entram na comparação.
- Trabalhe só com o que está em `fotos/`. Não baixe dataset, não gere imagem sintética,
  não invente arquivo para "completar" a amostra.
- O código tem que funcionar igual com 6 ou com 300 fotos — nada de número fixo.
- As fotos são **privadas**. Não publicar, não enviar para serviço externo, não subir
  para repositório, **não virar Artifact**. O `server.py` escuta só em 127.0.0.1 por
  isso — não mude para 0.0.0.0. O relatório visual é HTML local (`file://`)
  por causa disto. O uso é exclusivamente comparação interna.

## 4. Estrutura

```
fotomac_face.py     motor YuNet + SFace: detecta, alinha, gera o vetor
modelos.py          catálogo das tecnologias, TODAS na configuração de fábrica
indice.py           indexa o acervo e guarda em cache, um índice por tecnologia
gabarito_io.py      lê e grava o gabarito (por modelo, quatro estados), com backup
metricas.py         AUC, mAP, intrusos — métricas independentes de limiar
scoring.py          notas e validação cruzada
avaliar_todos.py    calcula a nota de cada tecnologia e monta o ranking
estado_modelos.py   registra quais tecnologias já foram conferidas (o selo verde)
server.py           servidor local (só 127.0.0.1) com as três telas
ui_comum.py         paleta e menu compartilhados — NÃO duplique CSS nas páginas
marcar_page.py      tela /marcar: conferência manual do gabarito
painel.py           lê resultados/*_ranking.json para o painel
painel_page.py      tela /painel: ranking e gráficos — é o que vai para a banca
capture.py          captura pela webcam, sem navegador
diagnostico.py      investiga por que um detector não achou rosto numa foto
verificar_instalacao.py  confere o ambiente e roda cada tecnologia
gabarito.json       a verdade conferida à mão, separada por tecnologia
modelos_testados.json  progresso da conferência de cada tecnologia
fotos/              acervo (privado, 388 fotos)
consultas/          fotos de consulta tiradas ou enviadas
models/             os .onnx do YuNet e do SFace
cache/              índices e miniaturas — descartável, regenera sozinho
resultados/         rankings e CSVs de cada rodada
backups/            cópias do gabarito antes de cada limpeza
docs/               documentação; entregaveis/ tem os PDFs
.venv/              ambiente Python local
```

REMOVIDOS em 24/09 por estarem superados: `benchmark.py` (reindexava do zero),
`report_html.py` (relatório file://) e `engine_deepface.py` (adaptador com
pré-processamento nosso, produziu a nota errada de 42,3). Não os recrie.

O `modelos.py` é uma camada **por cima** dos motores, nunca dentro deles. É isso
que permite trocar a tecnologia sem reescrever a medição.

## 5. Como rodar

```bash
# página de busca com webcam e envio (http://127.0.0.1:8777/)
.venv/bin/python server.py

# teste completo: varre fotos/, cronometra, gera CSV + JSON + página visual
.venv/bin/python benchmark.py --consulta fotos/IMG_1128.JPG

# outras opções
--acervo <pasta>     outra pasta de fotos (padrão: fotos)
--consulta <arquivo> pode repetir; o acervo é indexado uma vez só
--limiar 0.45        muda a régua da similaridade
--sem-html           pula as miniaturas (mais rápido)

.venv/bin/python fotomac_face.py <selfie> <foto_evento>   # compara duas imagens
.venv/bin/python diagnostico.py fotos/IMG_1128.JPG        # investiga uma detecção
```

Sempre `.venv/bin/python`, nunca o `python` do sistema — o OpenCV está instalado só no venv.

## 6. Convenções

- Python 3.9 (`.venv`), opencv-python 5.0, numpy 2.0.
- Código em inglês (nomes de variáveis, funções, classes, arquivos).
  Docstrings, comentários e mensagens de terminal em português.
- Parâmetros do modelo ficam como **constantes no topo do arquivo, com comentário
  explicando o porquê do valor** — é assim que `fotomac_face.py` já faz. Siga.
- Nova dependência: diga o que é e por que vale a pena **antes** de instalar.
- Sem git neste projeto por enquanto.

## 7. Armadilhas desta medição

Coisas que já sei que podem invalidar o resultado. Levante antes de rodar, não depois:

- **O limiar foi CALIBRADO em 23/09: 0.45, não o 0.363 padrão do SFace.** Medido
  contra o gabarito: pior acerto 0.5202, melhor erro 0.3728. O 0.363 deixa passar
  `IMG_3011` como falso positivo. Não volte para 0.363 sem novos dados.
- **O gabarito existe (`gabarito.json`) e cobre UMA pessoa, com 3 fotos positivas.**
  Dá para afirmar que 0.363 erra e que 0.45 é melhor aqui. NÃO dá para afirmar que
  0.45 é certo em geral — recall medido em 2 fotos por consulta tem pouca força.
  Ampliar para 3-4 pessoas é a pendência de maior retorno.
- **O sistema compara TODOS os rostos indexados, não só o verde.** Verde é apenas o
  de maior similaridade naquela foto; cinza são os outros. Se um rosto não tem caixa
  nenhuma, ele foi descartado pelos filtros antes de virar vetor — é esse o único
  caso em que um rosto fica fora da comparação.
- **Filtros calibrados: MIN_DET_SCORE=0.50, MIN_FACE_SIDE=10.** Não suba de volta
  para 0.60/40 sem motivo: isso perde 2500 rostos e deixa 7 fotos sem rosto nenhum.
  E não baixe MIN_DET_SCORE para 0.30 — o detector cria caixa espúria grande no
  autorretrato e, como query_face escolhe pela maior área, a consulta vira lixo.
- **A PESSOA PROCURADA NOS TESTES É O COORDENADOR DO CURSO**, não o Thiago. O acervo
  TEM três fotos dele (IMG_1128/1129/1130), mas são autorretratos — sozinho, rosto
  ocupando o quadro. Achá-las é trivial e não ordena tecnologia nenhuma. O
  coordenador aparece em dezenas de fotos de evento, de perfil e ao fundo, que é a
  dificuldade real.
- **Todos os modelos comparam TODOS os rostos da foto.** Verificado: 43, 33 e 23
  comparações numa mesma foto. A diferença entre eles é de DETECÇÃO, não de
  comparação — YuNet acha 18,2 rostos/foto, InsightFace 9,8, RetinaFace 6,9.
- **RANKING ATUAL (24/09, 1 pessoa, 388 fotos conferidas por modelo):**
  InsightFace 97,6 · SFace 89,5 · ArcFace 64,0 · Facenet512 60,3 · VGG-Face 57,1.
  O InsightFace vence com AUC 0,9995 e 7 intrusos contra 203 do SFace.
  Isso CONTRARIA as tabelas publicadas do DeepFace — provável causa: elas medem
  pares de rostos recortados (LFW), não busca em foto de plateia.
- **A nota sai de `avaliar_todos.py`, não do `benchmark.py`.** Ele lê o que foi
  marcado na tela e reaproveita os índices em cache. O painel lê
  `resultados/*_ranking.json`.
- **O GABARITO É POR MODELO** (`pessoas[nome]["por_modelo"][chave]`). Nunca leia as
  marcações de um modelo ao avaliar outro: foi o erro que contaminou o teste do
  Facenet512 com as respostas do SFace. `gabarito_io.marcacoes(d, pessoa, modelo)`
  é o único jeito certo de ler.
- **O ranking traz a PROPOSTA do modelo, e proposta não é gabarito.** O campo
  `proposta` (sim/nao pelo limiar) é separado de `marca` (o que o Thiago confirmou).
  Nada vira gabarito sem ação dele. `revisao.aceitas_em_bloco` conta quantas vieram
  do botão de aceitar em bloco — se esse número for alto, o gabarito mede o modelo
  contra ele mesmo, e o relatório precisa dizer isso.
- **O gabarito tem QUATRO estados, não dois.** `aparece_em` (está, rosto certo),
  `rosto_errado` (está, mas o modelo casou o rosto de outra pessoa),
  `nao_aparece_em`, e ausente. Duas leituras: MODELO (rosto errado é negativo — é a
  da nota de comparação) e PRODUTO (rosto errado é acerto de recuperação). Sempre
  diga qual leitura o número usa.
- **Fotos NÃO conferidas não entram na métrica.** O gabarito tem três estados:
  `aparece_em`, `nao_aparece_em` e ausente. Medido: contar as não conferidas como
  negativo levou AUC de 0.700 para 0.9996 nos mesmos dados. Nunca volte a assumir
  negativo por omissão.
- **A tarefa real tem distribuições SOBREPOSTAS.** O Thiago mediu à mão: foto com a
  pessoa a 0.2862 e foto sem a pessoa a 0.37. Não prometa que existe limiar perfeito
  — no caso fácil (selfies) existe, no caso real não.
- **O teste real já existe: o coordenador, 150 fotos conferidas (59 está / 91 não).**
  Nota do YuNet+SFace nele: **55,5/100**, contra 97,8 no conjunto fácil das selfies.
  Use SEMPRE o gabarito do coordenador para comparar modelos. O conjunto não está
  mais saturado — há espaço de sobra para um candidato melhor.
- **O DeepFace ponta a ponta NÃO detecta nas fotos de 20 MP.** Medido: numa foto
  6240x4160 ele devolve "1 rosto" que é a imagem inteira, confiança 0.0. Ele não
  reduz antes de detectar. Sempre detecte por fora (YuNet ou RetinaFace reduzido a
  1920px) e passe o recorte — é o que `engine_deepface.py` faz.
- **RetinaFace: SEMPRE reduzir para 1920px antes.** 22,19 s por foto no original
  contra 0,51 s reduzida, achando os mesmos rostos. Não é atalho, é viabilidade.
- **REGRA: toda tecnologia é medida primeiro na configuração de FÁBRICA.** Sem
  recorte, alinhamento ou redimensionamento nossos. É o que o Thiago exigiu, e o
  motivo é defesa numa banca: nota de modelo ajustado por nós não responde "esse
  número é do modelo ou do seu código?". Ajuste vem depois, como variante rotulada.
  Use `modelos.py`, não `engine_deepface.py`.
- **O padrão de fábrica do DeepFace não roda aqui.** O detector default é a cascata
  de Haar e o opencv-python 5.0 não traz mais os XML. Por isso o catálogo declara
  `retinaface` — API oficial, parâmetro da documentação, não código nosso.
- **RetinaFace leva 0,57 s por foto de 20 MP, não 22 s.** Os 22 s da primeira
  medição eram o download do modelo. Corrigido em 24/09.
- **O DeepFace recusa nome de arquivo com acento.** Entregue a imagem já decodificada
  (`cv2.imread`), nunca o caminho.
- **A nota antiga do Facenet512 (42,3) foi DESCARTADA** — era do meu adaptador, não
  do modelo. O valor válido é o do Teste 1 (60,3), medido de fábrica.
- **`TF_USE_LEGACY_KERAS=1` tem que ser definido ANTES de qualquer import** que puxe
  TensorFlow. O DeepFace roda sobre `tf-keras`; se o TensorFlow carregar primeiro, o
  Keras 3 assume e os três modelos quebram com "A KerasTensor cannot be used as
  input to a TensorFlow function". Já está no topo de `modelos.py` e de
  `verificar_instalacao.py`.
- **NOME DE ARQUIVO SEMPRE NORMALIZADO EM NFC.** O macOS grava acento em NFD, shell
  e navegador entregam NFC. Use `scoring.nfc()` em toda comparação e
  `benchmark.resolver_caminho()` ao abrir. Este bug já custou duas execuções
  completas — `cv2.imread` devolve None num arquivo que existe.
- **A nota de comparação é a v2 (`metricas.py`), independente de limiar.** A v1 (F1
  no limiar) fica como diagnóstico operacional. Não use a v1 para comparar modelos:
  o limiar é calibrado no mesmo gabarito onde a nota é medida.
- **Não ajuste parâmetros até o gabarito ficar perfeito.** Já testei: a combinação de
  maior margem (MAX_SIDE=1280, MIN_FACE_SIDE=150) guarda 9 rostos em 204 fotos. Ela
  acerta o gabarito jogando fora o que o sistema real precisa achar. Margem melhor com
  acervo esvaziado é ajuste ao gabarito, não melhoria. Os parâmetros de detecção estão
  como devem ficar.
- **Tempo depende da máquina.** O relatório registra máquina, resolução das imagens e
  `MAX_SIDE` usado. Número de tempo sem esse contexto não serve para comparar nada.
- **Numa foto de evento, o que casou pode ser qualquer um dos 20 rostos.** Medido:
  `IMG_3008` deu similaridade 0.3373 com a consulta, e o rosto responsável era o de uma
  **mulher ao fundo, desfocada** — pessoa completamente diferente. Por isso o relatório
  visual mostra o recorte do rosto que casou, não só a foto. Contagem de fotos sem
  mostrar o rosto que gerou a contagem é número sem prova.
- **Rosto não encontrado não é erro do teste.** Foto girada, rosto pequeno ou de perfil
  fazem o YuNet devolver zero. Isso é *dado*, entra no relatório como categoria própria
  — não vira exceção silenciosa nem crash no meio da varredura.

## 7-A. Interface

- **A aparência das três telas vive em `ui_comum.py`**, e é injetada ao servir por
  `Handler._pagina()`. Não copie CSS nem menu para dentro de uma página: foi o que
  fez o `/painel` parecer outro site e perder o link "Marcar gabarito".
- Ao mexer em qualquer tela, confira por script que nenhuma variável de cor é usada
  sem estar definida. Órfã não dá erro — vira cor transparente e só aparece na tela.

## 7-A2. Gráficos

- Carregue a skill `dataviz` ANTES de escrever qualquer gráfico e **rode o validador
  de paleta** (`scripts/validate_palette.py`, há versão Python — não há node aqui).
- Paleta em uso: a de referência da skill, validada em claro e escuro. No tema claro
  três slots ficam abaixo de 3:1 — por isso as fatias empilhadas levam rótulo direto.
- **A cor segue o modelo, nunca a colocação.** Candidato novo não pode repintar os
  outros.
- Tempo varia em ordens de grandeza entre modelo local e API: use **pontos em escala
  log**, nunca barra. Barra em escala log mente sobre a proporção.

## 8. Como você trabalha aqui

- Leia o `HISTORICO.md` da raiz antes de começar; escreva nele ao terminar cada marco.
- Entregue rodando: nada é "pronto" sem você ter executado e visto a saída real.
- Escopo é meu. Se achar que falta algo, proponha em uma linha — não implemente sozinho.
