import json, re
from PIL import Image
P='/home/claude/build/index.html'; s=open(P,encoding='utf-8').read()
def sub1(old,new,cnt=1):
    global s; n=s.count(old); assert n==cnt,(n,old[:90]); s=s.replace(old,new)
RUBY=re.compile(r'([㐀-鿿豈-﫿々〆ヵヶ]+)\{([ぁ-ゖー・]+)\}')
conv=lambda t: RUBY.sub(r'<ruby>\1<rt>\2</rt></ruby>', t)
allq=[]
for k in 'ABCDEF': allq+=json.load(open(f'/home/claude/l2/out_h{k}.json'))
LQ2=[]; imgs=[]
IDM=json.load(open('/home/claude/l2/idmap.json')); nxt=max(int(v[1:]) for v in IDM.values())
for o in allq:
    if o['id'] not in IDM: nxt+=1; IDM[o['id']]=f'm{nxt:03d}'
    qid=IDM[o['id']]; n=int(qid[1:])
    q=dict(id=qid,cat=o['cat'],src=o['src'],stem=conv(o['stem_f']).replace('（）','（　　）'),opts=[conv(x) for x in o['opts_f']],ans=o['ans'],
           th=conv(o['th']),sth=conv(o['sth']),ath=conv(o['ath']),oth=[conv(x) for x in o['oth']])
    if o.get('img'):
        im=Image.open('/home/claude/l2/'+o['img']).convert('RGB'); c=o.get('crop') or [0,0,1,1]; W,H=im.size
        im=im.crop((int(c[0]*W),int(c[1]*H),int(c[2]*W),int(c[3]*H))); im.thumbnail((640,640))
        fn=f'img/l2_{n:03d}.jpg'; im.save('/home/claude/build/'+fn,quality=84); q['img']=fn; imgs.append(fn)
    if o.get('dup_of'): q['dup']=o['dup_of']
    LQ2.append(q)
i=s.index('\nconst JV = [')
s=s[:i]+'\n/* ライフライン ver.2: only the points the user highlighted after sitting the real exam (src = JAC 実技テキスト + printed page), independently reviewed */\nconst LQ2 = '+json.dumps(LQ2,ensure_ascii=False)+';'+s[i:]
sub1('].concat(JQ, LQ);','].concat(JQ, LQ, LQ2);')
sub1("const qCode = q => ({ j:'ป-', l:'ล-' }[q.id[0]] || 'ท-') + q.id.slice(1);",
     "const qCode = q => ({ j:'ป-', l:'ล-', m:'ล2-' }[q.id[0]] || 'ท-') + q.id.slice(1);")
# set filter for lifeline: all / ver1 / ver2
sub1("const pool = () => QUESTIONS.map((q, i) => i).filter(i => partOf(QUESTIONS[i]) === prefs.part);",
     "const lsetOk = q => prefs.part !== 'life' || !prefs.lset || prefs.lset === 'all' || (prefs.lset === 'v2' ? q.id[0] === 'm' : q.id[0] === 'l');\nconst pool = () => QUESTIONS.map((q, i) => i).filter(i => partOf(QUESTIONS[i]) === prefs.part && lsetOk(QUESTIONS[i]));")
for pid in ('partTitle','practiceTitle'):
    old=f'<div class="partbar" id="{pid}"></div>\n    <div class="seg trackseg" data-track><button data-v="jitsugi">土木 งานโยธา</button><button data-v="life">ライフライン・設備</button></div>'
    sub1(old, old+'\n    <div class="seg trackseg lsetseg" data-lset><button data-v="all">ทั้งหมด</button><button data-v="v1">ชุด 1 (110)</button><button data-v="v2">ชุด 2 จุดที่ออกสอบ</button></div>')
sub1('body[data-part="gakka"] .trackseg{ display:none }','body[data-part="gakka"] .trackseg{ display:none } body:not([data-part="life"]) .lsetseg{ display:none } .lsetseg{ margin-top:8px } .lsetseg button{ font-size:.74rem }')
sub1("part:'gakka', track:'jitsugi', sound:'on', view:'one', tts:'slow' }","part:'gakka', track:'jitsugi', lset:'all', sound:'on', view:'one', tts:'slow' }")
sub1("  document.querySelectorAll('[data-track] button').forEach(b => b.classList.toggle('on', b.dataset.v === prefs.part));",
     "  document.querySelectorAll('[data-track] button').forEach(b => b.classList.toggle('on', b.dataset.v === prefs.part));\n  document.querySelectorAll('[data-lset] button').forEach(b => b.classList.toggle('on', b.dataset.v === (prefs.lset || 'all')));")
sub1("$('furiBtn').addEventListener('click',",
"""document.querySelectorAll('[data-lset]').forEach(el => el.addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b || b.dataset.v === prefs.lset) return;
  prefs.lset = b.dataset.v; applyPrefs(); onPartChange();
}));
$('furiBtn').addEventListener('click',""")
# ver.2 questions that test the same fact as a ver.1 question never appear together in one mock exam
sub1("""  return sib;
})();
function pickReal(part) {""","""  const byId = new Map(QUESTIONS.map((q, i) => [q.id, i]));
  QUESTIONS.forEach((q, i) => { const j = q.dup && byId.get(q.dup); if (j !== undefined) { sib[i].add(j); sib[j].add(i); } });
  return sib;
})();
function pickReal(part) {""")
open(P,'w',encoding='utf-8').write(s)
sw=open('/home/claude/build/sw.js').read()
anchor="  './img/l_110.jpg',\n"; assert anchor in sw
sw=sw.replace(anchor,anchor+''.join(f"  './{f}',\n" for f in imgs)).replace("jac-exam-v14","jac-exam-v16")
open('/home/claude/build/sw.js','w').write(sw)
print('LQ2',len(LQ2),'imgs',len(imgs))

json.dump(IDM,open('/home/claude/l2/idmap.json','w'),indent=0)
