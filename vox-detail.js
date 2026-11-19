(()=>{'use strict';
const code=(document.body.dataset.vox||'').toUpperCase();
const allowed=new Set(['M1','M2','F1','F2','F5','F6','F7']);
if(!allowed.has(code))return;
let activeController=null,activeHost=null,activeStatus=null,playVersion=0,apiPromise=null,apiObject=null;
const $=id=>document.getElementById(id);
function node(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=String(txt);return e}
function safeSpotify(url){try{const u=new URL(url);const m=u.pathname.match(/^\/(album|track)\/([A-Za-z0-9]+)\/?$/);return u.protocol==='https:'&&u.hostname==='open.spotify.com'&&m&&!u.port&&!u.username&&!u.password?{url:'https://open.spotify.com/'+m[1]+'/'+m[2],id:m[2],kind:m[1]}:null}catch{return null}}
function safeImage(src){try{const u=new URL(src,location.href);if(u.origin===location.origin && /^assets\/vox\/(?:m1|m2|f1|f2|f5|f6|f7)\/[a-z0-9-]+\.webp$/i.test(u.pathname.replace(/^\//,'')))return u.href;if(u.origin===location.origin && /^\/?(?:[^/]+\/)?assets\/tiktok\/tiktok-[0-9a-f]{15,64}\.jpg$/i.test(u.pathname.replace(/^\//,'')))return u.href;if(u.protocol==='https:'&&(u.hostname==='i.ytimg.com'||u.hostname==='i.scdn.co')&&/^(\/vi\/[\w-]{11}\/[\w.-]+\.jpg|\/image\/[a-z0-9]+)$/i.test(u.pathname))return u.href;return ''}catch{return ''}}
function stop(){playVersion++;if(activeController){try{activeController.destroy()}catch{}activeController=null}if(activeHost)activeHost.replaceChildren();if(activeStatus)activeStatus.textContent='Dinleme durduruldu.';activeHost=null;activeStatus=null}
function spotifyApi(){if(apiObject)return Promise.resolve(apiObject);if(apiPromise)return apiPromise;apiPromise=new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(Error('Spotify API zaman aşımı')),14000);window.onSpotifyIframeApiReady=api=>{clearTimeout(t);apiObject=api;resolve(api)};const s=node('script');s.src='https://open.spotify.com/embed/iframe-api/v1';s.onerror=()=>{clearTimeout(t);reject(Error('Spotify yüklenemedi'))};document.body.append(s)});return apiPromise}
async function play(rec,host,status){stop();activeHost=host;activeStatus=status;const v=playVersion;status.textContent='Spotify oynatıcısı yükleniyor…';try{const api=await spotifyApi();if(v!==playVersion)return;api.createController(host,{url:rec.spotify.url,width:'100%',height:152},p=>{if(v!==playVersion){p.destroy();return}activeController=p;p.addListener('ready',()=>{if(v!==playVersion)return;status.textContent='Oynatıcı hazır. Otomatik başlamazsa ▶ düğmesine dokunun.';try{p.play()}catch{}});p.addListener('playback_update',e=>{if(v!==playVersion)return;const position=Number(e?.data?.position||0);if(position>=60000){try{p.pause()}catch{}status.textContent='60 saniyelik dinleme sınırına ulaşıldı. Tamamı için Spotify bağlantısını kullanın.'}})})}catch{if(v!==playVersion)return;status.textContent='Gelişmiş oynatıcı açılamadı. Spotify yerleşik oynatıcısı açıldı; önizleme süresini Spotify belirler.';const iframe=node('iframe');iframe.title=rec.title+' Spotify önizlemesi';iframe.src='https://open.spotify.com/embed/'+rec.spotify.kind+'/'+rec.spotify.id;iframe.height='152';iframe.loading='lazy';iframe.allow='autoplay; encrypted-media; fullscreen; picture-in-picture';host.append(iframe)}}
function renderIdentity(p){
document.title=p.name+' | EoTeN VØX Sanatçısı';
$('title').textContent=p.name;$('role').textContent=p.role;$('style').textContent=p.style;
$('intro').textContent=p.summary;$('sound').textContent=p.vocal;$('look').textContent=p.appearance;$('age').textContent=p.age;
document.documentElement.style.setProperty('--artist-color',p.palette);
const hero=$('portrait');hero.replaceChildren();
const assets=(p.images||[]).map(i=>({...i,url:safeImage(i.src)})).filter(i=>i.url);
const preferred=safeImage(p.heroImage||'');
const fallback=assets.find(i=>i.type==='Karakter fotoğrafı'||i.type==='Yakın portre');
if(preferred||fallback){
 const img=node('img');img.src=preferred||fallback.url;img.alt=p.name+' · yakın plan resmî karakter portresi';
 img.loading='eager';img.decoding='async';
 img.onerror=()=>{hero.replaceChildren(node('div','fallback',p.name),node('span','sub','Portre bekleniyor'))};
 hero.append(img,node('div','picture-note',p.name+' · Yakın plan sanatçı portresi'));
}else{hero.append(node('div','fallback',p.name),node('span','sub','Yakın plan portre bekleniyor'))}
const gallery=$('gallery');gallery.replaceChildren();
const order=[['front','Ön'],['back','Arka'],['right','Sağ'],['left','Sol']];
const views=p.views||{};
const section=node('section','views-section');const heading=node('h3','views-title','Dört Ana Görünüm');
const hint=node('p','views-note','Aynı karakterin tam boy görünüm sırası: Ön · Arka · Sağ · Sol');
const row=node('div','view-grid');
order.forEach(([key,label])=>{
 const card=node('figure','frame view-frame');
 const src=safeImage(views[key]||'');
 if(src){
  const link=node('a','gallery-link');link.href=src;link.target='_blank';link.rel='noopener noreferrer';link.title=label+' görünümü büyüt';
  const img=node('img');img.src=src;img.alt=p.name+' · tam boy '+label.toLocaleLowerCase('tr-TR')+' görünüm';img.loading='lazy';
  img.onerror=()=>{card.replaceChildren(node('div','view-missing',label+' görünüm yüklenemedi'),node('figcaption','',label+' · Görsel yüklenemedi'))};
  link.append(img);card.append(link);
 }else{card.append(node('div','view-missing',label+' görünümün resmî fotoğrafı bekleniyor'))}
 card.append(node('figcaption','view-caption',label));
 row.append(card);
});
section.append(heading,hint,row);gallery.append(section);
const extras=(p.gallery||p.images||[]).map(i=>({...i,url:safeImage(i.src)})).filter(i=>i.url&&!Object.values(views).includes(i.src));
const seen=new Set();const distinct=extras.filter(i=>{if(seen.has(i.url))return false;seen.add(i.url);return true});
if(distinct.length){
 const more=node('section','extras-section');more.append(node('h3','views-title','Portreler, Tanıtım Kartları ve Diğer Görseller'));
 const grid=node('div','extra-grid');
 distinct.forEach(i=>{
  const fig=node('figure','frame');if(i.type==='Karakter kartı')fig.classList.add('wide');
  const link=node('a','gallery-link');link.href=i.url;link.target='_blank';link.rel='noopener noreferrer';
  link.title=i.title+' · büyüt';const img=node('img');img.src=i.url;img.loading='lazy';img.alt=i.title;
  img.onerror=()=>{fig.replaceChildren(node('figcaption','',i.title+' görseli yüklenemedi.'))};
  link.append(img);const cap=node('figcaption');cap.append(node('strong','',i.title),node('br'),node('small','',i.type+' · Büyütmek için dokunun'));
  fig.append(link,cap);grid.append(fig);
 });
 more.append(grid);gallery.append(more);
}
const roster=$('other-artists');roster.replaceChildren();
['M1','M2','F1','F2','F5','F6','F7'].filter(id=>id!==code).forEach(id=>{
 const a=node('a','','VØX-'+id);a.href='vox-'+id.toLowerCase()+'.html';roster.append(a)
});
}
function oneRelease(rec){const box=node('article','release');const head=node('div','release-head');const img=node('img');img.alt='';img.loading='lazy';img.src=/^https:\/\/i\.scdn\.co\/image\/[a-z0-9]+$/i.test(rec.image||'')?rec.image:'assets/eoten-brand-logo.svg';const titles=node('div');titles.append(node('div','release-title',rec.title),node('div','release-date',rec.date||'Spotify yayını'));head.append(img,titles);const actions=node('div','release-actions');const btn=node('button','play','▶ Kısa dinle');btn.type='button';const link=node('a','open','Spotify’da tamamını aç ↗');link.href=rec.spotify.url;link.target='_blank';link.rel='noopener noreferrer';const host=node('div','player');const status=node('p','status');status.setAttribute('role','status');btn.addEventListener('click',()=>play(rec,host,status));actions.append(btn,link);box.append(head,actions,host,status);return box}
async function loadMusic(){const out=$('song-grid');try{const [cr,mr]=await Promise.all([fetch('catalog.json',{cache:'no-store'}),fetch('vox-mapping.json',{cache:'no-store'})]);if(!cr.ok||!mr.ok)throw Error('İndirme hatası');const catalog=await cr.json(),mapping=await mr.json();const all=(catalog.items||[]).filter(r=>r.platform==='Spotify').map(r=>({...r,spotify:safeSpotify(r.url)})).filter(r=>r.spotify);const keys=new Set((mapping.assignments||[]).filter(m=>m.artist===code).map(m=>m.spotifyType+':'+m.spotifyId));const matched=all.filter(r=>keys.has(r.spotify.kind+':'+r.spotify.id)).sort((a,b)=>Date.parse(b.addedAt||b.date||'')-Date.parse(a.addedAt||a.date||''));out.replaceChildren();$('track-status').textContent=matched.length?matched.length+' eşleştirilmiş Spotify yayını · Resmî oynatıcı':"Henüz doğrulanmış Spotify–VØX şarkı eşleşmesi bulunmuyor.";if(matched.length){matched.forEach(x=>out.append(oneRelease(x)))}else{out.append(node('div','empty','Bu sanatçıya henüz doğrulanmamış şarkıları bağlamıyoruz. Spotify’da yayımlanan diğer EoTeN eserleri için genel müzik kataloğunu ziyaret edin.'))}}catch(e){$('track-status').textContent='Spotify kayıtları şu anda yüklenemedi.';out.replaceChildren(node('div','empty','Spotify verileri yüklenemedi. Biraz sonra tekrar deneyebilirsiniz.'))}}
async function init(){try{const r=await fetch('vox-artists.json',{cache:'no-store'});if(!r.ok)throw Error('Karakter kimlikleri yüklenemedi');const x=await r.json();const p=(x.profiles||[]).find(a=>a.id===code);if(!p)throw Error('Karakter bulunamadı');renderIdentity(p)}catch{$('title').textContent='VØX-'+code;$('intro').textContent='Karakter bilgileri şu anda yüklenemiyor.'}await loadMusic()}
window.addEventListener('pagehide',stop);init();
})();