# Handout: negative / "trap" grammar in "choose the WRONG one" questions.
# Input: rawq.json (id -> code, stem html, opts html, ans) dumped from the app; output: jac_trap_grammar.html (+ PDF via print).
import json, re, sys, html as H
SP = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/repo/tools/'
D = json.load(open(SP + 'rawq.json'))
STATS = json.load(open(SP + 'trap_stats.json'))
R = lambda k, r: f'<ruby>{k}<rt>{r}</rt></ruby>'

def marked(h, rx):
    """option html (with ruby) → same html with the part matching rx (on plain text) wrapped in <mark>"""
    units = []
    for m in re.finditer(r'<ruby>(.*?)<rt>(.*?)</rt></ruby>|<[^>]+>|([^<])', h):
        if m.group(1) is not None: units.append((m.group(1), m.group(0)))
        elif m.group(3): units.append((m.group(3), H.escape(m.group(3))))
    plain = ''.join(t for t, _ in units)
    m = re.search(rx, plain)
    if not m: raise SystemExit(f'pattern {rx!r} not found in {plain}')
    a, b, pos, out = m.start(), m.end(), 0, []
    for t, u in units:
        s, e = pos, pos + len(t); pos = e
        out.append(f'<mark>{u}</mark>' if s < b and e > a else u)
    return ''.join(out).replace('</mark><mark>', '')

def opt(qid, i, rx):
    q = D[qid]
    return marked(q['opts'][i - 1], rx), q['code']

# (grammar html, Thai meaning, question id, option no., regex to mark, why it is wrong / right)
TRAP_SKIP = [
 ('〜なくてよい・〜なくてもよい', 'ไม่ต้อง〜ก็ได้', 'm137', 3, r'しなくてよい', 'ใบอนุญาตใช้ถนนต้องพกติดตัวที่หน้างานเสมอ'),
 (f'〜{R("必要","ひつよう")}はない', 'ไม่จำเป็นต้อง〜', 'g066', 4, r'必要はない', 'กฎหมายบังคับให้แต่งตั้งตามขนาดสถานประกอบการ'),
 ('〜なくても〜', 'ถึงไม่〜ก็〜ได้', 'm174', 3, r'掛けなくても', 'ใส่ฮาร์เนสแต่ไม่เกี่ยวตะขอ = ตกได้'),
 ('〜ずに', 'โดยไม่〜', 'm117', 2, r'とらずに', 'ก่ออิฐต้องเหลื่อมรอยต่อเสมอ'),
 ('〜まま', 'ทั้งที่ยัง〜อยู่', 'l074', 2, r'着けたまま', 'ใส่ถุงมือผ้ากับเครื่องหมุน = มือถูกดึงเข้าไป'),
 ('Aではなく、B', 'ไม่ใช่ A แต่เป็น B (โยนหน้าที่)', 'g072', 3, r'行うのではなく', f'{R("職長","しょくちょう")} ต้องลงมือเป็นตัวอย่างเอง'),
 ('Aではなく、B', 'ไม่ใช่ A แต่เป็น B (โยนหน้าที่)', 'g096', 2, r'職長ではなく', f'เป็นความรับผิดชอบของ {R("職長","しょくちょう")}'),
 ('〜ことはない', 'ไม่มีทาง〜 / ไม่เคย〜เลย', 'm166', 4, r'死に至ることはない', 'โรคลมแดดทำให้ตายได้'),
 ('〜ではない', 'ไม่ใช่〜', 'g067', 2, r'作業環境ではない', 'ห้องพัก/ห้องเปลี่ยนชุดก็นับเป็นสภาพแวดล้อมการทำงาน'),
]
TRAP_EXTREME = [
 ('〜だけ', 'เฉพาะ〜 / แค่〜', 'g101', 1, r'時だけ', 'ต้องทำตามขั้นตอนทุกครั้ง ไม่ใช่แค่ตอนมีคนตรวจ'),
 ('すべて', 'ทั้งหมด', 'j093', 4, r'すべて', 'รื้อเฉพาะที่ระบุในสัญญา ไม่ใช่ทุกอย่าง'),
 ('〜にかかわらず', 'ไม่ว่า〜ก็ตาม', 'g066', 4, r'規模にかかわらず', 'ข้อบังคับขึ้นกับขนาดสถานประกอบการ'),
 (f'{R("両方","りょうほう")}', 'ทั้งสองอย่าง', 'g070', 4, r'両方', 'จริงๆ มีอย่างใดอย่างหนึ่งก็พอ'),
 ('〜でも', 'ถึงจะ〜ก็', 'm153', 3, r'以内でも', 'ใกล้ท่อเดิม 50cm ต้องขุดด้วยมือ'),
 ('すぐに', 'ทันที (ข้ามขั้นตอน)', 'j029', 2, r'すぐに', 'ต้องจอดให้ปลอดภัยและตรวจก่อนกลับ'),
]
TRAP_REASON = [
 ('〜ため（に）', 'เพื่อ〜 (เหตุผลมักง่าย)', 'm109', 4, r'早くするため', 'ห้ามใช้เลื่อย/เครื่องเจียร เศษจะเข้าท่อ'),
 ('〜やすいよう（に）', 'เพื่อให้〜ง่าย', 'm110', 4, r'取り除きやすいよう', 'ต้องคว่ำท่อลง เศษจะได้ไม่ตกเข้าท่อ'),
 ('〜てから', 'หลังจาก〜แล้วจึง (ลำดับสลับ)', 'g077', 3, r'連絡してから', 'ต้องช่วยชีวิตคนเจ็บก่อน'),
 ('〜ほど', 'ยิ่ง〜ยิ่ง', 'm101', 4, r'急なほど', 'บันไดชันเกินจะหงายหลัง มุมที่ถูกคือ 75°'),
 ('もっと〜もっと', 'ยิ่ง〜ยิ่ง', 'g071', 2, r'もっと低く', 'ยิ่งเร่งงาน ต้นทุนยิ่งสูง'),
]
SAFE = [
 ('〜ないよう（に）', 'เพื่อไม่ให้〜 (ป้องกัน)', 'j015', 2, r'散乱しないよう', 'ข้อนี้ถูก'),
 ('〜てはいけない', 'ห้าม〜', 'j076', 2, r'入ってはいけません', 'ข้อนี้ถูก'),
 (f'{R("必","かなら")}ず〜', 'ต้อง〜เสมอ', 'j076', 1, r'必ず', 'ข้อนี้ถูก'),
 ('〜しない (กฎ)', 'ไม่ทำ〜 (ข้อห้าม)', 'm117', 1, r'使用しない', 'ข้อนี้ถูก'),
 ('〜ずに (บรรยาย)', 'โดยไม่〜', 'l093', 4, r'停滞せずに', 'ข้อนี้ถูก'),
]

