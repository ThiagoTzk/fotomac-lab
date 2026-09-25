"""
FotoMac Lab — a aparência compartilhada pelas três telas.

Antes cada página trazia a sua própria paleta e o seu próprio menu. O resultado
era que `/painel` parecia outro site, e o link "Marcar gabarito" existia em duas
telas e faltava na terceira. Sistema apresentado a uma banca não pode parecer
três sistemas.

Aqui ficam os TOKENS (as variáveis de cor), os COMPONENTES (menu, painel, botão,
tabela, cartão de número) e o MENU. Cada página acrescenta só o que é específico
dela.

As cores de série (`--s1` a `--s5`) são a paleta de referência da skill de
visualização, validada em claro e escuro: nenhuma fatia fica abaixo do piso de
contraste sem rótulo direto, e os pares vizinhos passam no teste de daltonismo.
Não troque sem rodar o validador de novo.
"""

CSS_BASE = """
  :root{
    color-scheme: light;
    /* superfícies e texto */
    --bg:#f2f2ef; --card:#fcfcfb; --ink:#15181d; --ink-2:#52514e; --muted:#76756f;
    --line:#dfe3e8; --linha-forte:#c9c8c2;
    /* ação e estado */
    --acc:#2a78d6; --ok:#0ca30c; --ok-bg:#e8f6ee;
    --no:#d03b3b; --no-bg:#fbeaea; --nao-ink:#b32020;
    --warn:#fab219; --warn-bg:#fdf5e3; --warn-ink:#8a5f05;
    /* séries dos gráficos — paleta validada, não altere sem revalidar */
    --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --s4:#eda100; --s5:#e87ba4;
    --grid:#e6e5e1; --axis:#c9c8c2;
    --sombra:0 1px 2px rgba(15,18,20,.05), 0 4px 16px rgba(15,18,20,.04);
    --raio:12px;
  }
  @media (prefers-color-scheme:dark){
    :root:where(:not([data-theme="light"])){
      color-scheme: dark;
      --bg:#111110; --card:#1a1a19; --ink:#e8ebef; --ink-2:#c3c2b7; --muted:#95948b;
      --line:#2a3037; --linha-forte:#45443f;
      --acc:#6ea2ff; --ok:#4fd07f; --ok-bg:#16301f;
      --no:#ff8d8d; --no-bg:#3a1616; --nao-ink:#ff8d8d;
      --warn:#e0a24a; --warn-bg:#2a2410; --warn-ink:#e8c77a;
      --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#c98500; --s5:#d55181;
      --grid:#2e2e2b; --axis:#45443f;
      --sombra:0 1px 2px rgba(0,0,0,.4), 0 4px 18px rgba(0,0,0,.25);
    }
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font:15px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
    -webkit-font-smoothing:antialiased}
  .wrap{max-width:1180px;margin:0 auto;padding:0 18px 90px}
  h1{font-size:27px;margin:0 0 5px;letter-spacing:-.015em}
  h2{font-size:18px;margin:34px 0 10px;padding-top:16px;border-top:1px solid var(--line);
    letter-spacing:-.01em}
  h3{font-size:15px;margin:22px 0 7px}
  code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.92em}

  /* ---------------------------------------------------------- topo e menu */
  .topo{position:sticky;top:0;z-index:40;background:var(--card);
    border-bottom:1px solid var(--line);margin-bottom:22px}
  .topo-in{max-width:1180px;margin:0 auto;padding:11px 18px;display:flex;
    align-items:center;gap:20px;flex-wrap:wrap}
  .marca{font-weight:800;font-size:15px;letter-spacing:-.02em;white-space:nowrap}
  .marca span{color:var(--muted);font-weight:600}
  .nav{display:flex;gap:4px;flex-wrap:wrap}
  .nav a{padding:7px 14px;border-radius:8px;color:var(--ink-2);text-decoration:none;
    font-size:13.5px;font-weight:600;white-space:nowrap}
  .nav a:hover{background:var(--bg);color:var(--ink)}
  .nav a.on{background:var(--acc);color:#fff}
  .topo-dir{margin-left:auto;font-size:12.5px;color:var(--muted)}

  /* ------------------------------------------------------------ blocos */
  .panel{background:var(--card);border:1px solid var(--line);border-radius:var(--raio);
    padding:17px 19px;margin:15px 0;box-shadow:var(--sombra)}
  .sub{color:var(--ink-2);margin:0 0 18px;font-size:14px;max-width:78ch}
  .cap{color:var(--ink-2);font-size:13.5px;margin:0 0 15px;max-width:78ch}
  .tiles{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
    margin:18px 0}
  .tile{background:var(--card);border:1px solid var(--line);border-radius:11px;
    padding:13px 15px;box-shadow:var(--sombra)}
  .tile .v{font-size:29px;font-weight:750;font-variant-numeric:tabular-nums;
    letter-spacing:-.02em;line-height:1.05}
  .tile .k{color:var(--ink-2);font-size:12.5px;margin-top:3px}
  .tile .sub{color:var(--muted);font-size:11.5px;margin:2px 0 0}

  /* ------------------------------------------------------------ controles */
  .btn{padding:10px 18px;border-radius:9px;border:none;background:var(--acc);
    color:#fff;font-size:14.5px;font-weight:700;cursor:pointer;font-family:inherit}
  .btn:hover{filter:brightness(1.07)}
  .btn:disabled{opacity:.45;cursor:not-allowed;filter:none}
  .btn.sec{background:transparent;color:var(--ink);border:1px solid var(--line)}
  .btn.sec:hover{background:var(--bg);filter:none}
  label{display:block;font-size:12.5px;color:var(--ink-2);margin-bottom:4px;font-weight:600}
  input[type=text],select{width:100%;padding:9px 11px;border-radius:8px;
    border:1px solid var(--line);background:var(--bg);color:var(--ink);
    font-size:14px;font-family:inherit}

  /* ------------------------------------------------------------ tabela */
  table{border-collapse:collapse;width:100%;font-size:13.5px}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
  th{color:var(--muted);font-weight:600;font-size:11.5px;text-transform:uppercase;
    letter-spacing:.05em}
  td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}

  /* ------------------------------------------------------------ avisos */
  .aviso{background:var(--warn-bg);color:var(--warn-ink);border:1px solid var(--warn);
    border-left-width:4px;border-radius:10px;padding:12px 15px;font-size:13.5px;margin:14px 0}
  .erro{background:var(--no-bg);color:var(--nao-ink);border-radius:10px;
    padding:12px 15px;font-weight:600}
  .spin{display:inline-block;width:15px;height:15px;border:2px solid var(--line);
    border-top-color:var(--acc);border-radius:50%;animation:girar .7s linear infinite;
    vertical-align:-3px}
  @keyframes girar{to{transform:rotate(360deg)}}
  .legend{display:flex;gap:17px;flex-wrap:wrap;margin:2px 0 13px;font-size:13px;
    color:var(--ink-2)}
  .legend i{display:inline-block;width:11px;height:11px;border-radius:3px;
    margin-right:6px;vertical-align:-1px}
  kbd{background:var(--bg);border:1px solid var(--line);border-bottom-width:2px;
    border-radius:5px;padding:1px 6px;font:600 11.5px ui-monospace,Menlo,monospace}
  footer{color:var(--muted);font-size:12.5px;margin-top:36px;
    border-top:1px solid var(--line);padding-top:14px}
  .hide{display:none!important}
  @media (max-width:560px){
    .wrap{padding:0 14px 80px} h1{font-size:22px}
    .topo-in{padding:9px 14px;gap:10px} .topo-dir{display:none}
  }
"""

# As três telas, na mesma ordem em todas. Ordem fixa: menu que muda de lugar
# entre páginas faz a pessoa procurar em vez de clicar.
PAGINAS = [
    ("/", "Busca por rosto"),
    ("/marcar", "Marcar gabarito"),
    ("/painel", "Comparação de tecnologias"),
]


def topo(ativo: str, direita: str = "") -> str:
    partes = []
    for href, rot in PAGINAS:
        classe = ' class="on"' if href == ativo else ''
        partes.append('<a href="%s"%s>%s</a>' % (href, classe, rot))
    itens = "".join(partes)
    dir_html = f'<div class="topo-dir">{direita}</div>' if direita else ""
    return f'''<div class="topo"><div class="topo-in">
  <div class="marca">FotoMac <span>Lab</span></div>
  <nav class="nav">{itens}</nav>
  {dir_html}
</div></div>'''
