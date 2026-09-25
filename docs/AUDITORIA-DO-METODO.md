---
title: "Auditoria do método de avaliação"
subtitle: "O que dá para confiar antes de trocar de modelo — e o que não dá"
author: "Thiago José Nunes"
date: "23 de setembro de 2026"
lang: pt-BR
---

# 1. A resposta direta

O método tinha quatro defeitos. **Três eu corrigi. O quarto é o mais grave e só
você pode resolver.**

E ele é decisivo: **do jeito que o conjunto de teste está hoje, o modelo novo vai
empatar com o SFace.** Não porque seja igual, mas porque o teste não consegue
separar os dois. Trocar de modelo com base nesta nota seria decidir no escuro.

# 2. Sobre o seu 0,440

Você baixou o limiar para 0,440 e funcionou melhor. **A sua evidência é melhor que
a minha.**

Eu calibrei 0,45 comparando as três fotos `IMG_1128/1129/1130` entre si. São três
selfies tiradas na mesma sessão, com o mesmo celular. Achar uma a partir da outra é
quase reconhecer uma cópia — tarefa fácil.

Olhando as fotos que você enviou pela página, vi o que você estava realmente
testando: você subiu **fotos do evento** (`IMG_3008`, `IMG_3012`, `IMG_3016`,
`IMG_3020`, `IMG_2993`) e pediu para achar aquelas pessoas nas outras fotos. Essa é
a tarefa do produto — mesma pessoa, ângulos diferentes, distâncias diferentes, luz
diferente — e é muito mais difícil.

Nessas consultas aparecem casos exatamente na faixa onde o limiar decide:

| Consulta | Resultado | Similaridade | Passa em 0,44? | Passa em 0,45? |
|---|---|---|---|---|
| pessoa de `IMG_3008` | `IMG_3214` | 0,4780 | sim | sim |
| pessoa de `IMG_3008` | `IMG_3004` | 0,4605 | sim | sim |
| pessoa de `IMG_3008` | `IMG_3028` | 0,4235 | **não** | não |
| pessoa de `IMG_3016` | `IMG_3213` | 0,4628 | sim | sim |

Meu gabarito não tem **nenhum** caso nessa faixa. Ele nunca poderia ter apontado o
0,44. Você achou olhando o problema real; eu calibrei olhando um problema fácil.

# 3. Os quatro defeitos

## Defeito 1 — o gabarito testa a tarefa errada (GRAVE, aberto)

O gabarito tem uma pessoa, três fotos, todas selfies da mesma sessão. E essa pessoa
**não estava no evento**.

Isso significa que o teste mede "achar uma selfie a partir de outra selfie", quando
o produto precisa de "achar a pessoa em fotos de evento, de longe, de lado, com
outra iluminação". São dificuldades diferentes. Um modelo pode ir muito bem numa e
mal na outra.

**Consequência medida:** no conjunto atual o SFace tira nota máxima em tudo que
mede qualidade — AUC 1,000, mAP 1,000, zero intrusos. Não sobra espaço para o
modelo novo ser melhor. A comparação passaria a ser decidida só pela velocidade.

Isto não se conserta com métrica melhor. Só com conjunto mais difícil.

## Defeito 2 — o limiar era calibrado e avaliado nos mesmos dados (CORRIGIDO)

Eu escolhi 0,45 usando o gabarito e depois anunciei F1 = 1,000 medido no mesmo
gabarito. O resultado estava garantido por construção — é o erro clássico de
"treinar no teste".

**Correção:** validação cruzada. O limiar que julga uma consulta é calibrado
**sem** ver essa consulta. Nas três consultas, F1 = 1,000 com limiares 0,4465,
0,4506 e 0,4506. Agora é uma estimativa honesta, e não uma tautologia.

## Defeito 3 — a nota dependia da escala de similaridade (CORRIGIDO)

A nota antiga media F1 num limiar. Mas o cosseno do SFace vai de −1 a 1 e uma API
paga pode devolver 0 a 100. Comparar modelos num mesmo número não compara nada.