IMG = 'file:///home/claude/build/'
def qblock(qid):
    q = D[qid]
    thumb = f'<img class="thumb" src="{IMG + q["img"]}">' if q.get('img') else ''
    return (f'<div class="q">{thumb}<span class="lab">โจทย์</span><span class="ja">{q["stem"]}</span>'
            f'<span class="qt">แปล: {q["sth"]}</span></div>')

def note(cls, qid, i, why):
    is_ans = D[qid]['ans'] == i
    if cls == 'bad':
        assert is_ans, (qid, i)                 # every ❌ example must be the real answer
        return 'ข้อนี้คือคำตอบ (ข้อที่ผิด) — ' + why
    return ('ข้อความนี้ถูก และเป็นคำตอบของข้อนี้ (โจทย์ให้หาข้อถูก)' if is_ans
            else 'ข้อความนี้ถูก จึงไม่ใช่คำตอบ (โจทย์ให้หาข้อผิด)')

def table(rows, cls):
    trs = ''
    for g, th, qid, i, rx, why in rows:
        ex, code = opt(qid, i, rx)
        mark = '✗' if cls == 'bad' else '✓'
        trs += (f'<tr><td class="g ja">{g}</td><td class="m">{th}</td><td class="ex">{qblock(qid)}'
                f'<div class="o"><span class="lab">ตัวเลือก {i}</span><span class="ja">{ex}</span></div>'
                f'<span class="why">{mark} {note(cls, qid, i, why)} <i>{code}</i></span></td></tr>')
    return f'<table class="{cls}"><colgroup><col class="c1"><col class="c2"><col class="c3"></colgroup><tr><th>ไวยากรณ์</th><th>ความหมาย</th><th>โจทย์จริงในแอป → ตัวเลือกที่มีคำนี้</th></tr>{trs}</table>'

