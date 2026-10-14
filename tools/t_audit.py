import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        pg=await b.new_page(); await pg.route('https://**',lambda r:r.abort())
        await pg.goto('file:///home/claude/build/index.html'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("""()=>{
          const strip=s=>String(s||'').replace(/<rt>.*?<\\/rt>/g,'').replace(/<[^>]+>/g,'').replace(/\\s/g,'');
          const out={n:QUESTIONS.length, badAns:[], noSth:0, noAth:0, noOth:0, dupStem:[], dupOpt:[], noTh:0, parts:{}};
          const seen={};
          QUESTIONS.forEach(q=>{
            out.parts[partOf(q)]=(out.parts[partOf(q)]||0)+1;
            if(!(q.ans>=1&&q.ans<=(q.opts||[]).length)) out.badAns.push(q.id);
            if(!q.sth) out.noSth++; if(!q.ath) out.noAth++; if(!q.oth||!q.oth.length) out.noOth++; if(!q.th) out.noTh++;
            const k=strip(q.stem)+'|'+(q.opts||[]).map(strip).sort().join('/');
            if(seen[k]) out.dupStem.push(seen[k]+'='+q.id); else seen[k]=q.id;
            const os=(q.opts||[]).map(strip); if(new Set(os).size!==os.length && !q.img) out.dupOpt.push(q.id);
          });
          const ansDist={}; QUESTIONS.forEach(q=>ansDist[q.ans]=(ansDist[q.ans]||0)+1); out.ansDist=ansDist;
          return out;}""")
        print(json.dumps(r,ensure_ascii=False)[:1500]); await b.close()
asyncio.run(main())
