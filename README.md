# HHC AI Team Kit

**Sürüm: 1.3.6**

HHC AI Team Kit, OpenCode projelerine küçük, SMART ve model/sağlayıcı bağımsız bir yapay zekâ yazılım ekibi kurar. OpenCode'un yerleşik ana ajan, alt ajan, Task, beceri, komut ve izin mekanizmalarını kullanır; ikinci bir görev veya kanıt sistemi kurmaz.

## Hızlı Kurulum

### Önerilen: GitHub üzerinden kurulum

**Windows**

```powershell
git clone https://github.com/huseyincig/HHC-AI-Team-Kit.git
cd HHC-AI-Team-Kit
HHC-KUR.cmd
```

**macOS / Linux**

```bash
git clone https://github.com/huseyincig/HHC-AI-Team-Kit.git
cd HHC-AI-Team-Kit
./HHC-KUR.sh
```

Makine kurulumu tamamlandıktan sonra hedef projeyi OpenCode'da açın:

```text
/hhc-install
```

Kurulum asistanı çalışma profilini ve rol bazlı model atamalarını sorar; Playwright yalnız `browser_ui` doğrulanırsa opt-in sunulur. Scout ise yalnız kullanılan OpenCode runtime gerçekten native `scout` yüzeyini keşfederse isteğe bağlı olarak sorulur. Web/Desktop gibi proje özellikleri mümkün olduğunca depodan otomatik çıkarılır.

> Gereksinimler: Git ve Python 3.9+.

### ZIP ile kurulum

1. GitHub Releases bölümünden güncel ZIP paketini indirin.
2. ZIP'i çıkarın.
3. Windows'ta `HHC-KUR.cmd`, macOS/Linux'ta `./HHC-KUR.sh` çalıştırın.
4. Hedef projede `/hhc-install` çalıştırın.

Ayrıntılar: [KURULUM.md](KURULUM.md)

## Öne Çıkan Özellikler

- **SMART görev yönlendirme:** sabit ajan zinciri yerine görev için gereken en küçük ekip seçilir.
- **3 sade çalışma profili:** Basic, Standard ve Powerful yalnız çalışma politikasını değiştirir; uzmanları profile göre kapatmaz.
- **Otomatik proje özellikleri:** Web arayüzü, masaüstü arayüzü, arka uç, CLI, kütüphane, veritabanı, WordPress, konteyner ve mobil sinyalleri çoklu olarak çıkarılır.
- **Az ajan, az bağlam:** ayrı uzman yalnız gerçek kalite, bağımsızlık veya bağlam yalıtımı değeri sağlıyorsa çağrılır.
- **Rol bazlı model seçimi:** model yetenekleri, bağlam sınırı ve maliyet bilgisi doğrulanabildiği ölçüde değerlendirilir.
- **Yerel / harici araştırma ayrımı:** yerel depo keşfi `repository-explorer`; harici/güncel araştırmanın varsayılan native yolu ana ajan `websearch` + `webfetch` araçlarıdır. Scout yalnız runtime gerçekten sunarsa isteğe bağlı bağlam yalıtımıdır.
- **İhtiyaç halinde yüklenen skill'ler:** ayrıntılı skill gövdeleri yalnız gerektiğinde devreye girer.
- **Deterministik doğrulama önceliği:** test, derleme, linter, diff ve benzeri güvenilir kanıt yeterliyse gereksiz ikinci LLM görüşü çağrılmaz.
- **Kontrollü paralellik:** bağımsız işler yalnız kullanılan OpenCode çalışma zamanı Task aracında `background` yüzeyi gerçekten mevcutsa arka planda paralelleştirilebilir; OpenCode 1.18.15 Desktop/CLI doğrulamasında bu yüzey experimental `OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS=true` ile açılır. HHC flag'i varsayılan zorlamaz; yüzey yoksa güvenli ön plan akışı kullanılır. Bağımlı veya aynı dosyayı değiştiren işler sıralı kalır.
- **Kullanıcı etkileşimi handoff:** HHC specialist talimatları, OAuth/device code, MFA, izin/onay veya başka kullanıcı işlemi gerektiğinde alt ajanın beklemek/retry etmek yerine `USER_ACTION_REQUIRED` ile güvenli URL/kodu Manager’a döndürmesini ister. Specialist'larda native `question` izni kapatılarak kullanıcı soruları parent'a yönlendirilir; bash içindeki harici/interaktif auth akışlarında bu davranış agent instruction seviyesinde best-effort'tur. Manager `WAIT_FOR_USER` olarak kullanıcıya gösterir ve işlem tamamlanınca mümkünse aynı `task_id` oturumunu sürdürür.
- **İsteğe bağlı Playwright:** yalnız `browser_ui` özelliği doğrulanan projelerde kullanıcı isterse açılır ve `visual-qa` ile sınırlandırılır.
- **MCP varsayılan kapalı:** güvenilir CLI varsa ayrıca MCP kurulmaz.
- **Alt ajan derinliği koruması:** `subagent_depth: 1` korunur. `compaction.auto=true` ve HHC tarafından açıkça ayarlanan `prune=true` kullanılır; ancak budama etkisi OpenCode çalışma zamanı/sürümüne bağlıdır ve kayıpsız bir garanti olarak yorumlanmamalıdır.

