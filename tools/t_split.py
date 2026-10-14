import asyncio
from playwright.async_api import async_playwright
async def run(b, touch):
    ctx = await b.new_context(has_touch=touch, is_mobile=touch); pg = await ctx.new_page()
    await pg.route('https://**', lambda r: r.abort())
    await pg.goto('file:///home/claude/build/dist/index.html'); await pg.wait_for_timeout(1500)
    tp = await pg.evaluate("navigator.maxTouchPoints")
    await pg.evaluate("window.dispatchEvent(new Event('blur'))")
    blur = await pg.evaluate("document.documentElement.classList.contains('shield')")
    await pg.evaluate("window.dispatchEvent(new Event('focus')); window.dispatchEvent(new Event('pagehide'))")
    hide = await pg.evaluate("document.documentElement.classList.contains('shield')")
    print(('iPad/phone' if touch else 'computer'), 'touchPoints', tp, '| covered on blur:', blur, '| covered on leaving app:', hide)
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        await run(b, True); await run(b, False); await b.close()
asyncio.run(main())
