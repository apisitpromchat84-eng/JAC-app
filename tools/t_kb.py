import asyncio, json
from playwright.async_api import async_playwright
SP='/home/claude/repo/tools/'
TESTS=['玉掛け คืออะไร','足場 แปลว่าอะไร','นั่งร้าน ภาษาญี่ปุ่นว่าอะไร','รถแบคโฮภาษาญี่ปุ่นเรียกว่าอะไร','ข้อ ท-012','ป-5','施工 อ่านว่าอะไร','型枠 คืออะไร',
 'ความสูงกี่เมตรต้องใช้เข็มขัดนิรภัย','KY活動 คืออะไร','職長 คืออะไร','ทำไมต้องมีการประชุมเช้า','ห้องน้ำอยู่ไหน','5S คืออะไร','ヘルメット','เหล็กเสริม ภาษาญี่ปุ่น',
 'ข้อที่ยังไม่เคยทำ 10 ข้อ','ข้อที่เคยผิดมีกี่ข้อ','ทำไปเท่าไหร่แล้ว','ความปลอดภัย','กินข้าวยัง','ฮีทสโตรก ป้องกันยังไง','บดอัดดิน ใช้เครื่องอะไร','ท่อ PE ต่อยังไง']
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        pg=await b.new_page(viewport={'width':390,'height':844}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.route('https://**', lambda r: r.abort())
        await pg.goto('file:///home/claude/build/dist/index.html'); await pg.wait_for_timeout(2500)
        await pg.click('#asstFab'); await pg.wait_for_timeout(300)
        for t in TESTS:
            await pg.evaluate("t=>asstAsk(t)", t)
            r=await pg.evaluate("()=>{const m=asstLog[asstLog.length-1]; const d=document.createElement('div'); d.innerHTML=m.html.replace(/<rt>.*?<\\/rt>/g,''); d.querySelectorAll('.say,.aschip').forEach(x=>x.remove()); return d.innerText.replace(/\\s+/g,' ').slice(0,330)+(m.sid?' [START '+(asstSets[m.sid].idx?asstSets[m.sid].idx.length:'mock')+']':'')}")
            print('>',t,'\n   ',r)
        await pg.evaluate("asstAsk('玉掛け คืออะไร')"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=SP+'shots/asst_kb.png')
        print('errs',errs); await b.close()
asyncio.run(main())
