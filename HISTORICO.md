# Histórico — FotoMac Lab

## 2026-09-25 — repositórios locais apagados

Pedido: "criei um repositório mas ele está bugado, apague ele e deixe eu subir no
github, só apague esse repositório".

- Havia **dois** repositórios locais, não um:
  - `fotomac-lab/.git` — 585 MB, 1 commit, 34.108 arquivos, remoto
    `ThiagoTzk/fotomac-lab`. **Nada tinha sido enviado** (`git ls-remote` vazio).
  - `Fotomac-TESTE/` — repositório aninhado, remoto `ThiagoTzk/Fotomac-TESTE`,
    gravado no commit de fora como *gitlink* (modo 160000). É o que "bugava": pasta
    que no GitHub vira um link cinza que não abre.
- Antes de apagar: árvore limpa e sem stash nos dois, então o commit não guardava
  nada que a pasta já não tivesse. Nenhum arquivo de trabalho se perdeu.
- Os dois `.git` foram removidos. Os repositórios **no GitHub continuam lá** — apagar
  conta de terceiro é irreversível e é decisão do Thiago.
- O Thiago tinha esvaziado `fotos/` de propósito, para não subir as imagens. A
  proteção estava **incompleta**: o commit ainda levava 388 miniaturas das mesmas
  fotos em `cache/thumbs/`, 16 autorretratos em `consultas/`, 6 imagens de
  `diagnostico/` e **18.762 vetores de rosto** nos `.pkl` (126 MB). Vetor de rosto é
  dado pessoal sensível — LGPD art. 5º, II.
- Criado `.gitignore` cobrindo `fotos/`, `consultas/`, `diagnostico/`, `cache/`,
  `backups/`, `.venv/` e `models/*.onnx`. Verificado com `git --git-dir` apontando
  para fora da pasta (para não recriar repositório aqui): passaria de 34.108 para
  **43 arquivos, 1,1 MB, zero imagem e zero vetor**.
- Armadilha encontrada na primeira versão: `.gitignore` **não aceita comentário na
  mesma linha do padrão**. `fotos/ # acervo` vira um padrão literal e não ignora
  nada. Comentário só em linha própria.

**Parei em:** pasta sem repositório, pronta para o `git init` dele. Falta o Thiago
decidir o que fazer com os dois repositórios que continuam no GitHub.

## 2026-09-25 — manual de instalação para o orientador

Pedido: o orientador precisa instalar e rodar os modelos na máquina dele.

### `README.md` ganhou um manual completo

Nove passos, do Python 3.9 ao servidor no ar, escritos para quem nunca viu o
projeto: ambiente virtual, bibliotecas base, cada modelo em bloco independente,
o atalho com tudo numa linha, os pesos que baixam sozinhos (com tamanhos e o
comando para baixar de antemão), onde ficam as fotos e como rodar.

Fechado com uma tabela de **sintomas e soluções** — os sete problemas que eu
mesmo enfrentei durante o projeto — e as **versões exatas** usadas no Teste 1,
que é o que permite alguém repetir a medição e chegar ao mesmo número.

Espaço em disco declarado: ~2,5 GB (1 GB de bibliotecas + 1,5 GB de pesos).

### `verificar_instalacao.py`

O orientador roda um comando e sabe se pode começar. Testa cada biblioteca,
confere os `.onnx` locais, lista quais pesos já estão no disco, e **roda cada uma
das cinco tecnologias numa imagem real**, dizendo quantos rostos achou e de que
tamanho é o vetor. Termina em "Tudo pronto" ou lista o que falta com o comando
de instalação de cada item.

### Bug real encontrado ao escrever o verificador

A primeira execução acusou os três modelos do DeepFace como quebrados:
*"A KerasTensor cannot be used as input to a TensorFlow function"*. **O ambiente
estava são — o bug era do verificador.**

Causa: o DeepFace roda sobre `tf-keras` (API antiga do Keras) e liga essa
compatibilidade ao ser importado. Se o TensorFlow já foi carregado antes, é tarde
— o Keras 3 assume. Meu verificador importava `tensorflow` explicitamente na
lista de checagem, antes do `retinaface`.

Corrigido definindo `TF_USE_LEGACY_KERAS=1` no topo de `verificar_instalacao.py`
**e de `modelos.py`** — no segundo como defesa, porque qualquer script que
importe TensorFlow antes sofreria o mesmo. Entrou também na tabela de problemas
do README.

### Conferido

- 8 versões fixadas no manual × o que está instalado: todas batem.
- 15 arquivos `.py` citados no README: todos existem.
- Os 2 links de download do opencv_zoo: HTTP 200, tamanhos iguais aos locais.
- `verificar_instalacao.py` depois do conserto: as 5 tecnologias em `[ok]`.

### `claude.md` estava desatualizado

A seção "Estrutura" ainda listava `benchmark.py`, `report_html.py` e
`engine_deepface.py`, apagados em 24/09, e dizia que `fotos/` tinha 204 imagens
quando tem 388. Corrigido, com uma linha explícita de que os três foram removidos
e não devem ser recriados.

- **Parei em:** manual pronto no README. Se o orientador preferir o manual em PDF
  separado, é mover para `docs/` e exportar — não fiz porque a regra do projeto é
  não gerar entregável de README.

## 2026-09-25 — visual unificado e correção sobre o acervo

### Correção do Thiago

**O acervo TEM três fotos dele** (IMG_1128/1129/1130). Eu havia escrito no relatório
que ele não aparecia em nenhuma. O correto: essas três são autorretratos, ele está
sozinho e o rosto ocupa quase todo o quadro — **achá-las é trivial, qualquer
tecnologia acerta**. Um teste em que todos acertam não ordena ninguém.

O coordenador é o oposto: dezenas de fotos de evento, de perfil, ao fundo, a metros
da câmera, encoberto por outras pessoas. Por isso ele é o alvo do teste.

O contraste virou argumento no relatório: *a mesma tecnologia que acerta 100% num
autorretrato isolado cai para 60% quando a pessoa está numa plateia*. Relatório e
PDF refeitos.

### O site parecia três sites

Cada tela trazia a própria paleta, com nomes de variável diferentes
(`--text-primary` no painel, `--ink` nas outras), e o menu do `/painel` tinha dois
links em vez de três — faltava "Marcar gabarito".

