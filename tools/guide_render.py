# usage: guide_render.py <dir with guide.html> <version id> <name1,name2,...>
import asyncio, sys, io, os
from playwright.async_api import async_playwright
from PIL import Image
D, ver, names = sys.argv[1].rstrip('/') + '/', sys.argv[2], sys.argv[3].split(',')
app = f'/home/claude/build/img/whatsnew/{ver}/'; os.makedirs(app, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        pg = await b.new_page(viewport={'width': 1100, 'height': 1400}); await pg.goto('file://' + D + 'guide.html'); await pg.wait_for_timeout(800)
        for i, n in enumerate(names):
            png = await pg.locator(f'#c{i}').screenshot()
            open(D + f'jac_update_{ver}_{i}_{n}.png', 'wb').write(png)
            Image.open(io.BytesIO(png)).convert('RGB').resize((720, 900), Image.LANCZOS).save(app + f'{i}.webp', 'WEBP', quality=82, method=6)
        await b.close()
asyncio.run(main())
print('ok', len(names))
