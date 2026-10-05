# Builds the single-file preview (all images inlined once as WebP) from index.html
import re,base64,io,json
from PIL import Image
s=open('dist/index.html' if __import__('os').path.exists('dist/index.html') else 'index.html',encoding='utf-8').read()
data={}
src_all=s+open('index.html',encoding='utf-8').read()   # image refs also live inside the scrambled data
for f in sorted(set(re.findall(r'img/[\w-]+\.jpg',src_all))):
    if f.startswith('img/score_'): continue
    im=Image.open(f).convert('RGB'); b=io.BytesIO(); im.save(b,'WEBP',quality=74,method=6)
    data[f]='data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode()
for m in re.findall(r"'((?:score|jig)_[\w]+)'",src_all):
    data[f'img/{m}.webp']='data:image/webp;base64,'+base64.b64encode(open(f'img/{m}.webp','rb').read()).decode()
art=s
for line in ['<link rel="manifest" href="manifest.webmanifest">\n','<link rel="icon" href="icon-192.png">\n','<link rel="apple-touch-icon" href="apple-touch-icon.png">\n']:
    assert line in art, line; art=art.replace(line,'')
i=art.index("if ('serviceWorker' in navigator) {"); j=art.index("\n}\n",i)+3; art=art[:i]+art[j:]
art=art.replace('<script>\nconst R =','<script>window.IMGDATA='+json.dumps(data)+';</script>\n<script>\nconst R =',1)
open('/mnt/user-data/outputs/jac-app-3d.html','w',encoding='utf-8').write(art)
print('images',len(data),'size',len(art)//1024,'KB')