## HHC Envanteri

| Bileşen | Adet |
|---|---:|
| Çalışma profili | **3** |
| HHC rolü | **8** |
| HHC skill'i | **13** |
| HHC paket komutu | **6** (4 bootstrap + 2 proje komutu) |
| Proje özelliği | **9** |
| OpenCode Scout entegrasyonu | **1** (çalışma zamanı desteğine bağlı) |
| Opsiyonel MCP | **1 — Playwright** |

HHC sistem komutları `/hhc-install`, `/hhc-reconfigure`, `/hhc-update`, `/hhc-status`; proje-ekip komutları `/hhc-team-status` ve `/hhc-team-review` olarak aynı `hhc-` namespace'i altında tutulur. Bu **paket envanteri** sayımıdır. OpenCode 1.18.15 runtime command catalog ayrıca 13 skill'i `source: skill` olarak slash-command yüzeyine eklediği için kurulu projede 2 explicit proje komutu + 13 skill = 15 HHC isimli runtime catalog girdisi görülebilir; bu full skill body'lerinin başlangıç context'ine yüklendiği anlamına gelmez.

## SMART Çalışma Mantığı

```text
Kullanıcı
  ↓
Working Manager kısa ön değerlendirme
  ↓
Çalışma profili politikası
  ↓
Gerekli en küçük uzman seti
  ↓
Role atanmış uygun model
  ↓
Gerekirse Scout / QA / Security / Visual QA
  ↓
Deterministik ve uzman kanıtı
  ↓
Yeterli kanıt → DUR
```

**SMART, daha fazla ajan demek değildir.** Amaç doğru görevi doğru uzmanla çözmek, gereksiz soru/LLM çağrısı/bağlam tüketimini azaltmak ve yeterli kanıt oluşunca durmaktır.

## Çalışma Profilleri

Profil artık ajan kadrosu değildir. Üç profilde de temel uzmanlar erişilebilir kalır; fark, uzman çağırma, paralellik ve doğrulama yoğunluğudur.

| Profil | Ne zaman? | Davranış |
|---|---|---|
| **Basic** | Maliyet ve bağlam ekonomisi öncelikliyse | Uzman çağırma eşiği yüksek, paralellik muhafazakâr, ikinci görüş yalnız kritik durumda. Gerekli uzman yine çağrılabilir. |
| **Standard** | Çoğu proje için | **Varsayılan ve önerilen.** Minimum gerekli ekip, risk bazlı QA/Security/Visual QA, bağımsız işlerde kontrollü paralellik. |
| **Powerful** | Kalite/güvence öncelikliyse | Uzman ve bağımsız doğrulama eşiği daha düşük; bağımsız yüksek değerli işler daha istekli paralelleştirilir. Her ajanı çalıştırmaz, aynı rolü varsayılan çoğaltmaz. |

`web-development`, `desktop-development`, `high-assurance`, `minimal` ve `custom` yeni kurulum seçenekleri değildir; yalnız eski kurulumların güvenli geçişi için tanınır.

## Proje Özellikleri

HHC tek bir “proje türü” seçmek yerine birden fazla özelliği aynı anda algılayabilir:

- `browser_ui`
- `desktop_ui`
- `backend`
- `cli`
- `library`
- `database`
- `wordpress`
- `containerized`
- `mobile`

Örneğin React + .NET + Docker projesi aynı anda `browser_ui`, `backend` ve `containerized` olabilir. Algılama birden fazla repo sinyaline dayanır; zayıf tek ipucu kesin sınıflandırma sayılmaz. Bu bilgiler kurulum durumu ve Playwright uygunluğu gibi seçimlerde kullanılır; her görevde Manager istemine statik bağlam olarak eklenmez. Manager gerektiğinde güncel depo kanıtını doğrudan inceler.

## Roller ve Görevleri

