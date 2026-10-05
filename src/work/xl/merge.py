import json, re, glob
P='/home/claude/build/index.html'; s=open(P,encoding='utf-8').read()
RUBY=re.compile(r'([㐀-鿿豈-﫿々〆ヵヶ]+)\{([ぁ-ゖー・]+)\}')
conv=lambda t: RUBY.sub(r'<ruby>\1<rt>\2</rt></ruby>', t)
allo={}
for fn in sorted(glob.glob('/home/claude/xl/out_*.json')):
    for o in json.load(open(fn)):
        allo[o['id']]={k:(conv(o[k]) if isinstance(o[k],str) else [conv(x) for x in o[k]]) for k in ('sth','ath','oth','th')}
js=lambda v: json.dumps(v, ensure_ascii=False)
done=set()
# gakka objects (JS literals)
for qid,d in allo.items():
    if not qid.startswith('g'): continue
    m=re.search(r"\{ id:'%s',.*?\n\s*th:(?:'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\") *\}" % qid, s, re.S)
    assert m, qid
    blk=m.group(0); assert 'sth:' not in blk, qid
    nb=re.sub(r"\n(\s*)th:(?:'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\") *\}$",
              lambda mm: f"\n{mm.group(1)}sth:{js(d['sth'])},\n{mm.group(1)}ath:{js(d['ath'])},\n{mm.group(1)}oth:{js(d['oth'])},\n{mm.group(1)}th:{js(d['th'])} }}", blk)
    assert nb!=blk, qid
    s=s.replace(blk,nb,1); done.add(qid)
# jitsugi JSON line
lines=s.split('\n'); i=[k for k,l in enumerate(lines) if l.startswith('const JQ = [')][0]
arr=json.loads(lines[i][len('const JQ = '):].rstrip().rstrip(';'))
for q in arr:
    if q['id'] in allo: q.update(allo[q['id']]); done.add(q['id'])
lines[i]='const JQ = '+json.dumps(arr,ensure_ascii=False)+';'
s='\n'.join(lines)
missing=set(allo)-done; assert not missing, missing
open(P,'w',encoding='utf-8').write(s); print('merged',len(done))
