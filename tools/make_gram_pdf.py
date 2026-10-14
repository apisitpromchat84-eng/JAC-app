import json, re, sys, html as H
SP = '/home/claude/repo/tools/'
sys.path.insert(0, SP)
from gram_items import ITEMS, R

d = json.load(open(SP + 'stems.json'))
N = len(d)

def tokens(h):
    """stem html -> list of (plain_text, html) units; a ruby word is one unit"""
    out = []
    for m in re.finditer(r'<ruby>(.*?)<rt>(.*?)</rt></ruby>|<[^>]+>|([^<])', h):
        if m.group(1) is not None: out.append((m.group(1), m.group(0)))
        elif m.group(3): out.append((m.group(3), H.escape(m.group(3))))
    return out

def snippet(x, rx, width=30):
    tk = tokens(x['html']); plain = ''.join(t for t, _ in tk)
    m = re.search(rx, plain)
    if not m: return H.escape(x['stem'][:width])
    a, b = m.start(), m.end()
    if len(plain) <= width + 6: lo, hi = 0, len(plain)
    else:
        lo = max(0, a - (width - (b - a)) // 2); hi = min(len(plain), lo + width); lo = max(0, hi - width)
    # cut on unit boundaries, mark the keyword
    pos, parts = 0, []
    for t, h in tk:
        s, e = pos, pos + len(t); pos = e
        if e <= lo or s >= hi: continue
        hit = s < b and e > a
        parts.append(f'<mark>{h}</mark>' if hit else h)
    txt = ''.join(parts).replace('</mark><mark>', '')
    return ('…' if lo > 0 else '') + txt + ('…' if hi < len(plain) else '')

GROUPS = {
 'A': ('1', 'คำสั่งท้ายโจทย์', 'บอกว่าต้องตอบอะไร — อ่านท้ายประโยคก่อนเสมอ'),
 'B': ('2', '⭕ หาอันที่ถูก', ''),
 'C': ('3', '❌ หาอันที่ผิด — ระวัง!', 'มีคำปฏิเสธ (ない / ' + R('誤','あやま') + ' / ' + R('間違','まちが') + ' / ' + R('不','ふ') + ') = ต้องเลือกข้อที่ผิด'),
 'D': ('4', 'หัวข้อที่โจทย์ถาม', 'คำที่อยู่หน้า で / として / について คือเรื่องที่ถาม'),
 'E': ('5', 'รูปภาพ / ช่องว่าง', ''),
 'F': ('6', 'เงื่อนไข · เวลา · เหตุผล', ''),
 'G': ('7', 'กฎ · ข้อบังคับ · ระดับ', ''),
 'H': ('8', 'ตัวเลข', 'สำคัญมากในข้อกฎหมาย/ความปลอดภัย'),
 'I': ('9', 'รูปกริยาที่เจอบ่อย', ''),
}
neg = sum(1 for x in d if re.search(r'正しくない|誤って|間違|適切でない|不適切|当てはまらない|含まれない|含まない|でないもの|ではない|してはいけない', x['stem']))

rows_by = {}
for g, k, rx, disp, th in ITEMS:
    ex = [x for x in d if re.search(rx, x['stem'])]
    if not ex: continue
    first = rx.split('|')[0]
    try: re.compile(first)
    except re.error: first = rx
    ex.sort(key=lambda x: (0 if re.search(first, x['stem']) else 1, len(x['stem'])))
    e = ex[0]
    rows_by.setdefault(g, []).append((disp, th, len(ex), snippet(e, rx), e['code']))

sections = ''
for g, (num, title, note) in GROUPS.items():
    rows = rows_by.get(g, [])
    if not rows: continue
    trs = ''.join(f'<tr><td class="ja">{disp}</td><td class="th">{th}</td><td class="n">{n}</td><td class="ex"><span class="ja">{ex}</span><span class="code">{code}</span></td></tr>' for disp, th, n, ex, code in rows)
    keep = ' class="keep"' if len(rows) <= 12 else ''
    sections += f'''<section{keep}><h2><span class="num">{num}</span>{title}{f'<small>{note}</small>' if note else ''}</h2>
<table><colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4"></colgroup>
<tr><th>คำ / ไวยากรณ์</th><th>ความหมาย</th><th>ข้อ</th><th>ตัวอย่างจากโจทย์จริง</th></tr>{trs}</table></section>'''

particles = [('は', 'หัวเรื่อง (〜นั้น)'), ('の', 'ของ'), ('を', 'กรรม (ทำ〜)'), ('に', 'ที่ / ไปยัง / ให้'), ('で', 'ที่ / ด้วย / ใน'), ('が', 'ประธาน'),
             ('と', 'กับ / ว่า'), ('や', '〜และ〜 (ยกตัวอย่าง)'), ('から', 'จาก'), ('まで', 'ถึง'), ('も', '〜ก็'), ('か', 'ไหม / หรือ (คำถาม)')]
ptab = ''.join(f'<div class="pt"><b class="ja">{p}</b><span>{t}</span></div>' for p, t in particles)

example = (f'<span class="seg"><span class="ja">{R("熱中症対策","ねっちゅうしょうたいさく")}</span><small>มาตรการกันโรคลมแดด</small></span>'
           f'<span class="seg"><span class="ja">として、</span><small>ในฐานะ</small></span>'
           f'<span class="seg pos"><span class="ja">{R("正","ただ")}しいもの</span><small>อันที่ถูก</small></span>'
           f'<span class="seg"><span class="ja">を{R("選","えら")}べ。</span><small>จงเลือก</small></span>')
example2 = (f'<span class="seg"><span class="ja">{R("熱中症","ねっちゅうしょう")}について、</span><small>เกี่ยวกับโรคลมแดด</small></span>'
            f'<span class="seg neg"><span class="ja">{R("誤","あやま")}っているもの</span><small>อันที่ผิด ⚠</small></span>'
            f'<span class="seg"><span class="ja">を{R("選","えら")}びなさい。</span><small>จงเลือก</small></span>')

page = f'''<!doctype html><html lang="th"><head><meta charset="utf-8"><title>JAC question grammar</title><style>
@page {{ size: A4; margin: 12mm 11mm 13mm }}
* {{ box-sizing: border-box }}
body {{ font-family: 'Loma', 'Noto Sans CJK JP', sans-serif; color: #1d2b3a; font-size: 10.3pt; line-height: 1.45; margin: 0 }}
.ja, ruby {{ font-family: 'Noto Sans CJK JP', sans-serif }}
rt {{ font-size: 50%; color: #4a5a6a; font-family: 'Noto Sans CJK JP', sans-serif }}
h1 {{ font-size: 17pt; margin: 0 0 2px }} .sub {{ color: #5b6b7b; font-size: 9.5pt; margin-bottom: 8px }}
.how {{ border: 2px solid #f0b400; background: #fff8e1; border-radius: 10px; padding: 8px 12px; margin: 6px 0 10px; break-inside: avoid }}
.how b.t {{ font-size: 11pt }} .how ol {{ margin: 4px 0 6px; padding-left: 20px }} .how li {{ margin: 1px 0 }}
.sent {{ display: flex; flex-wrap: wrap; gap: 4px; margin: 4px 0 }}
.seg {{ display: inline-flex; flex-direction: column; align-items: center; border: 1.5px solid #c9d2da; border-radius: 7px; padding: 2px 7px; background: #fff }}
.seg .ja {{ font-size: 12pt }} .seg small {{ font-size: 8pt; color: #4a5a6a }}
.seg.pos {{ border-color: #1f9d55; background: #e9f8ef }} .seg.neg {{ border-color: #d9480f; background: #fdecea }}
h2 {{ font-size: 12pt; margin: 10px 0 4px; display: flex; align-items: baseline; gap: 7px; break-after: avoid }}
h2 .num {{ background: #1d2b3a; color: #fff; border-radius: 6px; padding: 0 7px; font-size: 10pt }}
h2 small {{ font-weight: normal; color: #5b6b7b; font-size: 8.8pt }}
section {{ break-inside: auto }} section.keep {{ break-inside: avoid }}
table {{ width: 100%; border-collapse: collapse; table-layout: fixed }}
col.c1 {{ width: 27% }} col.c2 {{ width: 27% }} col.c3 {{ width: 6% }} col.c4 {{ width: 40% }}
th {{ text-align: left; font-size: 8.3pt; color: #5b6b7b; font-weight: normal; border-bottom: 1.5px solid #1d2b3a; padding: 2px 4px }}
td {{ border-bottom: 1px solid #dde3e8; padding: 2px 4px; vertical-align: middle }}
tr {{ break-inside: avoid }}
td.ja {{ font-size: 11.3pt; font-weight: 700 }} td.n {{ text-align: center; color: #5b6b7b; font-size: 8.8pt }}
td.ex {{ font-size: 9.2pt }} td.ex .code {{ display: block; color: #8a97a3; font-size: 7.6pt }}
mark {{ background: #ffe08a; padding: 0 1px; border-radius: 2px }}
section.c table td.th {{ color: #b23a0a; font-weight: 700 }}
.pgrid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px 10px; margin-top: 4px }}
.pt {{ display: flex; gap: 6px; align-items: baseline; border-bottom: 1px dashed #dde3e8; padding: 2px 0 }} .pt b {{ font-size: 12pt; min-width: 34px }}
.foot {{ margin-top: 10px; color: #8a97a3; font-size: 8pt }}
</style></head><body>
<h1>คำและไวยากรณ์ที่ใช้ตั้งคำถาม</h1>
<div class="sub">ข้อสอบ JAC <span class="ja">{R('建設分野','けんせつぶんや')} {R('特定技能','とくていぎのう')}2{R('号','ごう')}</span> — รวบรวมจากโจทย์ {N} ข้อในแอป JAC · ช่อง "ข้อ" = จำนวนโจทย์ที่ใช้คำนี้</div>
<div class="how"><b class="t">อ่านโจทย์ยาวๆ ให้เร็ว: 3 ขั้น</b>
<ol><li><b>ดูท้ายประโยค</b> — <span class="ja">{R("選","えら")}べ / どれですか / {R("何","なん")}ですか</span> บอกว่าต้องเลือกอะไร</li>
<li><b>ดูว่าหาอันถูกหรืออันผิด</b> — ถ้ามี <span class="ja">ない・{R("誤","あやま")}って・{R("間違","まちが")}い・{R("不適切","ふてきせつ")}</span> ให้เลือก<b>ข้อที่ผิด</b> (มี {neg} ข้อจาก {N} ข้อ)</li>
<li><b>หาเรื่องที่ถาม</b> — คำหน้า <span class="ja">で・として・について</span> คือหัวข้อ ไม่ต้องแปลทุกคำ</li></ol>
<div class="sent">{example}</div><div class="sent">{example2}</div></div>
{sections.replace('<section class="keep"><h2><span class="num">3</span>', '<section class="keep c"><h2><span class="num">3</span>')}
<section><h2><span class="num">10</span>คำช่วย (เจอในทุกโจทย์)<small>ตัวเล็กๆ ที่เชื่อมคำ รู้ความหมายคร่าวๆ ก็อ่านออก</small></h2><div class="pgrid">{ptab}</div></section>
<div class="foot">แอป JAC · jac-app.deadpoo258.workers.dev · ตัวอย่างทุกบรรทัดมาจากโจทย์จริงในแอป (รหัสข้อใต้ตัวอย่าง)</div>
</body></html>'''
open(SP + 'jac_question_grammar.html', 'w', encoding='utf-8').write(page)
print('rows', sum(len(v) for v in rows_by.values()), 'neg', neg)