Criado `ui_comum.py`: um único conjunto de tokens (claro e escuro), os componentes
compartilhados (menu fixo no topo, painel, botão, tabela, cartão de número, aviso)
e o menu com as três telas na mesma ordem.

**Decisão: o CSS e o menu são injetados na hora de servir**, por `_pagina()`, em vez
de copiados em cada arquivo. É o que garante que as três continuem iguais quando uma
mudar.

Conferido por script, e não no olho: nas três telas o CSS base chega, o menu tem os
três links, o link da própria página está marcado como ativo, nenhum marcador
sobrou, e **nenhuma variável de cor é usada sem estar definida** — essa última
checagem pegou 4 órfãs na tela de marcação (`--sim`, `--sim-bg`, `--nao`, `--sec`),
restos da paleta antiga que teriam virado cor transparente.

- **Parei em:** três telas com a mesma aparência e o mesmo menu; Teste 1 intacto.

## 2026-09-24 — Teste 1 fechado, projeto reorganizado

### Correção do Thiago, importante para o TCC

**Não é ele nas fotos testadas.** A busca foi feita com a imagem
`Captura de Tela ... .png`, que é o **coordenador do curso**. Ele escolheu essa
pessoa porque **não esteve presente em nenhum dos dois eventos** e não aparece em
nenhuma das 388 fotos — seria impossível medir recall com alguém ausente do acervo.
Isso agora está dito no relatório, no painel e nos registros.

### "O modelo vê só um rosto?" — investigado, não procede

Medido numa mesma foto de plateia: **todos comparam todos os rostos** — 43, 33 e 23
comparações. O que muda é a DETECÇÃO:

| Tecnologia | Rostos nessa foto | Média no acervo |
|---|---|---|
| YuNet + SFace | 43 | 18,2/foto |
| InsightFace (SCRFD) | 33 | 9,8/foto |
| DeepFace (RetinaFace) | 23 | 6,9/foto |

O YuNet está calibrado aqui para aceitar rosto pequeno; os outros usam limites de
fábrica e reduzem a imagem antes de detectar. **Rosto não detectado é foto perdida**,
e o InsightFace venceu apesar de achar quase metade dos rostos do YuNet — o que
sugere margem se o detector dele for ajustado. Fica para o Teste 3.

### Reorganização

Removidos por estarem superados:
- `engine_deepface.py` — adaptador com pré-processamento meu; produziu a nota
  errada de 42,3 que foi descartada. Substituído por `modelos.py`.
- `benchmark.py` — reindexava do zero. Substituído por `avaliar_todos.py`, que usa
  o cache. A única função útil dele (CSV por foto) foi migrada.
- `report_html.py` — relatório estático `file://`. Substituído pelas telas do servidor.
- 4 backups de gabarito soltos na raiz (as cópias estão em `backups/`).

Criados: `README.md` (porta de entrada, com o mapa dos arquivos) e `docs/` para a
documentação. **O gabarito não foi tocado.**

### Rodada rotulada

`avaliar_todos.py --rotulo "Teste 1"`. O rótulo aparece no ranking, no painel e no
rodapé. As próximas rodadas usam o mesmo mecanismo.

### `docs/TESTE-1.md` (+PDF, 6 páginas)

Relatório para o orientador: o que foi testado e por quê, quem é a pessoa procurada
e o motivo da escolha, as cinco tecnologias, **como instalar cada uma (`pip install`
e de onde vêm os pesos)**, como o teste foi feito, como a nota é calculada, o
resultado, e as limitações.

### Painel apresentável

Pódio com as três primeiras em destaque, selo da rodada, e o contexto do acervo e
da pessoa procurada no cabeçalho. Bug encontrado ao fazer: o `${podio()}` foi
inserido no template mas a função não — a página quebrava ao renderizar. Passei a
conferir, por script, que toda função chamada no template existe.

- **Parei em:** Teste 1 fechado. Projeto com 14 arquivos de código, documentação em
  `docs/`, PDFs em `entregaveis/`.

## 2026-09-24 (madrugada) — o ranking das 5 tecnologias

O Thiago conferiu **foto a foto, com gabarito próprio por modelo**, as 5
tecnologias. Faltava a ponte: a conferência gravava no `gabarito.json`, mas a
nota só saía do `benchmark.py`, que reindexa do zero. Criado `avaliar_todos.py`,
que reaproveita os índices em cache.

### Ranking (leitura MODELO — rosto errado conta como erro)

| # | Tecnologia | Nota | mAP | AUC | Intrusos | Rosto errado | Nota produto |
|---|---|---|---|---|---|---|---|
| 1 | **InsightFace buffalo_l** | **97,6** | 0,998 | 0,9995 | **7** | 2 | 96,0 |
| 2 | YuNet + SFace (OpenCV) | 89,5 | 0,927 | 0,970 | 203 | 3 | 87,0 |
| 3 | ArcFace + RetinaFace | 64,0 | 0,627 | 0,823 | 311 | **27** | 43,0 |
| 4 | Facenet512 + RetinaFace | 60,3 | 0,669 | 0,886 | 314 | 9 | 53,9 |
| 5 | VGG-Face + RetinaFace | 57,1 | 0,563 | 0,806 | 261 | 12 | 51,5 |

**O InsightFace ganha com folga:** AUC 0,9995 (separação quase total) e apenas
**7 intrusos** contra 203 do SFace — 29x menos ruído acima do pior acerto.

**Contraria as tabelas publicadas do DeepFace**, onde o Facenet512 lidera. Duas
razões prováveis, ambas registradas: (a) essas tabelas medem pares de rostos já
recortados (LFW), não busca em foto de evento com plateia; (b) o InsightFace traz
detector e reconhecedor **casados de fábrica**, enquanto os modelos do DeepFace
rodam com um detector escolhido por nós porque o padrão deles não funciona aqui.

**O `rosto_errado` provou o seu valor:** o ArcFace tem 27 fotos em que a pessoa
aparece mas a similaridade veio do rosto de outra — quase metade dos "acertos"
dele foram coincidência. Por isso a nota de produto dele (43,0) fica ABAIXO da
nota de modelo (64,0): tratando essas fotos como alvo, ele não consegue
encontrá-las de novo. Sem esse terceiro estado, ele pareceria bem melhor do que é.

### Painel reescrito

`painel.py` agora lê `resultados/*_ranking.json` em vez de reconstruir do
benchmark. Gráficos: ranking por nota, as três medidas lado a lado (agrupadas, não
empilhadas — elas não somam), velocidade em escala log, distribuição do 1º lugar
com as três populações, e a tabela.

