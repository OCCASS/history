import json, re, html, os
from collections import Counter, defaultdict

src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data.js'), encoding='utf-8').read()
D = json.loads(src[src.index('=')+1:].rstrip().rstrip(';'))
CHS = sorted(D['chapters'], key=lambda c: c['chapter'])
PER = {p['n']: p for p in D['periods']}
CHP = {c['chapter']: c['period'] for c in CHS}
RUL = {r['id']: r for r in D['rulers']}

esc = lambda s: html.escape(str(s or ''), quote=True)
def md(s):
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', esc(s))
def shortdate(s):
    s = re.sub(r'\s*\([^)]*\)', '', str(s or ''))
    s = s.replace('около', 'ок.').replace('приблизительно', 'ок.')
    s = re.sub(r'\s*(гг?\.)', '', s)
    return re.sub(r'\s+', ' ', s).strip(' ,–—-')

def norm(s):
    s = str(s or '').lower().replace('ё','е')
    return re.sub(r'\s+',' ', re.sub(r'[«»"().,:;!?–—-]',' ', s)).strip()

# ---------- рейтинг событий по «спросу» банка вопросов ----------
mcq_txt, seq_items = [], Counter()
for ch in CHS:
    for m in ch.get('mcq', []):
        mcq_txt.append(norm(' '.join([m['q']] + m.get('options', []) + [m.get('explain','')])))
    for s in ch.get('sequences', []):
        for it in s['items']: seq_items[norm(it['t'])] += 1
for s in D['pastExam']['seq']:
    for it in s['items']: seq_items[norm(it['t'])] += 1

scored, seen = [], set()
for ch in CHS:
    for e in ch.get('events', []):
        nm = norm(e['title'])
        if len(nm) < 6 or nm in seen: continue
        sc = seq_items.get(nm, 0)*3 + sum(1 for t in mcq_txt if nm in t)
        if sc > 0:
            seen.add(nm)
            scored.append({'sc':sc, 'y':e.get('year'), 'm':e.get('month') or 0, 'date':e.get('date',''),
                           'title':e['title'], 'ch':ch['chapter'], 'per':CHP[ch['chapter']], 'ruler':e.get('ruler')})
scored.sort(key=lambda r: -r['sc'])
TOP = scored[:200]
top_keys = {norm(r['title']) for r in TOP}
TOP.sort(key=lambda r: ((r['y'] if r['y'] is not None else 0), r['m']))

# ---------- правители по эпохам ----------
rul_per = defaultdict(list)
ev_by_ruler = defaultdict(int)
for ch in CHS:
    for e in ch.get('events', []):
        if e.get('ruler'): ev_by_ruler[e['ruler']] += 1
for r in D['rulers']:
    p = None
    if r.get('start') is not None:
        for pp in D['periods']:
            if pp['from'] and pp['to'] and pp['from'] <= r['start'] < pp['to']: p = pp['n']; break
    if p is None: p = r.get('period', 0)
    rul_per[p].append(r)

