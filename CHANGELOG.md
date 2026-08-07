# Changelog

## 1.1.0-rc.19
- Windows OpenCode Desktop model keşfi gerçek Desktop kullanıcı state'ine bağlandı: `%APPDATA%\ai.opencode.desktop\opencode.global.dat` içindeki `model.user[]` kayıtlarında yalnız `visibility == "show"` modelleri alınır.
- Desktop model kimlikleri `providerID/modelID` olarak üretilir; `hide` kayıtları, bozuk kayıtlar ve tekrarlar kullanıcı listesine girmez.
- Desktop state mevcut ve görünür model içeriyorsa CLI/cache'ten önce kullanılır; state yoksa/boşsa `opencode models`, ardından doğrulanmış provider cache fallback'i korunur. Desktop state dosya biçimi public/stable OpenCode API olmadığı için BEST-EFFORT olarak işaretlenir.
- rc.18'deki Çoklu Ajan rol→model zorunluluğu korunur: her kurulu rol ayrı model kararı almadan kuruluma geçilemez.
- DIST ve SOURCE paketlerinde kişisel/root `.opencode/`, `opencode.jsonc` ve `AGENTS.md` bulunmaması release testiyle korunur.

## 1.1.0-rc.18
- Çoklu Ajan model seçimi deterministik hale getirildi: kurulu her rol için bağımsız model cevabı zorunlu; tüm roller tamamlanmadan onaya geçilmez.
- Manuel `provider/model` girişi de rol bazlıdır; bir rolün seçimi diğer rollere otomatik taşınmaz.
- Kurulum/reconfigure/bootstrap talimatlarındaki model eşleme akışı tek bir pozitif algoritma halinde sadeleştirildi.
- SOURCE paketleme kuralı temizlendi: kişisel/root `.opencode/`, `opencode.jsonc` ve `AGENTS.md` SOURCE ve DIST arşivlerine alınmaz.

## 1.1.0-rc.17
- Kurulum/reconfigure akışı Profil → Çalışma Biçimi → Model şeklinde sadeleştirildi.
- Tek Ana Ajan artık `working-manager + profil uzmanları`; alt ajan/delegation kapısı açık kalır.
- Ayrı model policy, OpenCode devral, hangi roller farklı ve tam bağımsız solo wizard seçenekleri kaldırıldı.
- Çoklu ajanda doğrudan Türkçe rol → model eşlemesi kullanılır.
- Cache model fallback'i yalnız etkinliği doğrulanabilen provider'larla filtrelenir; katalog sızıntısı engellenir.
- Custom profil capability fallback davranışı netleştirildi.
- Eski rc.16 solo state için güvenli reconfigure migration yolu korundu.

# Değişiklik Günlüğü

## 1.1.0-rc.16

- Model keşfinde `opencode models` resmî birincil kaynak olarak açıkça ayrıldı; yerel cache yolları `UNDOCUMENTED / BEST-EFFORT FALLBACK` olarak işaretlendi.
- `scripts/model_discovery.py --refresh` ile yalnız kullanıcı açıkça isterse resmî `opencode models --refresh` yolu eklendi; otomatik refresh ve tekrar döngüsü oluşturulmadı.
- Installer sonucu mevcut `opencode.jsonc` korunduğunda bunu makine-okunur `config.action`/`config.notice` alanlarıyla açıkça bildirir; kullanıcı config'i ezilmez ve yeni merge framework'ü eklenmez.
- Manager/Working Manager yalnız projede gerçekten mevcut ve çağrılabilir uzmanlara delegation yapacak şekilde netleştirildi.
- Coder, QA ve `task-classification` içinde yalnız OpenCode LSP gerçekten etkin/kullanılabilir olduğunda syntax/diagnostic/sembol doğrulamalarının native deterministik kanıt olarak kullanılabileceği netleştirildi; aksi durumda lint/typecheck/build/test akışı korunur.
- Windows native/OpenCode Desktop ile WSL içinde çalışan OpenCode backend'in ayrı kullanıcı/config ortamları olduğu kurulum dokümantasyonuna eklendi.
- `steps`, sabit `reserved`, plugin dönüşümü, custom tool/MCP framework'ü, AGENTS.md üretimi veya explicit `doom_loop` gürültüsü eklenmedi.

## 1.1.0-rc.15

