import asyncio
from playwright.async_api import async_playwright
SP='/home/claude/repo/tools/review/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        for theme in ('light','dark'):
            pg=await b.new_page(viewport={'width':390,'height':844}, device_scale_factor=2); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.route('https://**', lambda r: r.abort())
            await pg.goto('file:///home/claude/build/dist/index.html?nowhatsnew'); await pg.wait_for_timeout(2000)
            await pg.evaluate(f"""()=>{{$('nickSheet').classList.remove('on'); prefs.theme='{theme}'; applyPrefs(); const run=(cat,acc)=>{{const idx=QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].cat===cat).slice(0,10);
              startQuiz(idx,'t','mini',0); layout.forEach((it,i)=>{{picks[i]= i/10<acc ? QUESTIONS[it.qi].ans : (QUESTIONS[it.qi].ans%4)+1;}}); grade(true); grading=false;}};
              ['anzen','hourei','doboku','kanri','setsubi'].forEach((c,i)=>run(c,[.8,.6,.9,.7,.5][i])); document.getElementById('grading').classList.remove('on'); go('record');}}""")
            await pg.wait_for_timeout(500)
            await (await pg.query_selector('#readyCard')).screenshot(path=SP+f'rz_{theme}.png')
            print(theme, errs); await pg.close()
        await b.close()
asyncio.run(main())