**Correção:** a maior parte da nota agora vem da **ordem** do ranking, que não
depende de escala nenhuma:

| Componente | Pontos | O que é |
|---|---|---|
| Ordenação | 40 | mAP — os acertos ficaram no topo? |
| Separação | 25 | fração dos erros abaixo do pior acerto |
| Robustez | 15 | F1 na validação cruzada |
| Busca | 10 | milissegundos |
| Indexação | 10 | segundos por foto |

Também troquei a medida de separação. A antiga (d-prime, "σ") divide pelo
desvio-padrão dos erros e pressupõe uma distribuição bem comportada — com 3583
rostos de estranhos, não é. A nova só conta: *que fração dos erros ficou abaixo do
pior acerto?* Não supõe nada e continua comparável entre modelos.

## Defeito 4 — o código não fazia o que o documento prometia (CORRIGIDO)

O `SISTEMA-DE-PONTUACAO.md` afirmava que cada modelo seria avaliado no seu melhor
limiar. A função existia (`scoring.melhor_limiar`) e **nunca era chamada**: a nota
saía no limiar passado na linha de comando. Erro meu, de ligação.

**Correção:** o melhor limiar de cada consulta agora é calculado e aparece no
relatório. E a nota de comparação nem depende mais dele.

# 4. O que foi verificado e está bom

- **Tempo é confiável.** Três medições da indexação: 0,1901 / 0,1905 / 0,1901 s por
  foto — 0,2% de variação. A oscilação que eu tinha visto antes (0,12 a 0,27) era
  mudança de código, não ruído. Como a velocidade pode acabar decidindo o empate,
  era importante confirmar isso.
- **A exclusão da auto-correspondência funciona.** A foto de consulta casando
  consigo mesma não entra em nenhuma métrica.
- **Fotos que o detector perdeu contam como erro.** Foto que existia e não foi
  indexada entra como perdida, não é ignorada — é o que o visitante sente.
- **O diagnóstico do conjunto avisa sozinho** quando o teste está saturado ou com
  amostra pequena. Hoje ele avisa as duas coisas.

# 5. O que fazer antes de trocar de modelo

O gabarito precisa conter a tarefa real. Isso quer dizer: **pessoas que estavam no
evento, aparecendo em várias fotos diferentes.**

Não precisa ser grande. Com **4 a 6 pessoas do evento**, cada uma marcada nas fotos
em que aparece, o conjunto passa a ter casos difíceis — e aí a nota volta a
significar alguma coisa.

O trabalho é marcar. Para cada pessoa escolhida:

1. escolha uma foto dela como consulta;
2. rode a busca;
3. percorra o ranking de cima para baixo e marque quais são realmente ela;
4. desça até onde as similaridades ficarem claramente baixas.

A parte boa: como o ranking já vem ordenado, você não olha 204 fotos por pessoa —
olha as 15 ou 20 primeiras.

Depois disso, três coisas mudam:

- o limiar passa a ser calibrado na tarefa certa (e provavelmente confirma o seu
  0,44 em vez do meu 0,45);
- a nota volta a discriminar, porque vão existir casos que um modelo acerta e o
  outro erra;
- o TCC pode afirmar precisão sobre o problema real, não sobre selfies.

# 6. O que a nota diz hoje

**YuNet + SFace — 97,8 / 100**, com dois avisos que o próprio relatório imprime:

> CONJUNTO SATURADO: todos os acertos ficaram acima de todos os erros. Um modelo
> melhor vai empatar aqui — a nota passa a ser decidida só pela velocidade.

> AMOSTRA PEQUENA: 6 acertos esperados no total. Uma foto a mais ou a menos muda a
> métrica em dezenas de pontos percentuais.

Leia a nota junto com os avisos. Sozinha, ela parece dizer que o modelo é quase
perfeito. Com os avisos, ela diz a verdade: **o modelo passou num teste fácil.**
