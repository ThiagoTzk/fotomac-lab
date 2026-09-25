"""Página de marcação manual do gabarito (/marcar).

É onde o julgamento humano entra no sistema: o modelo propõe o ranking, a
pessoa confirma foto a foto. Sem isso não existe acerto nem erro, só
similaridade."""

PAGINA_MARCAR = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FotoMac — marcar gabarito</title>
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
  /* ------- modo revisão: uma foto por vez, grande, pelo teclado -------- */
  .rev{position:fixed;inset:0;background:#0b0b0b;z-index:100;display:none;
    flex-direction:column}
  .rev.on{display:flex}
  .rev-top{display:flex;align-items:center;gap:14px;padding:10px 16px;
    background:#151513;color:#e8e8e4;flex-wrap:wrap;flex-shrink:0}
  .rev-top .nome{font-family:ui-monospace,Menlo,monospace;font-size:12.5px;color:#a9a8a1}
  .rev-sim{font-variant-numeric:tabular-nums;font-weight:800;font-size:20px}
  .rev-sim.acima{color:#6ea2ff}
  .rev-pos{color:#a9a8a1;font-size:13px}
  /* A foto ocupa a area inteira e é encaixada por object-fit:contain.
     Antes, `.rev-img` não tinha altura definida, então o `max-height:100%` da
     <img> não resolvia, ela saía no tamanho natural e o `overflow:hidden` do
     pai cortava — era isso que parecia "zoom alto demais".
     A caixa verde deixou de ser posicionada em porcentagem do elemento e passa
     a ser posicionada em pixels sobre a area REAL da foto, calculada no JS. */
  .rev-mid{flex:1;position:relative;overflow:hidden;background:#000}
  .rev-img{position:absolute;inset:0}
  .rev-img img{width:100%;height:100%;display:block;object-fit:contain}
  .rev-img .box{position:absolute}
  .rev-img .box{border-color:#4fd07f;border-width:4px;
    box-shadow:0 0 0 2px rgba(0,0,0,.75),0 0 26px rgba(79,208,127,.55)}
  /* recorte ampliado do rosto: é o que decide quando a pessoa está de lado */
  .rev-zoom{position:absolute;right:14px;top:14px;width:210px;height:210px;
    border:3px solid #4fd07f;border-radius:10px;overflow:hidden;background:#000;
    box-shadow:0 8px 30px rgba(0,0,0,.6)}
  .rev-zoom img{position:absolute;transform-origin:0 0;max-width:none;max-height:none}
  .rev-zoom span{position:absolute;left:0;right:0;bottom:0;background:rgba(0,0,0,.72);
    color:#dfe7df;font-size:10.5px;text-align:center;padding:2px}
  .rev-bot{display:flex;align-items:center;gap:12px;padding:12px 16px;
    background:#151513;flex-wrap:wrap;flex-shrink:0}
  .rev-b{padding:11px 22px;border-radius:9px;border:none;font-size:15px;
    font-weight:800;cursor:pointer;color:#fff}
  .rev-b.s{background:#0ca30c} .rev-b.n{background:#d03b3b}
  .rev-b.e{background:#fab219;color:#2a2410}
  .rev-mk.errado{background:#fab219;color:#2a2410}
  .rev-b.x{background:transparent;color:#cfcec7;border:1px solid #3a3a36}
  .rev-mk{font-size:12.5px;font-weight:800;padding:4px 12px;border-radius:99px}
  .rev-mk.sim{background:#0ca30c;color:#fff} .rev-mk.nao{background:#d03b3b;color:#fff}
  .rev-mk.vazio{border:1px solid #3a3a36;color:#a9a8a1}
  .rev-dica{color:#8d8c86;font-size:12px}
  .rev-dica kbd{background:#242421;border:1px solid #3a3a36;color:#deddd6}
  .prog{height:4px;background:#242421;flex-shrink:0}
  .prog i{display:block;height:100%;background:#6ea2ff;transition:width .15s}
  @media (max-width:620px){.rev-zoom{width:120px;height:120px}}
  @media (max-width:560px){.grid{grid-template-columns:repeat(auto-fill,minmax(145px,1fr))}}
</style>
</head>
<body>
<!--__TOPO__-->
<div class="wrap">
  <h1>Marcar o gabarito</h1>
  <p class="sub">Escolha uma pessoa, e diga foto por foto se ela está ou não está.
    É isso que transforma "o modelo achou 32 fotos" em "o modelo acertou 27 e errou 5".
    Sem esta marcação, nenhuma comparação entre modelos mede acerto.</p>

  <div class="panel">
    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap">
      <div><b>Tecnologia em teste</b>
        <div style="color:var(--muted);font-size:12.5px">O visto verde marca os que
          você já conferiu foto a foto. Todos rodam na configuração de fábrica,
          menos o SFace, que foi calibrado aqui.</div></div>
      <span id="mod-status" style="font-size:12.5px;color:var(--muted)"></span>
    </div>
    <div class="mods" id="mods"></div>
  </div>
  <div class="panel">
    <div class="campos">
      <div><label for="pessoa">Nome da pessoa</label>
        <input type="text" id="pessoa" placeholder="ex.: coordenador"></div>
      <div><label for="descricao">Descrição (opcional)</label>
        <input type="text" id="descricao" placeholder="ex.: Prof. coordenador do curso"></div>
      <div><label for="consulta">Foto de consulta</label>
        <select id="consulta"><option value="">carregando...</option></select></div>
      <div><label for="quantos">Quantas fotos revisar</label>
        <select id="quantos">
          <option value="40">as 40 mais parecidas</option>
          <option value="80" selected>as 80 mais parecidas</option>
          <option value="150">as 150 mais parecidas</option>
          <option value="400">o acervo inteiro</option>
        </select></div>
    </div>
    <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap;align-items:center">
      <button class="btn" id="b-carregar">Carregar ranking</button>
      <span style="color:var(--muted);font-size:12.5px">
        Atalhos: <kbd>S</kbd> está &nbsp;<kbd>N</kbd> não está &nbsp;<kbd>←</kbd><kbd>→</kbd> navegar
        &nbsp;<kbd>Esc</kbd> desmarcar</span>
    </div>
  </div>

  <div id="saida"></div>
</div>

<div class="rev" id="rev">
  <div class="rev-top">
    <span class="rev-sim" id="rv-sim"></span>
    <span class="nome" id="rv-nome"></span>
    <span class="rev-mk" id="rv-mk"></span>
    <div style="flex:1"></div>
    <span class="rev-pos" id="rv-pos"></span>
    <button class="rev-b x" id="rv-sair">Sair (Esc)</button>
  </div>
  <div class="prog"><i id="rv-prog"></i></div>
  <div class="rev-mid">
    <div class="rev-img" id="rv-img"></div>
    <div class="rev-zoom" id="rv-zoom"><span>rosto comparado</span></div>
  </div>
  <div class="rev-bot">
    <button class="rev-b ok" id="rv-ok-b">ENTER — confirmo a proposta</button>
    <button class="rev-b s" id="rv-sim-b">S — ESTÁ (rosto certo)</button>
    <button class="rev-b e" id="rv-err-b">E — ESTÁ, rosto errado</button>
    <button class="rev-b n" id="rv-nao-b">N — NÃO ESTÁ</button>
    <button class="rev-b x" id="rv-limpa">Backspace — tirar marca</button>
    <div style="flex:1"></div>
    <span class="rev-dica"><kbd>←</kbd><kbd>→</kbd> navegar sem marcar ·
      <kbd>Enter</kbd> aceita a proposta do modelo ·
      <kbd>Z</kbd> liga/desliga o recorte · marcar já pula para a próxima</span>
  </div>
</div>

<div class="barra" id="barra" style="display:none">
  <div class="cont" id="cont"></div>
  <div style="flex:1"></div>
  <button class="btn" id="b-revisar">Revisar em tela cheia</button>
  <button class="btn sec" id="b-aceitar">Aceitar as propostas restantes</button>
  <button class="btn sec" id="b-resto-nao">Marcar o resto como "não está"</button>
  <button class="btn" id="b-salvar">Salvar no gabarito</button>
  <span id="status" style="font-size:13px;color:var(--muted)"></span>
</div>

<script>
let R = null, marcas = {}, atual = 0, aceitas_em_bloco = 0;

/* A resposta que o modelo daria sozinho, no limiar em uso.
   Fica separada de `marcas` de propósito: proposta não é gabarito. Ela aparece
   tracejada na tela e só vira marca quando você confirma — senão a contagem de
   "fotos conferidas" incluiria fotos que ninguém olhou.                       */
function proposta(arq){
  const it = R && R.itens.find(x => x.arquivo === arq);
  return it ? it.proposta : null;
}

/* ===================================================================== */
/* Seletor de tecnologia.                                                */
/*                                                                       */
/* O selo verde não é decorativo: ele marca que ALGUÉM CONFERIU fotos com */
/* aquele modelo. Indexar não acende o selo — indexar só produz números,  */
/* e número sem conferência humana não prova nada.                       */
/* ===================================================================== */
let MODELOS = [], TROCANDO = false;

async function carregaModelos(){
  const r = await (await fetch('/modelos')).json();
  MODELOS = r.modelos;
  pintaModelos();
}

function pintaModelos(){
  const box = document.getElementById('mods');
  if (!box) return;
  box.innerHTML = MODELOS.map(m => `
    <div class="mod ${m.ativo?'ativo':''} ${TROCANDO?'ocupado':''}" data-k="${esc(m.chave)}">
      <span class="check ${m.verificado?'on':'off'}"
        title="${m.verificado?'Você já conferiu fotos com este modelo':'Ainda não conferido'}">
        ${m.verificado?'&#10003;':'&#9675;'}</span>
      <div class="nome">${esc(m.rotulo)}</div>
      <div class="desc">${esc(m.descricao)}</div>
      <div class="pe">
        ${m.de_fabrica ? '<span class="selo fab">de fábrica</span>'
                       : '<span class="selo">calibrado por nós</span>'}
        ${m.verificado ? `<span class="selo ok">${m.marcadas} foto(s) conferida(s)</span>` : ''}
        ${m.carregado ? '<span class="selo">indexado</span>'
                      : `<span class="selo">~${m.estimativa_min} min para indexar</span>`}
      </div>
    </div>`).join('');
  for (const el of box.querySelectorAll('.mod'))
    el.onclick = () => trocaModelo(el.dataset.k);
}

async function trocaModelo(chave){
  if (TROCANDO) return;
  const m = MODELOS.find(x => x.chave === chave);
  if (!m || m.ativo) return;
  if (!m.carregado && !confirm(
      `Indexar o acervo com "${m.rotulo}" leva cerca de ${m.estimativa_min} minutos.\n\n`
      + `Isso acontece uma vez só: depois fica em cache e a troca é instantânea.\n\nComeçar?`))
    return;
  TROCANDO = true; pintaModelos();
  const av = document.getElementById('mod-status');
  if (av) av.innerHTML = `<span class="spin"></span> preparando ${esc(m.rotulo)}...`;
  try{
    const r = await (await fetch('/modelo/trocar', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({modelo: chave})})).json();
    if (!r.ok){ if (av) av.textContent = 'Erro: ' + r.erro; }
    else if (av) av.textContent =
      `${r.rotulo}: ${r.rostos} rostos em ${r.fotos_com_rosto} fotos.`;
  } catch(e){ if (av) av.textContent = 'Falhou: ' + e.message; }
  TROCANDO = false;
  await carregaModelos();
  if (typeof aoTrocarModelo === 'function') aoTrocarModelo();
}

/* ao trocar de modelo, o ranking antigo deixa de valer */
function aoTrocarModelo(){ if (R) { R = null; marcas = {};
  document.getElementById('saida').innerHTML =
    '<div class="aviso">Modelo trocado. Carregue o ranking de novo.</div>';
  document.getElementById('barra').style.display = 'none'; } }
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

/* ------------------------------------------------ carregar as opções --- */
carregaModelos();
fetch('/consultas').then(r=>r.json()).then(d=>{
  const sel = $('#consulta');
  const op = (v,t) => `<option value="${esc(v)}">${esc(t)}</option>`;
  sel.innerHTML = '<option value="">escolha uma foto</option>'
    + (d.consultas.length ? '<optgroup label="Fotos que você tirou ou enviou">'
        + d.consultas.map(n=>op(n,n)).join('') + '</optgroup>' : '')
    + '<optgroup label="Fotos do acervo">'
    + d.acervo.map(n=>op(n,n)).join('') + '</optgroup>';
});

/* -------------------------------------------------------- carregar ----- */
$('#b-carregar').onclick = async () => {
  const consulta = $('#consulta').value, pessoa = $('#pessoa').value.trim();
  if (!consulta) return alert('Escolha a foto de consulta.');
  if (!pessoa) return alert('Dê um nome à pessoa — é a chave no gabarito.');
  $('#saida').innerHTML = '<div class="panel"><span class="spin"></span> buscando...</div>';
  const r = await (await fetch('/marcar/ranking', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({consulta, pessoa, quantos: +$('#quantos').value})})).json();
  if (!r.ok){ $('#saida').innerHTML = `<div class="panel aviso">${esc(r.erro)}</div>`; return; }
  R = r; marcas = {}; atual = 0;
  for (const it of r.itens) if (it.marca) marcas[it.arquivo] = it.marca;
  aceitas_em_bloco = 0;
  render();
};

/* ---------------------------------------------------------- render ----- */
function render(){
  const [bx,by,bw,bh] = R.caixa_consulta;
  let cards = '', passouLimiar = false;
  R.itens.forEach((it,i)=>{
    if (!passouLimiar && it.similaridade < R.limiar){
      passouLimiar = true;
      cards += `<div class="div-limiar">abaixo do limiar ${R.limiar} —
        o sistema NÃO mostraria estas ao visitante</div>`;
    }
    const [x,y,w,h] = it.caixa;
    const m = marcas[it.arquivo];
    const cls = m ? m : `prop prop-${it.proposta}`;
    cards += `<div class="card ${cls}" data-i="${i}" tabindex="0">
      <div class="ph">
        <img src="/thumb/${encodeURIComponent(it.arquivo)}" alt="" loading="lazy">
        <div class="box" style="left:${x*100}%;top:${y*100}%;width:${w*100}%;height:${h*100}%"></div>
      </div>
      <div class="meta">
        <div class="fname">${esc(it.arquivo)}</div>
        <div class="row">
          <span class="sim-v ${it.similaridade>=R.limiar?'acima':''}">${it.similaridade.toFixed(4)}</span>
          <span class="mk">${m ? rotulo(m)
            : (it.proposta==='sim' ? 'o modelo diz: ESTÁ' : 'o modelo diz: não')}</span>
        </div>
        <div style="color:var(--muted);font-size:10.5px;margin-top:2px">${it.rostos} rosto(s)</div>
      </div></div>`;
  });

  $('#saida').innerHTML = `
    <div class="panel" style="display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap">
      <div class="qprev"><img src="${esc(R.consulta_url)}" alt="consulta">
        <div class="box" style="left:${bx*100}%;top:${by*100}%;width:${bw*100}%;height:${bh*100}%"></div></div>
      <div style="flex:1;min-width:260px">
        <p style="margin:0 0 6px"><b>${esc(R.consulta)}</b> — ${R.itens.length} foto(s)
          para revisar, de ${R.total_no_acervo} no acervo. Busca em ${R.busca_ms} ms.</p>
        <p style="margin:0 0 8px;padding:8px 11px;border-radius:8px;
          background:var(--warn-bg);color:var(--warn-ink);font-size:13px">
          Marcando com <b>${esc(R.modelo_rotulo)}</b>. Cada tecnologia tem o seu
          gabarito — o que você marcar aqui <b>não</b> vai para as outras.
          ${R.ja_marcadas ? `Já havia ${R.ja_marcadas} foto(s) conferida(s) com este modelo.` : ''}</p>
        <p style="margin:0 0 8px"><b>O modelo já respondeu:</b>
          ${R.itens.filter(i=>i.proposta==='sim').length} "está" e
          ${R.itens.filter(i=>i.proposta==='nao').length} "não está", no limiar ${R.limiar}.
          As propostas aparecem <b>tracejadas</b>; você confirma ou corrige, e aí
          viram marcação.</p>
        <p style="margin:0;color:var(--ink-2);font-size:13px">
          Clique numa foto para alternar <b>está</b> → <b>não está</b> → sem marca.
          A caixa verde mostra o rosto que o modelo comparou — numa foto de plateia,
          é ela que diz de quem ele está falando.</p>
      </div>
    </div>
    <div class="aviso"><b>Revisar em tela cheia</b> (botão na barra de baixo, ou
      duplo clique numa foto) abre a imagem grande, com o rosto comparado ampliado
      no canto — marcar com <kbd>S</kbd>/<kbd>N</kbd> já pula para a próxima.
      É o jeito de julgar rosto de lado sem sair do site.<br><br>
      <b>Três respostas, não duas:</b> <kbd>S</kbd> a pessoa está e o modelo
      marcou o rosto dela · <kbd>E</kbd> a pessoa está, mas o modelo marcou o
      rosto de outra · <kbd>N</kbd> a pessoa não está.
      O <kbd>E</kbd> separa acerto de coincidência: a foto é dela, mas a
      similaridade veio do rosto errado e não se repete.<br><br>
      Marque <b>todas</b> que você olhar, inclusive as que estão
      abaixo do limiar. É só assim que dá para contar as que o modelo <b>deixou
      escapar</b> — e foi exatamente isso que você encontrou olhando à mão.</div>
    <div class="grid" id="grid">${cards}</div>`;

  for (const c of document.querySelectorAll('.card')){
    c.onclick = () => { atual = +c.dataset.i; alterna(R.itens[atual].arquivo); };
    c.ondblclick = e => { e.preventDefault(); abreRevisao(+c.dataset.i); };
  }
  $('#barra').style.display = 'flex';
  contadores(); foco();
}

/* --------------------------------------------------------- marcação ---- */
function alterna(arq, forca){
  const a = marcas[arq];
  // ciclo: sem marca -> está -> está mas rosto errado -> não está -> sem marca
  marcas[arq] = forca !== undefined ? forca
              : (a === 'sim' ? 'errado' : a === 'errado' ? 'nao'
                 : a === 'nao' ? undefined : 'sim');
  if (!marcas[arq]) delete marcas[arq];
  const i = R.itens.findIndex(x=>x.arquivo===arq);
  const card = document.querySelector(`.card[data-i="${i}"]`);
  card.classList.remove('sim','nao','errado','prop','prop-sim','prop-nao');
  if (marcas[arq]){
    card.classList.add(marcas[arq]);
    card.querySelector('.mk').textContent = rotulo(marcas[arq]);
  } else {
    const pr = proposta(arq);
    card.classList.add('prop', 'prop-' + pr);
    card.querySelector('.mk').textContent =
      pr === 'sim' ? 'o modelo diz: ESTÁ' : 'o modelo diz: não';
  }
  contadores();
}

/* Conta acertos e erros COMO SE o limiar em uso fosse a decisão do sistema.
   É a tradução direta do que ele quer saber: quantas ele acertou, quantas errou. */
function rotulo(m){
  return m==='sim' ? 'ESTÁ' : m==='errado' ? 'ROSTO ERRADO'
       : m==='nao' ? 'NÃO ESTÁ' : '?';
}

/* Conta pelas duas leituras ao mesmo tempo:
   MODELO  — só "está com o rosto certo" é acerto; rosto errado é erro.
   PRODUTO — "está" e "rosto errado" são acerto, porque a foto entregue tem
             mesmo a pessoa e o visitante fica satisfeito.                    */
function contadores(){
  let tp=0, fp=0, fn=0, tn=0, semMarca=0, err=0, tpProduto=0, fnProduto=0;
  let confirmadas=0;
  for (const it of R.itens){
    const m = marcas[it.arquivo];
    if (!m){ semMarca++; continue; }
    confirmadas++;
    const mostrou = it.similaridade >= R.limiar;
    const presente = (m==='sim' || m==='errado');
    if (m==='errado') err++;
    if (presente && mostrou) tpProduto++; else if (presente) fnProduto++;
    if (m==='sim' && mostrou) tp++;
    else if (m==='sim') fn++;
    else if (mostrou) fp++;
    else tn++;
  }
  const prec = tp+fp ? tp/(tp+fp) : 0, rec = tp+fn ? tp/(tp+fn) : 0;
  const f1 = prec+rec ? 2*prec*rec/(prec+rec) : 0;
  const recProd = tpProduto+fnProduto ? tpProduto/(tpProduto+fnProduto) : 0;
  $('#cont').innerHTML = `
    <div><b style="color:var(--ok)">${tp}</b><span>acertou (rosto certo)</span></div>
    <div><b style="color:var(--warn-ink)">${err}</b><span>está na foto, rosto errado</span></div>
    <div><b style="color:var(--no)">${fp}</b><span>errou (mostrou e não é)</span></div>
    <div><b>${fn}</b><span>deixou escapar</span></div>
    <div><b>${(prec*100).toFixed(0)}%</b><span>precisão (modelo)</span></div>
    <div><b>${(rec*100).toFixed(0)}%</b><span>recall (modelo)</span></div>
    <div><b>${(f1*100).toFixed(0)}%</b><span>F1 no limiar ${R.limiar}</span></div>
    <div><b style="color:var(--acc)">${(recProd*100).toFixed(0)}%</b><span>recall do produto</span></div>
    <div><b style="color:var(--muted)">${semMarca}</b><span>só proposta, não confirmada</span></div>
    <div><b>${confirmadas}</b><span>conferidas por você</span></div>`;
}

function foco(){
  document.querySelectorAll('.card').forEach(c=>c.classList.remove('atual'));
  const c = document.querySelector(`.card[data-i="${atual}"]`);
  if (c){ c.classList.add('atual'); c.scrollIntoView({block:'nearest', behavior:'smooth'}); }
}


/* ===================================================================== */
/* MODO REVISÃO — uma foto por vez, grande, tudo pelo teclado.           */
/*                                                                       */
/* Existe porque a miniatura não decide nada: quando a pessoa está de     */
/* lado, ou só aparece a lateral da cabeça, 190px não bastam. Sair do     */
/* site para abrir o arquivo à mão é o que trava a marcação — aqui a      */
/* foto abre em tamanho cheio e a marcação já pula para a próxima.       */
/* ===================================================================== */
let revI = 0, revOn = false, zoomOn = true;

function abreRevisao(i){
  revI = Math.max(0, Math.min(R.itens.length-1, i ?? atual));
  revOn = true;
  document.getElementById('rev').classList.add('on');
  document.body.style.overflow = 'hidden';
  pintaRevisao();
}
function fechaRevisao(){
  revOn = false;
  document.getElementById('rev').classList.remove('on');
  document.body.style.overflow = '';
  atual = revI; render();          // devolve a grade já com o que foi marcado
}

function pintaRevisao(){
  const it = R.itens[revI];
  const m = marcas[it.arquivo];
  const [x,y,w,h] = it.caixa;

  document.getElementById('rv-sim').textContent = it.similaridade.toFixed(4);
  document.getElementById('rv-sim').className =
    'rev-sim' + (it.similaridade >= R.limiar ? ' acima' : '');
  document.getElementById('rv-nome').textContent =
    it.arquivo + ' · ' + it.rostos + ' rosto(s) na foto'
    + (it.similaridade >= R.limiar ? ' · o sistema MOSTRARIA' : ' · o sistema ESCONDERIA');

  const mk = document.getElementById('rv-mk');
  const pr = it.proposta;
  if (m){ mk.className = 'rev-mk ' + m; mk.textContent = rotulo(m) + ' (você)'; }
  else { mk.className = 'rev-mk prop';
         mk.textContent = (pr === 'sim' ? 'o modelo diz: ESTÁ' : 'o modelo diz: não está')
                          + ' — confirme'; }
  const bOk = document.getElementById('rv-ok-b');
  bOk.textContent = `ENTER — confirmo: ${pr === 'sim' ? 'ESTÁ' : 'NÃO ESTÁ'}`;
  bOk.style.display = m ? 'none' : '';

  const marcadas = R.itens.filter(t => marcas[t.arquivo]).length;
  document.getElementById('rv-pos').textContent =
    `${revI+1} de ${R.itens.length} · ${marcadas} confirmada(s) por você`;
  document.getElementById('rv-prog').style.width =
    (100*(revI+1)/R.itens.length).toFixed(1) + '%';

  // a foto em tamanho cheio (o original, não a miniatura)
  const alvo = document.getElementById('rv-img');
  alvo.innerHTML = `<img id="rv-foto" src="/foto/${encodeURIComponent(it.arquivo)}" alt="">
    <div class="box" id="rv-caixa"></div>`;

  const foto = document.getElementById('rv-foto');
  const desenha = () => { posicionaCaixa(foto, it); zoomRosto(foto, it); };
  foto.onload = desenha;
  if (foto.complete && foto.naturalWidth) desenha();
  window.onresize = () => { if (revOn) desenha(); };

  // pré-carrega as vizinhas: sem isto cada S/N espera o download da próxima
  for (const j of [revI+1, revI+2, revI-1]){
    if (j >= 0 && j < R.itens.length)
      new Image().src = '/foto/' + encodeURIComponent(R.itens[j].arquivo);
  }
}

/* Onde a foto REALMENTE está dentro do quadro.
   Com object-fit:contain sobra faixa preta em cima/baixo ou nas laterais. A
   caixa do rosto vem em fração da FOTO, não do quadro — posicionar em
   porcentagem do elemento colocaria a caixa fora do rosto em toda foto cuja
   proporção não bate com a da tela.                                          */
function areaDaFoto(foto){
  const cw = foto.clientWidth, ch = foto.clientHeight;
  const nw = foto.naturalWidth || 1, nh = foto.naturalHeight || 1;
  const k = Math.min(cw / nw, ch / nh);
  const w = nw * k, h = nh * k;
  return {x: (cw - w) / 2, y: (ch - h) / 2, w, h};
}

function posicionaCaixa(foto, it){
  const caixa = document.getElementById('rv-caixa');
  if (!caixa) return;
  const a = areaDaFoto(foto);
  const [x, y, w, h] = it.caixa;
  caixa.style.left   = (a.x + x * a.w) + 'px';
  caixa.style.top    = (a.y + y * a.h) + 'px';
  caixa.style.width  = (w * a.w) + 'px';
  caixa.style.height = (h * a.h) + 'px';
}

/* Recorte ampliado do rosto que o modelo comparou. É o que resolve o caso
   difícil: numa foto de plateia, saber DE QUEM o número está falando.      */
function zoomRosto(foto, it){
  const cx = document.getElementById('rv-zoom');
  cx.style.display = zoomOn ? '' : 'none';
  if (!zoomOn) return;
  const lado = cx.clientWidth || 210;
  const a = areaDaFoto(foto);
  const [x,y,w,h] = it.caixa;
  const fw = Math.max(w * a.w, 1), fh = Math.max(h * a.h, 1);
  // rosto ocupando ~70% da caixinha; teto de 12x para um rosto de 10px não
  // virar um borrão de 200px que não ajuda ninguém a decidir
  const k = Math.min((lado * 0.7) / Math.max(fw, fh), 12);
  const px = lado / 2 - (a.x + x * a.w + fw / 2) * k;
  const py = lado / 2 - (a.y + y * a.h + fh / 2) * k;
  cx.querySelector('img')?.remove();
  const clone = document.createElement('img');
  clone.src = foto.src;
  clone.style.width = foto.clientWidth + 'px';
  clone.style.height = foto.clientHeight + 'px';
  clone.style.objectFit = 'contain';
  clone.style.transform = `translate(${px}px, ${py}px) scale(${k})`;
  clone.style.transformOrigin = '0 0';
  cx.prepend(clone);
}

function marcaEAvanca(valor){
  const it = R.itens[revI];
  marcas[it.arquivo] = valor;
  if (!valor) delete marcas[it.arquivo];
  contadoresRev();
  if (valor && revI < R.itens.length - 1){ revI++; pintaRevisao(); }
  else pintaRevisao();
}

/* mantém a barra de baixo da grade em dia enquanto se revisa em tela cheia */
function contadoresRev(){ if (R) contadores(); }

document.getElementById('rv-sair').onclick = fechaRevisao;
document.getElementById('rv-sim-b').onclick = () => marcaEAvanca('sim');
document.getElementById('rv-ok-b').onclick = () =>
  marcaEAvanca(proposta(R.itens[revI].arquivo));
document.getElementById('rv-err-b').onclick = () => marcaEAvanca('errado');
document.getElementById('rv-nao-b').onclick = () => marcaEAvanca('nao');
document.getElementById('rv-limpa').onclick = () => marcaEAvanca(undefined);
document.getElementById('b-revisar').onclick = () => abreRevisao(0);

document.addEventListener('keydown', e => {
  if (!revOn || /INPUT|SELECT/.test(e.target.tagName)) return;
  const k = e.key.toLowerCase();
  if (k === 's'){ marcaEAvanca('sim'); e.preventDefault(); }
  else if (k === 'e'){ marcaEAvanca('errado'); e.preventDefault(); }
  else if (k === 'n'){ marcaEAvanca('nao'); e.preventDefault(); }
  else if (e.key === 'Enter'){ marcaEAvanca(proposta(R.itens[revI].arquivo));
                               e.preventDefault(); }
  else if (e.key === 'Backspace'){ marcaEAvanca(undefined); e.preventDefault(); }
  else if (e.key === 'ArrowRight'){ if (revI < R.itens.length-1){ revI++; pintaRevisao(); } e.preventDefault(); }
  else if (e.key === 'ArrowLeft'){ if (revI > 0){ revI--; pintaRevisao(); } e.preventDefault(); }
  else if (k === 'z'){ zoomOn = !zoomOn; pintaRevisao(); e.preventDefault(); }
  else if (e.key === 'Escape'){ fechaRevisao(); e.preventDefault(); }
  e.stopPropagation();
}, true);

document.addEventListener('keydown', e => {
  if (!R || revOn || /INPUT|SELECT/.test(e.target.tagName)) return;
  const k = e.key.toLowerCase();
  if (k==='s'){ alterna(R.itens[atual].arquivo,'sim'); avanca(1); e.preventDefault(); }
  else if (k==='e'){ alterna(R.itens[atual].arquivo,'errado'); avanca(1); e.preventDefault(); }
  else if (k==='n'){ alterna(R.itens[atual].arquivo,'nao'); avanca(1); e.preventDefault(); }
  else if (e.key==='Enter'){ const a=R.itens[atual].arquivo;
    alterna(a, proposta(a)); avanca(1); e.preventDefault(); }
  else if (e.key==='Escape'){ alterna(R.itens[atual].arquivo, undefined); }
  else if (e.key==='ArrowRight'){ avanca(1); e.preventDefault(); }
  else if (e.key==='ArrowLeft'){ avanca(-1); e.preventDefault(); }
});
function avanca(d){ atual = Math.max(0, Math.min(R.itens.length-1, atual+d)); foco(); }

$('#b-aceitar').onclick = () => {
  const pendentes = R.itens.filter(it => !marcas[it.arquivo]);
  if (!pendentes.length) return alert('Nada pendente: tudo já foi confirmado.');
  if (!confirm(`Aceitar a resposta do modelo para ${pendentes.length} foto(s) sem `
    + `confirmação?\n\nIsso registra a opinião do modelo como se fosse sua. Use só `
    + `depois de olhar — aceitar sem olhar transforma a nota numa profecia `
    + `auto-realizável.`)) return;
  for (const it of pendentes) marcas[it.arquivo] = it.proposta;
  aceitas_em_bloco += pendentes.length;
  render();
  $('#status').textContent = `${pendentes.length} proposta(s) aceitas em bloco.`;
};

$('#b-resto-nao').onclick = () => {
  let n = 0;
  for (const it of R.itens) if (!marcas[it.arquivo]){ marcas[it.arquivo]='nao'; n++; }
  render();
  $('#status').textContent = `${n} foto(s) marcadas como "não está".`;
};

$('#b-salvar').onclick = async () => {
  const sim = [], nao = [], errado = [];
  for (const [arq,m] of Object.entries(marcas))
    (m==='sim'?sim : m==='errado'?errado : nao).push(arq);
  if (!sim.length && !nao.length && !errado.length) return alert('Nada marcado ainda.');

  const pendentes = R.itens.filter(it => !marcas[it.arquivo]).length;
  // Confirmação nomeando o modelo: era possível marcar tudo achando que estava
  // testando um e gravar no outro. Perder uma sessão inteira de conferência por
  // causa disso é caro demais para depender de atenção.
  const texto =
    `Salvar no gabarito de:\n\n    ${R.modelo_rotulo}\n\n`
    + `Pessoa: ${$('#pessoa').value.trim()}\n`
    + `${sim.length} "está"  ·  ${errado.length} "rosto errado"  ·  ${nao.length} "não está"\n`
    + (aceitas_em_bloco ? `(${aceitas_em_bloco} aceitas em bloco)\n` : '')
    + (pendentes ? `\nATENÇÃO: ${pendentes} foto(s) ainda sem confirmação — elas NÃO serão salvas.\n` : '')
    + `\nÉ este o modelo que você testou?`;
  if (!confirm(texto)) return;

  $('#status').innerHTML = '<span class="spin"></span> salvando...';
  const revisadas = R.itens.filter(it=>marcas[it.arquivo]);
  const menor = revisadas.length ? Math.min(...revisadas.map(it=>it.similaridade)) : null;
  let r;
  try{
    r = await (await fetch('/marcar/salvar', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({pessoa: $('#pessoa').value.trim(),
        descricao: $('#descricao').value.trim(), consulta: R.consulta,
        sim, nao, rosto_errado: errado, menor_similaridade_revisada: menor,
        aceitas_em_bloco, ranking_visto: R.itens.length})})).json();
  } catch(e){ $('#status').textContent = 'Falhou: ' + e.message; return; }

  if (!r.ok){ $('#status').textContent = 'Erro: ' + r.erro; return; }
  await carregaModelos();

  // Limpa a tela para o próximo modelo. Deixar o ranking antigo na tela depois
  // de salvar é o caminho curto para marcar duas vezes a mesma coisa.
  const resumo = `${sim.length} "está", ${errado.length} "rosto errado", ${nao.length} "não está"`;
  R = null; marcas = {}; aceitas_em_bloco = 0;
  document.getElementById('barra').style.display = 'none';
  $('#saida').innerHTML = `
    <div class="panel" style="border-left:4px solid var(--ok)">
      <h3 style="margin:0 0 6px;font-size:16px">Salvo em ${esc(r.rotulo)}</h3>
      <p style="margin:0 0 4px">${resumo}.</p>
      <p style="margin:0;color:var(--muted);font-size:13px">
        Escolha a próxima tecnologia acima e carregue o ranking de novo. O gabarito
        dela começa vazio — o que você acabou de marcar vale só para
        ${esc(r.rotulo)}.</p>
    </div>`;
  $('#status').textContent = `Salvo em ${r.rotulo}.`;
};
</script>
</body>
</html>
"""
