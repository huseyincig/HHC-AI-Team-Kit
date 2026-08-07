---
description: HHC AI Team Kit kurulum asistanını başlat
---

# HHC AI Team Kit — Kurulum Asistanı

Bu komut etkileşimli kurulum sihirbazıdır. Kullanıcı açıkça hızlı kurulum istemedikçe sessizce dosya yazma. Seçimler için OpenCode'un yerleşik `question` aracını kullan.

Önce proje kökünü salt-okunur incele. `.opencode/hhc-team.json` varsa yeni kurulum yerine `/hhc-reconfigure` öner.

## 1. Profil — her zaman ilk soru

Projeyi salt-okunur inceleyip bir profil öner; ama ilk kullanıcı kararı profil olsun:
- **Minimal** (`minimal`)
- **Standard** (`standard`)
- **Web Development** (`web-development`)
- **Desktop Development** (`desktop-development`)
- **High Assurance** (`high-assurance`)
- **Özel** (`custom`)

Hazır profil seçildiyse tekrar rol sorma. Yalnız **Özel** profil seçilirse uzman rolleri Türkçe görünen adlarla seçtir:
- Mimar → `architect`
- Depo Gezgini → `repository-explorer`
- Kodlayıcı → `coder`
- Kalite İnceleyici → `qa-reviewer`
- Görsel QA → `visual-qa`
- Güvenlik İnceleyici → `security-reviewer`

Teknik agent ID'lerini kullanıcıya gösterme. Primary/yönetici rolü bu ekranda seçilmez; çalışma biçiminden otomatik türetilir.

## 2. Çalışma biçimi

Yalnız iki seçenek sun:
- **Tek Ana Ajan** — kullanıcı tek ana muhatap olarak Çalışan Yönetici ile çalışır; profil uzmanları yine kurulur ve gerektiğinde alt ajan olarak kullanılabilir.
- **Çoklu Ajan Ekibi** — yönetici + uzman ekip; roller için ayrı model atanabilir.

`Tam bağımsız tek ajan`, `Gerçek solo ajan` veya alt ajanları tamamen kapatan üçüncü seçenek gösterme.

### Tek Ana Ajan
Primary otomatik **Çalışan Yönetici** (`working-manager`) olur. Yönetici tipi SORMA. Profil uzmanlarını kaldırma ve Task/delegation kapısını kapatma.

### Çoklu Ajan Ekibi
Yönetici tipini sor:
- **Çalışan Yönetici** (`hands_on` → `working-manager`)
- **Orkestratör** (`orchestrator` → `manager`)

Özel profilde en az bir uzman rol olmalıdır. Hazır profilde rol kadrosu profilden gelir.

## 3. Scout — proje bazında opt-in

Çalışma biçiminden sonra kullanıcıya şu soruyu sor:

**Bu projede harici dokümantasyon, dependency ve upstream kaynak araştırması için OpenCode Scout kullanmak istiyor musunuz?**

Kısa açıklama: Scout yalnız harici araştırma içindir; yerel repository araştırmaları `repository-explorer` ile devam eder.

- **Hayır** (varsayılan): Scout HHC tarafından çağrılmaz ve Scout modeli sorulmaz.
- **Evet**: Scout etkinleştirilir ve model keşfinden sonra Scout / Dış Araştırma için ayrıca model seçilir.

Preset Scout'u otomatik açmaz. Kullanıcı açıkça Evet demeden enable etme.

## 4. Web Development ise Playwright MCP — opt-in

Profil `web-development` ise Scout kararından sonra şunu sor:

**Web projelerinde tarayıcı üzerinden görsel, responsive ve etkileşimli doğrulama için Playwright MCP kullanmak istiyor musunuz?**

- **Hayır** (varsayılan): MCP eklenmez.
- **Evet**: Microsoft Playwright MCP proje-local olarak eklenir; global `playwright_*` deny ve yalnız Görsel QA agent override `allow` kullanılır. PHP, SQL, Docker, Composer veya WP-CLI MCP yapılmaz.

Web dışı profillerde bu soruyu gösterme. Chrome DevTools veya ikinci browser MCP ekleme.

## 5. Model keşfi + SMART capability danışmanı

Model adımından hemen önce, kurulu roller kesinleştikten sonra bir kez:

`{{PYTHON}} "{{KIT_ROOT}}/scripts/model_advisor.py" --project-path . --role <kurulu-role> ... [--role scout]`

çalıştır. Scout açıksa `--role scout` ekle. `model_advisor.py`, mevcut `model_discovery.py` keşfini kullanır ve erişilebilirse models.dev metadata ile capability/context/maliyet bilgisi ekler.


OpenCode Desktop state'i mevcutsa `model_discovery.py` önce `%APPDATA%\ai.opencode.desktop\opencode.global.dat` içindeki `model.user[]` kayıtlarından yalnız `visibility == "show"` olan modelleri kullanır. Bu, Windows Desktop `/models` görünürlüğü için doğrulanmış yerel kullanıcı state'idir; dosya biçimi public/stable OpenCode API olmadığı için **BEST-EFFORT** kabul edilir. Sonuç `providerID/modelID` biçimindedir.

Desktop state yoksa veya görünür model döndürmüyorsa resmî `opencode models` CLI çıktısına geçilir. CLI da kullanılamıyorsa cache yalnız **UNDOCUMENTED / BEST-EFFORT** fallback olabilir; fallback hiçbir zaman cache'deki bütün katalogu körlemesine kullanıcıya taşımaz, yalnız yapılandırıldığı/bağlı olduğu doğrulanabilen provider modellerini kullanır.

Model listesi boşsa kendi kendine tekrar etme. Kullanıcı açıkça isterse bir normal yeniden deneme veya bir kez:

