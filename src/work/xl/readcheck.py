import json,re,glob,collections
s=open('/home/claude/build/index.html',encoding='utf-8').read()
known=collections.defaultdict(set)
for k,f in re.findall(r"R\('([^']+)','([^']+)'\)",s): known[k].add(f)
for k,f in re.findall(r"<ruby>([^<]+)<rt>([^<]+)</rt></ruby>",s): known[k].add(f)
for t,r in re.findall(r"\{ t:'([^']+)', r:'([^']+)'",s):
    if re.fullmatch(r'[㐀-鿿々]+',t): known[t].add(r)
RUBY=re.compile(r'([㐀-鿿豈-﫿々〆ヵヶ]+)\{([ぁ-ゖー・]+)\}')
out=[]
for fn in sorted(glob.glob('out_*.json')):
    for o in json.load(open(fn)):
        txt=' '.join([o['sth'],o['ath'],o['th']]+o['oth'])
        for k,f in RUBY.findall(txt):
            if k in known and f not in known[k]: out.append((o['id'],k,f,'/'.join(known[k])))
print(len(out))
for x in out: print(*x)