| Kullanıcı adı | Teknik ID | Görev |
|---|---|---|
| **Çalışan Yönetici** | `working-manager` | Küçük/orta işleri doğrudan uygular; gerektiğinde uzman çağırır. Normal kurulumun ana muhatabıdır. |
| **Orkestratör** | `manager` | Uygulama yerine yönlendirme ve kalite kapısına odaklanan alternatif ana ajandır; Gelişmiş Yapılandırma içindir. |
| **Mimar** | `architect` | Gerçek mimari, sözleşme, veri modeli veya büyük sınır değişikliklerini planlar. |
| **Depo Gezgini** | `repository-explorer` | İlgili dosya, sembol, bağımlılık ve testleri minimum bağlamla çıkarır. |
| **Kodlayıcı** | `coder` | Değişikliği uygular ve uygun deterministik kontrolleri çalıştırır. |
| **Kalite İnceleyici** | `qa-reviewer` | Diff, test, kabul ölçütü ve regresyon riskini bağımsız inceler. |
| **Güvenlik İnceleyici** | `security-reviewer` | Kimlik doğrulama/yetkilendirme, izin, veri değişikliği, ağ yüzeyi, bağımlılık ve benzeri güvenlik sınırlarında devreye girer. |
| **Görsel QA** | `visual-qa` | Arayüz/CSS/yerleşim/farklı ekran boyutlarına uyum/etkileşim değişikliklerini görsel ve tarayıcı kanıtıyla doğrular. |

Normal kullanıcı rol kadrosunu seçmek zorunda değildir. Eski Custom profilin karşılığı artık **Gelişmiş Yapılandırma** altında isteğe bağlı uzman daraltmadır.

## Skill Sistemi

HHC'nin 13 skill'i `hhc-` namespace'i altında OpenCode'un ihtiyaç halinde yükleme mekanizmasıyla kullanılır.

| Skill ID | Ne işe yarar? |
|---|---|
| `hhc-task-classification` | Görev kapsamı, risk, belirsizlik ve gereken uzmanlığı değerlendirir. |
| `hhc-repository-analysis` | İlgili dosya, sembol, bağımlılık ve test yüzeyini çıkarır. |
| `hhc-implementation-planning` | Gerçek çok adımlı işler için en küçük uygulanabilir planı kurar. |
| `hhc-safe-refactoring` | Davranışı koruyan yeniden düzenlemeyi güvenli adımlarla yürütür. |
| `hhc-test-strategy` | Değişiklik için minimum yeterli deterministik doğrulamayı seçer. |
| `hhc-code-review` | Diff, davranış, edge-case ve abstraction risklerini inceler. |
| `hhc-regression-review` | Komşu davranışlarda regresyon riskini kontrol eder. |
| `hhc-security-review` | Gerçek güvenlik sınırı etkilendiğinde veri/izin/saldırı yüzeyini inceler. |
| `hhc-visual-qa` | Arayüz değişikliklerini görsel ve tarayıcı kanıtıyla doğrular. |
| `hhc-accessibility-review` | Klavye, odak, etiket ve temel erişilebilirlik davranışlarını inceler. |
| `hhc-browser-testing` | Gerçek tarayıcı akışlarını hedefli biçimde test eder. |
| `hhc-release-guardrails` | Sürüm/dağıtım öncesi gerekli güvenlik kapılarını uygular. |
| `hhc-changelog-and-documentation` | Kullanıcıyı etkileyen değişikliklerin dokümantasyonunu tutarlı tutar. |

Skill gövdeleri her çağrıda bağlama taşınmaz; yalnız ilgili olduğunda yüklenir.

## Model Seçimi

Normal kurulumda kurulu her rol için kullanıcı model seçer. HHC profile göre modeli sessizce daha pahalı bir modele değiştirmez: **ROLE → ASSIGNED MODEL** korunur.

`scripts/model_advisor.py`, models.dev üst verisi erişilebildiğinde araç çağırma, görsel girdi, akıl yürütme, bağlam/çıktı sınırı ve maliyet bilgisini değerlendirir:

- zorunlu yetenek açıkça yoksa **INCOMPATIBLE**,
- bilgi eksik/belirsizse **WARNING**,
- bilinmeyen fiyat/yetenek tahmin edilmez,
- çalışma zamanı model yönlendiricisi veya pahalı modele sessiz geri dönüş yoktur.

Gelişmiş Yapılandırma'da tek ortak model kullanılabilir; bu çalışma profilini değiştirmez.

## OpenCode Scout

Scout üç profilde de profile bağlı olmadan **isteğe bağlı ve varsayılan kapalıdır**. Harici dokümantasyon, bağımlılık ve üst kaynak/güncel kaynak araştırması içindir. Yerel repo keşfi `repository-explorer` alanında kalır.

