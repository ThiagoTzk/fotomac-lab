"""Página do painel de comparação. Template separado do servidor porque é
um documento grande e tem ciclo de vida próprio — muda quando a apresentação
muda, não quando o servidor muda."""

PAGINA_PAINEL = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FotoMac — comparação de tecnologias</title>
<style>
/*__CSS_BASE__*/
  .selo-teste{display:inline-block;background:var(--s1);color:#fff;font-size:11.5px;
    font-weight:800;padding:3px 11px;border-radius:99px;letter-spacing:.04em;
    margin-bottom:10px}
  .podio{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
    margin:20px 0 6px}
  .pod{background:var(--card);border:1px solid var(--line);border-radius:14px;
    padding:16px 18px;position:relative;overflow:hidden}
  .pod.ouro{border-color:var(--s4);border-width:2px}
  .pod .med{font-size:12px;font-weight:800;color:var(--muted);letter-spacing:.06em}
  .pod.ouro .med{color:var(--s4)}
  .pod .nome{font-size:15.5px;font-weight:700;margin:4px 0 8px;line-height:1.3}
  .pod .nota{font-size:40px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums;
    letter-spacing:-.025em}
  .pod .de{color:var(--muted);font-size:12px;margin-top:2px}
  .pod .det{color:var(--ink-2);font-size:12px;margin-top:9px;
    padding-top:9px;border-top:1px solid var(--line)}
  .tiles{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));margin:18px 0}
  .tile{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
  .tile .v{font-size:31px;font-weight:750;font-variant-numeric:tabular-nums;
    letter-spacing:-.02em;line-height:1.05}
  .tile .k{color:var(--ink-2);font-size:12.5px;margin-top:3px}
  .tile .sub{color:var(--muted);font-size:11.5px;margin-top:2px}
  svg{display:block;width:100%;height:auto;overflow:visible}
  .gl{stroke:var(--grid);stroke-width:1}
  .ax{stroke:var(--axis);stroke-width:1}
  .tk{fill:var(--muted);font-size:11.5px;font-variant-numeric:tabular-nums}
  .lb{fill:var(--ink-2);font-size:12.5px}
  .vl{fill:var(--ink);font-size:12.5px;font-weight:700;font-variant-numeric:tabular-nums}
  .seg-lb{fill:#fff;font-size:11.5px;font-weight:700;font-variant-numeric:tabular-nums}
  .legend{display:flex;gap:18px;flex-wrap:wrap;margin:2px 0 14px;font-size:13px;
    color:var(--ink-2)}
  .legend i{display:inline-block;width:11px;height:11px;border-radius:3px;
    margin-right:6px;vertical-align:-1px}
  table{border-collapse:collapse;width:100%;font-size:13.5px}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
  th{color:var(--muted);font-weight:600;font-size:11.5px;text-transform:uppercase;
    letter-spacing:.05em}
  td.n{text-align:right;font-variant-numeric:tabular-nums}
  details{margin-top:12px}
  summary{cursor:pointer;color:var(--ink-2);font-size:13px}
  .nota{background:var(--warn-bg);border:1px solid var(--warn);border-left-width:4px;
    border-radius:10px;padding:14px 16px;margin:18px 0}
  .nota b{color:var(--warn-ink)}
  .nota p{margin:6px 0 0;font-size:13.5px;color:var(--ink-2)}
  .tip{position:fixed;pointer-events:none;background:var(--ink);
    color:var(--card);padding:7px 10px;border-radius:7px;font-size:12.5px;
    opacity:0;transition:opacity .09s;z-index:50;white-space:nowrap;
    font-variant-numeric:tabular-nums}
  .hit{fill:transparent;cursor:crosshair}
  footer{color:var(--muted);font-size:12.5px;margin-top:34px;
    border-top:1px solid var(--line);padding-top:14px}
  @media (max-width:560px){.wrap{padding:16px}header h1{font-size:23px}}
</style>
</head>
<body>
<!--__TOPO__-->
<div class="wrap" id="app">carregando...</div>
<div class="tip" id="tip"></div>
<script>
const CORES = ['var(--s1)','var(--s2)','var(--s3)','var(--s4)','var(--s5)'];
const esc = s => String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmt = (v,d=2) => v==null ? '—' : Number(v).toFixed(d);
let D = null;

/* ---------------------------------------------------------- tooltip ---- */
const tip = document.getElementById('tip');
function mostra(e, html){
  tip.innerHTML = html; tip.style.opacity = 1;
  const r = tip.getBoundingClientRect();
  let x = e.clientX + 14, y = e.clientY - r.height - 10;
  if (x + r.width > innerWidth - 8) x = e.clientX - r.width - 14;
  if (y < 8) y = e.clientY + 16;
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
}
function esconde(){ tip.style.opacity = 0; }

/* Pódio: as três primeiras em destaque. Numa apresentação a primeira pergunta é
   "qual ganhou", e ela precisa ser respondida antes de qualquer eixo.          */
function podio(){
  const tres = D.modelos.slice(0, 3);
  const medalhas = ['1º LUGAR', '2º LUGAR', '3º LUGAR'];
  return `<div class="podio">${tres.map((m,i)=>`
    <div class="pod ${i===0?'ouro':''}">
      <div class="med">${medalhas[i]}</div>
      <div class="nome">${esc(m.modelo)}</div>
      <div class="nota">${m.nota.toFixed(1)}</div>
      <div class="de">nota de acerto, de 0 a 100</div>
      <div class="det">AUC ${fmt(m.auc,3)} · ${m.intrusos} intruso(s) ·
        ${m.rosto_errado} rosto(s) errado(s)<br>
        ${m.de_fabrica ? 'configuração de fábrica' : 'calibrado nesta bancada'}</div>
    </div>`).join('')}</div>`;
}

/* ------------------------------------------- GRÁFICO 1: separação ------ */
/* Histograma espelhado da MELHOR tecnologia: fotos em que a pessoa aparece
   crescem para cima, fotos em que não aparece crescem para baixo. Espelhado e
   não sobreposto — com as populações misturadas, transparência vira sopa.     */
function gSeparacao(){
  const s = D.distribuicao;
  if (!s) return '';
  const W=900,H=400, ml=58,mr=24,mt=56,mb=56;
  const pw=W-ml-mr, ph=H-mt-mb;
  const x0=-0.3, x1=1.0;
  const X = v => ml + (v-x0)/(x1-x0)*pw;
  const meio = mt + ph*0.52;
  const cima = meio-mt, baixo = (mt+ph)-meio;
  const maxP = Math.max(...s.esta, ...s.rosto_errado, 1);
  const maxN = Math.max(...s.nao_esta, 1);

  let barras='';
  for (let i=0;i<s.bins.length-1;i++){
    const xa=X(s.bins[i]), xb=X(s.bins[i+1]);
    const larg=Math.max(1, xb-xa-2);
    const dica = `similaridade ${s.bins[i].toFixed(2)} a ${s.bins[i+1].toFixed(2)}`;
    const p=s.esta[i], er=s.rosto_errado[i], n=s.nao_esta[i];
    let base = meio;
    if (p){
      const h=(p/maxP)*(cima-20);
      barras += `<rect x="${xa+1}" y="${base-h}" width="${larg}" height="${h}" rx="3"
        fill="var(--s1)"></rect>`;
      base -= h + 2;
    }
    if (er){
      const h=(er/maxP)*(cima-20);
      barras += `<rect x="${xa+1}" y="${base-h}" width="${larg}" height="${Math.max(h,3)}" rx="3"
        fill="var(--s4)"></rect>`;
    }
    if (p || er) barras += `<rect class="hit" x="${xa+1}" y="${mt}" width="${larg}"
      height="${meio-mt}" data-tip="<b>a pessoa APARECE</b><br>${p} com o rosto certo${
      er?`<br>${er} com o rosto errado`:''}<br>${dica}"></rect>`;
    if (n){
      const h=(n/maxN)*(baixo-16);
      barras += `<rect x="${xa+1}" y="${meio+2}" width="${larg}" height="${h}" rx="3"
        fill="var(--s2)"></rect>
        <rect class="hit" x="${xa+1}" y="${meio+2}" width="${larg}" height="${(mt+ph)-meio}"
        data-tip="<b>${n} foto(s) SEM a pessoa</b><br>${dica}"></rect>`;
    }
  }

  let eixo='';
  for (let v=-0.2; v<=1.001; v+=0.2){
    eixo += `<line class="gl" x1="${X(v)}" y1="${mt}" x2="${X(v)}" y2="${mt+ph}"></line>
      <text class="tk" x="${X(v)}" y="${mt+ph+20}" text-anchor="middle">${v.toFixed(1)}</text>`;
  }

  const a = X(s.pior_acerto), b = X(s.melhor_erro);
  const sobrepoe = s.pior_acerto <= s.melhor_erro;
  const faixa = sobrepoe
    ? `<rect x="${a}" y="${mt}" width="${b-a}" height="${ph}" fill="var(--s4)" opacity="0.12"></rect>
       <text class="lb" x="${(a+b)/2}" y="${mt-30}" text-anchor="middle"
         fill="var(--ink)" font-weight="700">zona de confusão</text>
       <text class="tk" x="${(a+b)/2}" y="${mt-14}" text-anchor="middle">
         ${s.pior_acerto} a ${s.melhor_erro}</text>`
    : `<rect x="${b}" y="${mt}" width="${a-b}" height="${ph}" fill="var(--s3)" opacity="0.12"></rect>
       <text class="lb" x="${(a+b)/2}" y="${mt-30}" text-anchor="middle"
         fill="var(--ink)" font-weight="700">vão livre</text>`;

  return `<div class="fig">
    <h2>O que separa "é ela" de "não é ela" — ${esc(D.modelo_da_distribuicao)}</h2>
    <p class="cap">A tecnologia melhor colocada, sobre as fotos conferidas à mão.
      Para cima, as ${s.n_esta} fotos em que a pessoa aparece e o modelo marcou o
      rosto dela${s.n_errado?`, mais ${s.n_errado} em que ela aparece mas o modelo
      marcou o rosto de outra`:''}; para baixo, as ${s.n_nao} em que ela não aparece.
      Quanto mais separadas as duas nuvens, mais folga o limiar tem.</p>
    <div class="legend">
      <span><i style="background:var(--s1)"></i>aparece, rosto certo (${s.n_esta})</span>
      ${s.n_errado?`<span><i style="background:var(--s4)"></i>aparece, rosto errado (${s.n_errado})</span>`:''}
      <span><i style="background:var(--s2)"></i>não aparece (${s.n_nao})</span>
    </div>
    <svg viewBox="0 0 ${W} ${H}" role="img"
      aria-label="Histograma espelhado das similaridades de ${esc(D.modelo_da_distribuicao)}">
      ${faixa}${eixo}${barras}
      <line class="ax" x1="${ml}" y1="${meio}" x2="${W-mr}" y2="${meio}"></line>
      <text class="lb" x="${ml-8}" y="${mt+18}" text-anchor="end">aparece</text>
      <text class="lb" x="${ml-8}" y="${mt+ph-4}" text-anchor="end">não aparece</text>
      <text class="lb" x="${ml}" y="${H-6}">← menos parecido</text>
      <text class="lb" x="${W-mr}" y="${H-6}" text-anchor="end">mais parecido →</text>
    </svg>
  </div>`;
}

/* --------------------------------- GRÁFICO 2: nota por tecnologia ------ */
function gNota(){
  const ms = D.modelos;
  const W=900, alt=46, mt=14, ml=250, mr=70;
  const H = mt + ms.length*alt + 34;
  const pw = W-ml-mr;
  const max = 100;
  let barras='', eixo='';
  for (let v=0; v<=100; v+=20){
    const x = ml + v/max*pw;
    eixo += `<line class="gl" x1="${x}" y1="${mt-6}" x2="${x}" y2="${mt+ms.length*alt}"></line>
      <text class="tk" x="${x}" y="${mt+ms.length*alt+18}" text-anchor="middle">${v}</text>`;
  }
  ms.forEach((m,i)=>{
    const y = mt + i*alt + 7, h = alt-18;
    const w = m.nota/max*pw;
    barras += `<rect x="${ml}" y="${y}" width="${w}" height="${h}" rx="4"
        fill="${CORES[m.cor % CORES.length]}"></rect>
      <text class="lb" x="${ml-12}" y="${y+h/2+4}" text-anchor="end"
        fill="var(--ink)" font-weight="600">${m.posicao}º ${esc(m.modelo)}</text>
      <text class="vl" x="${ml+w+9}" y="${y+h/2+4}">${m.nota.toFixed(1)}</text>
      <rect class="hit" x="${ml}" y="${y-5}" width="${pw}" height="${h+10}"
        data-tip="<b>${m.posicao}º — ${esc(m.modelo)}</b><br>nota de acerto ${m.nota.toFixed(1)} de 100<br>mAP ${fmt(m.mAP,3)} · AUC ${fmt(m.auc,3)}<br>${m.intrusos} intruso(s) · ${m.rosto_errado} rosto(s) errado(s)"></rect>`;
  });
  const so_um = ms.length === 1;
  return `<div class="fig">
    <h2>Ranking — nota de acerto</h2>
    <p class="cap">Escala de 0 a 100: é o melhor F1 que cada tecnologia alcança
      sobre as fotos conferidas à mão. A cor identifica a tecnologia e não muda
      quando a ordem do ranking muda.</p>
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Nota final de cada tecnologia">
      ${eixo}${barras}
    </svg>
  </div>`;
}

/* ------------------------------- GRÁFICO 3: as três métricas ----------- */
/* Barras agrupadas: as mesmas três medidas para cada tecnologia. Agrupadas e
   não empilhadas porque elas NÃO somam — são três leituras independentes da
   mesma coisa, e empilhar sugeriria um total que não existe.                  */
function gComposicao(){
  const ms = D.modelos, comps = D.componentes;
  const W=900, altG=74, mt=16, ml=250, mr=64;
  const H = mt + ms.length*altG + 30;
  const pw = W-ml-mr;
  const altB = 18, gap = 3;
  let corpo='';
  ms.forEach((m,i)=>{
    const y0 = mt + i*altG + 6;
    comps.forEach((c,j)=>{
      const v = m[c.chave] || 0;
      const w = Math.max(1, v*pw);
      const y = y0 + j*(altB+gap);
      corpo += `<rect x="${ml}" y="${y}" width="${w}" height="${altB}" rx="3"
          fill="${CORES[j]}"></rect>
        <text class="vl" x="${ml+w+7}" y="${y+altB/2+4}" style="font-size:11.5px">${v.toFixed(3)}</text>
        <rect class="hit" x="${ml}" y="${y}" width="${pw}" height="${altB}"
          data-tip="<b>${esc(c.rotulo)}</b><br>${v.toFixed(4)} (de 0 a 1)<br>${esc(m.modelo)}"></rect>`;
    });
    corpo += `<text class="lb" x="${ml-12}" y="${y0+28}" text-anchor="end"
        fill="var(--ink)" font-weight="600">${m.posicao}º ${esc(m.modelo)}</text>`;
  });
  return `<div class="fig">
    <h2>As três medidas, lado a lado</h2>
    <p class="cap">Todas vão de 0 a 1 e <b>não somam</b> — são três leituras
      independentes. <b>F1</b> é o acerto no melhor limiar. <b>mAP</b> diz se os
      acertos foram para o topo do ranking. <b>AUC</b> é a chance de um acerto
      ficar acima de um erro: 0,5 é sorteio, 1,0 é separação total.</p>
    <div class="legend">${comps.map((c,j)=>
      `<span><i style="background:${CORES[j]}"></i>${esc(c.rotulo)}</span>`).join('')}</div>
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="F1, mAP e AUC de cada tecnologia">${corpo}</svg>
  </div>`;
}

/* -------------------------------------- GRÁFICO 4: velocidade ---------- */
/* Duas medidas de grandezas diferentes => DOIS gráficos. Nunca dois eixos y no
   mesmo gráfico.
   E PONTOS, não barras: o tempo de busca varia em ordens de grandeza (0,4 ms de
   um modelo local contra centenas de ms de uma API). Numa escala linear a barra
   rápida vira 2 pixels e some; numa escala log a BARRA mente, porque o
   comprimento dela deixa de ser proporcional ao valor. Ponto não promete
   proporção — então ponto pode viver em escala log, e barra não.          */
function gVelocidade(){
  const ms = D.modelos;

  function mini(titulo, campo, unidade, casas, legenda){
    const W=430, alt=38, mt=26, ml=138, mr=78;
    const H = mt + ms.length*alt + 34;
    const pw = W-ml-mr;
    const vals = ms.map(m=>m[campo]).filter(v=>v>0);
    // escala log com uma década de folga de cada lado, arredondada
    const lo = Math.floor(Math.log10(Math.min(...vals)) - 0.15);
    const hi = Math.ceil(Math.log10(Math.max(...vals)) + 0.15);
    const X = v => ml + (Math.log10(Math.max(v, Math.pow(10,lo))) - lo)/(hi-lo)*pw;

    let eixo='';
    for (let e=lo; e<=hi; e++){
      const x = X(Math.pow(10,e));
      const r = Math.pow(10,e);
      const txt = r >= 1 ? r.toLocaleString('pt-BR') : r.toString().replace('.',',');
      eixo += `<line class="gl" x1="${x}" y1="${mt-10}" x2="${x}" y2="${mt+ms.length*alt-8}"></line>
        <text class="tk" x="${x}" y="${mt+ms.length*alt+10}" text-anchor="middle">${txt}</text>`;
    }

    let corpo='';
    ms.forEach((m,i)=>{
      const y = mt + i*alt;
      const v = m[campo];
      corpo += `<line x1="${ml}" y1="${y}" x2="${X(v)}" y2="${y}"
          stroke="var(--grid)" stroke-width="2"></line>
        <circle cx="${X(v)}" cy="${y}" r="7" fill="${CORES[m.cor % CORES.length]}"
          stroke="var(--card)" stroke-width="2"></circle>
        <text class="lb" x="${ml-10}" y="${y+4}" text-anchor="end">${esc(m.modelo.split(' (')[0])}</text>
        <text class="vl" x="${X(v)+13}" y="${y+4}">${fmt(v,casas)}</text>
        <rect class="hit" x="${ml}" y="${y-13}" width="${pw+60}" height="26"
          data-tip="<b>${esc(m.modelo)}</b><br>${esc(titulo)}: ${fmt(v,casas)} ${esc(unidade)}"></rect>`;
    });

    return `<div style="flex:1;min-width:300px">
      <h3 style="font-size:14px;margin:0 0 2px">${esc(titulo)} <span style="font-weight:400;color:var(--muted)">(${esc(unidade)})</span></h3>
      <p style="color:var(--muted);font-size:12px;margin:0 0 6px">${esc(legenda)}</p>
      <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(titulo)} por tecnologia">
        ${eixo}${corpo}
        <text class="tk" x="${ml}" y="${mt+ms.length*alt+26}">escala logarítmica — cada marca é 10x</text>
      </svg></div>`;
  }

  return `<div class="fig">
    <h2>Velocidade</h2>
    <p class="cap">Duas medidas separadas, em gráficos separados: acontecem em
      momentos diferentes e têm grandezas diferentes. Somar as duas esconderia qual
      delas o visitante sente. A escala é logarítmica porque os tempos variam em
      ordens de grandeza — um modelo local responde em frações de milissegundo,
      uma API pela internet em centenas.</p>
    <div style="display:flex;gap:30px;flex-wrap:wrap">
      ${mini('Busca','busca_ms','ms',2,'o visitante espera por isto, na frente do totem')}
      ${mini('Indexação','index_s','s por foto',3,'roda uma vez, sem ninguém esperando')}
    </div></div>`;
}

/* ------------------------------------------------------ tabela --------- */
function tabela(){
  const ms = D.modelos;
  return `<div class="fig">
    <h2>Os números</h2>
    <p class="cap">A mesma informação dos gráficos, em tabela — para conferir,
      copiar e citar no trabalho.</p>
    <div style="overflow-x:auto"><table>
      <tr><th>#</th><th>Tecnologia</th><th class="n">Nota</th><th class="n">Nota produto</th>
        <th class="n">mAP</th><th class="n">AUC</th><th class="n">Intrusos</th>
        <th class="n">Rosto errado</th><th class="n">Busca</th>
        <th class="n">Indexação</th><th class="n">Rostos</th></tr>
      ${ms.map(m=>`<tr>
        <td><b>${m.posicao}º</b></td>
        <td><b>${esc(m.modelo)}</b><br><span style="color:var(--muted);font-size:11.5px">${
          m.de_fabrica?'configuração de fábrica':'calibrado nesta bancada'} · ${m.conferidas} fotos conferidas</span></td>
        <td class="n"><b>${m.nota.toFixed(1)}</b></td>
        <td class="n">${m.nota_produto.toFixed(1)}</td>
        <td class="n">${fmt(m.mAP,3)}</td><td class="n">${fmt(m.auc,3)}</td>
        <td class="n">${m.intrusos ?? '—'}</td>
        <td class="n">${m.rosto_errado}</td>
        <td class="n">${fmt(m.busca_ms,2)} ms</td><td class="n">${fmt(m.index_s,3)} s</td>
        <td class="n">${m.rostos}</td></tr>`).join('')}
    </table></div>
    <details><summary>O que cada coluna significa</summary>
      <table style="margin-top:10px">
        <tr><td><b>Nota</b></td><td>melhor F1 possível, ×100. Leitura <b>modelo</b>: rosto errado conta como erro.</td></tr>
        <tr><td><b>Nota produto</b></td><td>mesma conta, mas rosto errado conta como acerto — a foto entregue tem mesmo a pessoa.</td></tr>
        <tr><td><b>Rosto errado</b></td><td>a pessoa está na foto, mas a similaridade veio do rosto de outra.</td></tr>
        <tr><td><b>mAP</b></td><td>o modelo colocou os acertos no topo do ranking? 1,000 é perfeito.</td></tr>
        <tr><td><b>AUC</b></td><td>chance de um acerto ficar acima de um erro. 0,5 é sorteio; 1,0 é separação total.</td></tr>
        <tr><td><b>Intrusos</b></td><td>quantos rostos errados ficaram acima do pior acerto. Zero é o ideal.</td></tr>
        <tr><td><b>F1 cruzado</b></td><td>acerto com o limiar calibrado <i>sem</i> ver a pessoa testada.</td></tr>
        <tr><td><b>Rostos</b></td><td>quantos rostos o detector encontrou e indexou no acervo.</td></tr>
      </table></details>
  </div>`;
}

/* -------------------------------------------------------- render ------- */
function render(){
  const m = D.modelos[0];
  const app = document.getElementById('app');
  if (!m){ app.innerHTML = '<p>Nenhuma execução com gabarito em resultados/.</p>'; return; }

  app.innerHTML = `
    <header>
      <span class="selo-teste">${esc(D.rotulo || 'Teste 1')}</span>
      <h1>Comparação de tecnologias de reconhecimento facial</h1>
      <p>Bancada de teste do FOTOMAC. Cada tecnologia foi submetida ao mesmo acervo
        e teve <b>cada foto conferida à mão</b>, uma a uma, com gabarito próprio —
        nenhuma herdou as respostas de outra. Os números desta página vêm dessa
        conferência; nenhum foi digitado.</p>
      <p style="margin:10px 0 0;color:var(--ink-2);font-size:13.5px">
        <b>Acervo:</b> 388 fotos de duas colações de grau, em resolução original.
        <b>Pessoa procurada:</b> o coordenador do curso — escolhido porque o autor
        não esteve presente em nenhum dos dois eventos e não aparece em nenhuma
        foto, o que impossibilitaria medir recall.</p>
    </header>
    ${podio()}
    <div class="tiles">
      <div class="tile"><div class="v">${m.conferidas}</div>
        <div class="k">fotos conferidas à mão</div><div class="sub">por tecnologia, uma a uma</div></div>
      <div class="tile"><div class="v">${D.modelos.length}</div>
        <div class="k">tecnologias comparadas</div><div class="sub">todas de configuração de fábrica, menos o SFace</div></div>
      <div class="tile"><div class="v">${fmt(m.busca_ms,2)}<span style="font-size:15px"> ms</span></div>
        <div class="k">tempo de busca</div><div class="sub">o que o visitante espera</div></div>
      <div class="tile"><div class="v">${m.intrusos ?? '—'}</div>
        <div class="k">erros acima do pior acerto</div><div class="sub">zero = separação total</div></div>
    </div>
    ${gSeparacao()}
    ${gNota()}
    ${gComposicao()}
    ${gVelocidade()}
    ${tabela()}
    ${D.avisos.length ? `<div class="nota"><b>Limitações deste teste — leia junto com os números</b>
      ${D.avisos.map(a=>`<p>${esc(a)}</p>`).join('')}
      <p>Um conjunto de teste em que todo candidato acerta tudo não consegue ordenar
      candidatos. Ampliar o gabarito com pessoas que estavam no evento é o que faz
      esta comparação voltar a discriminar.</p></div>` : ''}
    <footer>${esc(D.rotulo || 'Teste 1')} · gerado em ${esc(D.gerado_em.replace('T',' às '))} ·
      Página local, servida de 127.0.0.1 — as fotos não saem desta máquina.</footer>`;

  for (const el of document.querySelectorAll('[data-tip]')){
    el.addEventListener('mousemove', e => mostra(e, el.dataset.tip));
    el.addEventListener('mouseleave', esconde);
  }
}

fetch('/painel/dados').then(r=>r.json()).then(d=>{ D=d; render(); })
  .catch(e=>{ document.getElementById('app').textContent = 'Erro ao carregar: '+e.message; });
</script>
</body>
</html>
"""
