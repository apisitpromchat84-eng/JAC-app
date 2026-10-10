# Builds the deploy folder dist/: question/vocab data is watermarked and scrambled so it is not readable in the page source
import re, base64, os, shutil
SIG = 'JAC26'
# invisible watermark: U+2060 start, bits as U+200B (0) / U+200C (1), U+2060 end
WM = '⁠' + ''.join('‌' if b == '1' else '​' for ch in SIG for b in format(ord(ch), '08b')) + '⁠'

s = open('index.html', encoding='utf-8').read()
a = s.index('const CHART = `')
b = s.index('].concat(JV, LV);\n', a) + len('].concat(JV, LV);\n')
data = s[a:b]
# watermark every Thai explanation / meaning (JS literal th:'…' and JSON "th": "…")
# the mark goes at the END of each text so short labels and searches are unaffected
data, n1 = re.subn(r"(\bth:\s*'(?:[^'\\\n]|\\.)*)'", lambda m: m.group(1) + WM + "'", data)
data, n2 = re.subn(r'("th":\s*"(?:[^"\\\n]|\\.)*)"', lambda m: m.group(1) + WM + '"', data)
# full translations (sth / ath, and th written with double quotes)
data, n3 = re.subn(r'(\b(?:th|sth|ath):\s*"(?:[^"\\\n]|\\.)*)"', lambda m: m.group(1) + WM + '"', data)
data, n4 = re.subn(r'("(?:sth|ath)":\s*"(?:[^"\\\n]|\\.)*)"', lambda m: m.group(1) + WM + '"', data)
raw = data.encode('utf-8')
KEY = [0x4A, 0x61, 0x43, 0x9E, 0x21, 0x7D, 0xB3, 0x55, 0x0F, 0xC8, 0x3A, 0x92, 0x66]
enc = bytes(c ^ KEY[i % len(KEY)] ^ ((i * 7) & 255) for i, c in enumerate(raw))
b64 = base64.b64encode(enc).decode()
loader = ("const { CHART, JQ, JV, QUESTIONS, VOCAB } = (() => {\n"
          f"  const P = '{b64}';\n"
          f"  const k = {KEY}, b = atob(P), u = new Uint8Array(b.length);\n"
          "  for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i) ^ k[i % k.length] ^ ((i * 7) & 255);\n"
          "  return new Function('R', new TextDecoder().decode(u) + '\\nreturn { CHART, JQ, JV, QUESTIONS, VOCAB };')(R);\n"
          "})();\n")
out = s[:a] + loader + s[b:]
assert 'QUESTIONS = [' not in out and 'const VOCAB = [' not in out
if os.path.exists('dist'): shutil.rmtree('dist')
os.makedirs('dist')
open('dist/index.html', 'w', encoding='utf-8').write(out)
for f in ['sw.js', 'manifest.webmanifest', 'netlify.toml', '_headers', 'robots.txt', 'privacy.html', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png', 'apple-touch-icon.png']:
    shutil.copy(f, 'dist/' + f)
shutil.copytree('img', 'dist/img')
print('watermarked', n1 + n2 + n3 + n4, 'entries; data', len(raw) // 1024, 'KB -> scrambled', len(b64) // 1024, 'KB')