### Ressalvas impressas na própria página

- O gabarito cobre **1 pessoa**. A ordem do ranking é confiável; os valores
  exatos, menos.
- A nota é o **melhor F1 alcançável** por cada tecnologia: o limiar é escolhido
  olhando as respostas. Iguala a régua entre elas — nenhuma leva vantagem por ter
  um padrão de fábrica melhor calibrado — mas é otimista e não diz como cada uma
  se sai com uma pessoa nova.

- **Parei em:** ranking no ar em `/painel`, pronto para apresentação.

## 2026-09-24 (noite, 2) — gabarito POR MODELO

**Erro meu, encontrado pelo Thiago:** o gabarito era único e compartilhado. Ao
terminar de marcar as 388 fotos com o YuNet+SFace e trocar para o Facenet512, as
marcações do SFace apareciam pré-marcadas — contaminando exatamente o que o teste
deveria isolar. Um modelo não pode ser avaliado com as respostas de outro.

- O gabarito passou a ter `pessoas[nome]["por_modelo"][chave]`, cada tecnologia
  com o seu conjunto. `gabarito_io.carregar()` migra o formato antigo
  automaticamente para `sface`, que é onde todo o trabalho feito até aqui foi.
- **O trabalho do Thiago foi preservado:** 58 "está", 3 "rosto errado" e 327 "não
  está" do coordenador, as 388 fotos conferidas à mão, zero aceite em bloco.
  Backup em `backups/gabarito_sface_*.json`.
- `server.py` lê e grava sempre no modelo ativo; `benchmark.py` pontua um modelo
  com o gabarito DELE e avisa quando aquele modelo ainda não foi conferido.
- **Ao salvar, confirmação nomeando o modelo**, com o resumo do que vai ser
  gravado e quantas fotos ficaram sem confirmação. Marcar uma sessão inteira
  achando que era um modelo e gravar no outro custa horas; não pode depender de
  atenção.
- **Depois de salvar, a tela reseta** com a mensagem de qual modelo recebeu, e
  lembra que o gabarito do próximo começa vazio. Deixar o ranking antigo na tela
  é o caminho curto para marcar duas vezes a mesma coisa.
- O cabeçalho do ranking agora avisa, em destaque, com qual tecnologia você está
  marcando e quantas fotos já foram conferidas com ela.

Provado pela rota real: SFace com 388 conferidas e Facenet512 com 0; marcar 3
fotos no Facenet512 deixou o SFace intacto em 58/3/327.

- **Parei em:** gabarito do SFace completo e isolado. Facenet512, ArcFace,
  VGG-Face e InsightFace com gabarito vazio, prontos para serem conferidos um a um.

## 2026-09-24 (noite) — o modelo responde primeiro, o Thiago confirma

Pedido: ao carregar o ranking, o modelo já mostra a resposta dele, e o Thiago só
confirma ou corrige — em vez de marcar 150 fotos do zero.

- Cada item do ranking passa a trazer `proposta` ("sim" se a similaridade passa do
  limiar, "nao" se não). Campo **separado** de `marca`: proposta não é gabarito.
- Na tela, proposta aparece **tracejada e apagada**, com o texto "o modelo diz:
  ESTÁ / não". Marcação confirmada aparece sólida. O contador separa "conferidas
  por você" de "só proposta, não confirmada".
- <kbd>Enter</kbd> aceita a proposta e pula; <kbd>S</kbd>/<kbd>E</kbd>/<kbd>N</kbd>
  corrigem. No modo revisão o botão mostra qual é a proposta daquela foto.
- Botão "Aceitar as propostas restantes" para o volume, com aviso explícito.

**Ressalva dita ao Thiago e registrada no código:** resposta pré-preenchida enviesa.
Na dúvida a pessoa tende a aceitar o que já está marcado, e isso infla a nota do
modelo — gabarito construído aceitando o modelo em bloco mede o modelo contra ele
mesmo. Por isso:

1. proposta e confirmação são visualmente distintas e ficam em campos distintos;
2. nada vira gabarito sem uma ação explícita;
3. `revisao.aceitas_em_bloco` guarda **quantas** vieram do botão de aceitar em
   bloco, para o relatório poder declarar isso em vez de esconder.

- **Parei em:** fluxo testado de ponta a ponta pela rota real (proposta aparece,
  confirmação grava, correção sobrepõe, recarregar distingue confirmada de
  proposta, aceite em bloco é contado). Gabarito zerado de novo, pronto para o
  Thiago começar.

## 2026-09-24 (fim) — terceiro estado no gabarito e conserto do enquadramento

### "Está na foto, mas o modelo marcou o rosto errado"

Pedido do Thiago, e é uma distinção que faltava. O gabarito passa a ter **quatro**
estados: `aparece_em` (está, rosto certo), `rosto_errado` (está, mas a
similaridade veio do rosto de outra pessoa), `nao_aparece_em`, e ausente.

Por que importa: os dois primeiros são idênticos na contagem e opostos na
prática. Agora o relatório calcula **duas leituras** e diz qual usou:

- **MODELO** — só rosto certo é acerto; `rosto_errado` entra como negativo. É a
  leitura da nota de comparação, porque mede a tecnologia.
- **PRODUTO** — `rosto_errado` conta como acerto: a foto entregue tem mesmo a
  pessoa e o visitante fica satisfeito, não importa por qual rosto o sistema
  chegou lá.

Na tela: <kbd>S</kbd> está · <kbd>E</kbd> está, rosto errado · <kbd>N</kbd> não
está. O ciclo do clique passou a ser sem marca → está → rosto errado → não está.
Contadores ganharam "está na foto, rosto errado" e "recall do produto".

### Conserto do "zoom alto demais"

Não era zoom: era a foto **estourando o quadro e sendo cortada**. `.rev-img` não
tinha altura definida, então o `max-height:100%` da `<img>` não resolvia, ela
saía no tamanho natural e o `overflow:hidden` do pai cortava. Clássico de cadeia
de altura percentual quebrada.

Consertado com `inset:0` no contêiner e `object-fit:contain` na imagem. Como
isso cria faixa preta, a caixa verde deixou de ser posicionada em porcentagem do
elemento e passou a ser calculada em pixels sobre a **área real** da foto
(`areaDaFoto`) — em porcentagem ela cairia fora do rosto em toda foto cuja
proporção não bate com a da tela.

