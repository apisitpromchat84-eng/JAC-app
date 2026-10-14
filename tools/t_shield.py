import asyncio
from playwright.async_api import async_playwright
SP='/home/claude/repo/tools/shield/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True)
        pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.route('https://**',lambda r:r.abort())
        await pg.goto('file:///home/claude/build/dist/index.html'); await pg.wait_for_timeout(2000)
        await pg.evaluate("$('wnSheet').hidden || $('wnX').click(); save('jac-nick','ชายอาม'); save('jac-anon','abc123xyz7q9'); showNick(); $('nickSheet').classList.remove('on')")
        await pg.evaluate("go('practice'); startQuiz(pool().slice(0,5),'t','mini',0)"); await pg.wait_for_timeout(400)
        await pg.screenshot(path=SP+'quiz_light.png')
        await pg.evaluate("document.documentElement.dataset.theme='dark'"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=SP+'quiz_dark.png')
        await pg.evaluate("document.documentElement.dataset.theme='light'; window.dispatchEvent(new Event('blur'))"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=SP+'cover.png')
        await pg.evaluate("window.dispatchEvent(new Event('focus'))"); 
        print('cover off after focus:', not await pg.evaluate("document.documentElement.classList.contains('shield')"))
        await pg.evaluate("document.dispatchEvent(new KeyboardEvent('keyup',{key:'PrintScreen'}))")
        print('flash on:', await pg.evaluate("document.documentElement.classList.contains('shield')"))
        await pg.wait_for_timeout(1700)
        print('flash off:', not await pg.evaluate("document.documentElement.classList.contains('shield')"))
        # clicks still go through the watermark
        await pg.evaluate("closeSheets && closeSheets(); go('home')"); await pg.wait_for_timeout(200)
        el=1

        print('errors', errs)
        await b.close()
asyncio.run(main())
