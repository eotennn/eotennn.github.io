(()=>{'use strict';const list=document.getElementById('library-list'),panel=document.getElementById('spotlight-content');function node(tag,text){const e=document.createElement(tag);if(text)e.textContent=text;return e}function valid(r){try{const u=new URL(r.url);return u.protocol==='https:'&&['open.spotify.com','music.youtube.com','www.youtube.com','youtube.com','youtu.be','www.tiktok.com','www.instagram.com'].includes(u.hostname)}catch{return false}}function picture(r){const s=String(r.image||'');return /^assets\/(instagram|tiktok)\/[a-z0-9-]+\.(jpg|png|webp)$/.test(s)||/^https:\/\/(i.scdn.co|i.ytimg.com)\//.test(s)?s:''}

let spotifyAPI,apiPromise,controller,generation=0,cleanup=()=>{},ytPromise;
function getAPI(){if(spotifyAPI)return Promise.resolve(spotifyAPI);if(apiPromise)return apiPromise;apiPromise=new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error()),15000);window.onSpotifyIframeApiReady=api=>{clearTimeout(timer);spotifyAPI=api;resolve(api)};const s=node('script');s.src='https://open.spotify.com/embed/iframe-api/v1';s.onerror=()=>{clearTimeout(timer);reject(Error())};document.body.append(s)});return apiPromise}
function getYT(){if(window.YT?.Player)return Promise.resolve(window.YT);if(ytPromise)return ytPromise;ytPromise=new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(Error()),15000);window.onYouTubeIframeAPIReady=()=>{clearTimeout(t);resolve(window.YT)};const s=node('script');s.src='https://www.youtube.com/iframe_api';s.onerror=()=>{clearTimeout(t);reject(Error())};document.body.append(s)});return ytPromise}
const dialog=node('dialog');dialog.setAttribute('aria-label','Müzik ve video tanıtımı');dialog.style.cssText='background:#181818;color:white;border:1px solid #555;border-radius:16px;width:min(94vw,650px);max-height:92vh;overflow:auto;padding:24px;box-shadow:0 20px 80px #000b';document.body.append(dialog);
function stopPreview(){generation++;cleanup();cleanup=()=>{};if(controller){controller.destroy();controller=null}dialog.replaceChildren();if(dialog.open)dialog.close()}
dialog.addEventListener('cancel',e=>{e.preventDefault();stopPreview()});
async function preview(r){
 stopPreview();const version=generation;
 const close=node('button','Kapat ×');close.className='btn secondary';close.style.float='right';close.onclick=stopPreview;
 const title=node('h2',r.title);title.style.cssText='font-size:22px;padding-top:52px';
 const note=node('p',r.platform==='Instagram'?'Instagram önizlemesi · Bu oynatıcıda otomatik 60 saniye sınırı uygulanamaz.':'60 saniyelik tanıtım başlatılıyor. Otomatik başlamazsa oynatıcıdaki ▶ düğmesine basın.');note.setAttribute('role','status');
 const host=node('div');
 const full=node('a','Tamamını '+r.platform+' üzerinde '+(['Spotify','YouTube Music'].includes(r.platform)?'dinle':'izle')+' ↗');full.className='btn';full.href=r.url;full.target='_blank';full.rel='noopener noreferrer';full.style.marginTop='16px';
 dialog.append(close,title,note,host,full);dialog.showModal();
 let finished=false;

 const finish=(message)=>{if(version!==generation||finished)return;finished=true;note.textContent=message||'60 saniyelik tanıtım bitti. Tamamı için aşağıdaki platform bağlantısını kullanın.';full.focus()};
 function frame(src,height){const f=node('iframe');f.src=src;f.title=r.platform+' — '+r.title;f.width='100%';f.height=String(height);f.style.cssText='border:0;border-radius:10px';f.allow='autoplay; encrypted-media; fullscreen; picture-in-picture';f.allowFullscreen=true;host.append(f);return f}
 try{
 const u=new URL(r.url);
 if(r.platform==='Spotify'){
  const api=await getAPI();if(version!==generation)return;
  api.createController(host,{url:r.url,width:'100%',height:152},p=>{if(version!==generation){p.destroy();return}controller=p;p.addListener('ready',()=>{if(version===generation&&!finished)p.play()});p.addListener('playback_update',e=>{if(version!==generation)return;if(finished){if(!e.data.isPaused)p.pause();return}if(e.data.position>=60000){p.pause();finish()}})});
 }else if(['YouTube','YouTube Music'].includes(r.platform)){
  const id=u.hostname==='youtu.be'?u.pathname.slice(1).split('/')[0]:u.searchParams.get('v')||u.pathname.split('/').filter(Boolean)[1];
  if(!/^[\w-]{11}$/.test(id||''))throw Error();
  const api=await getYT();if(version!==generation)return;
  const mount=node('div');host.append(mount);
  const p=new api.Player(mount,{width:'100%',height:320,videoId:id,playerVars:{playsinline:1,autoplay:1,origin:location.origin},events:{onReady:e=>{if(version===generation&&!finished){e.target.unMute();e.target.setVolume(80);e.target.playVideo()}},onAutoplayBlocked:()=>{if(version===generation){note.textContent='Başlatmak için oynatıcının ▶ düğmesini kullanın.'}},onStateChange:e=>{if(version!==generation)return;if(!finished&&e.data===1){if(p.isMuted()){note.textContent='Sesi açmak için videodaki hoparlör simgesini kullanın.'}else{note.textContent='60 saniyelik tanıtım oynatılıyor.'}}if(finished&&e.data===1)p.pauseVideo();if(e.data===0)finish('Tanıtım sona erdi. Tamamı için YouTube bağlantısını kullanın.')},onError:()=>{note.textContent='Bu video burada oynatılamıyor. YouTube bağlantısından açabilirsiniz.'}}});
  
  const timer=setInterval(()=>{if(version===generation&&!finished&&p.getCurrentTime&&p.getCurrentTime()>=60){p.pauseVideo();finish()}},200);
  cleanup=()=>{clearInterval(timer);p.destroy()};
 }else if(r.platform==='TikTok'){
  const id=u.pathname.match(/\/video\/(\d+)/)?.[1];if(!id)throw Error();
  const f=frame('https://www.tiktok.com/player/v1/'+id+'?autoplay=1&muted=0&loop=0',480);
  const send=type=>f.contentWindow?.postMessage({'x-tiktok-player':true,type},'https://www.tiktok.com');
  const pause=()=>f.contentWindow?.postMessage({'x-tiktok-player':true,type:'pause'},'https://www.tiktok.com');
  const listener=e=>{if(version!==generation||e.origin!=='https://www.tiktok.com'||e.source!==f.contentWindow||!e.data?.['x-tiktok-player'])return;const m=e.data;if(m.type==='onPlayerReady'&&!finished){send('unMute');send('play');}if(m.type==='onMute'&&!finished){if(m.value===true){note.textContent='Sesi açmak için videodaki hoparlör simgesini kullanın.'}else{}}if(m.type==='onCurrentTime'&&Number(m.value?.currentTime)>=60){pause();finish()}if(m.type==='onStateChange'&&m.value===1&&finished)pause();if(m.type==='onStateChange'&&m.value===0)finish('Tanıtım sona erdi. Tamamı için TikTok bağlantısını kullanın.');if(m.type==='onPlayerError')note.textContent='Video burada oynatılamıyor. TikTok bağlantısından açabilirsiniz.'};
  window.addEventListener('message',listener);cleanup=()=>{window.removeEventListener('message',listener);f.remove()};
 }else if(r.platform==='Instagram'){
  const path=u.pathname.match(/^\/(?:reel|p|tv)\/([A-Za-z0-9_-]+)\/?$/);if(!path)throw Error();
  frame('https://www.instagram.com/p/'+path[1]+'/embed/',520);
 }else throw Error();
 }catch{if(version===generation)note.textContent='Oynatıcı yüklenemedi. Aşağıdaki platform bağlantısından açabilirsiniz.'}
}