O recorte do rosto também ganhou **teto de 12x**: um rosto de 10 px ampliado sem
limite virava um borrão de 200 px que não ajudava a decidir nada.

Conferido por cálculo em 4 proporções de tela × 3 tamanhos de rosto: a foto cabe
inteira em todas, a caixa sempre cai sobre o rosto, o recorte fica centrado.

### Testes apagados a pedido, imagens intactas

Backup antes de qualquer coisa em `backups/` (gabarito com 55+330 marcações do
coordenador, registro de modelos, e `resultados/` compactado).

Apagado: marcações do gabarito, `modelos_testados.json`, `resultados/`.
**Preservado: `fotos/` (388), `consultas/` (15), `cache/` (2 índices) e as
pessoas e consultas do gabarito** — quem são as pessoas e qual foto é a consulta
não é resultado de teste, é a definição dele. Os índices em cache poupam 7 a 11
minutos por modelo e são cálculo determinístico, não teste.

- **Parei em:** tudo zerado e pronto para o Thiago refazer os testes modelo a
  modelo, com as três respostas. SFace e Facenet512 já indexados; ArcFace,
  VGG-Face e InsightFace indexam sob demanda pelo seletor.

## 2026-09-24 (tarde) — todas as tecnologias de fábrica, com troca pela tela

**Correção do Thiago, registrada em memória:** *"certifique-se que cada tecnologia
funcione padrão sem nenhuma alteração sua... quero ver ela padrão, podemos testar
ajustes depois"*. Eu tinha entregado uma nota do Facenet512 (42,3) que era do meu
adaptador, não do modelo. Esse número foi descartado.

### Cada biblioteca na configuração de fábrica — medido

| Configuração | Retrato 2316x3088 | Evento 6240x4160 |
|---|---|---|
| DeepFace **padrão de fábrica** (detector opencv) | FALHA | FALHA |
| DeepFace + RetinaFace | 1,67 s · 1 rosto | 1,30 s · 23 rostos |
| InsightFace buffalo_l | 73 s (baixa modelo) · 1 rosto | 1,67 s · 33 rostos |
| RetinaFace (só detecção) | 0,49 s | 0,57 s · 33 rostos |
| YuNet + SFace | 0,10 s | 0,36 s · 43 rostos |

**Duas correções ao que eu tinha afirmado antes:**

1. **O RetinaFace NÃO é lento.** Eu disse 22,19 s por foto. São **0,57 s** — os 22 s
   da primeira medição eram o download do modelo, que eu contei como tempo de
   processamento. Erro meu de medição.
2. **O padrão de fábrica do DeepFace não roda neste ambiente.** O detector default
   dele é a cascata de Haar do OpenCV, e o opencv-python 5.0 não distribui mais os
   `cv2/data/haarcascade_*.xml`. Falha em Facenet512, ArcFace e VGG-Face igualmente.
   Por isso os modelos do DeepFace no catálogo declaram `retinaface` — que continua
   sendo API oficial com parâmetro da própria documentação, não código meu.

### Criados

- `modelos.py` — catálogo com 5 candidatos, todos pela API oficial da biblioteca.
  `MotorDeepFacePadrao` e `MotorInsightFacePadrao` não fazem recorte, alinhamento
  nem redimensionamento próprio. O antigo `engine_deepface.py` (com o meu
  pré-processamento) fica como variante para a fase de ajustes, mais tarde.
- `estado_modelos.py` + `modelos_testados.json` — registro de quais modelos já
  foram conferidos. **O selo verde só acende quando alguém marcou fotos com aquele
  modelo**; indexar não acende, porque indexar não prova nada.
- Seletor de tecnologia nas telas `/` e `/marcar`, com o visto, o selo "de fábrica"
  e a estimativa de tempo antes de começar a indexar.
- Índice em cache **por modelo** (`cache/indice_<modelo>_<assinatura>.pkl`): a
  primeira troca custa minutos, as seguintes são instantâneas (medido: 0 s).

### Dois bugs encontrados e corrigidos no caminho

1. **O DeepFace recusa nome de arquivo com acento** — "Input image must not have
   non-english characters". A foto de consulta do coordenador (`... às ...png`)
   derrubava a requisição inteira. Corrigido entregando a imagem já decodificada
   em vez do caminho; o pipeline da biblioteca continua idêntico.
2. **Erro do motor derrubava a conexão** em vez de virar mensagem. Agora vira JSON.
   Ao consertar, eu mesmo inverti a ordem dos `except` e o pega-tudo engoliu os
   erros de negócio — corrigido, os específicos vêm primeiro.

### Medido com os dois modelos prontos (388 fotos)

| Modelo | Rostos | Fotos com rosto | Indexação | Busca |
|---|---|---|---|---|
| YuNet + SFace | 7046 | 388/388 | 2 min | 0,76 ms |
| Facenet512 + RetinaFace | 2639 | 380/388 | 6,8 min | 0,57 ms |

- **Parei em:** SFace e Facenet512 indexados e testados de ponta a ponta pela rota
  real. ArcFace, VGG-Face e InsightFace estão no catálogo e indexam sob demanda
  (8 a 11 min cada), pelo próprio seletor. Nenhum tem selo verde ainda — o selo é
  do Thiago, conferindo foto a foto.

## 2026-09-24 — DeepFace / InsightFace / RetinaFace: diagnóstico e primeiro teste

### Diagnóstico das bibliotecas (pedido do Thiago)

As três importam e funcionam. **O `retina-face` NÃO precisa reinstalar** — o que
pareceu erro é que ele leva **22 segundos por foto** quando roda no original de
6240x4160. Reduzida para 1920px ele leva **0,51 s e acha os mesmos 33 rostos**.

| Biblioteca | Versão | Estado |
|---|---|---|
| deepface | 0.0.101 | ok (avisa que o backend TF será opcional no futuro) |
| insightface | 1.0.1 | ok (importa; ainda não testado a fundo) |
| retina-face | 0.0.18 | **ok, não precisa reinstalar** |

### Custos medidos (Apple M5 Pro)

| Item | Custo |
|---|---|
| Carregar Facenet512 | 36,7 s na 1ª vez (baixa 95 MB) |
| Embedding um a um | 59,3 ms por rosto |
| **Embedding em lote de 32** | **10,4 ms por rosto** — 6x |
| RetinaFace no original 20 MP | 22,19 s por foto |
| RetinaFace reduzido a 1920px | 0,51 s por foto, mesmos rostos |
| YuNet a 1920px | 0,32 s por foto, 43 rostos |

