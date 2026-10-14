import asyncio, json
from playwright.async_api import async_playwright
JS=r"""()=>{
  const res={A:[0,0,0],B:[0,0,0],C:[0,0,0]}, failA=[], failB=[], failC=[];
  const seen=new Set();
  VOCAB.forEach(v=>{ const th=plainX(v.th).split(/ — |\(|（|,|、/)[0].trim(); if(!th||th.length<2||seen.has(th)) return; seen.add(th);
    const r=askSearch(th+' ภาษาญี่ปุ่นว่าอะไร'); res.A[2]++; const vs=r?r.voc.map(x=>x.v):[];
    if(vs[0]===v||(vs[0]&&vs[0].t===v.t)) res.A[0]++; else if(vs.some(x=>x.t===v.t)) res.A[1]++; else if(failA.length<12) failA.push(th+' → '+(vs[0]?vs[0].t:'-')+' (ควร '+v.t+')'); });
  const seenT=new Set();
  VOCAB.forEach(v=>{ if(!v.t||seenT.has(v.t)) return; seenT.add(v.t); const r=askSearch(v.t+' คืออะไร'); res.B[2]++; const vs=r?r.voc.map(x=>x.v):[];
    if(vs[0]&&vs[0].t===v.t) res.B[0]++; else if(vs.some(x=>x.t===v.t)) res.B[1]++; else if(failB.length<8) failB.push(v.t+' → '+(vs[0]?vs[0].t:'-')); });
  QUESTIONS.forEach((q,i)=>{ const a=plainX(q.opts[q.ans-1]); if(a.length>14||!/[぀-ヿ一-鿿]/.test(a)) return; const r=askSearch(a+' คืออะไร'); res.C[2]++;
    const qs=r?r.qs:[]; if(qs.slice(0,3).includes(i)) res.C[0]++; else if(qs.includes(i)) res.C[1]++; else if(failC.length<8) failC.push(qCode(q)+' '+a+' → '+(qs.slice(0,3).map(j=>qCode(QUESTIONS[j])).join(',')||'-')); });
  return {res,failA,failB,failC};
}"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        pg=await b.new_page(); await pg.route('https://**', lambda r: r.abort())
        await pg.goto('file:///home/claude/build/dist/index.html'); await pg.wait_for_timeout(2500)
        r=await pg.evaluate(JS); print(json.dumps(r,ensure_ascii=False,indent=1)); await b.close()
asyncio.run(main())
