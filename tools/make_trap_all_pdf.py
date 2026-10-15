# Every "choose the WRONG one" question in the app, split into:
#   A) the answer contains trap grammar (grouped by pattern, full question with all options)
#   B) the answer is wrong because of content (compact list)
# Input: neg_all.json (made from the app data, duplicates removed). Output: jac_wrong_choice_all.html → print to PDF.
import json, re, sys, html as H
SP = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/repo/tools/'
DATA = json.load(open(SP + 'neg_all.json'))
NEG = {x['code']: x for x in DATA['neg']}
R = lambda k, r: f'<ruby>{k}<rt>{r}</rt></ruby>'
IMG = 'file:///home/claude/build/'

def units(h):
    out = []
    for m in re.finditer(r'<ruby>(.*?)<rt>(.*?)</rt></ruby>|<[^>]+>|([^<])', h):
        if m.group(1) is not None: out.append((m.group(1), m.group(0)))
        elif m.group(3): out.append((m.group(3), H.escape(m.group(3))))
    return out

def marked(h, rx):
    u = units(h); plain = ''.join(t for t, _ in u)
    m = re.search(rx, plain)
    if not m: raise SystemExit(f'pattern {rx!r} not found in {plain}')
    a, b, pos, out = m.start(), m.end(), 0, []
    for t, x in u:
        s, e = pos, pos + len(t); pos = e
        out.append(f'<mark>{x}</mark>' if s < b and e > a else x)
    return ''.join(out).replace('</mark><mark>', '')

def cut(h, n):
    """shorten html (ruby-aware) to about n visible characters"""
    out, k = [], 0
    for t, x in units(h):
        if k >= n: return ''.join(out) + '…'
        out.append(x); k += len(t)
    return ''.join(out)

def plain(h): return re.sub(r'<rt>.*?</rt>|<[^>]+>', '', h)

# code → (group, grammar label html, Thai meaning, regex in the answer)
TRAPS = [
 ('1', 'ท-066', f'〜{R("必要","ひつよう")}はない', 'ไม่จำเป็นต้อง〜', r'必要はない'),
 ('1', 'ล2-137', '〜なくてよい', 'ไม่ต้อง〜ก็ได้', r'しなくてよい'),
 ('1', 'ล2-174', '〜なくても', 'ถึงไม่〜ก็', r'掛けなくても'),
 ('1', 'ล2-117', '〜ずに', 'โดยไม่〜', r'とらずに'),
 ('1', 'ล-100', '〜ずに', 'โดยไม่〜', r'取らずに'),
 ('1', 'ล-062', '〜ず、', 'โดยไม่〜', r'使わず'),
 ('1', 'ล-074', '〜まま', 'ทั้งที่ยัง〜อยู่', r'着けたまま'),
 ('1', 'ล-075', '〜まま', 'ทั้งที่ยัง〜อยู่', r'残したまま'),
 ('1', 'ท-072', 'Aではなく、B', 'ไม่ใช่ A แต่เป็น B', r'行うのではなく'),
 ('1', 'ท-096', 'Aではなく、B', 'ไม่ใช่ A แต่เป็น B', r'職長ではなく'),
 ('1', 'ล2-166', '〜ことはない', 'ไม่มีทาง〜', r'死に至ることはない'),
 ('1', 'ท-067', '〜ではない', 'ไม่ใช่〜', r'作業環境ではない'),
 ('1', 'ท-015', '〜ない〜がある', 'มี〜ที่ไม่〜 (อ้างข้อยกเว้น)', r'適用されない'),
 ('2', 'ท-101', '〜だけ', 'เฉพาะ〜', r'時だけ'),
 ('2', 'ป-093', 'すべて', 'ทั้งหมด', r'すべて'),
 ('2', 'ท-070', R('両方', 'りょうほう'), 'ทั้งสองอย่าง', r'両方'),
 ('2', 'ล2-153', '〜でも', 'ถึงจะ〜ก็', r'以内でも'),
 ('2', 'ป-029', 'すぐに', 'ทันที (ข้ามขั้นตอน)', r'すぐに'),
 ('3', 'ล2-109', '〜ため', 'เพื่อ〜 (มักง่าย)', r'早くするため'),
 ('3', 'ล2-110', '〜やすいよう', 'เพื่อให้〜ง่าย', r'取り除きやすいよう'),
 ('3', 'ป-102', '〜ために', 'เพื่อ〜 (เหตุผลผิด)', r'守るために'),
 ('3', 'ล2-114', '〜のため', 'เพื่อ〜 (เหตุผลผิด)', r'防食のため'),
 ('3', 'ท-075', '〜ため', 'เพื่อ〜 (วิธีผิด)', r'責任を追及'),
 ('3', 'ท-077', '〜てから', 'หลังจาก〜แล้วจึง', r'連絡してから'),
 ('3', 'ล2-101', '〜ほど', 'ยิ่ง〜ยิ่ง', r'急なほど'),
 ('3', 'ท-071', 'もっと〜もっと', 'ยิ่ง〜ยิ่ง', r'もっと低く'),
]
GROUPS = {'1': '"ไม่ต้องทำ" · ข้ามขั้นตอน · โยนหน้าที่ · ปฏิเสธ', '2': 'คำสุดโต่ง / จำกัดเกินจริง', '3': 'เหตุผลมักง่าย · ลำดับสลับ · ยิ่ง…ยิ่ง'}
trap_codes = {c for _, c, *_ in TRAPS}
assert all(c in NEG for c in trap_codes), [c for c in trap_codes if c not in NEG]
others = [x for x in DATA['neg'] if x['code'] not in trap_codes]