### Achado que importa para o TCC

**O DeepFace ponta a ponta NÃO funciona neste acervo.** Chamado com
`detector_backend="yunet"` numa foto de 6240x4160, ele devolve "1 rosto" que é a
**imagem inteira**, com confiança 0.0 — ele não reduz a imagem antes de detectar.
Numa foto de retrato (2316x3088) funciona normalmente. Ou seja: a biblioteca
pronta não dá conta de foto de evento em alta resolução; é preciso detectar por
fora, como esta bancada já faz.

### Criado `engine_deepface.py`

Mesma interface de `fotomac_face.FaceEngine`, então `benchmark.py`, `server.py` e
`indice.py` não mudaram. Novas opções: `--motor deepface --rede Facenet512
--detector yunet|retinaface`.

### Erros meus no adaptador, e o que ficou em aberto

1. **Redimensionava com `cv2.resize` direto para 160x160**, esmagando rosto não
   quadrado. O DeepFace preserva a proporção e preenche com preto. Custou uma
   varredura inteira e fez o Facenet512 parecer pior do que é. Corrigido usando o
   `resize_image` do próprio DeepFace.
2. **Cortava e depois girava.** O DeepFace gira a imagem inteira, projeta a caixa
   com `project_facial_area` e só então corta. Corrigido.
3. **Folga da caixa** escolhida por medição contra o caminho oficial:
   0.00 -> cosseno 0.65 | 0.10 -> 0.86 | **0.20 -> 0.90** | 0.30 -> 0.87.

**EM ABERTO:** mesmo com as três correções, o vetor do meu adaptador só chega a
**cosseno 0.90** contra `DeepFace.represent(foto, detector_backend="yunet")`.
A causa provável é que a detecção do DeepFace devolve uma caixa diferente da
minha — mas não confirmei. **Enquanto isso não fechar, qualquer nota do
Facenet512 medida aqui é provisória e não serve de veredito sobre o modelo.**

Hipóteses já descartadas por medição: folga do recorte (4 valores), ordem
girar/cortar, convenção dos olhos (trocar destrói: cosseno cai para -0.08), e
tamanho mínimo do rosto (10/40/80/120 — a margem não melhora).

- **Parei em:** adaptador funcionando e ligado ao benchmark; nota do Facenet512
  sendo medida com o pré-processamento corrigido. A ressalva acima vale até
  alguém fechar os 0.10 de cosseno que faltam.

## 2026-09-23 (manhã seguinte) — o teste real, e o SFace mostrou o limite

O Thiago marcou **150 fotos do coordenador dele**: 59 "está", 91 "não está".
Acervo cresceu para 388 fotos. Primeira medição da tarefa real.

- **Nota caiu de 97,8 para 55,5 / 100.** Não é regressão: é o teste fácil saindo
  de cena. Ordenação continua boa (mAP 0,927, AUC 0,917), mas a separação desabou
  para 0,5 de 25 pontos.
- **As distribuições se sobrepõem, como o Thiago tinha visto à mão:**
  fotos COM ele vão de 0.2446 a 1.0 (mediana 0.4690); fotos SEM ele vão até 0.3985.
  **89 fotos sem ele pontuam acima da pior foto com ele.** Não existe limiar que
  acerte tudo.
- **Ponto de operação medido** (59 fotos dele no acervo):
  | limiar | achou | errou | precisão | recall | F1 |
  |---|---|---|---|---|---|
  | 0.3741 | 48 | 1 | 98% | 81% | **89%** |
  | 0.44 | 35 | 0 | 100% | 59% | 75% |
  | 0.45 | 33 | 0 | 100% | 56% | 72% |
  O melhor F1 é 0.3741, não 0.45. Decisão sobre trocar é do Thiago: 0.3741 acha
  13 fotos a mais ao custo de 1 estranho.
- **Dois bugs de normalização Unicode custaram duas execuções inteiras.** O macOS
  grava acento em NFD, shell e navegador entregam NFC. O arquivo de consulta tem
  "às" no nome: `cv2.imread` devolvia None num arquivo que existe, e depois o
  gabarito não era reconhecido. Corrigido em `benchmark.resolver_caminho`,
  `server._resolver_consulta` e `scoring.nfc` — **toda comparação de nome de
  arquivo passa por NFC agora**.
- **Modo revisão em tela cheia** (`/marcar`, botão ou duplo clique): foto original
  grande, recorte do rosto comparado ampliado no canto (sempre a 70% da caixa,
  conferido de rosto de 0,5% a 32% da foto), S/N marcam e já pulam, setas navegam,
  Z liga/desliga o zoom, Esc sai. Pré-carrega as vizinhas para não travar entre uma
  foto e outra. Era o gargalo: ele estava saindo do site para abrir o arquivo.
- **Painel corrigido:** a distribuição agora é por pessoa e **só sobre o que foi
  conferido**. O gráfico virou histograma espelhado (aparece para cima, não aparece
  para baixo) com a **zona de confusão** destacada — porque "vão livre" deixou de
  existir. Espelhado e não sobreposto: com as populações misturadas, transparência
  vira sopa.
- **Parei em:** painel mostrando o teste real. O conjunto deixou de estar saturado
  — agora existe espaço de sobra para um modelo melhor aparecer. Observação do
  Thiago a confirmar com dado: SFace parece fraco em rosto de perfil.

## 2026-09-23 (madrugada) — ferramenta de marcação do gabarito

Gatilho: o Thiago testou o coordenador dele e achou o que o meu gabarito fácil
nunca mostraria — fotos onde a pessoa ESTÁ com similaridade 0.2862 e fotos onde ela
NÃO está com 0.37. **As distribuições se sobrepõem: não existe limiar que acerte
tudo na tarefa real.** É a confirmação da auditoria.

- Criada a tela `/marcar`: escolhe pessoa + foto de consulta, mostra o ranking com
  a caixa do rosto em cada miniatura, e a pessoa marca **está / não está** clicando
  ou pelo teclado (S, N, setas, Esc). Contadores ao vivo de acertou / errou /
  deixou escapar / rejeitou certo, mais precisão, recall e F1.
- Uma linha divide o ranking no limiar, e a tela insiste para marcar **também as de
  baixo** — é a única forma de contar falso negativo.
