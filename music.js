(() => {
  'use strict';
  const area = document.getElementById('catalog-grid');
  const status = document.getElementById('catalog-status');
  const refresh = document.getElementById('refresh-note');
  const total = document.getElementById('total-count');
  const search = document.getElementById('catalog-search');
  const platform = document.getElementById('catalog-platform');
  const kind = document.getElementById('catalog-kind');
  const more = document.getElementById('catalog-more');
  const pageSize = 24;
  let records = [], count = pageSize;
  const allowedHosts = {
    Spotify: ['open.spotify.com'], YouTube: ['youtube.com','www.youtube.com','youtu.be'],
    TikTok: ['tiktok.com','www.tiktok.com'], Instagram: ['instagram.com','www.instagram.com'],
    'YouTube Music': ['music.youtube.com'], 'Apple Music': ['music.apple.com'],
    Deezer: ['deezer.com','www.deezer.com'], 'Amazon Music': ['music.amazon.com','music.amazon.co.uk','music.amazon.de'],
    Tidal: ['tidal.com','listen.tidal.com'], SoundCloud: ['soundcloud.com']
  };
  const symbols = {Spotify:'♫', YouTube:'▶', TikTok:'♪', Instagram:'◎'};
  function el(tag, cls, txt) {
    const node = document.createElement(tag);
    if(cls) node.className = cls;
    if(txt !== undefined) node.textContent = String(txt);
    return node;
  }
  function safeLink(url, p) {
    try {
      const u = new URL(url);
      if(u.protocol !== 'https:' || u.username || u.password || !allowedHosts[p]?.includes(u.hostname)) return '';
      if (u.searchParams.has('access_token') || u.searchParams.has('refresh_token')) return '';
      return u.toString();
    } catch { return ''; }
  }
  function filterRecords() {
    const q = search.value.toLocaleLowerCase('tr').trim();
    return records.filter(r => (platform.value === 'all' || r.platform === platform.value) &&
      (kind.value === 'all' || r.type === kind.value) &&
      (!q || [r.title,r.platform,...(r.songs || []),r.songCandidate].join(' ').toLocaleLowerCase('tr').includes(q)));
  }
  // Cover URLs are produced by the local exporter. No access tokens in browser code.
  function safeImage(url, p) {
    try {
      const u = new URL(url);
      if (u.protocol !== 'https:' || u.username || u.password || u.port) return '';
      const host = u.hostname.toLowerCase();
      const tikTokCdn = /^p\d{1,3}(?:-[a-z0-9-]+)?\.tiktokcdn(?:-[a-z0-9-]+)?\.com$/.test(host);
      // TikTok CDN image links may contain a *signed CDN* parameter named
      // refresh_token. It is not an OAuth credential. Only allow it on TikTok CDN.
      for (const [key, val] of u.searchParams) {
        const name = key.toLowerCase();
        if (['access_token', 'client_secret', 'auth_token', 'authorization', 'id_token'].includes(name)) return '';
        if (name === 'refresh_token' && (!tikTokCdn || /^rft[._]/i.test(val))) return '';
      }
      if (p === 'Spotify' && host === 'i.scdn.co' && u.pathname.startsWith('/image/')) return u.toString();
      if (p === 'YouTube' && host === 'i.ytimg.com' && u.pathname.startsWith('/vi/')) return u.toString();
      if (p === 'TikTok' && tikTokCdn) return u.toString();
    } catch (_) { /* Image unavailable: keep the platform icon. */ }
    return '';
  }
  function buildCard(rec) {
    const card = el('article','release-card');
    const url = safeLink(rec.url,rec.platform);
    const cover = el('div','release-cover cover-' + rec.platform.toLowerCase().replace(/[^a-z0-9]/g, '-'));
    const imageUrl = safeImage(rec.image, rec.platform);
    if(imageUrl) {
      const pic = el('img'); pic.loading='lazy'; pic.decoding='async'; pic.src=imageUrl; pic.alt='';
      pic.onerror = () => { pic.remove(); cover.appendChild(el('span','cover-glyph',symbols[rec.platform]||'♫')); };
      cover.appendChild(pic);
    } else {
      cover.appendChild(el('span','cover-glyph',symbols[rec.platform]||'♫'));
    }
    cover.appendChild(el('span','cover-type',rec.type === 'album'?'ALBÜM / SINGLE':rec.type==='video'?'VİDEO':'MÜZİK'));
    const coverAnchor = el('a','cover-link');
    if(url) { coverAnchor.href=url; coverAnchor.target='_blank'; coverAnchor.rel='noopener noreferrer';
      coverAnchor.setAttribute('aria-label',rec.title+' — '+rec.platform+' platformunda aç');
    } else { coverAnchor.setAttribute('aria-disabled','true'); }
    coverAnchor.appendChild(cover);
    card.appendChild(coverAnchor);
    const body = el('div','release-body');
    body.appendChild(el('span','release-platform',rec.platform));
    body.appendChild(el('h3','release-title',rec.title));
    if(rec.date) {
      const d = el('span','release-date');
      const v = /^\d{4}-\d{2}-\d{2}$/.test(rec.date) ? rec.date.split('-').reverse().join('.') : rec.date;
      d.textContent=v;
      body.appendChild(d);
    }
    if (rec.type === 'album') {
      const songs = rec.songs || [];
      if(songs.length) body.appendChild(el('p','release-subtitle',songs.length > 1 ? songs.length + ' şarkı · ' + songs.slice(0,2).join(' • ') : songs[0]));
    } else if (rec.songCandidate && rec.songCandidate.toLocaleLowerCase('tr') !== rec.title.toLocaleLowerCase('tr')) {
      body.appendChild(el('p','release-subtitle','Şarkı adayı: ' + rec.songCandidate));
    }
    const a = el('a','release-link',rec.platform==='Spotify'?'Spotify’da aç':rec.platform==='YouTube'?'YouTube’da izle':rec.platform==='TikTok'?'TikTok’ta izle':rec.platform==='Instagram'?'Instagram’da izle':rec.platform+'’da aç');
    if(url) { a.href=url; a.target='_blank'; a.rel='noopener noreferrer'; }
    else { a.removeAttribute('href');a.setAttribute('aria-disabled','true'); }
    body.appendChild(a);
    card.appendChild(body);
    return card;
  }
  function draw() {
    const matches = filterRecords();
    area.replaceChildren();
    for(const item of matches.slice(0,count)) area.appendChild(buildCard(item));
    const shown = Math.min(count,matches.length);
    status.textContent = matches.length ? matches.length.toLocaleString('tr')+' yayın bulundu · '+shown.toLocaleString('tr')+' gösteriliyor.' : 'Aramanıza uygun yayın yok.';
    more.hidden = shown >= matches.length;
  }
  function reset() {count = pageSize; draw();}
  search.addEventListener('input',reset);
  platform.addEventListener('change',reset);
  kind.addEventListener('change',reset);
  more.addEventListener('click',() => {count += pageSize; draw();});
  fetch('catalog.json', {cache:'no-cache'})
    .then(r => {if(!r.ok) throw Error('Katalog dosyası açılamadı.'); return r.json();})
    .then(data => {
      if(!Array.isArray(data.items)) throw Error('Katalog biçimi geçersiz.');
      records = data.items.filter(r => typeof r.title === 'string' && typeof r.platform === 'string' && safeLink(r.url,r.platform));
      total.textContent = records.length.toLocaleString('tr')+' yayın';
      const found = [...new Set(records.map(r=>r.platform))].sort((a,b)=>a.localeCompare(b,'tr'));
      for (const name of found) { const o=el('option','',name); o.value=name;platform.appendChild(o); }
      refresh.textContent='Son katalog derleme: '+(data.generatedAt ? new Date(data.generatedAt).toLocaleString('tr-TR') : 'Bilinmiyor');
      draw();
    })
    .catch(() => {refresh.textContent='Katalog henüz yayımlanmadı.';status.textContent='Lütfen catalog.json dosyasının siteye yüklendiğini kontrol edin.';});
})();
