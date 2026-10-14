const B='http://localhost:8790';
const ua='Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1';
const ping=(dev,ip,scr,name,ev,summary)=>fetch(B+'/api/ping',{method:'POST',headers:{'content-type':'application/json','user-agent':ua,'cf-connecting-ip':ip},body:JSON.stringify({dev,name,part:'jitsugi',events:ev||[],scr,summary})});
const cat=(id,th,part,total,tried,done,c,t,wrong=0)=>({id,th,part,total,tried,done,c,t,wrong});
const summ={exam:'2026-11-08',lset:'all',parts:{gakka:{n:40,pass:75,min:60},jitsugi:{n:25,pass:75,min:40}},cats:[
 cat('anzen','ความปลอดภัย','gakka',20,18,15,30,40,2),cat('hourei','กฎหมาย/ประกัน','gakka',17,12,9,14,22,3),cat('doboku','งานโยธา/โครงสร้าง','gakka',32,20,18,25,30),cat('setsubi','งานระบบ','gakka',15,4,3,3,5),cat('kanri','บริหาร/หัวหน้างาน','gakka',30,25,20,28,40,2),cat('manner','มารยาท/การสื่อสาร','gakka',3,3,3,3,3),cat('gyokai','อุตสาหกรรม/แรงงาน','gakka',6,0,0,0,0),
 cat('j_kikai','เครื่องจักรก่อสร้าง','jitsugi',13,13,12,20,24,1),cat('j_dougu','เครื่องมือ/ชิ้นส่วน','jitsugi',25,25,25,42,44),cat('j_kaiyo','งานโยธาทางทะเล','jitsugi',10,10,10,15,17),cat('j_tekkin','เหล็กเสริม/คอนกรีต','jitsugi',20,20,19,30,35,1),cat('j_dobo','งานดิน/ฐานราก/วางท่อ','jitsugi',13,13,12,20,23),cat('j_anzen','ความปลอดภัย','jitsugi',22,22,21,35,40),cat('j_kanri','บริหารงานก่อสร้าง','jitsugi',10,10,10,13,13)]};
const now=Date.now(); const ev=(r,part,mode,n,s,ago)=>({rid:r,ts:now-ago,part,mode,n,s});
await ping('aaaa000001','1.1.1.1','393x852@3','ชายอาม',[ev('1','jitsugi','real',25,23,3600e3),ev('2','jitsugi','real',25,22,86400e3),ev('3','gakka','mini',10,7,7200e3),ev('4','jitsugi','mini',10,9,600e3)],summ);
await ping('bbbb000001','2.2.2.2','430x932@3','นิว',[ev('5','gakka','mini',10,6,1800e3)]);
await ping('cccc000001','3.3.3.3','393x852@3','',[ev('6','gakka','mini',10,4,5000e3)]);
for (let i=0;i<5;i++) await ping('dddd00000'+i,'4.4.4.'+i,'375x812@3','');
console.log('seeded');