# one full worked question, all four options
WQ = 'g101'
W_TH = ['ทำตามขั้นตอนอย่างดี <b>เฉพาะ</b>ตอนมีคนมาตรวจ', 'ถึงไม่ได้ถูกแต่งตั้งเป็น ' + R('安全管理者','あんぜんかんりしゃ') + ' หัวหน้างานก็ต้องรักษาความปลอดภัย',
        'สถานประกอบการ 50 คนขึ้นไป ต้องแต่งตั้ง ' + R('安全管理者','あんぜんかんりしゃ') + ' และ ' + R('衛生管理者','えいせいかんりしゃ'), 'ถ้ามีการฝ่าฝืนกฎ หัวหน้างานต้องตักเตือนทันที']
def worked():
    q = D[WQ]
    li = ''
    for k, o in enumerate(q['opts']):
        ans = k + 1 == q['ans']
        h = marked(o, r'時だけ') if ans else o
        li += f'<li class="{"ans" if ans else ""}"><span class="no">{k + 1}</span><div><span class="ja">{h}</span><small>{W_TH[k]}</small></div><span class="tick">{"❌ ข้อผิด = คำตอบ" if ans else "✓ ถูกตามกฎ"}</span></li>'
    return f'''<div class="work"><b class="t">ดูตัวอย่างเต็ม 1 ข้อ <i>{q["code"]}</i></b>
<div class="q big"><span class="lab">โจทย์</span><span class="ja">{q["stem"]}</span><span class="qt">แปล: {q["sth"]}</span></div>
<div class="flow"><span>① ท้ายโจทย์มี <b class="ja">{R("間違","まちが")}い</b> → หา<b>ข้อที่ผิด</b></span><span>② สแกนหาคำกับดัก → เจอ <b class="ja">だけ</b> ในข้อ 1</span><span>③ ข้ออื่นเป็นกฎปกติ → ตอบ <b>1</b></span></div>
<ol class="opts">{li}</ol></div>'''