`{{PYTHON}} "{{KIT_ROOT}}/scripts/model_advisor.py" --project-path . --refresh`

çalıştır. Refresh otomatik çalıştırılmamalı; yalnız kullanıcı açıkça seçerse çalıştırılmalıdır. Sonuç yine boşsa tam `provider/model` kimliğini elle girme veya kurulumu iptal etme seçenekleri sun. Normal kurulumda **OpenCode'u devral** seçeneği gösterme.

Liste uzunsa önce sağlayıcıyı, sonra modeli seçtir. Model kimliği uydurma.

Advisor çıktısında model başına `RECOMMENDED / COMPATIBLE / WARNING / INCOMPATIBLE` sınıfını, tool calling, image input, reasoning, context/output limiti ve varsa provider fiyatını kısa göster. Fiyat bilinmiyorsa tahmin etme.

- `INCOMPATIBLE`: zorunlu capability açıkça yok; seçtirme.
- `WARNING`: metadata eksik/belirsiz; kullanıcıya bunu açıkla ve **Yine de kullan / Başka model seç** şeklinde explicit karar al.
- metadata servisi yoksa kurulumu bozma; capability UNKNOWN/WARNING kabul et.

Hardcoded marka/model tavsiyesi yapma. Runtime model router/fallback oluşturma; bu danışman yalnız kurulum/reconfigure seçim aşamasındadır.

## 6. Model ataması

### Tek Ana Ajan
Yalnız **bir model** seçtir. Seçilen modeli Çalışan Yönetici ve profildeki bütün kurulu uzmanlara uygula. Backend'de `--shared-model provider/model` kullan. Bu model yalnız kurulu HHC rollerine uygulanır. Scout = Evet ise ayrıca **Scout / Dış Araştırma** modeli seçtir; Scout manager/shared modeli sessizce devralmasın.

### Çoklu Ajan Ekibi — zorunlu rol bazlı akış
Kurulu ekip listesini kesinleştir ve **her rol için ayrı model cevabı topla**. Model adımının tamamlanma koşulu, kurulu rollerin tamamının bir `provider/model` değerine sahip olmasıdır.

Uygulanacak algoritma:
1. Kurulu rolleri sırayla Türkçe görünen adlarıyla ele al.
2. Her rol için `Bu rol hangi modeli kullansın?` sorusunu sor ve yalnız o role ait cevabı kaydet.
3. Bir rol için verilen cevabı başka role otomatik kopyalama.
4. Kullanıcı manuel giriş seçerse manuel `provider/model` değerini yine yalnız o rol için iste.
5. Bütün rollerin modeli belirlenmeden model adımından çıkma ve son onaya geçme.
6. Backend'e kurulu **her rol için** bir `--model role=provider/model` argümanı geçir.

OpenCode `question` aracı tek çağrıda birden çok ayrı soru destekliyorsa rol başına ayrı soru alanı kullan; desteklemiyorsa rolleri sırayla sor. Her iki durumda da kullanıcıdan kurulu rol sayısı kadar bağımsız model kararı alınmalıdır.

Örnek sonuç:
- Çalışan Yönetici → `provider/model-a`
- Mimar → `provider/model-b`
- Depo Gezgini → `provider/model-c`
- Kodlayıcı → `provider/model-d`
- Kalite İnceleyici → `provider/model-e`
- Görsel QA → `provider/model-f`

Bu örnek yalnız sonuç biçimini gösterir; model kimliği uydurma.

Scout = Evet ise kurulu rollerden bağımsız olarak ayrıca **Scout / Dış Araştırma** için bir `provider/model` seçimi al. Bu seçim başka role otomatik kopyalanmaz ve pahalı manager modeline sessiz fallback yapılmaz.

## 7. Son onay

Dosya yazmadan önce tek özet göster:
- profil
- Özel profilde seçilen uzmanlar / hazır profilde profil kadrosu
- çalışma biçimi
- Tek Ana Ajan ise Ana Ajan: Çalışan Yönetici + seçilen tek model
- Çoklu Ajan ise yönetici tipi + Türkçe rol → model dağılımı
- Scout: Kapalı veya Açık + seçilen Scout modeli
- Playwright MCP: Web profilinde Kapalı/Açık
- role/model capability uyarıları ve explicit override varsa özeti
- hedef proje

`question` ile **Kur / Ayarları değiştir / İptal** seçeneklerini sun. Kur onayı olmadan backend'i çağırma.

## Backend

Tek Ana Ajan:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path . --team-mode single --preset <profil> [--roles <yalnız-custom-uzmanlar>] --shared-model provider/model --scout <enabled|disabled> [--scout-model provider/model] --playwright <enabled|disabled> --validate-model-capabilities`

Hazır Çoklu Ajan profili:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path . --team-mode multi --preset <profil> --manager-mode <mod> --model role=provider/model ... --scout <enabled|disabled> [--scout-model provider/model] --playwright <enabled|disabled> --validate-model-capabilities`

Özel Çoklu Ajan profili:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path . --team-mode multi --preset custom --manager-mode <mod> --roles coder,qa-reviewer,... --model role=provider/model ... --scout <enabled|disabled> [--scout-model provider/model] --playwright <enabled|disabled> --validate-model-capabilities`

Kurulum sonunda JSON çıktısından profil, çalışma biçimi, primary ajan, roller, model dağılımı, Scout açık/kapalı + Scout modeli, yazılan/korunan dosyalar ve `config` sonucunu kısa raporla. `config.action` `preserved-existing-config` ise mevcut `opencode.jsonc` dosyasının korunduğunu ve HHC'nin bu dosyadaki `default_agent`, `subagent_depth` veya `compaction` değerlerini değiştirmediğini açıkça belirt.
