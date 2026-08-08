# HHC AI Team Kit

[Türkçe](README.md) | [English](README.en.md)

**Sürüm: 1.2.3**

HHC AI Team Kit, OpenCode projelerine küçük, SMART ve model/sağlayıcı bağımsız bir yapay zekâ yazılım ekibi kurar. OpenCode'un yerleşik ana ajan, alt ajan, Task, skill, command ve permission mekanizmalarını kullanır; ikinci bir görev veya kanıt sistemi kurmaz.

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

Kurulum asistanı çalışma profilini, Scout/Playwright tercihlerini ve rol bazlı model atamalarını sorar. Web/Desktop gibi proje özellikleri mümkün olduğunca depodan otomatik çıkarılır.

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
- **Otomatik proje özellikleri:** Web arayüzü, masaüstü arayüzü, backend, CLI, kütüphane, veritabanı, WordPress, container ve mobil sinyalleri çoklu olarak çıkarılır.
- **Az ajan, az bağlam:** ayrı uzman yalnız gerçek kalite, bağımsızlık veya bağlam yalıtımı değeri sağlıyorsa çağrılır.
- **Rol bazlı model seçimi:** model yetenekleri, bağlam sınırı ve maliyet bilgisi doğrulanabildiği ölçüde değerlendirilir.
- **Yerel / harici araştırma ayrımı:** yerel depo keşfi `repository-explorer`, harici/güncel araştırma OpenCode Scout ile yapılır.
- **İhtiyaç halinde yüklenen skill'ler:** ayrıntılı skill gövdeleri yalnız gerektiğinde devreye girer.
- **Deterministik doğrulama önceliği:** test, derleme, linter, diff ve benzeri güvenilir kanıt yeterliyse gereksiz ikinci LLM görüşü çağrılmaz.
- **Kontrollü paralellik:** bağımsız işler arka planda paralel çalıştırılabilir; bağımlı veya aynı dosyayı değiştiren işler sıralı kalır.
- **İsteğe bağlı Playwright:** yalnız `browser_ui` özelliği doğrulanan projelerde kullanıcı isterse açılır ve `visual-qa` ile sınırlandırılır.
- **MCP varsayılan kapalı:** güvenilir CLI varsa ayrıca MCP kurulmaz.
- **Alt ajan derinliği koruması:** `subagent_depth: 1` korunur.

## SMART Çalışma Mantığı

