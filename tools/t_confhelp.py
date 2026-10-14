# มั่นใจ / ยังเดาอยู่ explainer: open under Q1 on the first practice quiz, ? toggles it, "เข้าใจแล้ว" closes it for good
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.route('https://**', lambda r: r.abort())
        await pg.goto('file:///home/claude/build/dist/index.html'); await pg.wait_for_timeout(1800)
        await pg.evaluate("$('wnSheet').hidden || $('wnX').click(); $('nickSheet').classList.remove('on'); go('practice'); startQuiz(pool().slice(0,5),'t','mini',0)")
        await pg.wait_for_timeout(300)
        vis = lambda: pg.evaluate("[...document.querySelectorAll('.confhelp')].filter(x=>!x.hidden).length")
        print('first quiz, open boxes:', await vis())
        await pg.screenshot(path='/tmp/confhelp.png')
        await pg.evaluate("document.querySelector('.confhelp .ok').click()"); print('after เข้าใจแล้ว:', await vis(), 'flag', await pg.evaluate("load('jac-confhelp',0)"))
        await pg.evaluate("document.querySelector('[data-cinfo]').click()"); print('after ? :', await vis())
        await pg.evaluate("document.querySelector('[data-cinfo]').click()"); print('after ? again:', await vis())
        await pg.evaluate("go('practice'); startQuiz(pool().slice(0,5),'t','mini',0)"); await pg.wait_for_timeout(200)
        print('second quiz, open boxes:', await vis()); print('errors', errs); await b.close()
asyncio.run(main())