- **Gabarito v2 com três estados**, em `gabarito_io.py`: `aparece_em` (conferido que
  está), `nao_aparece_em` (conferido que não está) e ausente (ninguém olhou).
  Salvamento com backup automático — meia hora de marcação não pode morrer num erro.
- **Decisão que mais muda os números:** a métrica passa a ser calculada **só sobre
  as fotos conferidas**. Medido com dados que imitam o caso do coordenador:
  contando as 3500 não conferidas como negativo dá AUC 0.9996 e separação 99.9%;
  só sobre o conferido dá **AUC 0.700 e separação 40%**. Mesmos dados. As fotos
  fáceis que ninguém olhou inflavam tudo.
- Ciclo completo testado por HTTP: grava, corrige (move a foto de um lado para o
  outro), recarrega lembrando as marcas, cria backup e preserva quem já estava no
  gabarito. Gabarito de teste removido depois.
- `COMO-TESTAR.md` atualizado (5 páginas) com o passo a passo da marcação.
- **Parei em:** ferramenta no ar em `/marcar`. **Não vi a tela renderizada** —
  a limitação de renderizar HTML nesta máquina continua. Próximo passo é o Thiago
  marcar o coordenador e rodar o benchmark: aí, pela primeira vez, a nota vai medir
  a tarefa real e o conjunto deve deixar de estar saturado.

## 2026-09-23 (noite) — painel de comparação para a apresentação

Pedido: um site apresentável, para a banca e o orientador, com gráfico comparando
as tecnologias testadas. Feito ANTES dele testar com mais imagens.

- **Ressalva dada na cara:** só existe UM modelo medido até agora. O gráfico de
  comparação tem uma barra. Montado para receber N modelos e se preencher sozinho.
- Criados `painel.py` (coleta) e `painel_page.py` (página). Rotas novas no
  servidor: `/painel` e `/painel/dados`. Link entre as duas páginas.
- **Decisão: nada digitado à mão.** O painel lê os `resultados/*_resumo.json`. Rodar
  o benchmark com um modelo novo e recarregar a página basta.
- **Decisão: a cor segue o MODELO, não a colocação** (fixada pela ordem alfabética).
  Se um candidato novo passar na frente, as cores dos outros não trocam de lugar.
- Paleta: usada a de referência da skill dataviz, **validada com o script** em claro
  e escuro. 5 fatias: todos os testes passam; no tema claro três cores ficam abaixo
  de 3:1, o que obriga rótulo direto dentro da fatia — implementado.
- **Gráfico principal — "o que separa é-você de não-é-você":** histograma dos 603
  rostos de outras pessoas contra os 6 pontos da mesma pessoa, com o vão anotado e
  o limiar como linha. É o gráfico que prova o sistema numa banca, e funciona com
  um modelo só.
- **Correção de forma durante o teste:** o gráfico de velocidade era de barras. Ao
  simular uma API (420 ms contra 0,39 ms), a barra rápida virou 2 px — invisível.
  Trocado por **pontos em escala logarítmica**: ponto não promete proporção de
  comprimento, então pode viver em log; barra não pode. Conferido com 1 e 3 modelos.
- Verificações feitas: rotas, conteúdo, e **a geometria dos quatro gráficos
  recalculada em Python** (marcas dentro do quadro, larguras positivas, empilhada
  somando a nota, limiar dentro do vão, rótulos sem estourar a borda). Zero erros.
- **Parei em:** painel no ar em `/painel`. **Não vi a página renderizada** — quarta
  tentativa de renderizar HTML nesta máquina falhou (Firefox não cria perfil nem
  fora do sandbox). Falta o Thiago abrir e dizer se está apresentável.

## 2026-09-23 (fim) — auditoria do método de avaliação

Motivo: o Thiago vai trocar de modelo e precisa que a comparação seja confiável.
Auditei o próprio método. Quatro defeitos; três corrigidos, um aberto.

- **Thiago baixou o limiar para 0.440 e funcionou melhor.** Investiguei as fotos em
  `consultas/`: ele estava enviando **fotos do evento** como consulta, procurando
  aquelas pessoas nas outras fotos. É a tarefa real do produto. O meu gabarito só
  tinha 3 selfies da mesma sessão — tarefa fácil, que nunca produziria um caso na
  faixa 0.42-0.48 onde o limiar decide. **A evidência dele era melhor que a minha.**
- **Defeito 1 (GRAVE, aberto):** o gabarito testa a tarefa errada. Uma pessoa, 3
  selfies, e essa pessoa não estava no evento. Consequência medida: AUC 1.000,
  mAP 1.000, zero intrusos — **conjunto saturado**. O modelo novo vai empatar, e a
  comparação seria decidida só pela velocidade.
- **Defeito 2 (corrigido):** limiar calibrado e avaliado nos mesmos dados. Agora há
  validação cruzada — o limiar que julga uma consulta é calibrado sem vê-la.
- **Defeito 3 (corrigido):** a nota dependia da escala de similaridade. Criado
  `metricas.py` com AUC, mAP, intrusos e separação não-paramétrica; nota v2 =
  ordenação 40 + separação 25 + robustez 15 + busca 10 + indexação 10.
  Trocado o d-prime (que pressupõe distribuição comportada) por contagem simples.
- **Defeito 4 (corrigido):** o PDF prometia avaliar no melhor limiar de cada modelo
  e `scoring.melhor_limiar` **nunca era chamada** — a nota saía no limiar da linha
  de comando. Erro meu de ligação.
- **Verificado e OK:** tempo de indexação é estável (0.1901/0.1905/0.1901 s por
  foto, 0.2% de variação). A oscilação anterior era mudança de código, não ruído.
  Importa porque, num conjunto saturado, a velocidade vira o critério de desempate.
- Adicionado `poder_de_discriminacao`: o relatório agora **avisa sozinho** quando o
  conjunto está saturado ou com amostra pequena. Hoje avisa os dois.
- Escrito `AUDITORIA-DO-METODO.md` (+PDF/DOCX).
- **Parei em:** método corrigido, mas o conjunto de teste não discrimina. Proposto
  ao Thiago: marcar 4-6 pessoas DO EVENTO no gabarito. Ofereci construir a
  ferramenta de marcação; aguardando ele decidir o escopo.

## 2026-09-23 (noite) — servidor local com webcam e envio

- Criados `server.py` (HTTP local) e `indice.py` (índice com cache em disco).
  A página em `http://127.0.0.1:8777/` tem duas abas: **Webcam** (getUserMedia,
  captura espelhada, envia o JPEG) e **Enviar arquivo** (marcada como só-teste).
