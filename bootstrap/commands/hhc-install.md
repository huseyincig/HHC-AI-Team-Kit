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

Profil **ajan kadrosu değildir**. Üç profilde de temel specialist roller erişilebilir kalır. Kullanıcıya Web/Desktop/High Assurance/Custom seçeneklerini ana profil olarak gösterme.

## 2. Proje özelliklerini otomatik çıkar

Kullanıcıya proje türü sorma. Şunu çalıştır:

`{{PYTHON}} "{{KIT_ROOT}}/scripts/project_characteristics.py" --project-path .`

Sonucu tek enum değil çoklu özellik olarak ele al: `browser_ui`, `desktop_ui`, `backend`, `cli`, `library`, `database`, `wordpress`, `containerized`, `mobile`.

Algılama kanıtı zayıfsa kesin hüküm verme. İleri düzey kullanıcı açıkça düzeltmek isterse backend'e tekrar edilebilir `--project-characteristic <özellik>` geçirilebilir. Bu normal kurulum sorusu değildir.

## 3. Takım biçimi — normal kullanıcıya SORMA

Yeni SMART mimaride **Tek Ana Ajan / Çoklu Ajan** ana kurulum kararı değildir. Normal kurulumda:

- backend `--team-mode multi --manager-mode hands_on` kullanır,
- primary `working-manager` olur,
- bütün temel specialist roller erişilebilir kalır,
- delegation SMART kararına göre yapılır.

Eski `single|multi` backend desteği migration ve Advanced Configuration için korunur. Kullanıcı açıkça tek ortak model veya salt orkestratör primary isterse gelişmiş ayar olarak kullanılabilir; normal kurulum akışına ayrı “team mode” sorusu ekleme.

## 4. Scout — proje bazında opt-in

Kullanıcıya sor:

**Harici dokümantasyon, dependency ve upstream kaynak araştırması için OpenCode Scout kullanmak istiyor musunuz?**

- **Hayır** (varsayılan): Scout HHC tarafından çağrılmaz ve Scout modeli sorulmaz.
- **Evet**: Scout etkinleştirilir; model adımında Scout / Dış Araştırma için ayrı model seçilir.

Scout profile bağlı değildir. Yerel repository araştırması `repository-explorer` ile kalır.

## 5. Playwright — yalnız browser UI varsa opt-in

`project_characteristics.py` sonucunda `browser_ui.detected == true` ise sor:

**Tarayıcı üzerinden görsel, responsive ve etkileşimli doğrulama için Playwright MCP kullanmak istiyor musunuz?**

- **Hayır** (varsayılan): MCP eklenmez.
- **Evet**: proje-local Microsoft Playwright MCP eklenir; global `playwright_*` deny, yalnız `visual-qa` override `allow` olur.

`browser_ui` doğrulanmadıysa bu soruyu gösterme. Playwright hiçbir profile tarafından otomatik açılmaz. Chrome DevTools veya ikinci browser MCP ekleme.

## 6. Model keşfi + SMART capability danışmanı

Model keşfi `model_discovery.py` üzerinden yürür. Windows OpenCode Desktop state'i mevcutsa model keşfi önce `%APPDATA%\ai.opencode.desktop\opencode.global.dat` içindeki `model.user[]` kayıtlarından yalnız `visibility == "show"` olan modelleri salt-okunur **BEST-EFFORT** kaynak olarak değerlendirebilir. Bu public/stable OpenCode API değildir. Bu kaynak yoksa resmî `opencode models` CLI kullanılır. CLI da kullanılamıyorsa cache yalnız **UNDOCUMENTED / BEST-EFFORT** fallback'tir ve yalnız yapılandırıldığı/bağlı olduğu doğrulanabilen provider modellerini kullanır. Sonuç boşsa otomatik retry yapma; `--refresh` otomatik çalıştırılmamalı. Kullanıcı isterse bir normal retry veya bir kez `model_discovery.py --project-path . --refresh`, sonra manuel `provider/model` ya da iptal sun.

Kurulu roller kesinleşince bir kez:

`{{PYTHON}} "{{KIT_ROOT}}/scripts/model_advisor.py" --project-path . --role working-manager --role architect --role repository-explorer --role coder --role qa-reviewer --role visual-qa --role security-reviewer [--role scout]`

çalıştır. Scout açıksa `--role scout` ekle.

Advisor çıktısında `RECOMMENDED / COMPATIBLE / WARNING / INCOMPATIBLE`, tool calling, image input, reasoning, context/output limiti ve varsa provider fiyatını kısa göster. Fiyat bilinmiyorsa tahmin etme.

- `INCOMPATIBLE`: zorunlu capability açıkça yok; seçtirme.
- `WARNING`: metadata eksik/belirsiz; **Yine de kullan / Başka model seç** şeklinde explicit karar al.
- metadata yoksa kurulumu bozma.

Hardcoded marka/model tavsiyesi yapma. Runtime model router veya sessiz premium fallback oluşturma.

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

Scout açıksa ayrıca Scout modeli seçilir ve başka role otomatik kopyalanmaz.

Advanced Configuration isteyen kullanıcı tek ortak model seçebilir; backend `--shared-model provider/model` bunu destekler. Bu seçenek profili değiştirmez.

## 8. Advanced Configuration

Normal kullanıcıya rol seçimi sorma. Eski `custom` profilin görevi artık buradadır.

Kullanıcı özellikle isterse:
- specialist rol havuzunu `--roles coder,qa-reviewer,...` ile daraltabilir,
- **Orkestratör** (`manager`) primary için `--manager-mode orchestrator` seçebilir,
- legacy `--team-mode single` veya shared model akışını kullanabilir,
- project characteristic override verebilir.

Bu ayarlar ana profile listesine `Custom` eklemez.

## 9. Son onay

Dosya yazmadan önce tek özet göster:
- profil: Basic / Standard / Powerful
- algılanan proje özellikleri + kısa kanıt
- primary: normal akışta Çalışan Yönetici
- rol → model dağılımı
- Scout: Kapalı/Açık + modeli
- Playwright: uygun projede Kapalı/Açık
- varsa Advanced Configuration override'ları
- model capability uyarıları

Onaydan sonra normal backend örneği:

`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path . --team-mode multi --manager-mode hands_on --preset <basic|standard|powerful> --model working-manager=provider/model ... --scout <enabled|disabled> [--scout-model provider/model] --playwright <enabled|disabled> --validate-model-capabilities`

Browser UI otomatik algılanamadı ama kullanıcı Advanced Configuration'da açıkça doğruladıysa ayrıca:

`--project-characteristic browser_ui`

geçilebilir.

Kurulum sonunda JSON çıktısından profil, proje özellikleri, primary, roller, model dağılımı, Scout/Playwright durumu, yazılan/korunan dosyalar ve config sonucunu kısa raporla.
