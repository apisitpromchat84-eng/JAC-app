import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        pg=await b.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e))); await pg.route('https://**', lambda r: r.abort())
        await pg.goto('file:///home/claude/build/dist/index.html'); await pg.wait_for_timeout(900)
        r=await pg.evaluate("""()=>{const bad=[];const K=/[\\u3400-\\u9fff々]/;
          const strip=h=>h.replace(/<ruby>.*?<\\/ruby>/g,'').replace(/<[^>]+>/g,'');
          for(const q of QUESTIONS){ if(!q.sth){bad.push(q.id+' no sth');continue}
            if(!Array.isArray(q.oth)||q.oth.length!==q.opts.length) bad.push(q.id+' oth len');
            else if(q.oth[q.ans-1].replace(/[\\u200b\\u200c\\u2060]/g,'')!=='') bad.push(q.id+' oth ans not empty');
            for(const t of [q.sth,q.ath,q.th,...(q.oth||[])]) if(K.test(strip(t))) bad.push(q.id+' kanji w/o ruby: '+strip(t).match(/[\\u3400-\\u9fff々]+/)[0]);
          }
          return {n:QUESTIONS.length,bad}}""")
        print(r['n'], len(r['bad']), r['bad'][:20], 'errs', errs); await b.close()
asyncio.run(main())
