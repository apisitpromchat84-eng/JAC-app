import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
import { DatabaseSync } from 'node:sqlite'; import worker from './worker.js';
const ROOT='/home/claude/build/dist'; const sq=new DatabaseSync(':memory:');
const stmt=(sql)=>{let a=[];const o={bind:(...x)=>{a=x;return o;},first:async()=>sq.prepare(sql).get(...a)??null,all:async()=>({results:sq.prepare(sql).all(...a)}),run:async()=>{sq.prepare(sql).run(...a);return{};}};return o;};
const DB={prepare:stmt,batch:async l=>{for(const s of l) await s.run();}};
const T={'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.webmanifest':'application/manifest+json','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp'};
const ASSETS={fetch:async r=>{let p=decodeURIComponent(new URL(r.url).pathname);if(p.endsWith('/'))p+='index.html';const f=path.join(ROOT,p);if(!fs.existsSync(f))return new Response('nf',{status:404});return new Response(fs.readFileSync(f),{headers:{'content-type':T[path.extname(f)]||'application/octet-stream'}});}};
http.createServer(async(req,res)=>{const body=['GET','HEAD'].includes(req.method)?undefined:await new Promise(r=>{const c=[];req.on('data',d=>c.push(d));req.on('end',()=>r(Buffer.concat(c)));});
 const r=await worker.fetch(new Request('http://localhost:8790'+req.url,{method:req.method,headers:req.headers,body}),{DB,ASSETS});const h={};r.headers.forEach((v,k)=>h[k]=v);res.writeHead(r.status,h);res.end(Buffer.from(await r.arrayBuffer()));}).listen(8790,()=>console.log('up'));
