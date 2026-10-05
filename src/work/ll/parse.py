import pdfplumber, json, re
F='/root/.claude/uploads/beb59762-83c7-50f5-8de5-af8319c8e710/ddb05e5c-JAC_Lifeline_Practice_110.pdf'
pdf=pdfplumber.open(F)
KANA=re.compile(r'[ぁ-ゖァ-ヺー]')
def isk(ch): return bool(re.match(r'[㐀-鿿々〆ヵヶ]',ch))
def ruby_groups(rs):
    rs=sorted(rs,key=lambda c:c['x0']); g=[]
    for c in rs:
        if g and c['x0']-g[-1][-1]['x0'] < c['size']*1.35: g[-1].append(c)
        else: g.append([c])
    return g
def render(base, rubies):
    """base: chars of one line (one region), rubies: ruby chars above. returns html with <ruby>"""
    base=sorted(base,key=lambda c:c['x0'])
    used=[None]*len(base)
    for gi,g in enumerate(ruby_groups(rubies)):
        rx0=g[0]['x0']; rx1=g[-1]['x1']
        idx=[i for i,c in enumerate(base) if min(c['x1'],rx1)-max(c['x0'],rx0) > (c['x1']-c['x0'])*0.25]
        for i in idx:
            if used[i] is None: used[i]=gi
        groups_reading=None
    out=''; i=0; G=ruby_groups(rubies)
    while i<len(base):
        gi=used[i]
        if gi is None: out+=base[i]['text']; i+=1; continue
        j=i
        while j<len(base) and used[j]==gi: j+=1
        word=''.join(c['text'] for c in base[i:j]); rd=''.join(c['text'] for c in G[gi])
        # strip shared kana prefix/suffix
        pre=''
        while word and rd and not isk(word[0]) and word[0]==rd[0]: pre+=word[0]; word=word[1:]; rd=rd[1:]
        suf=''
        while word and rd and not isk(word[-1]) and word[-1]==rd[-1]: suf=word[-1]+suf; word=word[:-1]; rd=rd[:-1]
        if word and rd and any(isk(ch) for ch in word): out+=pre+f'<ruby>{word}<rt>{rd}</rt></ruby>'+suf
        else: out+=pre+word+suf
        i=j
    return out.replace('　',' ').strip()
def page_items(pn):
    p=pdf.pages[pn]
    ch=[c for c in p.chars if 45<c['top']<800 and c['text'].strip()]
    qn={}
    for c in ch:
        if c['x0']<62 and c['size']>10.5 and c['text'].isdigit(): qn.setdefault(round(c['top']),[]).append(c)
    qnums=sorted((t,int(''.join(x['text'] for x in sorted(v,key=lambda c:c['x0'])))) for t,v in qn.items())
    optn=[c for c in ch if 9.5<c['size']<10.5 and c['text'] in '1234' and c['x0']>55]
    base=[c for c in ch if c['size']>10.5 and not (c['x0']<62 and c['text'].isdigit())]
    ruby=[c for c in ch if c['size']<7]
    imgs=[(im['x0'],im['top'],im['x1'],im['bottom']) for im in p.images]
    items=[]
    for k,(qt,num) in enumerate(qnums):
        end=qnums[k+1][0]-20 if k+1<len(qnums) else 805
        ops=sorted([c for c in optn if qt+5<c['top']<end],key=lambda c:(round(c['top']),c['x0']))
        first=min(c['top'] for c in ops)-6
        def region(y0,y1,x0,x1):
            bs=[c for c in base if y0<=c['top']<y1 and x0<=c['x0']<x1]
            lines={}
            for c in bs: lines.setdefault(round(c['top']/3),[]).append(c)
            txt=''
            for key in sorted(lines):
                L=lines[key]; t=min(c['top'] for c in L)
                rs=[r for r in ruby if 2<t-r['top']<9 and x0-3<=r['x0']<x1]
                txt+=render(L,rs)
            return txt
        stem=region(qt-12,first,0,999)
        rows={}
        for c in ops: rows.setdefault(round(c['top']/4),[]).append(c)
        rowk=sorted(rows); opts={}
        for ri,rk in enumerate(rowk):
            r=sorted(rows[rk],key=lambda c:c['x0']); y0=min(c['top'] for c in r)-6
            y1=(min(c['top'] for c in rows[rowk[ri+1]])-6) if ri+1<len(rowk) else end
            for ci,c in enumerate(r):
                x0=c['x0']+5; x1=r[ci+1]['x0'] if ci+1<len(r) else 560
                if imgs and len(r)==1: x1=min([im[0] for im in imgs if im[1]<y1 and im[3]>y0] or [560])
                opts[int(c['text'])]=region(y0,y1,x0,x1)
        img=[im for im in imgs if qt-15<im[1]<end]
        items.append(dict(n=num,page=pn,stem=stem,opts=[opts.get(i,'') for i in (1,2,3,4)],img=img[0] if img else None))
    return items
allq=[]
for pn in range(1,38): allq+=page_items(pn)
print(len(allq), [q['n'] for q in allq if not all(q['opts'])], sum(1 for q in allq if q['img']))
json.dump(allq,open('raw.json','w'),ensure_ascii=False,indent=1)
for q in allq[:3]+allq[99:101]+allq[106:107]: print(q['n'],q['stem'],'|',' / '.join(q['opts']),q['img'])