- `task-classification` becerisi eklendi; belirsiz/çok adımlı görevlerde minimum yeterli ajan, skill, doğrulama ve kullanıcı onayı ihtiyacını seçer.
- Preset'lerin sabit pipeline değil uzman havuzu olduğu manager davranışına işlendi; küçük görevler minimum ajanla başlar ve yalnız yeni ihtiyaçta dinamik genişler.
- Varsayım ekonomisi netleştirildi: kararı değiştirmeyecek bilinmeyen araştırılmaz, kararı değiştirecek bilinmeyen tahmin edilmez.
- Repository keşfi ve subagent handoff'ları kısa bulgu + dosya/sembol referansı odaklı hale getirildi; ham büyük context taşınması azaltıldı.
- QA, mimar, güvenlik ve görsel QA çağrıları görev etkisine göre koşullu hale getirildi; deterministik test/build/lint kanıtı ikinci LLM görüşüyle gereksiz tekrarlanmaz.
- Retry davranışı sabit tur sayısı yerine yeni bilgi/gerçek ilerleme ölçütüne bağlandı; OpenCode native `doom_loop` korumasının aşılmaması belirtildi.
- Uzman ajanlar kendi uzmanlığı gerekmiyorsa uzun çalışma üretmeden kısa gerekçeyle geri dönebilir.
- Rol/skill talimatları prompt-cache dostu sabit içerik olarak tutuldu; yeni runtime, schema, token server, cache motoru veya evidence framework eklenmedi.

## 1.1.0-rc.14

- Kurulum asistanına **Tek ajan / Çoklu ajan** seçimi eklendi.
- `solo-agent` ile gerçek tek ajan modu eklendi; alt ajan çağrıları kapalıdır.
- Model seçimi üç politika halinde netleştirildi: OpenCode modelini devral, tek model tüm ekipte, rol bazlı modeller.
- Model seçenekleri `opencode models` çıktısından alınarak OpenCode'un yerleşik `question` aracıyla seçenek olarak sunulur.
- `/hhc-reconfigure` ile sonradan profil, rol, çalışma modu, yönetici tipi ve model dağılımı değiştirme eklendi.
- `.opencode/hhc-team.json` yalnız ekip ayarlarını ve HHC tarafından yönetilen dosyaları takip eder.
- Yeniden yapılandırmada eski profilden kalan HHC dosyaları temizlenir; kullanıcı dosyaları korunur.
- Durum dosyası olmayan önceki HHC kurulumlarındaki birebir aynı kit dosyaları güvenli biçimde benimsenebilir.

## 1.1.0-rc.12

- `/hhc-install` sessiz Standard kurulum yerine etkileşimli kurulum asistanına dönüştürüldü.
- Profil rollerini `--roles` ile özelleştirme desteği eklendi.
- Kurulum öncesi seçim özeti ve kullanıcı onayı akışı tanımlandı.

## 1.1.0-rc.11

- Kullanıcıya ve ajana görünen metinler tutarlı Türkçeye çevrildi.
- OpenCode teknik anahtarları, ajan/beceri kimlikleri ve makine durum kodları değiştirilmedi.
- Kişisel geliştirme ekibinin `.opencode/` talimatları sadeleştirilmiş ürün mimarisiyle uyumlu hale getirildi.

## 1.1.0-rc.10

- Ürün OpenCode'un yerleşik ana ajan/alt ajan, Task, yapılacaklar, beceri ve komut yapısına sadeleştirildi.
- Özel HHC görev/kanıt runtime'ı, schema katmanı, özel araç sarmalayıcıları ve Node/Zod bağımlılığı kaldırıldı.
- Kurucu yalnız ajan/beceri/komut dosyalarını ve gerektiğinde `opencode.jsonc` dosyasını üretir.
- MCP profilleri kaldırıldı; MCP yapılandırması OpenCode'un yerleşik yapılandırmasına bırakıldı.

## 1.1.0-rc.14

- Model keşfi tek `opencode models` çağrısına bağımlı olmaktan çıkarıldı.
- `~/.cache/opencode/models.json` ve `~/.cache/opencode.json` (Windows eşdeğerleri dahil) salt-okunur fallback olarak eklendi.
- Model keşfi başarısız olduğunda otomatik tekrar döngüsü yasaklandı.
- Sabit profil seçildikten sonra gereksiz rol sorusu kaldırıldı.
- Yeni `custom` profil eklendi; rol seçimi yalnız bu profilde yapılır.
- `/hhc-reconfigure` içinde roller ayrı ana menü maddesi olmaktan çıkarıldı; profil `custom` olduğunda yönetilir.
- Tek model / rol bazlı model akışlarının backend argüman kuralları netleştirildi.
