# EoTeN VØX — Standart karakter ve web sayfası şablonu

Bu kayıt EoTeN sanal sanatçı sisteminin ortak standardıdır. Tüm sayfalar **vox-artists.json** ile yönetilir ve **vox-detail.js / vox-detail.css** ile görüntülenir.

## Sayfanın yerleşimi
1. Ana görsel: sadece o karakterin net, fotogerçekçi, **yakın plan yüz portresi**.
2. Karakter kimliği: kod, rol, müzik tarzı, yaş aralığı (sanal karakter), ses tipi, tanıtım metni ve imza görünüm.
3. Dört tam boy açı: **ÖN → ARKA → SAĞ → SOL**. Bir açı henüz yoksa dürüstçe *görsel bekleniyor* gösterilir, yanlış görsel kullanılmaz.
4. Ek galeri: yakın portreler, farklı pozlar, resmî tanıtım kartı, alternatif kıyafet setleri. Her görselin ait olduğu karakter ve görünüm açıklanır.
5. Spotify kısa dinleme: sadece **catalog.json** içinde gerçek Spotify bağlantısı bulunan ve **vox-mapping.json** ile o sanatçıya eşleştirilmiş yayınlar. Kısa oynatma kontrolü Spotify'ın izin verdiği sınırlar dahilindedir.
6. Diğer VØX sanatçılarına bağlantılar ve VØX galeriye dönüş.

## Yeni karakter kayıt alanları
**vox-artists.json** > profiles[] içinde:
- id: ör. "F8" veya "M3" (benzersiz; M/F + 1–99)
- name: ör. "VØX-F8"
- role: ör. "Kadın vokal / solist"
- style: müzik türü
- vocal: ses rengi / tonalite
- age: karakter yaş aralığı
- summary: kısa karakter biyografisi
- appearance: yüz, saç, kıyafet, aksesuar kimliği
- palette: CSS renk değeri
- heroImage: assets/vox/f8/... yakın plan portre yolu (yoksa null)
- views: {front, back, right, left} — aynı karakterin dört **bağımsız** tam boy fotoğrafı; eksikler null
- gallery: [{src,title,type}] — farklı kıyafetler, portreler, karakter kartları
- images: eski kayıtlarla geriye dönük uyumluluk için korunan görseller

Görselleri mümkünse WebP olarak **assets/vox/<kod-küçük-harf>/** altında sakla. Uzak üçüncü taraf fotoğrafları karakter referansı olarak kullanma. Her fotoğraf keskin, pus/sis/bulanıklık olmadan, fotogerçekçi olmalı. Yüz ve vücut oranları tüm açılarda aynı kalmalı.

## Yayına alma / otomasyon
- Yeni profili vox-artists.json içine ekleyip görselleri aynı GitHub değişikliğiyle yükle.
- **.github/workflows/vox-pages.yml**, profile kaydı main dalına gönderildiğinde **scripts/generate_vox_pages.py** ile yeni vox-f8.html / vox-m3.html gibi sayfayı üretir.
- Galeri liste ve bağlantıları profil kayıtlarından otomatik okunur. Var olan elle düzenlenmiş sanatçı sayfaları asla üzerine yazılmaz.
- Şarkı ilgili sanatçıya ait olduğu güvenle doğrulanmadan **vox-mapping.json** içine eklenmez.
- Siteye eklenen her sanatçı için resim yüklenmesi, 4 açı sırası, mobil görünüm, Spotify bağlantısı ve menü/diğer sanatçılar bağlantısı kontrol edilir.

## Kontrol listesi
- [ ] Kod / kimlik mevcut VØX'lerle çakışmıyor.
- [ ] Ana yüz yakın plan, orijinal ve fotogerçekçi.
- [ ] Ön / Arka / Sağ / Sol aynı kişiye ve aynı kombine ait.
- [ ] Kırpma, basık vücut, çizgi film, sis, bulanıklık yok.
- [ ] Alternatif kombinler asıl kimliği değiştirmiyor.
- [ ] Tüm fotoğraflar gerçekten GitHub assets klasörüne yüklendi.
- [ ] Yeni sanatçı sayfası oluşturuldu ve galeriden ulaşılabiliyor.
- [ ] Spotify bağlantısı katalogda var ve karakter eşleşmesi kanıtlandı.
- [ ] Oynatıcı, mobil menü, galeri ve yakınlaştırma kontrol edildi.

## Mevcut eksikler
VØX-F2 için şu an gerçek **arka tam boy bağımsız fotoğraf** kayıtlı değildir. Bu açı otomatik olarak üretilemez; özgün görseli oluşturup **views.back** alanına kaydetmek gerekir. Benzer eksikler diğer sanatçılarda da yeni fotoğraf üretilene kadar açıkça gösterilir.

Otomatik iş akışı GitHub'a dosya kaydı yapıldığında tetiklenir. Sadece ChatGPT'de karakter görseli üretmek GitHub'a otomatik yükleme anlamına gelmez; GitHub hesabına yazma izni ve gerçek dosya aktarımı gerekir.