function rotateHero(albums){
 const hero=document.querySelector('.showcase-hero');
 if(!hero)return;
 const covers=[...new Set(albums.map(picture).filter(Boolean))];
 if(!covers.length)return;
 let previous='';
 try{previous=localStorage.getItem('eoten-last-hero')||''}catch{}
 let pool=covers.filter(src=>src!==previous);
 if(!pool.length)pool=covers.slice();
 // Randomize once, then try another cover if an image fails to load.
 for(let i=pool.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[pool[i],pool[j]]=[pool[j],pool[i]]}
 const attempt=()=>{
  const src=pool.pop();if(!src)return;
  const image=new Image();
  image.onload=()=>{
   hero.style.backgroundImage='linear-gradient(0deg,#201208 0%,#08080850 80%),linear-gradient(90deg,#000b,#0005),url("'+src+'")';
   try{localStorage.setItem('eoten-last-hero',src)}catch{}
  };
  image.onerror=attempt;
  image.src=src;
 };
 attempt();
}

function latestSong(items){
 const songs=items.filter(r=>['Spotify','YouTube Music'].includes(r.platform));
 const time=value=>{const n=Date.parse(value||'');return Number.isFinite(n)?n:0};
 return (songs.length?songs:items).slice().sort((a,b)=>
  (time(b.addedAt)||time(b.date))-(time(a.addedAt)||time(a.date))||
  time(b.date)-time(a.date)||
  Number(b.platform==='Spotify')-Number(a.platform==='Spotify')||
  String(a.id||'').localeCompare(String(b.id||''))
 )[0];
}
function select(r){panel.replaceChildren();const src=picture(r);if(src){const im=node('img');im.src=src;im.alt=r.title;panel.append(im)}panel.append(node('h3',r.title),node('p','EoTeN AI Music Production · '+r.platform));const a=node('a',r.platform+' üzerinde aç ↗');a.className='btn';a.href=r.url;a.target='_blank';a.rel='noopener noreferrer';panel.append(a);if(['Spotify','YouTube','YouTube Music','TikTok','Instagram'].includes(r.platform)){const play=node('button',r.platform==='Instagram'?'▶ Önizlemeyi aç':'▶ 60 saniye '+(['Spotify','YouTube Music'].includes(r.platform)?'dinle':'izle'));play.className='btn';play.style.marginRight='8px';play.onclick=()=>preview(r);panel.insertBefore(play,a)}}document.querySelectorAll('[data-platform]').forEach(b=>b.addEventListener('click',()=>{const p=document.getElementById('catalog-platform');if(![...p.options].some(o=>o.value===b.dataset.platform))return;p.value=b.dataset.platform;p.dispatchEvent(new Event('change'));document.querySelectorAll('[data-platform]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)))}));fetch('catalog.json',{cache:'no-cache'}).then(r=>r.json()).then(d=>{const items=d.items.filter(valid),albums=items.filter(r=>r.platform==='Spotify');rotateHero(albums);const featured=latestSong(items);if(featured)select(featured);for(const r of albums.slice(0,12)){const b=node('button');b.className='library-item';const src=picture(r);if(src){const i=node('img');i.src=src;i.alt='';i.loading='lazy';b.append(i)}const t=node('span',r.title);t.append(node('small','Albüm / Single · EoTeN'));b.append(t);b.addEventListener('click',()=>{select(r);preview(r)});list.append(b)}const grid=document.getElementById('catalog-grid');grid.addEventListener('click',e=>{const a=e.target.closest('a');if(!a)return;const r=items.find(r=>r.url===a.href);if(r&&['Spotify','YouTube','YouTube Music','TikTok','Instagram'].includes(r.platform)){e.preventDefault();e.stopImmediatePropagation();select(r);preview(r)}},true);grid.addEventListener('click',e=>{const a=e.target.closest('a');if(a){const r=items.find(r=>r.url===a.href);if(r)select(r)}})}).catch(()=>{panel.textContent='Yayın ayrıntıları şu anda yüklenemedi.'})})();