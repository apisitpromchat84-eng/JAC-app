import asyncio, os
from playwright.async_api import async_playwright
SP='/tmp/claude-0/-home-claude/beb59762-83c7-50f5-8de5-af8319c8e710/scratchpad/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx=await b.new_context(viewport={'width':430,'height':900},device_scale_factor=2,accept_downloads=True)
        pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await ctx.route('https://**',lambda r:r.abort())
        await pg.goto('http://localhost:8790/stats'); await pg.wait_for_timeout(800)
        await pg.fill('#key',os.environ['STATS_KEY']); await pg.click('#go'); await pg.wait_for_timeout(1500)
        el=pg.locator('.mhead').first; await el.scroll_into_view_if_needed()
        await pg.screenshot(path=SP+'m_dash.png',full_page=True)
        async with pg.expect_download() as dl: await pg.click('#mDl')
        d=await dl.value; await d.save_as(SP+'m_all.csv'); print('file', d.suggested_filename)
        await pg.click('[data-pk]'); await pg.wait_for_timeout(1200)
        await pg.locator('#pDl').scroll_into_view_if_needed(); await pg.wait_for_timeout(200)
        await pg.screenshot(path=SP+'m_person.png')
        async with pg.expect_download() as dl: await pg.click('#pDl')
        d=await dl.value; await d.save_as(SP+'m_person.csv'); print('file', d.suggested_filename)
        await pg.select_option('#mSel','2026-09'); await pg.wait_for_timeout(800)
        print('sep rows', await pg.locator('#monthly tr.click').count())
        print('errors',errs); await b.close()
asyncio.run(main())
