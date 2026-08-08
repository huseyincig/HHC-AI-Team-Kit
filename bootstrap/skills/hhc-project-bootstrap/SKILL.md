---
name: hhc-project-bootstrap
description: Kullanıcı HHC AI Team Kit'i mevcut veya uzak bir projeye kurmak, Basic/Standard/Powerful çalışma profilini, model dağılımını veya gelişmiş ayarları değiştirmek istediğinde kullan.
---

# HHC Proje Kurulum ve Yeniden Yapılandırma Asistanı

HHC kurulum ve ekip değişikliği varsayılan olarak etkileşimlidir. Kullanıcı açıkça hızlı kurulum istemedikçe sessiz varsayım yapma. Kullanıcıya yalnız gerçekten gerekli kararları sor.

Karar sınıfları:
- **REQUIRED USER DECISION:** çalışma profili, model seçimi, browser UI varsa Playwright opt-in. Scout yalnız runtime discovery gerçekten native Scout yüzeyi gösterirse koşullu bir karar olur; aksi halde kullanıcıya sorulmaz.
- **CAN BE INFERRED:** proje özellikleri (`browser_ui`, `desktop_ui`, `backend`, `cli`, `library`, `database`, `wordpress`, `containerized`, `mobile`).
- **SMART DEFAULT:** uzman havuzu, skill havuzu, normal ana ajan (`working-manager`), normal team arka uç (`multi + hands_on`).
- **ADVANCED ONLY:** uzman daraltma (`--roles`), orchestrator ana ajan, eski single/shared team biçimi, project-characteristic override.

Ana profiller yalnız:
- **Basic**: maliyet/bağlam öncelikli, muhafazakâr paralellik; gerekli uzman profile yüzünden kapanmaz.
- **Standard**: varsayılan dengeli SMART politika.
- **Powerful**: kalite/güvence öncelikli, bağımsız yüksek değerli işlerde daha istekli paralellik ve risk bazlı bağımsız doğrulama; aynı rolü varsayılan çoğaltma yok.

Profil ajan kadrosu değildir. Tüm temel uzman roller normalde erişilebilir kalır. `web-development`, `desktop-development`, `high-assurance`, `custom`, `minimal` yalnız eski geçiş adlarıdır; yeni seçenek olarak gösterilmez.

Proje özelliklerini `{{PYTHON}} "{{KIT_ROOT}}/scripts/project_characteristics.py" --project-path <proje>` ile çıkar. Tek proje türü enum'u üretme. `browser_ui` doğrulanırsa Playwright sor; aksi halde sorma. Playwright opt-in/default-off ve yalnız Visual QA scope'unda kalır.

Harici/güncel kaynak araştırmasında varsayılan native yol `websearch` + `webfetch`tir. Scout default-off kalır ve yalnız çalışma zamanı native Scout'u gerçekten keşfederse isteğe bağlı bağlam yalıtımı için sorulur; yüzey yoksa Scout sorusu gösterilmez. Yerel repo keşfi `repository-explorer` alanıdır.

Arka planda çalışan alt ajan yüzeyi experimental ve capability-gated kabul edilir. OpenCode 1.18.15 Desktop/CLI doğrulamasında `OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS=true` ile Task schema'ya eklenir; HHC varsayılan olarak bu flag'i açmaz. Yüzey gerçekten mevcutsa yalnız ana ajanın beklemeden sürdürebileceği, bağımlılıktan bağımsız ve dosya/durum çakışması üretmeyecek işlerde kullan. Aynı dosyayı değiştiren veya birbirine bağımlı işleri sıralı tut. Aynı rolü varsayılan olarak iki kere çağırma; ikinci inceleme ancak gerçekten bağımsız yeni kanıt üretecek yüksek riskli durumda anlamlıdır. Deterministik PASS ve gerekli kalite kapıları yeterliyse dur.


Model keşfi notu: Windows OpenCode Desktop durum verisi varsa `%APPDATA%\ai.opencode.desktop\opencode.global.dat` içindeki `model.user[]` kayıtlarından yalnız `visibility == "show"` modeller salt-okunur EN İYİ ÇABA kaynak olarak değerlendirilebilir. Yoksa resmî `opencode models`, son çare olarak BELGELENMEMİŞ / EN İYİ ÇABA önbellek kullanılır.

Model danışmanı `INCOMPATIBLE` modeli seçtirmez; `WARNING`/UNKNOWN için açık kullanıcı kararı gerekir. Profile göre modeli sessizce pahalı modele yükseltme. `ROLE → ASSIGNED MODEL` korunur.

Normal kurulumda arka uç:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path <proje> --team-mode multi --manager-mode hands_on --preset <basic|standard|powerful> ...`

Yeniden yapılandırma:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path <proje> --reconfigure ...`

Eski state geçiş'da rol/model/Scout/Playwright seçimlerini kaybetme. Kullanıcıya eski preset listesini yeniden gösterme.
