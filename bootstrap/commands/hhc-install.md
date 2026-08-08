---
description: HHC AI Team Kit kurulum asistanını başlat
---

# HHC AI Team Kit — Kurulum Asistanı

Bu komut etkileşimli kurulum sihirbazıdır. Kullanıcı açıkça hızlı kurulum istemedikçe sessizce dosya yazma. Seçimler için OpenCode'un yerleşik `question` aracını kullan.

Önce proje kökünü salt-okunur incele. `.opencode/hhc-team.json` varsa yeni kurulum yerine `/hhc-reconfigure` öner.

## 1. Çalışma profili — ilk gerçek kullanıcı kararı

Yalnız üç seçenek sun:

- **Basic** (`basic`) — maliyet/bağlam öncelikli; uzman çağırma ve paralellik eşiği daha yüksektir. Gerekli uzman sırf profil nedeniyle kapatılmaz.
- **Standard** (`standard`) — **varsayılan ve önerilen** dengeli SMART çalışma; minimum gerekli ekip, risk bazlı doğrulama, bağımsız işlerde kontrollü paralellik.
- **Powerful** (`powerful`) — kalite/güvence öncelikli; bağımsız ve yüksek değerli işler daha istekli paralelleştirilir, önemli/kritik işlerde bağımsız doğrulama eşiği düşer. Her ajanı çalıştırmaz ve aynı rolü varsayılan olarak çoğaltmaz.

Profil **ajan kadrosu değildir**. Üç profilde de temel uzman roller erişilebilir kalır. Kullanıcıya Web/Desktop/High Assurance/Custom seçeneklerini ana profil olarak gösterme.

## 2. Proje özelliklerini otomatik çıkar

Kullanıcıya proje türü sorma. Şunu çalıştır:

`{{PYTHON}} "{{KIT_ROOT}}/scripts/project_characteristics.py" --project-path .`

Sonucu tek enum değil çoklu özellik olarak ele al: `browser_ui`, `desktop_ui`, `backend`, `cli`, `library`, `database`, `wordpress`, `containerized`, `mobile`.

Algılama kanıtı zayıfsa kesin hüküm verme. İleri düzey kullanıcı açıkça düzeltmek isterse arka uç'e tekrar edilebilir `--project-characteristic <özellik>` geçirilebilir. Bu normal kurulum sorusu değildir.

## 3. Takım biçimi — normal kullanıcıya SORMA

Yeni SMART mimaride **Tek Ana Ajan / Çoklu Ajan** ana kurulum kararı değildir. Normal kurulumda:

- arka uç `--team-mode multi --manager-mode hands_on` kullanır,
- ana ajan `working-manager` olur,
- bütün temel uzman roller erişilebilir kalır,
- delegation SMART kararına göre yapılır.

Eski `single|multi` arka uç desteği geçiş ve Gelişmiş Yapılandırma için korunur. Kullanıcı açıkça tek ortak model veya salt orkestratör ana ajan isterse gelişmiş ayar olarak kullanılabilir; normal kurulum akışına ayrı “team mode” sorusu ekleme.

## 4. External Research / Scout — runtime-gated

Harici/güncel araştırmanın varsayılan native yolu ana ajanın `websearch` + `webfetch` araçlarıdır. Scout için önce çalışma zamanının gerçek agent/Task yüzeyini kontrol et.

- Native `scout` gerçekten çağrılabilir **değilse** kullanıcıya Scout sorusu gösterme ve `--scout disabled` kullan.
- Native `scout` gerçekten çağrılabilir **ise** ancak geniş araştırmada bağlam yalıtımı faydalı olabilecekse kullanıcıya **"Araştırmayı gerektiğinde native Scout alt ajanına yalıtmak ister misiniz?"** diye sor.
- **Hayır** (varsayılan): `websearch` + `webfetch` ana ajan bağlamında kullanılır.
- **Evet**: yalnız runtime-native Scout'a izin verilir; HHC aynı adlı custom agent üretmez ve model override yazmaz.

Scout profile bağlı değildir. Yerel depo araştırması `repository-explorer` ile kalır.

## 5. Playwright — yalnız browser UI varsa opt-in

`project_characteristics.py` sonucunda `browser_ui.detected == true` ise sor:

**Tarayıcı üzerinden görsel, farklı ekran boyutlarına uyumlu ve etkileşimli doğrulama için Playwright MCP kullanmak istiyor musunuz?**

- **Hayır** (varsayılan): MCP eklenmez.
- **Evet**: proje-local Microsoft Playwright MCP eklenir; global `playwright_*` deny, yalnız `visual-qa` override `allow` olur.

`browser_ui` doğrulanmadıysa bu soruyu gösterme. Playwright hiçbir profile tarafından otomatik açılmaz. Chrome DevTools veya ikinci tarayıcı MCP ekleme.

## 6. Model keşfi + SMART yetenek danışmanı

