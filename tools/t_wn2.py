import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'); errs=[]
        for seen,exp in [('',5),('2026-10-12',5),('2026-10-12b',1),('2026-10-12c',0)]:
            pg=await b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); await pg.route('https://**', lambda r: r.abort())
            await pg.goto('file:///home/claude/build/dist/index.html'); await pg.evaluate(f"localStorage.setItem('jac-wn-seen', JSON.stringify('{seen}'))" if seen else "localStorage.removeItem('jac-wn-seen')")
            await pg.reload(); await pg.wait_for_timeout(1800)
            n=await pg.evaluate("$('wnSheet').hidden ? 0 : $('wnTrack').children.length"); print(seen or 'new', n, 'expected', exp); await pg.close()
        print('errs',errs); await b.close()
asyncio.run(main())