- **Decisão: só biblioteca padrão do Python.** Flask resolveria, mas é dependência
  nova para um servidor de laboratório que faz 4 rotas. `http.server` dá conta.
- **Decisão: escuta só em 127.0.0.1.** As fotos do fotógrafo são privadas; o
  servidor não pode ficar acessível na rede local.
- **Decisão: cache de índice em `cache/`, invalidado por assinatura** (nome+tamanho
  +data de cada arquivo, MAIS os parâmetros do modelo). Incluir os parâmetros é o
  que impede servir resultado calibrado com ajuste velho. Primeira vez 54s,
  reinícios **0.14s**.
- **Decisão: miniaturas servidas LIMPAS, sem caixa.** A caixa depende de qual rosto
  casou com a consulta da vez; o servidor devolve a caixa em fração da imagem e o
  navegador posiciona por CSS. Mesma miniatura serve para qualquer consulta.
- Medido de ponta a ponta pelo endpoint `/buscar`, com as 3 fotos do gabarito:
  3/3 acima do limiar em cada uma, zero falso positivo, **busca 0.4 ms**, ida e
  volta completa ~110 ms (o custo é decodificar e detectar na consulta, não buscar).
- Nota: a auto-correspondência agora dá 0.95-0.99 em vez de 1.0, porque a foto passa
  por recompressão JPEG no caminho. É mais realista que o 1.0 de antes.
- **Dois bugs encontrados e corrigidos durante o teste:**
  - `indice.py` decodificava a foto em tamanho cheio só para ler largura e altura
    (0.08s por foto jogados fora). Trocado por `IMREAD_REDUCED_COLOR_8`.
  - porta ocupada devolvia traceback cru de `OSError`. Agora explica e sugere
    `--porta` ou o comando para encerrar o processo antigo.
- Escrito `COMO-TESTAR.md` (+PDF/DOCX): passo a passo da webcam, do envio, do
  limiar, das permissões de câmera e do que cada programa faz.
- **Parei em:** servidor provado por HTTP em todas as rotas (página, miniatura,
  original, 404, imagem inválida, imagem sem rosto, foto de multidão como consulta).
  **Não testei a página renderizada nem a webcam no navegador** — continuo sem
  conseguir renderizar HTML nesta máquina. Falta o Thiago abrir e usar.

## 2026-09-23 (fim da tarde) — todos os rostos + captura por webcam

- **Correção de entendimento:** o Thiago achou que o sistema comparava só o rosto
  verde. Não: ele sempre comparou TODOS os rostos indexados; verde é só o de maior
  similaridade e cinza são os outros. O que faltava era rosto que os filtros
  descartavam antes de virar vetor — esse, sim, ficava de fora.
- **Filtros abertos, medidos contra o gabarito:** `MIN_DET_SCORE` 0.60 -> 0.50 e
  `MIN_FACE_SIDE` 40 -> 10. Resultado: **1004 -> 3583 rostos**, **197 -> 204 fotos
  cobertas** (todas). Pior acerto inalterado (0.5202), melhor erro sobe só de 0.3728
  para 0.3809. F1 continua 1.000; separação sobe para 5.07σ.
- **Custo honesto:** nota caiu de 99.4 para **97.9** — inteiramente pela indexação,
  que foi de 0.12 s para 0.19 s por foto. Não é piora de qualidade, é o preço de
  olhar 3.6x mais rostos. Registrado como tal.
- **`MIN_DET_SCORE=0.30` quebra** (pior acerto despenca para 0.0546) e a causa é de
  projeto: nesse nível o detector cria uma caixa espúria GRANDE no autorretrato
  (IMG_1128: área 356206 contra 319414 do rosto real) e, como `query_face` escolhe
  pela maior área, a caixa falsa vence. Bug do lado da CONSULTA, não do acervo.
  Fica como pendência conhecida; 0.50 está longe do precipício.
- Hipótese minha derrubada por medição: eu supus que rosto de 10-20 px viraria vetor
  degenerado. Medi — similaridade média entre eles +0.16, contra +0.12 dos grandes.
  Não é degenerado. Bom lembrete de medir antes de filtrar por intuição.
- Criado `capture.py`: captura do autorretrato pela webcam, com portão de qualidade
  ao vivo (sem rosto / pouco nítido / pequeno / mais de um) e dois modos — janela com
  prévia, ou sem janela contando 3,2,1 e escolhendo o melhor quadro. `--buscar` já
  dispara o benchmark com a foto tirada.
- **Parei em:** portão de qualidade testado em 6 cenários (webcam vazia, autorretrato
  bom, multidão, preto, ruído) e todos corretos. A câmera abre e entrega quadro real
  1920x1080. **Não testei a janela ao vivo nem a tecla ESPAÇO** — precisa de um rosto
  na frente da câmera. Falta o Thiago rodar.

## 2026-09-23 (tarde) — gabarito, calibração e sistema de pontuação

- **O Thiago deu o gabarito:** IMG_1128/1129/1130 são as únicas fotos com ele; nenhuma
  das ~200 do fotógrafo tem. Isso destrava medir precisão de verdade. Virou
  `gabarito.json`, formato editável e independente de modelo.
- Criado `scoring.py` + `SISTEMA-DE-PONTUACAO.md` (PDF/DOCX em `entregaveis/`):
  nota 0–100 = acerto 60 (F1) + separação 20 (σ) + busca 10 + indexação 10.
- **Decisão: cada modelo é avaliado no SEU melhor limiar.** O 0.363 do SFace não
  significa nada para uma API que devolve 0–100. A nota compara separação, não escala.
- **Decisão: custo fica FORA da nota**, ao lado dela na tabela. É decisão de negócio,
  não medida de qualidade; misturar esconde a escolha.
- **Bug real encontrado:** com IMG_1129 como consulta, `IMG_3011` dava 0.3728 e passava
  pelo limiar 0.363 — rapaz diferente, cabelo e bigode parecidos. Falso positivo.
- **Calibração:** pior acerto 0.5202, melhor erro 0.3728 → existe faixa que separa
  perfeitamente. `COSINE_THRESHOLD` de 0.363 para **0.45** (ponto médio, ~0.07 de folga
  de cada lado). Resultado: F1 = 1.000 nas 3 consultas, 0 falso positivo, 4.97σ,
  **nota 99.4/100**.
