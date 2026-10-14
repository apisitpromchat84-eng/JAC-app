import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx=await b.new_context(viewport={'width':1000,'height':700},device_scale_factor=1)
        pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.route('https://**',lambda r:r.abort())
        await pg.goto('file:///home/claude/build/dist/index.html'); await pg.wait_for_timeout(2000)
        await pg.evaluate("$('wnSheet').hidden || $('wnX').click(); $('nickSheet').classList.remove('on'); prefs.part='jitsugi'; prefs.track='jitsugi'; applyPrefs(); onPartChange(); go('practice')")
        cat=await pg.evaluate("P().cats.map(c=>c.id).find(c=>miniState(c).all.length>20)")
        # 10-question mini quiz with no confidence pressed, 7 right 3 wrong
        await pg.evaluate(f"""()=>{{const pick=miniPick('{cat}'); startQuiz(pick,'t','mini',0);
          layout.forEach((it,i)=>{{picks[i]= i<7 ? QUESTIONS[it.qi].ans : (QUESTIONS[it.qi].ans%4)+1;}}); conf[0]='sure'; grade(true); grading=false; document.getElementById('grading').classList.remove('on'); go('practice');}}""")
        await pg.wait_for_timeout(400)
        print(await pg.evaluate(f"document.querySelector('[data-cat={cat}]').innerText"))
        await pg.locator('#catMenu').screenshot(path='shield/mini.png')
        print('errors',errs); await b.close()
asyncio.run(main())
