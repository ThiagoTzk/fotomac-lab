---
title: "FotoMac Lab — como testar"
subtitle: "Webcam, envio de imagem, marcação do gabarito e o painel"
author: "Thiago José Nunes"
date: "23 de setembro de 2026"
lang: pt-BR
---

# 1. O jeito rápido: a página de busca

Um comando só. Ele indexa o acervo, sobe um servidor local e abre o navegador:

```bash
cd ~/fotomac-lab
.venv/bin/python server.py
```

Na primeira vez ele leva ~40 segundos indexando as 204 fotos. **Nas vezes seguintes
abre na hora**: o índice fica guardado em `cache/`.

O navegador abre em `http://127.0.0.1:8777/`. Duas abas:

## Aba "Webcam"

1. Clique em **Ligar a câmera**. O navegador pede permissão — aceite.
2. Enquadre o rosto e clique em **Tirar foto e buscar**.
3. Em milissegundos aparecem as fotos do acervo com você, ordenadas pela
   similaridade, com a caixa verde no rosto que casou.

A imagem é espelhada, como num espelho de verdade — é o que o totem faz.

## Aba "Enviar arquivo (teste)"

Arraste uma imagem (ou clique para escolher) e ele procura aquela pessoa no acervo.

**Isto é ferramenta de teste e não vai para o produto final.** Existe para você
comparar modelos sem precisar estar na frente da câmera: a mesma foto enviada
para dois modelos diferentes dá uma comparação justa, coisa que duas selfies
tiradas em momentos diferentes não dão.

## O controle de limiar

Embaixo do resultado tem um controle deslizante. Arraste e a contagem muda na hora.
**Nenhuma busca é refeita** — as similaridades já vieram do servidor; o limiar só
decide onde cai a régua. É a mesma separação entre cálculo caro e decisão barata
que existe entre indexar e buscar.

O valor calibrado é **0,45**. Abaixo de 0,3728 começam a entrar pessoas erradas.

# 2. Se a câmera não abrir

O navegador pede permissão na primeira vez. Se você negou antes:

- **Safari**: menu Safari > Ajustes > Sites > Câmera > permita `127.0.0.1`.
- **Chrome**: ícone de cadeado na barra de endereço > Câmera > Permitir.

A câmera só funciona em `localhost` ou `https`. Por isso o endereço é
`http://127.0.0.1:8777` e não o IP da sua máquina na rede.

# 3. Pelo terminal, sem navegador

Se quiser testar a captura sem abrir página nenhuma:

```bash
# janela com prévia ao vivo; ESPAÇO tira a foto, ESC cancela
.venv/bin/python capture.py

# sem janela: conta 3, 2, 1 e escolhe sozinho o melhor quadro
.venv/bin/python capture.py --sem-janela

# tira a foto e já roda a busca completa, com relatório e CSV
.venv/bin/python capture.py --buscar
```

O `capture.py` só deixa tirar a foto quando o rosto está bom. Ele recusa dizendo
o que fazer:

| Situação | Mensagem |
|---|---|
| Sem rosto | "Nenhum rosto: chegue mais perto e olhe para a camera" |
| Pouca nitidez | "Rosto pouco nitido: procure mais luz" |
| Rosto pequeno | "Rosto pequeno: chegue mais perto" |
| Mais de uma pessoa | "Mais de um rosto no quadro: fique sozinho" |

No macOS, o terminal precisa de permissão de câmera em **Ajustes do Sistema >
Privacidade e Segurança > Câmera**. Depois de liberar, feche e reabra o terminal.

> O `server.py` **não** tem esse problema: lá quem acessa a câmera é o navegador,
> e ele pede a própria permissão.

# 4. Marcar o gabarito — a parte que só você pode fazer

`http://127.0.0.1:8777/marcar`

O modelo devolve um ranking. **Ele não sabe se acertou.** Quem sabe é você, olhando.
Esta tela existe para transformar "achou 32 fotos" em "acertou 27 e errou 5".

## Como usar

1. **Nome da pessoa** — vira a chave no gabarito (`coordenador`, `professora_ana`).
2. **Foto de consulta** — pode ser uma foto do acervo ou uma que você tirou/enviou.
3. **Quantas revisar** — 80 é um bom começo. Se ainda aparecer gente certa lá no
   fim, aumente.
4. **Carregar ranking.**

Aí é clicar. Cada foto alterna entre **está** → **não está** → sem marca. Pelo
teclado vai mais rápido:

