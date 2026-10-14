# Weak-signal test: after the first visit, the server answers the page after 10 s; the app must still open within ~3 s
import asyncio, threading, time, http.server, functools, socketserver
from playwright.async_api import async_playwright
SLOW = {'on': False}
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if SLOW['on'] and self.path in ('/', '/index.html'): time.sleep(10)
        super().do_GET()
srv = socketserver.ThreadingTCPServer(('127.0.0.1', 8811), functools.partial(H, directory='/home/claude/build/dist'))
srv.daemon_threads = True
threading.Thread(target=srv.serve_forever, daemon=True).start()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = await b.new_context(); pg = await ctx.new_page()
        await ctx.route('https://**', lambda r: r.abort())
        await pg.goto('http://127.0.0.1:8811/'); await pg.wait_for_timeout(2500)
        await pg.reload(); await pg.wait_for_timeout(1500)        # SW now controls the page and has the copy
        SLOW['on'] = True
        t = time.time(); await pg.goto('http://127.0.0.1:8811/', wait_until='domcontentloaded'); dt = time.time() - t
        ok = await pg.evaluate("typeof QUESTIONS !== 'undefined' && QUESTIONS.length")
        print(f'slow network: opened in {dt:.1f}s, questions {ok}')
        SLOW['on'] = False
        t = time.time(); await pg.goto('http://127.0.0.1:8811/', wait_until='domcontentloaded'); print(f'normal: {time.time()-t:.1f}s')
        await b.close()
asyncio.run(main()); srv.shutdown()