S = STATS
page = f'''<!doctype html><html lang="th"><head><meta charset="utf-8"><title>JAC trap grammar</title><style>
@page {{ size: A4; margin: 10mm 11mm 9mm }}
* {{ box-sizing: border-box }}
body {{ font-family: 'Loma', 'Noto Sans CJK JP', sans-serif; color: #1d2b3a; font-size: 10.2pt; line-height: 1.45; margin: 0 }}
.ja, ruby {{ font-family: 'Noto Sans CJK JP', sans-serif }}
rt {{ font-size: 50%; color: #4a5a6a }}
h1 {{ font-size: 17pt; margin: 0 }} .sub {{ color: #5b6b7b; font-size: 9.3pt; margin: 2px 0 8px }}
.box {{ border: 2px solid #f0b400; background: #fff8e1; border-radius: 10px; padding: 8px 12px; margin: 0 0 8px; break-inside: avoid }}
.box b.t {{ font-size: 11pt; display: block; margin-bottom: 3px }}
.nums {{ display: flex; gap: 8px; margin: 6px 0 2px }}
.num {{ flex: 1; background: #fff; border: 1.5px solid #e2d3a0; border-radius: 8px; padding: 4px 8px; text-align: center }}
.num b {{ display: block; font-size: 16pt }} .num.hot b {{ color: #c0392b }}
.two {{ display: flex; gap: 8px; margin: 6px 0 }}
.two > div {{ flex: 1; border-radius: 8px; padding: 6px 9px; font-size: 9.6pt }}
.two .bad {{ background: #fdecea; border: 1.5px solid #e8a39b }} .two .ok {{ background: #e9f8ef; border: 1.5px solid #8fd1ab }}
h2 {{ font-size: 12pt; margin: 7px 0 2px; break-after: avoid }} h2 small {{ font-weight: normal; color: #5b6b7b; font-size: 8.8pt; margin-left: 6px }}
h2 .tag {{ border-radius: 6px; padding: 0 7px; color: #fff; font-size: 10pt; margin-right: 6px }}
.tag.bad {{ background: #c0392b }} .tag.ok {{ background: #1f9d55 }}
table {{ width: 100%; border-collapse: collapse; table-layout: fixed }}
col.c1 {{ width: 17% }} col.c2 {{ width: 15% }} col.c3 {{ width: 68% }}
th {{ text-align: left; font-size: 8.2pt; color: #5b6b7b; font-weight: normal; border-bottom: 1.5px solid #1d2b3a; padding: 2px 4px }}
td {{ border-bottom: 1px solid #dde3e8; padding: 2px 4px; vertical-align: middle }}
tr {{ break-inside: avoid }}
td.g {{ font-size: 11pt; font-weight: 700 }} table.bad td.g {{ color: #b23a0a }} table.ok td.g {{ color: #17804a }}
td.m {{ font-size: 9.4pt }}
.q {{ background: #f4f6f8; border-radius: 6px; padding: 3px 6px; margin: 1px 0 3px; font-size: 8.8pt; overflow: hidden }}
.q .ja {{ font-size: 9.2pt }} .q .qt {{ display: block; color: #4a5a6a; font-size: 8.2pt }}
.q .thumb {{ float: right; width: 52px; height: 52px; object-fit: cover; border-radius: 5px; margin-left: 6px }}
.lab {{ display: inline-block; background: #1d2b3a; color: #fff; border-radius: 4px; font-size: 7.4pt; padding: 0 5px; margin-right: 5px; vertical-align: 1px }}
.o .lab {{ background: #8a97a3 }} table.bad .o .lab {{ background: #c0392b }} table.ok .o .lab {{ background: #1f9d55 }}
td.ex .o .ja {{ font-size: 9.8pt }}
.work {{ border: 2px solid #1d2b3a; border-radius: 10px; padding: 7px 10px; margin: 0 0 6px; break-inside: avoid }}
.work b.t {{ font-size: 11pt }} .work b.t i {{ color: #8a97a3; font-style: normal; font-size: 8.5pt; margin-left: 6px }}
.q.big .ja {{ font-size: 11pt }}
.flow {{ display: flex; gap: 6px; margin: 4px 0 }} .flow span {{ flex: 1; background: #fff8e1; border-radius: 6px; padding: 3px 7px; font-size: 8.8pt }}
ol.opts {{ list-style: none; margin: 0; padding: 0 }}
ol.opts li {{ display: flex; gap: 8px; align-items: center; border: 1.5px solid #dde3e8; border-radius: 7px; padding: 3px 8px; margin: 3px 0 }}
ol.opts li.ans {{ border-color: #c0392b; background: #fdecea }} ol.opts li .no {{ font-weight: 800; width: 14px }}
ol.opts li div {{ flex: 1 }} ol.opts li .ja {{ font-size: 10pt; display: block }} ol.opts li small {{ color: #4a5a6a; font-size: 8.3pt }}
ol.opts li .tick {{ font-size: 8.3pt; white-space: nowrap; color: #17804a }} ol.opts li.ans .tick {{ color: #c0392b; font-weight: 700 }}
ol.opts mark {{ background: #ffd3cc }}
td.ex .ja {{ font-size: 9.6pt }} td.ex .why {{ display: block; font-size: 8.4pt; color: #5b6b7b }} td.ex .why i {{ color: #8a97a3; font-style: normal; margin-left: 4px }}
table.bad mark {{ background: #ffd3cc; padding: 0 1px; border-radius: 2px }} table.ok mark {{ background: #c9f0d8; padding: 0 1px; border-radius: 2px }}
.steps {{ border: 2px solid #1d2b3a; border-radius: 10px; padding: 7px 12px; margin-top: 10px; break-inside: avoid }}
.steps ol {{ margin: 3px 0 0; padding-left: 20px }} .steps li {{ margin: 2px 0 }}
.foot {{ margin-top: 8px; color: #8a97a3; font-size: 7.8pt }}
</style></head><body>
<h1>ไวยากรณ์ "กับดัก" ในข้อที่ให้เลือกข้อผิด</h1>
<div class="sub">ข้อสอบ JAC <span class="ja">{R('建設分野','けんせつぶんや')} {R('特定技能','とくていぎのう')}2{R('号','ごう')}</span> · วิเคราะห์จากโจทย์ {S['total']} ข้อในแอป JAC</div>
<div class="box"><b class="t">ผลตรวจ: ข้อสังเกตนี้ "จริงบางส่วน"</b>
มีโจทย์แบบ <span class="ja">{R('誤','あやま')}っているもの・{R('正','ただ')}しくないもの・{R('適切','てきせつ')}でないもの</span> (เลือกข้อผิด) <b>{S['neg']} ข้อ</b> · ในข้อที่ตัวเลือกเป็นประโยค:
<div class="nums"><div class="num hot"><b>{S['ans_pct']}%</b>ของ<b style="display:inline;font-size:inherit">คำตอบ</b> (ข้อที่ผิด) มีคำปฏิเสธ/คำสุดโต่ง</div><div class="num"><b>{S['dis_pct']}%</b>ของตัวเลือกอื่น มีคำแบบเดียวกัน</div><div class="num"><b>×{S['ratio']}</b>เจอในคำตอบบ่อยกว่า</div></div>
แปลว่าเป็น<b>สัญญาณที่ดี</b> แต่<b>ไม่ใช่ทุกข้อ</b> และ <span class="ja">ない</span> ธรรมดาก็อยู่ในข้อที่ถูกได้ ต้องดูว่าเป็น <span class="ja">ない</span> แบบไหน:
<div class="two"><div class="bad">❌ <b>"ไม่ต้องทำ / ข้ามขั้นตอน / โยนหน้าที่ / ไม่มีทาง"</b><br>= มักเป็น<b>ข้อที่ผิด</b> (ข้อสอบชอบหลอกว่าทำง่ายๆ ก็ได้)</div>
<div class="ok">✅ <b>"ห้าม / ต้องป้องกัน / ต้องทำเสมอ"</b><br>= มักเป็น<b>ข้อที่ถูก</b> (กฎความปลอดภัยพูดแบบนี้)</div></div></div>

{worked()}
<h2><span class="tag bad">❌ 1</span>"ไม่ต้องทำก็ได้" · ข้ามขั้นตอน · โยนหน้าที่<small>เจอคำพวกนี้ในข้อ "เลือกข้อผิด" ให้สงสัยก่อน</small></h2>
{table(TRAP_SKIP, 'bad')}
<h2><span class="tag bad">❌ 2</span>คำสุดโต่ง / จำกัดเกินจริง<small>"เฉพาะ" "ทั้งหมด" "ไม่ว่า…ก็" — โลกจริงมีข้อยกเว้นเสมอ</small></h2>
{table(TRAP_EXTREME, 'bad')}
<h2><span class="tag bad">❌ 3</span>เหตุผลมักง่าย · ลำดับสลับ · ยิ่ง…ยิ่ง<small>อ่านว่า "ทำเพื่ออะไร" และ "ทำอะไรก่อน"</small></h2>
{table(TRAP_REASON, 'bad')}
<h2><span class="tag ok">✅</span>ない ที่มักอยู่ใน<b>ข้อถูก</b> (อย่าตัดทิ้ง!)<small>เป็นภาษาของกฎความปลอดภัย</small></h2>
{table(SAFE, 'ok')}
<div class="steps"><b>ใช้ในห้องสอบ 3 ขั้น</b><ol>
<li>ดูท้ายโจทย์ — มี <span class="ja">{R('誤','あやま')}って・{R('正','ただ')}しくない・{R('適切','てきせつ')}でない・{R('間違','まちが')}い</span> ไหม → ถ้ามี = หา<b>ข้อที่ผิด</b></li>
<li>สแกนตัวเลือกหาคำในตาราง ❌ — ข้อที่มีคำพวกนี้ <b>มักเป็นคำตอบ</b> (แต่อ่านให้จบก่อนตัดสิน)</li>
<li>ถ้าไม่เจอคำกับดัก — ข้อผิดมักเป็น<b>ข้อเท็จจริงสลับกัน</b> เช่น บน↔ล่าง, หนา↔บาง, ใส่ผิดหมวด → ต้องใช้ความรู้เนื้อหา</li></ol></div>
<div class="foot">แอป JAC · ตัวอย่างทุกบรรทัดมาจากโจทย์จริงในแอป (รหัสข้อท้ายบรรทัด) · ส่วนที่ไฮไลต์ = คำที่เป็นจุดสังเกต</div>
</body></html>'''
open(SP + 'jac_trap_grammar.html', 'w', encoding='utf-8').write(page)
print('ok')
