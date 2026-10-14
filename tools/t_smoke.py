# Smoke test: open every tab, sheet and mode in all three parts, with and without progress. Any page error = fail.
import asyncio, sys
from playwright.async_api import async_playwright
SP = '/home/claude/repo/tools/'
SHOT = '--shots' in sys.argv
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        fails = []
        for withData in (False, True):
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
            pg = await ctx.new_page(); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e) + ' | ' + (e.stack or '').split(chr(10))[1:3].__str__()))
            await pg.route('https://**', lambda r: r.abort())
            await pg.goto('file:///home/claude/build/dist/index.html'); await pg.wait_for_timeout(2200)
            step = lambda js: pg.evaluate(js)
            await step("$('wnSheet').hidden || $('wnX').click(); $('nickSheet').classList.remove('on')")
            if withData:
                await step("""()=>{const run=(part,cat,acc)=>{prefs.part=part;applyPrefs();const idx=QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].cat===cat).slice(0,8);
                  startQuiz(idx,'t','mini',0); layout.forEach((it,i)=>{picks[i]= i/8<acc ? QUESTIONS[it.qi].ans : (QUESTIONS[it.qi].ans%4)+1; conf[i]= i%2?'sure':'guess';}); grade(true); grading=false;};
                  run('gakka','anzen',.5); run('jitsugi','j_kikai',.7); run('life','l_denki',.6); document.getElementById('grading').classList.remove('on');
                  seenMine[QUESTIONS[0].id]=['2026-09']; save('jac-seen-v1', seenMine); favs[QUESTIONS[1].id]=1; }""")
            for part in ('gakka', 'jitsugi', 'life'):
                await step(f"prefs.part='{part}'; if('{part}'!=='gakka') prefs.track='{part}'; applyPrefs(); onPartChange()")
                for tab in ('home', 'practice', 'bank', 'vocab', 'record', 'games'):
                    await step(f"go('{tab}')"); await pg.wait_for_timeout(120)
                    if SHOT and withData and part == 'gakka': await pg.screenshot(path=SP + f'review/new_{tab}.png', full_page=True)
                await step("go('vocab'); $('modeGram').click(); $('gramFlash').click(); $('modeList').click(); if ($('vocabMore')) $('vocabMore').click()")
                await step("go('practice'); startQuiz(pickReal(prefs.part),'สอบจำลอง','real',3600)"); await pg.wait_for_timeout(150)
                await step("stopClock(); grade(true); grading=false; document.getElementById('grading').classList.remove('on')"); await pg.wait_for_timeout(150)
                await step("go('home'); openQ(pool()[0]); $('qSheet').classList.remove('on')")
            # sheets and menus
            await step("$('setBtn').click()")
            if SHOT and withData: await pg.screenshot(path=SP + 'review/new_menu.png')
            for k in ('nick', 'data', 'settings'):
                await step(f"openMenu(); document.querySelector('[data-m={k}]').click()"); await pg.wait_for_timeout(150)
                if SHOT and withData: await pg.screenshot(path=SP + f'review/new_m_{k}.png')
                await step("closeSheets()")
            await step("openMenu(); document.querySelector('[data-wn]').click()"); await step("$('wnX').click()")
            await step("$('asstFab').click(); asstAsk('ข้อที่ยังไม่เคยทำ 5 ข้อ'); asstAsk('足場 คืออะไร'); closeSheets()")
            await step("go('games'); openQType(); closeSheets()")
            await step("go('record'); document.querySelectorAll('details.fold').forEach(d=>d.open=true)")
            if SHOT and withData: await pg.screenshot(path=SP + 'review/new_record_open.png', full_page=True)
            await ctx.close()
            print(('with data' if withData else 'fresh install') + ':', 'OK' if not errs else 'ERRORS'); [print('  ', e) for e in errs[:8]]
            fails += errs
        await b.close()
        sys.exit(1 if fails else 0)
asyncio.run(main())