- **Varredura de 60 combinações de MAX_SIDE / MIN_DET_SCORE / MIN_FACE_SIDE rejeitada.**
  A "melhor" (1280/150, margem 0.29 contra 0.15) guarda só **9 rostos em 204 fotos** —
  ganha margem jogando fora o que o sistema real precisa achar. Isso é ajustar ao
  gabarito, não melhorar o modelo. Parâmetros de detecção ficam como estavam.
  Contraexemplo registrado: MAX_SIDE=2560 piora muito (margem −0.26).
- **Bug meu, no script de varredura:** eu escolhia o rosto da consulta pela maior
  *lateral* da caixa; produção escolhe pela maior *área*. Em IMG_1129, que tem duas
  pessoas, isso trocava de pessoa e dava margem −0.27. A varredura contradizia o teste
  direto — foi o que denunciou o erro. Lição: quando duas medições discordam, uma está
  errada; não escolha a que agrada.
- Nova seção na página: **Imagens correspondentes** — cada par vira um JPEG único com
  os dois rostos ampliados lado a lado e as duas fotos inteiras com a caixa, mais o
  veredito (ACERTO / FALSO POSITIVO). Ficam em `resultados/<data>_pares/`.
- **Parei em:** modelo calibrado e pontuado, bancada pronta para o segundo candidato.
  Próximo passo com maior retorno: **ampliar o gabarito para 3-4 pessoas** — com uma
  pessoa e 3 fotos positivas, o recall tem pouca força estatística.

## 2026-09-23

- Chegaram ~200 fotos reais do fotógrafo. `fotos/` passou de 6 para **204 imagens**
  (957 MB, todas JPG — nenhum HEIC, o risco que eu tinha levantado não se concretizou).
- Medido no acervo real: **1004 rostos em 197 fotos**, 7 fotos sem rosto. São fotos de
  formatura com plateia; várias têm de 15 a 21 rostos.
- Criado o `report_html.py` — relatório visual em HTML local. Miniaturas ordenadas por
  similaridade, caixa verde no rosto que casou, cinza nos demais, controle de limiar que
  repinta a grade ao vivo, e clique abre o original em tamanho cheio.
- **Decisão: HTML local (`file://`), não página publicada.** As fotos são privadas.
  A página referencia os arquivos por caminho relativo; nada sai da máquina.
- **Decisão: cada miniatura leva um inset com o recorte do rosto que casou.** Motivo
  concreto: numa foto com 20 pessoas, a caixa do rosto que gerou a similaridade tem
  ~15 px e some. Sem o inset a página mostra "0.3373" sem mostrar de quem.
- **Achado que muda a leitura do teste:** `IMG_3008` deu 0.3373 com a consulta, e o
  rosto responsável era o de uma **mulher desfocada ao fundo** — pessoa diferente. Ou
  seja, as "quase correspondências" entre 0.30 e 0.36 são em boa parte lixo de fundo.
  Isso é evidência a favor de manter o limiar em 0.363 em vez de afrouxar.
- Varredura de limiares no acervo real: 0.20 → 83 fotos | 0.25 → 30 | 0.30 → 12 |
  0.363 → 3 | 0.55 → 1. O salto entre 0.30 e 0.363 é onde o lixo entra.
- Tempo no acervo real (M5 Pro): carregar 0,05 s | indexar 22,5 s (9,1 fotos/s) |
  buscar 4,1 ms | miniaturas +6 s.
- Bug encontrado e corrigido: o inset era recortado **depois** de desenhar as caixas,
  então a moldura verde entrava ampliada dentro do recorte e tapava o rosto. Agora o
  recorte sai da imagem limpa, antes de qualquer desenho.
- **Parei em:** a página é gerada e os dados dentro dela foram conferidos (197 cards,
  7 falhas, todos os caminhos existem, miniaturas inspecionadas uma a uma). **Não
  consegui renderizar a página eu mesmo** — Firefox headless falha com "Could not find
  profile folder" (3 abordagens) e `screencapture` está bloqueado por falta de permissão
  de Gravação de Tela. Layout e o controle de limiar dependem do Thiago abrir e olhar.

## 2026-09-22

- Reescrito o `claude.md` do projeto: de recado corrido para documento estruturado
  (identidade, objetivo mensurável, estado dos dados, estrutura, comandos,
  convenções, armadilhas). Motivo: é lido a cada sessão, precisa carregar o *porquê*
  junto com a regra.
- Criado o `benchmark.py` — a peça que faltava para o teste das 300 fotos.
  O `fotomac_face.py` só compara duas imagens; não havia varredura de acervo,
  medição de tempo nem saída em arquivo.
- **Decisão:** o tempo é medido em três fases separadas (carregar modelo / indexar
  acervo / buscar), não como um número só. No sistema real a indexação roda de
  madrugada e a busca roda com o visitante esperando — um número somado esconderia
  qual das duas é o gargalo.
- **Decisão:** o CSV grava TODAS as fotos com sua similaridade, não só as que
  passaram do limiar. Assim dá para recalcular qualquer limiar sem reindexar o acervo.
- **Decisão:** varredura de limiares (0.20 a 0.70) no relatório. Fixar só o 0.363
  mediria o limiar escolhido, não o modelo.
- Bugs encontrados e corrigidos durante o teste com 302 arquivos:
  - avisos `divide by zero / overflow / invalid` do NumPy no `matmul`. Investigado:
    falso positivo do SIMD (matriz sem NaN/inf, normas 1.0, diferença de 1.9e-08
    contra laço em float64, ordenação idêntica). Silenciado com `np.errstate` e
    comentário, mais checagem de `isfinite` para não esconder problema real;
  - terminal despejava 150 linhas de correspondência e empurrava os tempos para
    fora da tela. Limitado a 20, com o resto no CSV.
- Medido na prática (Apple M5 Pro, 302 arquivos ~1.3 GB, MAX_SIDE=1920):
  carregar modelos 0.03 s | indexar 23.7 s (12.7 fotos/s) | buscar 0.52 ms.
- **Parei em:** bancada pronta e provada com 302 arquivos simulados, incluindo
  arquivo ilegível e foto sem rosto. Próximo passo é rodar com as ~300 fotos reais
  do fotógrafo quando chegarem. Pendência aberta: **não existe gabarito** — sem
  alguém marcar em quais fotos a pessoa realmente aparece, o teste mede desempenho
  e comportamento, não precisão.
