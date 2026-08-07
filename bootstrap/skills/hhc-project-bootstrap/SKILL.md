---
name: hhc-project-bootstrap
description: Kullanıcı HHC AI Team Kit'i mevcut veya uzak bir projeye kurmak, profil/çalışma biçimi/model dağılımını değiştirmek ya da mevcut HHC ekibini yeniden yapılandırmak istediğinde kullan.
---

# HHC Proje Kurulum ve Yeniden Yapılandırma Asistanı

HHC kurulum ve ekip değişikliği varsayılan olarak etkileşimlidir. Kullanıcı açıkça hızlı kurulum istemedikçe sessiz varsayım yapma. Seçenekli kararları OpenCode'un native `question` aracıyla sor.

Karar sırası:
1. **Profil ilk soru.** Hazır profilde tekrar rol sorma; rol seçimi yalnız `custom` profilde.
2. Çalışma biçimi: **Tek Ana Ajan** veya **Çoklu Ajan Ekibi**.
3. Tek Ana Ajanda primary otomatik `working-manager`; yönetici tipi sorma. Profil uzmanlarını yine kur ve delegation'ı kapatma. Çoklu Ajanda `hands_on/orchestrator` seçtir.
4. `{{PYTHON}} "{{KIT_ROOT}}/scripts/model_discovery.py" --project-path <proje>` ile mevcut proje için kullanılabilir modelleri bul.
5. Tek Ana Ajanda bir model seçip bütün kurulu rollere uygula. Çoklu Ajanda kurulu rol sayısı kadar bağımsız model cevabı topla; her rolün modeli belirlenmeden ilerleme.
6. Özet + onay.

Bir sorunun cevabı önceki seçimden belliyse tekrar sorma. Çoklu Ajan model adımında ise cevaplar birbirinden bağımsızdır: her kurulu rolün modelini ayrı sor, hiçbir rolün seçimini diğer role otomatik taşıma ve tüm roller cevaplanmadan onaya geçme. Manuel `provider/model` girişi de rol bazındadır.

Windows OpenCode Desktop state'i mevcutsa model discovery önce `%APPDATA%\ai.opencode.desktop\opencode.global.dat` içindeki `model.user[]` kayıtlarından yalnız `visibility == "show"` modellerini alır ve `providerID/modelID` üretir. Bu dosya public/stable API değildir; salt-okunur **BEST-EFFORT** kaynaktır. Desktop state yoksa/boşsa resmî `opencode models` CLI kullanılır. CLI da başarısızsa cache yalnız **UNDOCUMENTED / BEST-EFFORT** fallback'tir ve bütün katalogu körlemesine UI'a taşımamalıdır; yalnız yapılandırıldığı/bağlı olduğu doğrulanabilen provider modellerini kullan. Sonuç boşsa otomatik retry yapma. Kullanıcı açıkça isterse bir normal retry veya bir `--refresh`; yine boşsa elle tam `provider/model` ya da iptal.

Kullanıcı arayüzünde teknik agent ID yerine Türkçe görünen ad kullan: Çalışan Yönetici, Orkestratör, Mimar, Depo Gezgini, Kodlayıcı, Kalite İnceleyici, Görsel QA, Güvenlik İnceleyici.

Özel profil bir capability hapishanesi değildir. Bir uzman kurulu değil diye o görev türünü otomatik reddetme: önce mevcut primary/ajanların native araçları ve yetenekleriyle güvenilir biçimde yapılıp yapılamayacağını değerlendir. Ayrı uzman ancak kalite, bağımsızlık veya context izolasyonu gerçek değer katıyorsa gerekir; güvenilir sonuç onsuz mümkün değilse `/hhc-reconfigure` ile rol eklemeyi öner.

Yerel backend:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path <proje> ...`

Yeniden yapılandırma:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path <proje> --reconfigure ...`

Uzak backend:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/remote_install.py" --repo <git-url> ...`

Installer `config.action=preserved-existing-config` döndürürse mevcut `opencode.jsonc` dosyasının korunduğunu ve HHC'nin `default_agent`, `subagent_depth` veya `compaction` değerlerini değiştirmediğini kullanıcıya açıkça bildir. Kullanıcı dosyalarını izinsiz ezme.