```text
Kullanıcı
  ↓
Working Manager kısa ön değerlendirme
  ↓
Çalışma profili politikası + proje özellikleri
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

`web-development`, `desktop-development`, `high-assurance`, `minimal` ve `custom` yeni kurulum seçenekleri değildir; yalnız eski kurulumların güvenli migration'ı için tanınır.

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

Örneğin React + .NET + Docker projesi aynı anda `browser_ui`, `backend` ve `containerized` olabilir. Algılama birden fazla repo sinyaline dayanır; zayıf tek ipucu kesin sınıflandırma sayılmaz.

## Roller ve Görevleri

| Kullanıcı adı | Teknik ID | Görev |
|---|---|---|
| **Çalışan Yönetici** | `working-manager` | Küçük/orta işleri doğrudan uygular; gerektiğinde uzman çağırır. Normal kurulumun ana muhatabıdır. |
| **Orkestratör** | `manager` | Uygulama yerine yönlendirme ve kalite kapısına odaklanan alternatif primary ajandır; Advanced Configuration içindir. |
| **Mimar** | `architect` | Gerçek mimari, sözleşme, veri modeli veya büyük sınır değişikliklerini planlar. |
| **Depo Gezgini** | `repository-explorer` | İlgili dosya, sembol, bağımlılık ve testleri minimum bağlamla çıkarır. |
| **Kodlayıcı** | `coder` | Değişikliği uygular ve uygun deterministik kontrolleri çalıştırır. |
| **Kalite İnceleyici** | `qa-reviewer` | Diff, test, kabul ölçütü ve regresyon riskini bağımsız inceler. |
| **Güvenlik İnceleyici** | `security-reviewer` | Auth, izin, veri mutasyonu, ağ yüzeyi, dependency ve benzeri güvenlik sınırlarında devreye girer. |
| **Görsel QA** | `visual-qa` | UI/CSS/layout/responsive/etkileşim değişikliklerini görsel ve tarayıcı kanıtıyla doğrular. |

Normal kullanıcı rol kadrosunu seçmek zorunda değildir. Eski Custom profilin karşılığı artık **Advanced Configuration** altında isteğe bağlı specialist daraltmadır.

## Skill Sistemi

HHC 13 skill'i OpenCode'un ihtiyaç halinde yükleme mekanizmasıyla kullanır:

`task-classification`, `repository-analysis`, `implementation-planning`, `safe-refactoring`, `code-review`, `test-strategy`, `regression-review`, `visual-qa`, `accessibility-review`, `browser-testing`, `security-review`, `release-guardrails`, `changelog-and-documentation`.

Skill gövdeleri her çağrıda bağlama taşınmaz; yalnız ilgili olduğunda yüklenir.

## Model Seçimi

Normal kurulumda kurulu her rol için kullanıcı model seçer. HHC profile göre modeli sessizce daha pahalı bir modele değiştirmez: **ROLE → ASSIGNED MODEL** korunur.

`scripts/model_advisor.py`, models.dev üst verisi erişilebildiğinde araç çağırma, görsel girdi, akıl yürütme, bağlam/çıktı sınırı ve maliyet bilgisini değerlendirir:

- zorunlu yetenek açıkça yoksa **INCOMPATIBLE**,
- bilgi eksik/belirsizse **WARNING**,
- bilinmeyen fiyat/yetenek tahmin edilmez,
- runtime model router veya sessiz premium fallback yoktur.

Advanced Configuration'da tek ortak model kullanılabilir; bu çalışma profilini değiştirmez.

## OpenCode Scout

Scout üç profilde de profile bağlı olmadan **isteğe bağlı ve varsayılan kapalıdır**. Harici dokümantasyon, dependency ve upstream/güncel kaynak araştırması içindir. Yerel repo keşfi `repository-explorer` alanında kalır.

Scout açılırsa modeli ayrıca seçilir. Local repo keşfi ile Scout araştırması gerçekten bağımsızsa arka planda paralel yürütülebilir.

## Playwright ile Web Doğrulaması

Playwright artık `web-development` profiline bağlı değildir. `browser_ui` proje özelliği doğrulanmışsa kullanıcıya opt-in olarak sunulur ve varsayılan kapalıdır.

Açıldığında proje düzeyinde MCP yapılandırması üretilir; `playwright_*` araçları genel olarak kapalı, yalnız `visual-qa` rolünde açıktır.

## Paralellik ve Powerful Koruması

Arka planda alt ajan çalıştırma HHC tasarımında kullanılabilir kabul edilir; ancak yalnız:

- parent'ın beklemeden sürdürebileceği,
- birbirinden bağımsız,
- dosya/state çakışması üretmeyecek

işlerde kullanılır.

Architecture → implementation → test gibi bağımlı işler ve aynı dosyayı değiştiren ajanlar sıralı kalır. Powerful aynı rolü varsayılan olarak iki kez çağırmaz; ikinci inceleme ancak gerçekten bağımsız yeni kanıt üretecek önemli/kritik durumda kullanılır. Deterministik kanıt ve gerekli kalite kapıları geçtiğinde durulur.

## Yeniden Yapılandırma ve Güncelleme

```text
/hhc-reconfigure
```

Profil, model atamaları, Scout, Playwright ve Advanced Configuration ayarlarını değiştirir. Eski profil adlarını yeni yapıya güvenli biçimde taşır.

```text
/hhc-update
```

Mevcut state'i koruyarak yeni kit sürümüne eşitler.

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

`hhc-team.json` artık `profile`, küçük `profile_policy` ve çoklu `project_characteristics` bilgisini de tutar. `subagent_depth: 1` korunur. Kullanıcının mevcut `opencode.jsonc` dosyası sessizce ezilmez.

### Legacy migration

- `minimal` → `basic`
- `standard` → `standard`
- `high-assurance` → `powerful`
- `web-development` → `standard` + `browser_ui`
- `desktop-development` → `standard` + `desktop_ui`
- `custom` → `standard` + eski specialist listesi Advanced Configuration olarak korunur

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
