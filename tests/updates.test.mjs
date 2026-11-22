import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parseHTML} from 'linkedom';
const source=readFileSync(new URL('../htdocs/luci-static/resources/view/athena-config.js',import.meta.url),'utf8');
function settings(readonly=false) {
 const {document,window}=parseHTML('<html lang="zh-cn"><body></body></html>');
 const E=(tag,attrs={},children=[])=>{const n=document.createElement(tag);for(const[k,v]of Object.entries(attrs))if(typeof v==='function')n.addEventListener(k,v);else if(v!=null)n.setAttribute(k,String(v));for(const c of [children].flat(Infinity))if(c!=null)n.append(typeof c==='object'?c:String(c));return n;};
 let checks=0,starts=0,result={result:0,current:'2.0.0',available:false,status:'unreleased'};
 const rpc={declare:({method})=>(...args)=>{if(method==='check_update'){checks++;return Promise.resolve(result);}if(method==='start_update'){starts++;return Promise.resolve({result:1,error:'No release'});}return Promise.resolve({result:0,phase:'idle'});}};
 const api=new Function('document','view','form','rpc','uci','ui','widgets','E','_','L',source)(document,{extend:v=>v},{},rpc,{}, {showModal(){},addNotification(){},hideModal(){}},{card:(title,children)=>E('section',{},[title,...children])},E,s=>s,{});
 api.upgradeRoot=E('div');document.body.append(api.upgradeRoot);api.assets={version:'2.0.0'};api.readonly=readonly;api.renderUpgrade();
 return {api,document,window,setResult:v=>result=v,counts:()=>({checks,starts}),flush:()=>new Promise(resolve=>setTimeout(resolve,0))};
}
test('update check shows an unpublished repository without enabling installation',async()=>{
 const c=settings();c.api.upgradeRoot.querySelector('button').dispatchEvent(new c.window.Event('click'));await c.flush();
 assert.match(c.api.upgradeRoot.textContent,/暂无正式发布/);assert.equal(c.api.upgradeRoot.querySelectorAll('button')[1].hasAttribute('disabled'),true);assert.deepEqual(c.counts(),{checks:1,starts:0});
});
test('release controls respect readonly permission and only enable a verified newer release',()=>{
 const c=settings(true);c.api.release={latest:'2.0.1',available:true,status:'available'};c.api.renderUpgrade();
 assert(c.api.upgradeRoot.querySelectorAll('button')[1].hasAttribute('disabled'));
 c.api.readonly=false;c.api.renderUpgrade();assert(!c.api.upgradeRoot.querySelectorAll('button')[1].hasAttribute('disabled'));
 c.api.release={latest:'2.0.1',available:false,status:'missing_asset'};c.api.renderUpgrade();assert(c.api.upgradeRoot.querySelectorAll('button')[1].hasAttribute('disabled'));assert.match(c.api.upgradeRoot.textContent,/可校验/);
});
test('an update-check retry clears a previous network error without replacing assets',async()=>{
 const c=settings(),assets=c.api.assets;c.api.upgradeError='old network error';c.api.renderUpgrade();
 c.api.upgradeRoot.querySelector('button').dispatchEvent(new c.window.Event('click'));await c.flush();
 assert(!c.api.upgradeRoot.textContent.includes('old network error'));assert.equal(c.api.assets,assets);
});
test('a missing release manifest disables a previously available update and explains the error',async()=>{
 const c=settings();c.api.release={latest:'2.0.1',available:true,status:'available'};c.api.renderUpgrade();
 c.setResult({result:1,error:'Release manifest is not published'});c.api.upgradeRoot.querySelector('button').dispatchEvent(new c.window.Event('click'));await c.flush();
 assert(c.api.upgradeRoot.querySelectorAll('button')[1].hasAttribute('disabled'));assert.match(c.api.upgradeRoot.textContent,/尚未提供更新清单/);assert.equal(c.api.assets.version,'2.0.0');
});