# ---------- стили: те же токены, что на основном сайте ----------
CSS = """
:root{--paper:#EEF1F0;--surface:#FBFCFB;--surface-2:#E4E9E8;--ink:#15191D;--ink-2:#39424B;--muted:#5E6873;
--line:#D3D9D8;--line-strong:#AEB8B7;--accent:#2344A8;--accent-ink:#fff;--accent-soft:#DDE4F6;
--good:#1F7A4D;--good-soft:#D9EFE3;--warn:#9A6400;--warn-soft:#F5E9CF;
--p0:#5E6873;--p1:#A8741F;--p2:#8A4F7D;--p3:#2C7A6A;--p4:#2344A8;--p5:#B3402E;--p6:#4C6274;
--f-display:"Oranienbaum","Playfair Display","Times New Roman",serif;
--f-body:"Golos Text","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
--f-mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;--r:10px}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#101316;--surface:#181C21;--surface-2:#222830;
--ink:#E7EAED;--ink-2:#C3CAD1;--muted:#909AA5;--line:#2B323A;--line-strong:#46505B;--accent:#8FA8F2;--accent-ink:#0E1420;
--accent-soft:#1F2A45;--good:#5DC08D;--good-soft:#15301F;--warn:#E0B458;--warn-soft:#352A12;
--p0:#909AA5;--p1:#D9A551;--p2:#C98DBB;--p3:#5FBFA9;--p4:#8FA8F2;--p5:#EE8069;--p6:#8FA7BA}}
:root[data-theme="dark"]{--paper:#101316;--surface:#181C21;--surface-2:#222830;--ink:#E7EAED;--ink-2:#C3CAD1;
--muted:#909AA5;--line:#2B323A;--line-strong:#46505B;--accent:#8FA8F2;--accent-ink:#0E1420;--accent-soft:#1F2A45;
--good:#5DC08D;--good-soft:#15301F;--warn:#E0B458;--warn-soft:#352A12;
--p0:#909AA5;--p1:#D9A551;--p2:#C98DBB;--p3:#5FBFA9;--p4:#8FA8F2;--p5:#EE8069;--p6:#8FA7BA}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font-family:var(--f-body);font-size:16px;line-height:1.62;
margin:0;padding-inline:16px;padding-block:0 72px}
.wrap{max-width:720px;margin:0 auto}
h1,h2,h3{font-family:var(--f-display);font-weight:400;margin:0;text-wrap:balance}
h1{font-size:32px;line-height:1.12}h2{font-size:25px;line-height:1.18}h3{font-size:19px}
a{color:var(--accent)}
.mono{font-family:var(--f-mono);font-variant-numeric:tabular-nums}
.label{font-family:var(--f-mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.muted{color:var(--muted)}
.top{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--paper) 90%,transparent);
backdrop-filter:blur(8px);border-bottom:1px solid var(--line);margin-inline:-16px;padding-inline:16px}
.top .wrap{display:flex;align-items:center;gap:12px;height:52px}
.top .back{font-size:14px;text-decoration:none;color:var(--ink-2);white-space:nowrap;flex:none;padding:6px 10px 6px 0}
.top .back:hover{color:var(--accent)}
.top nav{margin-left:auto;display:flex;gap:4px;overflow-x:auto}
.top nav a{font-size:13px;padding:5px 9px;border-radius:7px;text-decoration:none;color:var(--ink-2);white-space:nowrap}
.top nav a:hover{background:var(--surface-2)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:16px;margin:14px 0}
.plan{display:grid;gap:10px}
.plan .d{display:flex;gap:12px;align-items:baseline}
.plan .n{font-family:var(--f-mono);font-size:12px;color:var(--accent);flex:none;width:56px}
.bar{height:7px;background:var(--surface-2);border-radius:99px;overflow:hidden;margin:8px 0}
.bar i{display:block;height:100%;background:var(--accent);transition:width .25s}
.era{margin:38px 0 0;padding-top:18px;border-top:2px solid var(--line-strong)}
.era .tag{display:inline-flex;align-items:center;gap:7px;font-family:var(--f-mono);font-size:11.5px;
letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.sw{width:10px;height:10px;border-radius:3px;display:inline-block}
.rul{margin-top:10px}
.rrow{display:grid;grid-template-columns:auto minmax(0,1fr);gap:1px 10px;padding:7px 0;
border-bottom:1px solid var(--line);font-size:15px;align-items:baseline}
.rrow .y{font-family:var(--f-mono);font-size:12.5px;color:var(--muted);white-space:nowrap}
.rrow .n{font-weight:500}
.rrow.key .n{font-weight:700}
.rrow.key .y{color:var(--accent)}
.rrow .r{grid-column:2;font-size:13px;color:var(--muted);line-height:1.4}
.chap{margin:26px 0}
.chap h3{display:flex;align-items:baseline;gap:9px}
.chap h3 .num{font-family:var(--f-mono);font-size:12px;color:var(--muted);flex:none}
.chap p{margin:11px 0}
.chk{display:flex;align-items:center;gap:9px;margin-top:12px;font-size:13.5px;color:var(--muted);cursor:pointer;user-select:none}
.chk input{width:17px;height:17px;accent-color:var(--accent);cursor:pointer}
.dates{font-size:14.5px}
.dates .row{display:flex;gap:12px;padding:6px 0;border-bottom:1px solid var(--line);align-items:baseline}
.dates .dt{font-family:var(--f-mono);font-size:12px;color:var(--accent);flex:none;width:124px;line-height:1.45}
.dates .rl{color:var(--muted);font-size:12.5px}
body.hide-dates .dates .dt{color:transparent;background:var(--surface-2);border-radius:4px}
body.hide-dates .dates .row:hover .dt,body.hide-dates .dates .row:active .dt{color:var(--accent);background:none}
.btn{font:inherit;font-size:14px;color:inherit;background:var(--surface);border:1px solid var(--line-strong);
border-radius:8px;padding:8px 13px;cursor:pointer}
.btn.primary{background:var(--accent);color:var(--accent-ink);border-color:transparent}
.row-btns{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.note{background:var(--warn-soft);border:1px solid var(--warn);border-radius:var(--r);padding:13px 15px;font-size:14px;margin:16px 0}
.toc{columns:2;column-gap:20px;font-size:14px}
.toc a{display:block;padding:3px 0;text-decoration:none}
@media (max-width:560px){.toc{columns:1}.dates .dt{width:106px}.top nav{display:none}
.rrow{grid-template-columns:auto minmax(0,1fr)}}
@media print{.top,.chk,.row-btns,.note{display:none}body{padding:0;font-size:11pt}.card{break-inside:avoid}}
"""

