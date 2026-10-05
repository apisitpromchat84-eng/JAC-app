import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        pg=await b.new_page(); await pg.route('https://**', lambda r: r.abort())
        await pg.goto('file:///home/claude/build/index.html'); await pg.wait_for_timeout(800)
        qs=await pg.evaluate("""()=>{const pl=h=>h.replace(/<ruby>(.*?)<rt>(.*?)<\\/rt><\\/ruby>/g,'$1($2)').replace(/<[^>]+>/g,'');
          return QUESTIONS.map(q=>({id:q.id,cat:q.cat,src:q.src,stem:pl(q.stem),opts:q.opts.map(pl),ans:q.ans,old_tip:q.th,img:q.img||null,done:!!q.sth}))}""")
        await b.close()
    todo=[q for q in qs if not q['done']]
    for q in todo: del q['done']
    print(len(qs),len(todo))
    json.dump(todo,open('/home/claude/xl/all.json','w'),ensure_ascii=False,indent=1)
    N=12; size=-(-len(todo)//N)
    for i in range(N):
        part=todo[i*size:(i+1)*size]
        json.dump(part,open(f'/home/claude/xl/in_{i+1:02d}.json','w'),ensure_ascii=False,indent=1)
        print(i+1,len(part),part[0]['id'],part[-1]['id'])
asyncio.run(main())
