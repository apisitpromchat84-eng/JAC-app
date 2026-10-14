import asyncio
from playwright.async_api import async_playwright
SP='/home/claude/repo/tools/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        pg=await b.new_page(viewport={'width':390,'height':844}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.route('https://**', lambda r: r.abort())
        await pg.goto('file:///home/claude/build/dist/index.html'); await pg.wait_for_timeout(2500)
        # some progress: 2 categories answered, some wrong
        await pg.evaluate("""()=>{const run=(cat,acc)=>{const idx=QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].cat===cat).slice(0,8);
            startQuiz(idx,'t','mini',0); layout.forEach((it,i)=>{picks[i]= i/8<acc ? QUESTIONS[it.qi].ans : (QUESTIONS[it.qi].ans%4)+1; conf[i]= i%3? 'sure':'guess';}); grade(true); grading=false;};
          run('anzen',.5); run('hourei',.9); document.getElementById('grading').classList.remove('on'); go('home');}""")
        await pg.wait_for_timeout(800)
        print('CARD:', (await pg.inner_text('#asstCard'))[:200].replace('\n',' | '))
        await (await pg.query_selector('#asstCard')).screenshot(path=SP+'shots/asst_card.png')
        tests=['ข้อที่ยังไม่เคยทำ 15 ข้อ หมวดความปลอดภัย','ข้อที่เคยผิด','หมวดที่อ่อนที่สุด','ข้อออกสอบจริง','ทบทวน','ข้อที่ไม่มั่นใจ','ทำ 20 นาที','ทำไปเท่าไหร่แล้ว','ข้อที่ยังไม่ทำ ภาคปฏิบัติ 5 ข้อ','กฎหมาย ยังไม่เคยทำ ทั้งหมด','สอบจำลอง','ช่วยอะไรได้บ้าง','กินข้าวยัง']
        await pg.click('#asstFab'); await pg.wait_for_timeout(300)
        for t in tests:
            await pg.evaluate("t=>asstAsk(t)", t)
            r=await pg.evaluate("()=>{const m=asstLog[asstLog.length-1]; const d=document.createElement('div'); d.innerHTML=m.html; return d.innerText.replace(/\\n/g,' / ')+(m.sid?'  [START '+(asstSets[m.sid].mock?'mock '+asstSets[m.sid].n:asstSets[m.sid].idx.length)+' part='+asstSets[m.sid].part+']':'')+(m.next?'  [next: '+m.next+']':'')}")
            print('>',t,'\n   ',r)
        await pg.screenshot(path=SP+'shots/asst_sheet.png')
        # start a set
        sid=await pg.evaluate("()=>{const m=[...asstLog].reverse().find(x=>x.sid&&!asstSets[x.sid].mock); return m.sid}")
        await pg.evaluate(f"asstGo('{sid}')"); await pg.wait_for_timeout(500)
        print('quiz', await pg.evaluate("[current, modeLabel, layout.length, mode, quizPart]"), 'fab visible', await pg.is_visible('#asstFab'))
        print('errs',errs); await b.close()
asyncio.run(main())
