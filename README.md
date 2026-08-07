# HHC AI Team Kit

**Sürüm: 1.1.0-rc.21**

HHC AI Team Kit, OpenCode projelerine küçük ve model/sağlayıcı bağımsız bir yapay zekâ yazılım ekibi kurar. OpenCode'un native primary/subagent, Task, skill, command ve permission mekanizmalarını kullanır; ikinci bir görev/kanıt framework'ü kurmaz.

## Kurulum asistanı

Makineye bir kez kurduktan sonra OpenCode içinde `/hhc-install` çalıştırılır. Yeni sihirbazın karar sırası bilinçli olarak kısadır:

1. **Profil** — Minimal / Standard / Web Development / Desktop Development / High Assurance / Özel
2. Yalnız **Özel** profilde uzman rolleri
3. **Tek Ana Ajan / Çoklu Ajan Ekibi**
4. Çoklu ajanda yönetici tipi
5. **Scout** kullanımı: Evet / Hayır (varsayılan Hayır)
6. Mevcut proje için kullanılabilir modeller
7. Tek Ana Ajanda bir HHC ekip modeli; Çoklu Ajanda doğrudan Türkçe rol → model eşlemesi
8. Scout açıksa ayrıca **Scout / Dış Araştırma** modeli
9. Son özet ve **Kur** onayı

Hazır profil seçildiyse yeniden rol sorulmaz. Çoklu Ajan model adımında kurulu her rolün modeli ayrı ayrı belirlenir; bir rolün seçimi diğer rollere otomatik taşınmaz.

## Tek Ana Ajan

**Tek Ana Ajan**, sistemde yalnız bir agent dosyası olduğu anlamına gelmez. Kullanıcının tek ana muhatabı **Çalışan Yönetici (`working-manager`)** olur; seçilen profilin uzman rolleri yine kurulur ve gerektiğinde OpenCode'un native Task/subagent mekanizmasıyla çağrılabilir.

Tek Ana Ajanda yönetici tipi sorulmaz. Bir model seçilir ve bütün kurulu HHC rollerine uygulanır.

## Çoklu Ajan Ekibi

Çoklu Ajanda yönetici **Çalışan Yönetici** veya **Orkestratör** olabilir. Kurulu her rol için bağımsız model seçimi zorunludur; tüm rollerin modeli belirlenmeden kurulum özetine geçilmez.

Kullanıcıya görünen adlar Türkçedir: Çalışan Yönetici, Orkestratör, Mimar, Depo Gezgini, Kodlayıcı, Kalite İnceleyici, Görsel QA, Güvenlik İnceleyici. Teknik agent ID'leri backend/config tarafında kalır.

## Özel profil ve capability fallback

Özel profil bir capability hapishanesi değildir. Örneğin yalnız Çalışan Yönetici + Kodlayıcı kurulmuşsa basit dosya sayma/arama işi için Depo Gezgini zorunlu sayılmaz; mevcut agent native `list/glob/grep/read/bash` araçlarıyla güvenilir biçimde yapabiliyorsa görevi tamamlar. Aynı prensip basit görsel doğrulama, test veya küçük mimari/güvenlik kontrolleri için de geçerlidir.

Uzman rol ancak kalite, bağımsızlık veya context izolasyonu gerçek değer katıyorsa çağrılır. Uzman olmadan güvenilir sonuç mümkün değilse `/hhc-reconfigure` ile ilgili rolün eklenmesi önerilebilir.

## Native dış araştırma ve kontrollü paralellik

Yerel repository keşfi HHC `repository-explorer` rolünde kalır. Harici dokümantasyon, dependency kaynağı veya upstream implementasyon doğrulaması gerektiğinde manager, mevcut OpenCode runtime native `scout` subagent'ını sunuyorsa onu on-demand kullanabilir; HHC ayrı researcher/scout rolü veya MCP katmanı kurmaz. Scout görevi güncel ve birincil kaynak odaklı, dar bağlamlı ve kısa sonuçlu verilir.

Scout proje bazında **opt-in**'dir ve varsayılan kapalıdır. Kullanıcı Scout'u açarsa model ayrıca seçilir ve native `scout` agent override'ına açıkça yazılır; böylece pahalı manager modelinin sessizce devralınmasına bırakılmaz. Scout kapalıysa HHC manager Task iznini `deny` üretir ve Scout model/config override'ı oluşturmaz. Ağır `team-review` komutu primary context'i kirletmemek için zaten `subtask: true` kullanır; kısa `team-status` aynı oturum bağlamında kalır. Native Task aracı experimental `background` seçeneğini gerçekten sunuyorsa manager yalnız bağımsız, çakışmayan read-only işleri background çalıştırabilir; seçenek yoksa aynı görevler normal foreground akışında devam eder. HHC experimental flag'i kendiliğinden açmaz.

## Model keşfi

Windows OpenCode Desktop kullanılıyorsa HHC önce `%APPDATA%\ai.opencode.desktop\opencode.global.dat` içindeki `model.user[]` kayıtlarını okur. Yalnız `visibility == "show"` olan kayıtlar `providerID/modelID` biçiminde model seçimine alınır. Bu dosya OpenCode'un public/stable API'si olmadığı için salt-okunur **BEST-EFFORT** kaynaktır.