Model keşfi `model_discovery.py` üzerinden yürür. Windows OpenCode Desktop durum verisi mevcutsa model keşfi önce `%APPDATA%\ai.opencode.desktop\opencode.global.dat` içindeki `model.user[]` kayıtlarından yalnız `visibility == "show"` olan modelleri salt-okunur **EN İYİ ÇABA** kaynak olarak değerlendirebilir. Bu genel kullanıma açık/kararlı OpenCode API değildir. Bu kaynak yoksa resmî `opencode models` CLI kullanılır. CLI da kullanılamıyorsa önbellek yalnız **BELGELENMEMİŞ / EN İYİ ÇABA** yedek kaynak'tir ve yalnız yapılandırıldığı/bağlı olduğu doğrulanabilen provider modellerini kullanır. Sonuç boşsa otomatik yeniden deneme yapma; `--refresh` otomatik çalıştırılmamalı. Kullanıcı isterse bir normal yeniden deneme veya bir kez `model_discovery.py --project-path . --refresh`, sonra manuel `provider/model` ya da iptal sun.

Kurulu roller kesinleşince bir kez:

`{{PYTHON}} "{{KIT_ROOT}}/scripts/model_advisor.py" --project-path . --role working-manager --role architect --role repository-explorer --role coder --role qa-reviewer --role visual-qa --role security-reviewer`

çalıştır. Native Scout modelini HHC seçmediği için model danışmanına Scout rolü ekleme.

Advisor çıktısında `RECOMMENDED / COMPATIBLE / WARNING / INCOMPATIBLE`, araç çağırma, görsel girdi, akıl yürütme, bağlam/çıktı sınırı ve varsa provider fiyatını kısa göster. Fiyat bilinmiyorsa tahmin etme.

- `INCOMPATIBLE`: zorunlu yetenek açıkça yok; seçtirme.
- `WARNING`: üst veri eksik/belirsiz; **Yine de kullan / Başka model seç** şeklinde açık karar al.
- üst veri yoksa kurulumu bozma.

Sabit kodlanmış marka/model tavsiyesi yapma. Çalışma zamanı model yönlendiricisi veya sessiz premium yedek kaynak oluşturma.

## 7. Model ataması — gerçek kullanıcı kararı

Normal kurulumda her kurulu HHC rolü için ayrı model cevabı topla. Her kurulu HHC rolü için ayrı model seçimi alınır. Bir rolün modelini diğer role sessizce kopyalama. Bütün rollerin modeli belirlenmeden model adımından çıkma ve son onaya geçme.

Roller:
- Çalışan Yönetici → `working-manager`
- Mimar → `architect`
- Depo Gezgini → `repository-explorer`
- Kodlayıcı → `coder`
- Kalite İnceleyici → `qa-reviewer`
- Görsel QA → `visual-qa`
- Güvenlik İnceleyici → `security-reviewer`

Scout açıksa yalnız çalışma zamanının native Scout yüzeyini kullan; modelini HHC üzerinden override etme. Scout yüzeyi yoksa varmış gibi davranma.

Gelişmiş Yapılandırma isteyen kullanıcı tek ortak model seçebilir; arka uç `--shared-model provider/model` bunu destekler. Bu seçenek profili değiştirmez.

## 8. Gelişmiş Yapılandırma

Normal kullanıcıya rol seçimi sorma. Eski `custom` profilin görevi artık buradadır.

Kullanıcı özellikle isterse:
- uzman rol havuzunu `--roles coder,qa-reviewer,...` ile daraltabilir,
- **Orkestratör** (`manager`) ana ajan için `--manager-mode orchestrator` seçebilir,
- eski `--team-mode single` veya ortak model akışını kullanabilir,
- project characteristic override verebilir.

Bu ayarlar ana profile listesine `Custom` eklemez.

## 9. Son onay

Dosya yazmadan önce tek özet göster:
- profil: Basic / Standard / Powerful
- algılanan proje özellikleri + kısa kanıt
- ana ajan: normal akışta Çalışan Yönetici
- rol → model dağılımı
- Scout: çalışma zamanı native Scout yüzeyi sunuyorsa Kapalı/Açık; HHC Scout modeli seçmez veya override etmez
- Playwright: uygun projede Kapalı/Açık
- varsa Gelişmiş Yapılandırma override'ları
- model yetenek uyarıları

Onaydan sonra normal arka uç örneği:

`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path . --team-mode multi --manager-mode hands_on --preset <basic|standard|powerful> --model working-manager=provider/model ... --scout <enabled|disabled> --playwright <enabled|disabled> --validate-model-capabilities`

Tarayıcı arayüzü otomatik algılanamadı ama kullanıcı Gelişmiş Yapılandırma'da açıkça doğruladıysa ayrıca:

`--project-characteristic browser_ui`

geçilebilir.

Kurulum sonunda JSON çıktısından profil, proje özellikleri, ana ajan, roller, model dağılımı, Scout/Playwright durumu, yazılan/korunan dosyalar ve config sonucunu kısa raporla.
