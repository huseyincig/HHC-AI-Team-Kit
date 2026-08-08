---
name: hhc-project-bootstrap
description: Kullanıcı HHC AI Team Kit'i mevcut veya uzak bir projeye kurmak, Basic/Standard/Powerful çalışma profilini, model dağılımını veya gelişmiş ayarları değiştirmek istediğinde kullan.
---

# HHC Proje Kurulum ve Yeniden Yapılandırma Asistanı

HHC kurulum ve ekip değişikliği varsayılan olarak etkileşimlidir. Kullanıcı açıkça hızlı kurulum istemedikçe sessiz varsayım yapma. Kullanıcıya yalnız gerçekten gerekli kararları sor.

Karar sınıfları:
- **REQUIRED USER DECISION:** çalışma profili, model seçimi, Scout opt-in, browser UI varsa Playwright opt-in.
- **CAN BE INFERRED:** proje özellikleri (`browser_ui`, `desktop_ui`, backend, CLI, library, database, WordPress, containerized, mobile).
- **SMART DEFAULT:** specialist havuzu, skill havuzu, normal primary (`working-manager`), normal team backend (`multi + hands_on`).
- **ADVANCED ONLY:** specialist daraltma (`--roles`), orchestrator primary, legacy single/shared team biçimi, project-characteristic override.

Ana profiller yalnız:
- **Basic**: maliyet/bağlam öncelikli, muhafazakâr paralellik; gerekli specialist profile yüzünden kapanmaz.
- **Standard**: varsayılan dengeli SMART politika.
- **Powerful**: kalite/güvence öncelikli, bağımsız yüksek değerli işlerde daha istekli paralellik ve risk bazlı bağımsız doğrulama; aynı rolü varsayılan çoğaltma yok.

Profil ajan kadrosu değildir. Tüm temel specialist roller normalde erişilebilir kalır. `web-development`, `desktop-development`, `high-assurance`, `custom`, `minimal` yalnız legacy migration adlarıdır; yeni seçenek olarak gösterilmez.

Proje özelliklerini `{{PYTHON}} "{{KIT_ROOT}}/scripts/project_characteristics.py" --project-path <proje>` ile çıkar. Tek proje türü enum'u üretme. `browser_ui` doğrulanırsa Playwright sor; aksi halde sorma. Playwright opt-in/default-off ve yalnız Visual QA scope'unda kalır.

Scout her profile'da opt-in/default-off'tur. Harici/güncel kaynak araştırması için kullanılır; yerel repo keşfi `repository-explorer` alanıdır.

Background subagents HHC tasarımında kullanılabilir kabul edilir. Yalnız parent'ın beklemeden sürdürebileceği, dependency-independent ve file/state conflict üretmeyecek işlerde kullan. Aynı dosyayı değiştiren veya birbirine bağımlı işleri sıralı tut. Aynı rolü varsayılan olarak iki kere çağırma; ikinci review ancak gerçekten bağımsız yeni kanıt üretecek yüksek riskli durumda anlamlıdır. Deterministik PASS ve gerekli kalite kapıları yeterliyse dur.


Model keşfi notu: Windows OpenCode Desktop state'i varsa `%APPDATA%\ai.opencode.desktop\opencode.global.dat` içindeki `model.user[]` kayıtlarından yalnız `visibility == "show"` modeller salt-okunur BEST-EFFORT kaynak olarak değerlendirilebilir. Yoksa resmî `opencode models`, son çare olarak UNDOCUMENTED / BEST-EFFORT cache kullanılır.

Model danışmanı `INCOMPATIBLE` modeli seçtirmez; `WARNING`/UNKNOWN için explicit kullanıcı kararı gerekir. Profile göre modeli sessizce pahalı modele yükseltme. `ROLE → ASSIGNED MODEL` korunur.

Normal kurulumda backend:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path <proje> --team-mode multi --manager-mode hands_on --preset <basic|standard|powerful> ...`

Yeniden yapılandırma:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path <proje> --reconfigure ...`

Uzak backend:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/remote_install.py" --repo <git-url> ...`

Legacy state migration'da rol/model/Scout/Playwright seçimlerini kaybetme. Kullanıcıya eski preset listesini yeniden gösterme.