def period_chapters(pn):
    return [c for c in CHS if CHP[c['chapter']] == pn]

out = []
A = out.append
A('<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">')
A('<meta name="viewport" content="width=device-width,initial-scale=1">')
A('<title>Минимум на зачёт — Хронограф</title>')
A('<meta name="description" content="Весь курс истории России одним текстом: конспекты 22 глав подряд, лента правителей и 200 ключевых дат. Для подготовки с нуля.">')
A('<link rel="preconnect" href="https://fonts.googleapis.com">')
A('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
A('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Oranienbaum&family=Golos+Text:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">')
A(f'<style>{CSS}</style>\n</head>\n<body>')

A('<header class="top"><div class="wrap">'
  '<a class="back" href="index.html">← Приложение</a>'
  '<nav><a href="#plan">План</a><a href="#rulers">Правители</a>'
  '<a href="#read">Конспект</a><a href="#dates">Даты</a></nav></div></header>')
A('<main class="wrap">')

# ---- шапка ----
total_chars = sum(len(' '.join(c.get('summary', []))) for c in CHS)
A('<h1 style="margin-top:22px">Всё, что нужно прочитать</h1>')
A(f'<p class="muted" style="margin-top:10px">Конспекты всех {len(CHS)} глав подряд — '
  f'{sum(len(c.get("summary",[])) for c in CHS)} абзацев, около {total_chars//1800} страниц. '
  f'Плюс лента из {len(D["rulers"])} правителей и {len(TOP)} ключевых дат, отобранных по тому, '
  f'как часто их спрашивает банк вопросов курса.</p>')

A('<div class="card" id="plan"><span class="label">Как этим пользоваться</span>'
  '<div class="plan" style="margin-top:12px">'
  '<div class="d"><span class="n">Шаг 1</span><span>Прочитайте <b>ленту правителей</b>. Это каркас: '
  'почти любой вопрос на последовательность решается, если вы знаете, кто за кем правил.</span></div>'
  '<div class="d"><span class="n">Шаг 2</span><span>Прочитайте <b>конспект целиком, подряд</b>, не останавливаясь '
  'на запоминании дат. Задача первого прохода — построить связную картину.</span></div>'
  '<div class="d"><span class="n">Шаг 3</span><span>Пройдите <b>200 дат</b> внизу, включив режим «скрыть даты». '
  'Вспоминайте — не узнавайте.</span></div>'
  '<div class="d"><span class="n">Шаг 4</span><span>Второй проход конспекта — теперь даты цепляются за уже '
  'знакомый сюжет. Затем тесты в приложении.</span></div>'
  '</div>'
  '<div class="bar"><i id="pbar" style="width:0"></i></div>'
  '<p class="muted" style="font-size:13px" id="pnum">Прочитано 0 из 22 глав</p></div>')

A('<div class="note"><b>Про объём.</b> 53 страницы — это 4–6 часов чтения. Это заметно быстрее, '
  'чем 2 061 карточка, и даёт связную картину, на которую даты ложатся сами. '
  'Карточки и тесты имеет смысл включать уже после первого прохода.</div>')

# ---- оглавление ----
A('<div class="card"><span class="label">Оглавление</span><div class="toc" style="margin-top:10px">')
for p in D['periods']:
    chs = period_chapters(p['n'])
    if not chs: continue
    A(f'<a href="#era{p["n"]}"><b>{esc(p["short"])}</b></a>')
    for c in chs:
        A(f'<a href="#ch{c["chapter"]}" class="muted">{c["chapter"]}. {esc(c["title"][:40])}</a>')
A('</div></div>')

# ---- лента правителей ----
A('<h2 id="rulers" class="era" style="border:0;padding:0;margin-top:36px">Лента правителей</h2>')
A('<p class="muted" style="margin-top:8px;font-size:14.5px">Жирным — те, при ком в курсе больше всего событий. '
  'Начните с них.</p>')
for p in D['periods']:
    rs = rul_per.get(p['n'], [])
    if not rs: continue
    A(f'<div style="margin-top:18px"><span class="era"><span class="tag">'
      f'<span class="sw" style="background:var(--p{p["n"]})"></span>{esc(p["name"])}</span></span>')
    A('<div class="rul">')
    for r in rs:
        key = ev_by_ruler.get(r['id'], 0) >= 12
        yrs = r['years']; extra = ''
        if ' (' in yrs:
            yrs, tail = yrs.split(' (', 1)
            extra = tail.rstrip(')')
        role = ', '.join(x for x in (r.get('title',''), extra) if x)
        A(f'<div class="rrow{" key" if key else ""}"><span class="y">{esc(yrs)}</span>'
          f'<span class="n">{esc(r["name"])}</span>'
          + (f'<span class="r">{esc(role)}</span>' if role else '') + '</div>')
    A('</div></div>')

# ---- конспект подряд ----
A('<h2 id="read" class="era" style="margin-top:44px">Конспект курса</h2>')
for p in D['periods']:
    chs = period_chapters(p['n'])
    if not chs: continue
    A(f'<div class="era" id="era{p["n"]}"><span class="tag">'
      f'<span class="sw" style="background:var(--p{p["n"]})"></span>{esc(p["name"])}'
      + (f' · {p["from"]}–{p["to"]}' if p.get('from') else '') + '</span></div>')
    for c in chs:
        n = c['chapter']
        A(f'<section class="chap" id="ch{n}"><h3><span class="num">ГЛ. {n}</span>{esc(c["title"])}</h3>')
        for para in c.get('summary', []):
            A(f'<p>{md(para)}</p>')
        A(f'<label class="chk"><input type="checkbox" data-ch="{n}"> прочитано</label></section>')

# ---- 200 дат ----
A('<h2 id="dates" class="era" style="margin-top:44px">200 ключевых дат</h2>')
A('<p class="muted" style="margin-top:8px;font-size:14.5px">Отобраны по частоте в банке вопросов курса '
  '(888 вопросов): чем чаще событие встречается в тестах и последовательностях, тем выше приоритет. '
  'В хронологическом порядке.</p>')
A('<div class="row-btns"><button class="btn primary" type="button" id="hide">Скрыть даты</button>'
  '<span class="muted" style="font-size:13px;align-self:center">нажмите на строку, чтобы подсмотреть</span></div>')
A('<div class="dates">')
cur = None
for r in TOP:
    if r['per'] != cur:
        cur = r['per']
        A(f'<div style="margin:20px 0 6px"><span class="tag"><span class="sw" '
          f'style="background:var(--p{cur})"></span>{esc(PER[cur]["name"])}</span></div>')
    rl = RUL.get(r['ruler'], {}).get('name', '')
    A(f'<div class="row"><span class="dt mono">{esc(shortdate(r["date"]))}</span><span>{esc(r["title"])}'
      + (f'<br><span class="rl">{esc(rl)}</span>' if rl else '') + '</span></div>')
A('</div>')

A('<p class="muted" style="margin-top:32px;font-size:13px">Страница собрана из данных курса '
  '(<span class="mono">data.js</span>). <a href="index.html">Вернуться в приложение</a>.</p>')
A('</main>')

A("""<script>
(function(){
  var KEY='hronograf.read.v1', S={};
  try{ S=JSON.parse(localStorage.getItem(KEY)||'{}'); }catch(e){}
  var boxes=document.querySelectorAll('[data-ch]');
  function paint(){
    var n=0; boxes.forEach(function(b){ if(S[b.dataset.ch]){ b.checked=true; n++; } });
    document.getElementById('pbar').style.width=(n/boxes.length*100)+'%';
    document.getElementById('pnum').textContent='Прочитано '+n+' из '+boxes.length+' глав';
  }
  boxes.forEach(function(b){ b.onchange=function(){
    if(b.checked) S[b.dataset.ch]=1; else delete S[b.dataset.ch];
    try{ localStorage.setItem(KEY,JSON.stringify(S)); }catch(e){}
    paint();
  };});
  paint();
  var h=document.getElementById('hide'), on=false;
  h.onclick=function(){ on=!on; document.body.classList.toggle('hide-dates',on);
    h.textContent=on?'Показать даты':'Скрыть даты'; };
})();
</script>""")
A('</body>\n</html>')

open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'minimum.html'),'w',encoding='utf-8').write('\n'.join(out))
print("minimum.html:", len('\n'.join(out)), "байт")
print("глав:", len(CHS), "| правителей:", len(D['rulers']), "| дат:", len(TOP))