def card(g, code, label, th, rx, n):
    x = NEG[code]
    thumb = f'<img class="thumb" src="{IMG + x["img"]}">' if x['img'] else ''
    lis = ''
    for k, o in enumerate(x['opts']):
        ans = k + 1 == x['ans']
        lis += f'<li class="{"ans" if ans else ""}"><b class="no">{k + 1}</b><span class="ja">{marked(o, rx) if ans else o}</span>{"<span class=tick>❌ คำตอบ</span>" if ans else ""}</li>'
    dup = f' · ซ้ำกับ {", ".join(x["dups"])}' if x['dups'] else ''
    return f'''<div class="card"><div class="ch"><span class="n">{n}</span><span class="gram ja">{label}</span><span class="gm">{th}</span><span class="code">{code}{dup}</span></div>
<div class="q">{thumb}<span class="ja">{x["stem"]}</span><span class="qt">แปล: {x["sth"]}</span></div>
<ol class="opts">{lis}</ol><div class="why">✗ {cut(x["ath"], 150)}</div></div>'''

secA, n = '', 0
for g, title in GROUPS.items():
    items = [t for t in TRAPS if t[0] == g]
    cards = ''
    for t in items:
        n += 1; cards += card(*t, n)
    secA += f'<h3><span class="tag">❌ {g}</span>{title} <small>{len(items)} ข้อ</small></h3><div class="cards">{cards}</div>'

rows = ''
for k, x in enumerate(sorted(others, key=lambda x: ({'gakka': 0, 'jitsugi': 1, 'life': 2}.get(x['part'], 3), x['code'])), 1):
    a = x['opts'][x['ans'] - 1]
    dup = f'<br><i>= {", ".join(x["dups"])}</i>' if x['dups'] else ''
    rows += (f'<tr><td class="c">{k}<br><span class="code">{x["code"]}</span>{dup}</td>'
             f'<td><span class="ja s">{x["stem"]}</span><span class="qt">{x["sth"]}</span></td>'
             f'<td><span class="ja a">{a}</span><span class="qt">{cut(x["ath"], 95)}</span></td></tr>')