Harici/güncel araştırmanın varsayılan native yolu `websearch` + `webfetch`tir. Scout yalnız ek bağlam yalıtımı sağlayabilecek geniş araştırmalarda ve çalışma zamanı onu gerçekten çağrılabilir native alt ajan olarak sunarsa değerlendirilebilir. HHC aynı adlı custom agent üretmez ve `agent.scout` model override'ı yazmaz. Resmi docs Scout'u yerleşik alt ajan olarak tanımlasa da HHC tarafından test edilen OpenCode Desktop **1.18.15** ve standalone CLI **1.18.15** gerçek agent discovery yüzeylerinde Scout bulunmamıştır; bu nedenle yüzey yoksa kullanıcıya Scout sorusu da gösterilmemelidir. Yerel repo keşfi `repository-explorer` alanında kalır.

## Playwright ile Web Doğrulaması

Playwright artık `web-development` profiline bağlı değildir. `browser_ui` proje özelliği doğrulanmışsa kullanıcıya opt-in olarak sunulur ve varsayılan kapalıdır.

Açıldığında proje düzeyinde MCP yapılandırması üretilir; `playwright_*` araçları genel olarak kapalı, yalnız `visual-qa` rolünde açıktır.

## Paralellik ve Powerful Koruması

Arka planda alt ajan çalıştırma HHC tasarımında kullanılabilir kabul edilir; ancak yalnız:

- parent'ın beklemeden sürdürebileceği,
- birbirinden bağımsız,
- dosya/durum çakışması üretmeyecek

işlerde kullanılır.

Architecture → implementation → test gibi bağımlı işler ve aynı dosyayı değiştiren ajanlar sıralı kalır. Powerful aynı rolü varsayılan olarak iki kez çağırmaz; ikinci inceleme ancak gerçekten bağımsız yeni kanıt üretecek önemli/kritik durumda kullanılır. Deterministik kanıt ve gerekli kalite kapıları geçtiğinde durulur.

### HHC komutları

| Komut | Katman | İşlev |
|---|---|---|
| `/hhc-install` | Sistem | HHC'yi hedef projeye kurar. |
| `/hhc-reconfigure` | Sistem | Profil, model ve gelişmiş ayarları yeniden yapılandırır. |
| `/hhc-update` | Sistem | HHC-managed proje dosyalarını güncel kit ile eşitler. |
| `/hhc-status` | Sistem | HHC sürümü, profil, roller, modeller, Scout ve Playwright yapılandırmasını salt-okunur raporlar. |
| `/hhc-team-status` | Ekip | Aktif proje/görev çalışma durumunu Git, yapılacaklar ve test kanıtlarından kısa özetler. |
| `/hhc-team-review` | Ekip | Mevcut değişikliği `qa-reviewer` ile bağımsız incelemeye gönderir (`subtask: true`). |

`/hhc-status` ile `/hhc-team-status` aynı iş değildir: ilki HHC yapılandırma durumunu, ikincisi aktif proje/görev çalışma durumunu gösterir.

## Yeniden Yapılandırma ve Güncelleme

```text
/hhc-reconfigure
```

Profil, model atamaları, Scout, Playwright ve Gelişmiş Yapılandırma ayarlarını değiştirir. Eski profil adlarını yeni yapıya güvenli biçimde taşır.

```text
/hhc-update
```

Mevcut durum bilgisini koruyarak yeni kit sürümüne eşitler.

```text
/hhc-status
```

Mevcut HHC yapılandırma durumunu salt-okunur raporlar (sürüm, profil, roller, modeller, Scout, Playwright, MCP).

## Teknik Ayrıntılar

```text
.opencode/
  agents/
  skills/
  commands/
  hhc-team.json
  opencode.jsonc
opencode.jsonc
```

`hhc-team.json` artık `profile`, küçük `profile_policy` ve çoklu `project_characteristics` bilgisini de tutar. `subagent_depth: 1` korunur. `compaction.auto=true` ve HHC tarafından açıkça ayarlanan `prune=true` kullanılır; ancak budama etkisi OpenCode çalışma zamanı/sürümüne bağlıdır ve kayıpsız bir garanti olarak yorumlanmamalıdır. Kullanıcının mevcut `opencode.jsonc` dosyası sessizce ezilmez.

### Eski yapılandırmalardan geçiş

- `minimal` → `basic`
- `standard` → `standard`
- `high-assurance` → `powerful`
- `web-development` → `standard` + `browser_ui`
- `desktop-development` → `standard` + `desktop_ui`
- `custom` → `standard` + eski uzman listesi Gelişmiş Yapılandırma olarak korunur

## Test ve Doğrulama

```bash
python scripts/validate.py
python -m pytest -q
python scripts/release-build.py
```

## Katkı, Güvenlik ve Lisans

- [KURULUM.md](KURULUM.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SECURITY.md](SECURITY.md)
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- [LICENSE](LICENSE)