Desktop state yoksa veya görünür model içermiyorsa **hedef proje dizininde** resmî:

```text
opencode models
```

komutuna geçilir. CLI sonucu da alınamazsa yerel OpenCode cache adayları yalnız **UNDOCUMENTED / BEST-EFFORT** fallback olarak kullanılır; cache'deki bütün katalog körlemesine UI'a taşınmaz, yalnız config veya resmî `opencode auth list` görünümüyle etkinliği doğrulanabilen provider'ların modelleri dikkate alınır.

`opencode models --refresh` yalnız kullanıcı açıkça isterse bir kez çalıştırılır; otomatik değildir.

## Sonradan değiştirme

```text
/hhc-reconfigure
```

aynı karar ağacını kullanır. Eski rc.16 `single + solo-agent` state'i okunabilir; kullanıcı yeniden yapılandırdığında HHC-owned eski `solo-agent.md` güvenle kaldırılıp yeni `working-manager + profil uzmanları` düzenine geçirilebilir.

## Hedef projeye ne kurulur?

```text
.opencode/
  agents/
  skills/
  commands/
  hhc-team.json
  opencode.jsonc   # yalnız Scout açıksa HHC-owned minimal Scout model override
opencode.jsonc
```

`subagent_depth: 1` korunur: primary uzman subagent çağırabilir; uzmanların kendi alt ekiplerini açması engellenir.

## Adaptif orkestrasyon

Profil sabit pipeline değil kullanılabilir uzman havuzudur. HHC minimum yeterli ekiple başlar, ihtiyaçla genişler ve yeterli kanıt oluşunca durur. Deterministik test/build/lint/LSP ile doğrulanabileni gereksiz ikinci LLM görüşüyle tekrarlamaz; skill gövdeleri native on-demand mekanizmasıyla gerektiğinde yüklenir.

## İlk makine kurulumu

Windows:

```text
HHC-KUR.cmd
```

macOS/Linux:

```text
./HHC-KUR.sh
```

Global komutlar:

```text
/hhc-install
/hhc-install-remote
/hhc-reconfigure
```

## Mevcut OpenCode config ve platform notu

Projede kök `opencode.jsonc` zaten varsa HHC onu sessizce ezmez. Scout açıksa HHC yalnız `.opencode/opencode.jsonc` altında minimal `agent.scout.model` override katmanı üretir; mevcut kullanıcı `.opencode/opencode.jsonc` dosyasıyla çakışırsa güvenli olmak için kurulumu durdurur ve dosyayı ezmez. Config kaynaklarının merge edilmesi güncel OpenCode runtime davranışına dayanır. Config yoksa HHC kökte küçük varsayılanı oluşturur; kurulum sonucu config'in korunduğunu açıkça bildirir.

Windows üzerindeki OpenCode Desktop ile WSL içinde `opencode serve` çalıştırılan backend farklı kullanıcı ortamlarıdır. WSL backend kullanılıyorsa HHC global bootstrap'ı WSL içinde de ayrıca kurulmalıdır. Linux/container testleri native Windows Desktop testi sayılmaz.

## MCP

HHC varsayılan olarak MCP sunucusu kurmaz. Yalnız gerçek ihtiyaç varsa OpenCode'un native MCP yapılandırması kullanılmalıdır.

## Geliştirme

```bash
python scripts/validate.py
python -m pytest -q
python scripts/release-build.py
```


## SMART model seçimi

Kurulum sihirbazı mevcut OpenCode model keşfini korur; seçim aşamasında `scripts/model_advisor.py` ile models.dev metadata'sı erişilebilirse role göre capability/context/maliyet bilgisi gösterir. Zorunlu capability açıkça yoksa model uyumsuz kabul edilir; metadata eksik veya doğrulanamıyorsa kurulum kırılmaz ve seçim WARNING/UNKNOWN olarak kullanıcı onayına bırakılır. HHC runtime'da modeli otomatik değiştiren premium fallback/router oluşturmaz; seçilen rol önceden atanmış modeli kullanır.

Başlıca zorunlu kontroller: manager/working-manager/repository-explorer/coder için tool calling; visual-qa için tool calling + image input. Metadata provider'a göre değişebildiği için bilinmeyen alanlar tahmin edilmez. Fiyat varsa provider metadata'sından gösterilir, yoksa `bilinmiyor` kabul edilir.

## Web Development ve Playwright MCP

`web-development` profilinde Microsoft Playwright MCP **opt-in** sunulur ve varsayılan kapalıdır. Etkinleştirilirse HHC project-local MCP config üretir, `playwright_*` araçlarını global olarak deny eder ve yalnız `visual-qa` agent'ında allow override kullanır. Paket şu an doğrulanan `@playwright/mcp@0.0.78` sürümünü pinler. Node.js 18+ gerekir.

Chrome DevTools veya ikinci bir browser MCP varsayılan olarak eklenmez. PHP, Composer, WP-CLI, MySQL/MariaDB, Docker, Git, PHPUnit, PHPCS/WPCS, npm ve curl gibi deterministik CLI araçları MCP'ye çevrilmez. İlke: **güvenilir CLI varsa varsayılan MCP ekleme**.
