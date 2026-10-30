(() => {
  'use strict';
  const value = document.getElementById('visit-count');
  const detail = document.getElementById('visit-detail');
  if (!value || !detail) return;
  fetch('visitor-stats.json', {cache: 'no-cache'})
    .then(r => {if (!r.ok) throw Error(); return r.json();})
    .then(data => {
      if (data.schema !== 1 || data.metric !== 'sessions' ||
          !Number.isSafeInteger(data.total) || data.total < 0 ||
          !Number.isFinite(Date.parse(data.updatedAt))) throw Error();
      value.textContent = data.total.toLocaleString('tr-TR');
      detail.textContent = '30.10.2026’dan beri ziyaret oturumları · Güncelleme: ' +
        new Date(data.updatedAt).toLocaleString('tr-TR') +
        ' · Yaklaşık 4 saatte bir yenilenir.';
    })
    .catch(() => {
      value.textContent = '—';
      detail.textContent = 'Ziyaret verileri henüz hazır değil.';
    });
})();