T, U, N = DATA['total'], DATA['unique'], len(DATA['neg'])
nA = len(TRAPS); nB = N - nA
g1, g2, g3 = (sum(1 for t in TRAPS if t[0] == g) for g in '123')
page = f'''<!doctype html><html lang="th"><head><meta charset="utf-8"><title>JAC wrong-choice questions</title><style>
@page {{ size: A4; margin: 10mm 10mm 10mm }}
* {{ box-sizing: border-box }}
body {{ font-family: 'Loma', 'Noto Sans CJK JP', sans-serif; color: #1d2b3a; font-size: 9.6pt; line-height: 1.42; margin: 0 }}
.ja, ruby {{ font-family: 'Noto Sans CJK JP', sans-serif }} rt {{ font-size: 50%; color: #4a5a6a }}
h1 {{ font-size: 17pt; margin: 0 }} .sub {{ color: #5b6b7b; font-size: 9pt; margin: 2px 0 8px }}
.sum {{ border: 2px solid #f0b400; background: #fff8e1; border-radius: 10px; padding: 8px 12px; break-inside: avoid }}
.nums {{ display: flex; gap: 8px; margin: 6px 0 }}
.num {{ flex: 1; background: #fff; border: 1.5px solid #e2d3a0; border-radius: 8px; padding: 5px 8px; text-align: center; font-size: 8.8pt }}
.num b {{ display: block; font-size: 18pt; line-height: 1.15 }} .num.red b {{ color: #c0392b }} .num.blue b {{ color: #2b6cb0 }}
.bar {{ display: flex; height: 16px; border-radius: 8px; overflow: hidden; margin: 6px 0 2px; font-size: 8pt; color: #fff; font-weight: 700 }}
.bar span {{ display: flex; align-items: center; justify-content: center }}
.legend {{ font-size: 8.4pt; color: #4a5a6a }}
h2 {{ font-size: 13pt; margin: 12px 0 4px; break-after: avoid; border-bottom: 2px solid #1d2b3a; padding-bottom: 2px }}
h2 small, h3 small {{ font-weight: normal; color: #5b6b7b; font-size: 9pt; margin-left: 6px }}
h3 {{ font-size: 11pt; margin: 9px 0 4px; break-after: avoid }} h3 .tag {{ background: #c0392b; color: #fff; border-radius: 5px; padding: 0 6px; margin-right: 6px; font-size: 9.5pt }}
.cards {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px }}
.card {{ border: 1.5px solid #dde3e8; border-radius: 9px; padding: 5px 7px; break-inside: avoid; background: #fff }}
.ch {{ display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; margin-bottom: 2px }}
.ch .n {{ background: #1d2b3a; color: #fff; border-radius: 4px; font-size: 8pt; padding: 0 5px }}
.ch .gram {{ font-weight: 800; color: #b23a0a; font-size: 10.5pt }} .ch .gm {{ font-size: 8.6pt }} .ch .code {{ margin-left: auto; color: #8a97a3; font-size: 7.8pt }}
.q {{ background: #f4f6f8; border-radius: 6px; padding: 3px 6px; overflow: hidden }} .q .ja {{ font-size: 9.2pt }}
.qt {{ display: block; color: #4a5a6a; font-size: 7.9pt; line-height: 1.35 }}
.thumb {{ float: right; width: 50px; height: 50px; object-fit: cover; border-radius: 5px; margin-left: 5px }}
ol.opts {{ list-style: none; margin: 3px 0 2px; padding: 0 }}
ol.opts li {{ display: flex; gap: 5px; align-items: baseline; padding: 1px 4px; border-radius: 5px; font-size: 8.9pt }}
ol.opts li.ans {{ background: #fdecea; outline: 1.2px solid #e8a39b }} ol.opts li .no {{ width: 10px; flex: none }}
ol.opts li .ja {{ flex: 1 }} .tick {{ color: #c0392b; font-size: 7.8pt; font-weight: 700; white-space: nowrap }}
mark {{ background: #ffc2b8; border-radius: 2px; padding: 0 1px }}
.why {{ font-size: 7.9pt; color: #5b3a34; line-height: 1.35 }}
table {{ width: 100%; border-collapse: collapse; table-layout: fixed }}
col.a {{ width: 8% }} col.b {{ width: 46% }} col.c {{ width: 46% }}
th {{ text-align: left; font-size: 8pt; color: #5b6b7b; font-weight: normal; border-bottom: 1.5px solid #1d2b3a; padding: 2px 4px }}
td {{ border-bottom: 1px solid #dde3e8; padding: 3px 4px; vertical-align: top }} tr {{ break-inside: avoid }}
td.c {{ font-weight: 700; font-size: 8.5pt }} td .code, td i {{ color: #8a97a3; font-size: 7.4pt; font-weight: normal; font-style: normal }}
td .ja.s {{ font-size: 8.9pt }} td .ja.a {{ font-size: 9.1pt; color: #b23a0a; font-weight: 700 }}
.foot {{ margin-top: 8px; color: #8a97a3; font-size: 7.8pt }}
</style></head><body>
<h1>ข้อ "เลือกข้อผิด" ทั้งหมดในแอป JAC</h1>
<div class="sub"><span class="ja">{R('建設分野','けんせつぶんや')} {R('特定技能','とくていぎのう')}2{R('号','ごう')}</span> · ตรวจจากโจทย์ {T} ข้อ (ไม่นับข้อซ้ำเหลือ {U} ข้อ)</div>
<div class="sum"><b>สรุปตัวเลข</b>
<div class="nums"><div class="num"><b>{U}</b>ข้อทั้งหมด (ไม่นับซ้ำ)</div><div class="num"><b>{N}</b>ข้อแบบ "เลือกข้อผิด"<br>({round(N/U*100)}% ของทั้งหมด)</div>
<div class="num red"><b>{nA}</b>คำตอบมีไวยากรณ์กับดัก<br>({round(nA/N*100)}% ของข้อเลือกผิด)</div><div class="num blue"><b>{nB}</b>ผิดเพราะเนื้อหา<br>(ต้องใช้ความรู้)</div></div>
<div class="bar"><span style="width:{g1/N*100}%;background:#c0392b">{g1}</span><span style="width:{g2/N*100}%;background:#e67e22">{g2}</span><span style="width:{g3/N*100}%;background:#d4a017">{g3}</span><span style="width:{nB/N*100}%;background:#2b6cb0">{nB}</span></div>
<div class="legend">🟥 ไม่ต้องทำ/ข้ามขั้นตอน/ปฏิเสธ {g1} · 🟧 คำสุดโต่ง {g2} · 🟨 เหตุผล/ลำดับ/ยิ่ง…ยิ่ง {g3} · 🟦 ผิดเพราะเนื้อหา {nB}</div>
<div class="legend" style="margin-top:4px">คำท้ายโจทย์ที่บอกว่าให้หาข้อผิด: <span class="ja">{R('誤','あやま')}っている・{R('含','ふく')}まれない／{R('含','ふく')}まない・{R('適切','てきせつ')}でない・{R('正','ただ')}しくない・{R('間違','まちが')}い・ふさわしくない・〜でない・{R('不適切','ふてきせつ')}・{R('当','あ')}てはまらない・{R('違','ちが')}う</span></div></div>

<h2>A · คำตอบมีไวยากรณ์กับดัก <small>{nA} ข้อ — ส่วนที่ไฮไลต์คือคำสังเกต · แถบแดง = คำตอบ</small></h2>
{secA}
<h2>B · ผิดเพราะเนื้อหา <small>{nB} ข้อ — ไม่มีคำกับดัก ต้องรู้เรื่องนั้นจริง (สลับข้อเท็จจริง / ใส่ผิดหมวด / ตัวเลขผิด)</small></h2>
<table><colgroup><col class="a"><col class="b"><col class="c"></colgroup><tr><th>ข้อ</th><th>โจทย์ + แปล</th><th>คำตอบ (ข้อที่ผิด) + เหตุผล</th></tr>{rows}</table>
<div class="foot">แอป JAC · ทุกข้อมาจากโจทย์จริงในแอป (รหัสข้อเปิดดูในแอปได้) · "ซ้ำกับ" = ข้อเดียวกันที่อยู่อีกพาร์ท</div>
</body></html>'''
open(SP + 'jac_wrong_choice_all.html', 'w', encoding='utf-8').write(page)
print('A', nA, 'B', nB, 'groups', g1, g2, g3)
