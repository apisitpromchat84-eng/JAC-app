# Two devices against the local mock server (tools/mockserver/server2.mjs on :8790 with a fresh database):
# A turns sync on → B (fresh) sets the same nickname, is offered the pull, pulls → B studies → A is told B is newer and pulls
import asyncio
from playwright.async_api import async_playwright
U = 'http://localhost:8790/'
async def dev(b):
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}); pg = await ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); await ctx.route('https://**', lambda r: r.abort())
    await pg.goto(U); await pg.wait_for_timeout(1500)
    await pg.evaluate("$('wnSheet').hidden || $('wnX').click(); $('nickSheet').classList.remove('on')")
    return pg, errs
async def quiz(pg, n):
    await pg.evaluate(f"""()=>{{go('practice'); startQuiz(pool().slice(0,{n}),'t','mini',0); layout.forEach((it,i)=>{{picks[i]=QUESTIONS[it.qi].ans;}}); grade(true); grading=false; document.getElementById('grading').classList.remove('on'); go('home');}}""")
async def yes(pg, ms=6000):
    await pg.wait_for_selector('#askSheet.on', timeout=ms); msg = await pg.inner_text('#askMsg'); await pg.click('#askYes'); return msg.split(chr(10))[0]
hist = lambda pg: pg.evaluate("load(K.hist,[]).length")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        A, ea = await dev(b)
        await A.evaluate("save(NICK_KEY,'ทดสอบซิงก์'); showNick()"); await quiz(A, 5); await quiz(A, 3)
        await A.evaluate("openData(); $('syncPin').value='4826'; $('syncOn').click()"); await A.wait_for_timeout(1500)
        print('A sync on:', await A.inner_text('#syncStat'), '| A history', await hist(A))
        B, eb = await dev(b)
        await B.evaluate("openNick(); $('nickBox').value='ทดสอบซิงก์'; $('nickSave').click()")
        print('B offered:', await yes(B))
        await B.wait_for_timeout(400); await B.evaluate("$('syncPin').value='4826'; $('syncPull').click()")
        print('B import:', await yes(B)); await B.wait_for_load_state(); await B.wait_for_timeout(2500)
        await B.evaluate("$('wnSheet').hidden || $('wnX').click(); $('nickSheet').classList.remove('on')")
        print('B history after pull', await hist(B), '| B sync', await B.evaluate("JSON.stringify(load('jac-sync',{}).name)"))
        await quiz(B, 4); await B.wait_for_timeout(2500)
        await A.reload(); await A.wait_for_timeout(1500); await A.evaluate("$('wnSheet').hidden || $('wnX').click(); $('nickSheet').classList.remove('on')")
        print('A told:', await yes(A, 8000)); print('A import:', await yes(A)); await A.wait_for_load_state(); await A.wait_for_timeout(2000)
        print('A history now', await hist(A))
        # wrong PIN on a third device
        C, ec = await dev(b)
        await C.evaluate("openData(); $('syncName').value='ทดสอบซิงก์'; $('syncPin').value='1111'; $('syncPull').click()"); await C.wait_for_timeout(800)
        print('C wrong PIN toast:', (await C.evaluate("(document.querySelector('.toast')||{}).textContent||''")).replace(chr(10),' ')[:60])
        print('errors', ea, eb, ec); await b.close()
asyncio.run(main())