| Tecla | Faz |
|---|---|
| <kbd>S</kbd> | marca "está" e pula para a próxima |
| <kbd>N</kbd> | marca "não está" e pula para a próxima |
| <kbd>←</kbd> <kbd>→</kbd> | navega sem marcar |
| <kbd>Esc</kbd> | tira a marca |

Uma linha divide o ranking no limiar: acima dela é o que o sistema mostraria ao
visitante; abaixo é o que ele esconderia.

## Marque também as de baixo

É contraintuitivo, mas é o ponto principal: **marque as que estão abaixo do limiar
também.** Só assim dá para contar as que o modelo **deixou escapar** — e foi
justamente isso que você encontrou à mão, uma foto do coordenador com 0,2862
ficando de fora enquanto uma foto sem ele passava com 0,37.

A barra de baixo mostra, ao vivo:

| Contador | Significa |
|---|---|
| **acertou** | mostrou e é ela mesmo |
| **errou** | mostrou e não é ela |
| **deixou escapar** | é ela e o sistema não mostrou |
| **rejeitou certo** | não é ela e não mostrou |

Mais precisão, recall e F1 no limiar em uso.

## Por que "não está" é tão importante quanto "está"

O gabarito guarda três estados: você confirmou que **está**, você confirmou que
**não está**, e **ninguém olhou**. A métrica é calculada só sobre o que foi
conferido.

Isso não é detalhe. Medido com dados que imitam o seu caso:

| Como se conta | AUC | Separação |
|---|---|---|
| tratando as 3500 não conferidas como "não é ela" | 0,9996 | 99,9% |
| só sobre as fotos que alguém olhou | **0,700** | **40%** |

São os mesmos dados. A primeira linha parece quase perfeita porque milhares de
fotos fáceis, que ninguém verificou, entram como acerto de rejeição. A segunda
diz a verdade.

## Salvar

**Salvar no gabarito** grava em `gabarito.json`, com backup automático do anterior.
Você pode parar no meio e voltar depois: ao recarregar o mesmo ranking, o que já
estava marcado volta marcado.

# 5. O painel de comparação

`http://127.0.0.1:8777/painel`

É a tela para apresentar: nota de cada tecnologia, do que a nota é feita, velocidade,
a tabela dos números e o gráfico que mostra as duas populações — "mesma pessoa" e
"pessoas diferentes" — e onde a régua cai entre elas.

Ele se preenche sozinho: cada execução do `benchmark.py` com um modelo novo entra
no gráfico sem ninguém digitar número nenhum.

# 6. O relatório completo, para o TCC

O servidor é para olhar e testar. Para gerar os números e os arquivos que vão para
o trabalho, use o `benchmark.py`:

```bash
.venv/bin/python benchmark.py \
  --consulta fotos/IMG_1128.JPG \
  --consulta fotos/IMG_1129.JPG \
  --consulta fotos/IMG_1130.JPG
```

Ele gera em `resultados/`:

- a **nota do modelo** (hoje 97,9/100) contra o `gabarito.json`;
- CSV com **todas** as fotos e suas similaridades, para recalcular qualquer limiar
  no Excel sem reindexar;
- a **página visual** com os pares compilados lado a lado;
- o JSON com tudo, para virar gráfico.

# 7. Quais programas existem e para que servem

| Arquivo | Para que serve |
|---|---|
| `server.py` | as três páginas: busca, marcação e painel |
| `marcar_page.py` | a tela de marcação do gabarito |
| `painel.py` / `painel_page.py` | o painel de comparação de tecnologias |
| `gabarito_io.py` | lê e grava o gabarito, com backup |
| `metricas.py` | AUC, mAP, intrusos — métricas independentes de limiar |
| `benchmark.py` | mede, pontua e gera os arquivos do TCC |
| `capture.py` | captura pelo terminal, sem navegador |
| `indice.py` | indexa o acervo e guarda em cache |
| `scoring.py` | aplica o gabarito e calcula a nota |
| `fotomac_face.py` | o motor: detecta, alinha, gera o vetor |
| `report_html.py` | monta a página do relatório |
| `gabarito.json` | a verdade: quais fotos têm cada pessoa |

# 8. Privacidade

O servidor escuta **só em 127.0.0.1**. Ele não fica acessível para outras máquinas
da rede, nem para a internet. As fotos do fotógrafo não saem do seu computador —
nem para a página, que roda local, nem para serviço nenhum.

As fotos que você tira ou envia ficam em `consultas/`, para você conferir depois
qual imagem gerou qual resultado. Apague quando quiser.
