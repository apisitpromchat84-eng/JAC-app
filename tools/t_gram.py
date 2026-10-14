import asyncio
from playwright.async_api import async_playwright
SP='/home/claude/repo/tools/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        pg=await b.new_page(viewport={'width':390,'height':844}, device_scale_factor=2); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.route('https://**', lambda r: r.abort())
        await pg.goto('file:///home/claude/build/dist/index.html'); await pg.wait_for_timeout(2500)
        # quiz with a negative + normal question
        await pg.evaluate("()=>{const ids=['g092','g031','g024']; const idx=ids.map(id=>QUESTIONS.findIndex(q=>q.id===id)).filter(i=>i>=0); prefs.view='all'; applyPrefs(); startQuiz(idx.length?idx:[0,1,2],'t','mini',0);}")
        await pg.wait_for_timeout(600)
        print('gm marks', await pg.locator('#quizList .gm').count(), 'neg', await pg.locator('#quizList .neg').count())
        el=pg.locator('#quizList .gm').first; await el.click(); await pg.wait_for_timeout(300)
        print('tip:', await pg.inner_text('.gtip'), 'picked?', await pg.evaluate("picks.join(',')"))
        await pg.screenshot(path=SP+'shots/g_quiz.png')
        negel=pg.locator('#quizList .neg').first; await negel.scroll_into_view_if_needed()
        if await negel.count(): await negel.click(); await pg.wait_for_timeout(300); print('neg tip:', await pg.inner_text('.gtip'))
        await pg.screenshot(path=SP+'shots/g_quiz_neg.png')
        # toggle off
        await pg.evaluate("prefs.gram='off'; applyPrefs()"); await pg.wait_for_timeout(200)
        print('nogram class', await pg.evaluate("document.documentElement.classList.contains('nogram')"))
        await pg.evaluate("prefs.gram='on'; applyPrefs()")
        # mock exam: no marks
        await pg.evaluate("startQuiz(pickReal('gakka'),'สอบจำลอง','real',3600)"); await pg.wait_for_timeout(500)
        print('mock gm', await pg.locator('#quizList .gm').count())
        await pg.evaluate("stopClock(); graded=true; go('vocab')"); await pg.wait_for_timeout(300)
        await pg.click('#modeGram'); await pg.wait_for_timeout(400)
        print('gram items', await pg.locator('.gitem').count())
        await pg.screenshot(path=SP+'shots/g_list.png')
        await pg.click('#gramFlash'); await pg.wait_for_timeout(400)
        print('flash front', await pg.inner_text('#flashFront'))
        await pg.screenshot(path=SP+'shots/g_flash.png')
        await pg.evaluate("go('games')"); await pg.wait_for_timeout(300)
        print('best', await pg.inner_text('#best-qtype'))
        await pg.click('[data-game=qtype]'); await pg.wait_for_timeout(400)
        await pg.screenshot(path=SP+'shots/g_game.png')
        for r in range(10):
            k=await pg.evaluate("qt.list[qt.pos].k")
            await pg.click(f'[data-qt="{k if r%3 else "ok" if k!="ok" else "neg"}"]'); await pg.wait_for_timeout(150)
            if r==1: await pg.screenshot(path=SP+'shots/g_game_fb.png')
            await pg.click('#qtNext'); await pg.wait_for_timeout(100)
        print('end', (await pg.inner_text('#qtBody'))[:60].replace('\n',' '))
        print('errs',errs); await b.close()
asyncio.run(main())
