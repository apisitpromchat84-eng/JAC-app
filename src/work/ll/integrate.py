import json, re, glob
P='/home/claude/build/index.html'; s=open(P,encoding='utf-8').read()
def sub1(old,new,cnt=1):
    global s; n=s.count(old); assert n==cnt,(n,old[:90]); s=s.replace(old,new)
RUBY=re.compile(r'([㐀-鿿豈-﫿々〆ヵヶ]+)\{([ぁ-ゖー・]+)\}')
conv=lambda t: RUBY.sub(r'<ruby>\1<rt>\2</rt></ruby>', t)
items={i['id']:i for i in json.load(open('/home/claude/ll/items.json'))}
LQ=[]
for fn in sorted(glob.glob('/home/claude/ll/out_*.json')):
    for o in json.load(open(fn)):
        it=items[o['id']]
        q=dict(id=o['id'],cat=it['cat'],src=it['src'],stem=conv(o['stem_f']),opts=[conv(x) for x in o['opts_f']],ans=o['ans'],
               th=conv(o['th']),sth=conv(o['sth']),ath=conv(o['ath']),oth=[conv(x) for x in o['oth']])
        if it['img'] and o.get('img', it['img']) is not None: q['img']=it['img']
        LQ.append(q)
assert len(LQ)==110
# data
i=s.index('\nconst JV = [')
s=s[:i]+'\n/* ライフライン・設備 実技 practice set (110 questions, answers worked out and reviewed; not an official paper) */\nconst LQ = '+json.dumps(LQ,ensure_ascii=False)+';'+s[i:]
sub1('].concat(JQ);','].concat(JQ, LQ);')
# parts
sub1("""  { id:'j_kanri',  ja:'施工管理',         th:'บริหารงานก่อสร้าง' }
];""","""  { id:'j_kanri',  ja:'施工管理',         th:'บริหารงานก่อสร้าง' }
];
const CATS_L = [
  { id:'l_kikai',   ja:'建設機械',       th:'เครื่องจักร/ขนย้าย' },
  { id:'l_denki',   ja:'電気・通信',     th:'ไฟฟ้า/สื่อสาร' },
  { id:'l_kankan',  ja:'配管・衛生・消防', th:'งานท่อ/สุขาภิบาล/ดับเพลิง' },
  { id:'l_dougu',   ja:'工具・加工',     th:'เครื่องมือ/งานแปรรูป' },
  { id:'l_anzen',   ja:'安全',           th:'ความปลอดภัย' },
  { id:'l_kanri',   ja:'施工管理・埋設物', th:'บริหารงาน/สิ่งก่อสร้างใต้ดิน' },
  { id:'l_chikuro', ja:'築炉',           th:'งานก่อเตาเผา' }
];""")
sub1("""  jitsugi: { ja:'ภาคปฏิบัติ (งานโยธา)', cats:CATS_J, real:{ n:25, min:40, pass:75, photo:2 } }   // real 実技 paper has only 2 photo questions""",
"""  jitsugi: { ja:'ภาคปฏิบัติ (งานโยธา)', cats:CATS_J, real:{ n:25, min:40, pass:75, photo:2 } },  // real 実技 paper has only 2 photo questions
  life:    { ja:'ภาคปฏิบัติ (ไลฟ์ไลน์)', cats:CATS_L, real:{ n:25, min:40, pass:75, photo:2 } }   // ライフライン・設備 実技: same paper format assumed""")
sub1("const ALLCATS = CATS_G.concat(CATS_J);","const ALLCATS = CATS_G.concat(CATS_J, CATS_L);")
sub1("const partOf = x => (x.cat || '').startsWith('j_') ? 'jitsugi' : 'gakka';",
     "const partOf = x => { const c = x.cat || ''; return c.startsWith('j_') ? 'jitsugi' : c.startsWith('l_') ? 'life' : 'gakka'; };")
sub1("const qCode = q => (q.id[0] === 'j' ? 'ป-' : 'ท-') + q.id.slice(1);",
     "const qCode = q => ({ j:'ป-', l:'ล-' }[q.id[0]] || 'ท-') + q.id.slice(1);")
# vocab: lifeline has no own word list yet -> use the 学科 words
sub1("const vocabPart = () => VOCAB.filter(v => partOf(v) === prefs.part);",
     "const vocabPart = () => VOCAB.filter(v => partOf(v) === (prefs.part === 'life' ? 'gakka' : prefs.part));   // ライフライン has no own word list yet")
# header: ปฏิบัติ = the chosen practical track; track switch under the part title
sub1('<button data-v="jitsugi">ปฏิบัติ</button></div>','<button data-v="prac">ปฏิบัติ</button></div>')
for pid in ('partTitle','practiceTitle'):
    sub1(f'<div class="partbar" id="{pid}"></div>',
         f'<div class="partbar" id="{pid}"></div>\n    <div class="seg trackseg" data-track><button data-v="jitsugi">土木 งานโยธา</button><button data-v="life">ライフライン・設備</button></div>')
sub1(".partbar{ margin:14px 0 -4px; font-size:.8rem; color:var(--accent-ink); font-weight:800 }",
     ".partbar{ margin:14px 0 -4px; font-size:.8rem; color:var(--accent-ink); font-weight:800 }\n.trackseg{ margin:12px 0 -4px; width:max-content; max-width:100% } .trackseg button{ font-family:var(--thf) } body[data-part=\"gakka\"] .trackseg{ display:none }")
sub1("part:'gakka', sound:'on', view:'one', tts:'slow' }","part:'gakka', track:'jitsugi', sound:'on', view:'one', tts:'slow' }")
sub1("if (!PARTS[prefs.part]) prefs.part = 'gakka';","if (!PARTS[prefs.part]) prefs.part = 'gakka';\nif (prefs.part !== 'gakka') prefs.track = prefs.part;")
sub1("  SEGS.forEach(([sid, key]) => $(sid).querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.v === prefs[key])));",
"""  SEGS.forEach(([sid, key]) => $(sid).querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.v === prefs[key] || (key === 'part' && b.dataset.v === 'prac' && prefs.part !== 'gakka'))));
  document.body.dataset.part = prefs.part;
  document.querySelectorAll('[data-track] button').forEach(b => b.classList.toggle('on', b.dataset.v === prefs.part));""")
sub1("""  const v = e.target.dataset.v; if (!v) return;
  const changed = prefs[key] !== v;
  prefs[key] = v; applyPrefs();""","""  let v = e.target.dataset.v; if (!v) return;
  if (key === 'part' && v === 'prac') v = prefs.track || 'jitsugi';
  const changed = prefs[key] !== v;
  prefs[key] = v; if (key === 'part' && v !== 'gakka') prefs.track = v; applyPrefs();""")
sub1("$('furiBtn').addEventListener('click',",
"""document.querySelectorAll('[data-track]').forEach(el => el.addEventListener('click', e => {
  const v = e.target.closest('button') && e.target.closest('button').dataset.v; if (!v || v === prefs.part) return;
  prefs.part = v; prefs.track = v; applyPrefs(); onPartChange();
}));
$('furiBtn').addEventListener('click',""")
# both parts: 学科 + the chosen practical track
sub1("const rows = ['gakka', 'jitsugi'].map(p => {","const rows = ['gakka', prefs.track || 'jitsugi'].map(p => {")
open(P,'w',encoding='utf-8').write(s); print('ok', len(LQ))
