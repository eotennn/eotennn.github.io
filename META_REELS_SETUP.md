# EoTeN — Instagram ve Facebook Reels (güvenli taslak)

Bu modül, çalışan **YouTube Shorts otomasyonundan bağımsız** olarak tasarlandı. GitHub Releases içindeki 30 saniyelik orijinal sesli dikey videoları, mevcut `shorts-publish-queue/*.json` kayıtları üzerinden kullanır.

## Şu anki durum: YAYIN KAPALI

Bu değişiklik henüz yalnızca ayrı bir GitHub dalındaki **taslak PR** içindedir. Onaylanıp ana dala alınmadan GitHub Actions düzenli çalışmaz. Ana dala alındıktan sonra bile `META_REELS_LIVE=true` açıkça ayarlanmazsa **hiçbir Meta yayını yapılmaz**.

### Koruma önlemleri

- Metricool'a hiç istek göndermez; YouTube Shorts sistemi ve aylık Metricool Free 20 yayın hakkı etkilenmez.
- Varsayılan **yalnızca kuru testtir**.
- Sadece YouTube'da yayımlandığı doğrulanmış ve başlangıç saatinden **sonra oluşturulmuş** video kuyruklarını işler. Varsayılan başlangıç tarihi `2026-11-08T00:00:00+03:00`.
- Tek çalışmada en fazla **1 yeni video** işleme alınır.
- Her hedef platform için `social-publish-state/{videoId}-{platform}.json` durum dosyası daha Meta'ya istek gönderilmeden GitHub'a yazılır. İşlem yarıda kesilirse otomatik tekrar denemez; önce hesabın kontrol edilmesi gerekir.
- Instagram → Facebook otomatik çapraz paylaşımı halihazırda açık olabileceğinden **Facebook'a ayrı API yayını varsayılan olarak kapalıdır**. Aksi hâlde çift Reels oluşabilir.
- Başarılı API isteği her zaman görünür/oynatılabilir paylaşım anlamına gelmez. İlk yayında sonuç Meta üzerinde ayrıca incelenmelidir.

## Canlıya geçmeden önce gerekli teknik adımlar

1. Meta Developers uygulamasından Instagram profesyonel hesabın ve EoTeN Facebook sayfan için gereken yayınlama izinlerinin sağlandığını kontrol et. **Metricool'a bağlanmış olmak bu uygulamaya otomatik olarak Meta yayın token'ı sağlamaz.**
2. GitHub → `eotennn/eotennn.github.io` → Settings → Secrets and variables → Actions → **Secrets**:
   - `META_IG_USER_ID`
   - `META_PAGE_ACCESS_TOKEN` (gerekli yayınlama izinleriyle)
   - `META_FB_PAGE_ID` (yalnızca Facebook ayrı API yayını yapılacaksa)
3. **Variables**:
   - `META_REELS_LIVE=false`
   - `META_FB_REELS_LIVE=false`
   - `META_CUTOFF` = canlıya geçişten sonra seçilen başlangıç tarihi; önceden Instagram'da yayımlanmış hiçbir video bu tarihten sonra kuyruğa eklenmemiş olmalı.
4. İlk aşamada taslağı incele, ana dala al, GitHub Actions → `EoTeN - Meta Reels (safeguarded)` → Run workflow ile **kuru test** yap.
5. Meta API izinleri ve MP4 erişilebilirliği doğrulanıp mükerrer yayın riski giderildiğinde, Instagram için `META_REELS_LIVE=true` açılabilir. **Facebook için `META_FB_REELS_LIVE=false` kalmalı**, iki hedefin davranışı ayrıca test edilmedikçe açılmamalı.

## Teknik sınırlar

- Instagram Reels, Graph API üzerinden container oluşturma → işleme durumunu bekleme → yayınlama akışı kullanır.
- Facebook Reels için ayrı başlangıç → video yükleme → tamamlama akışı vardır. Ayrı Facebook yayını **varsayılan kapalıdır**.
- Github Release MP4 URL'sinin Meta sunucuları tarafından okunabildiği ilk gerçek denemede doğrulanmalıdır.
- MP4 ve müziklerin ticari kullanım hakları, Meta'nın telif politikası ve yapay zekâ üretimi içerik etiketlemesi ayrıca kontrol edilmelidir.
- İş akışı her 6 saatte bir kontrol edecek şekilde tasarlanmıştır; **yayınlamayı etkinleştirmek için gerçek token ve hesap yetkileri gerekir**.
- Herhangi bir hata halinde `social-publish-state/` dosyaları kontrol edilmeden yeniden deneme yapılmamalıdır.

## Mevcut sistem

**DEĞİŞTİRİLMEYEN DOSYALAR:**
- `.github/workflows/eoten-auto-shorts.yml`
- `.github/scripts/eoten_auto_shorts.py`
- `shorts-publish-queue/`

Bu taslak yalnızca yeni dosyalar ekler; canlı yayın otomatik başlatılmaz.
