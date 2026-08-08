# Kurulum

[README](README.md)

## 1. Önerilen: GitHub üzerinden makine kurulumu

### Windows

```powershell
git clone https://github.com/huseyincig/HHC-AI-Team-Kit.git
cd HHC-AI-Team-Kit
HHC-KUR.cmd
```

### macOS / Linux

```bash
git clone https://github.com/huseyincig/HHC-AI-Team-Kit.git
cd HHC-AI-Team-Kit
./HHC-KUR.sh
```

Gereksinimler: Git ve Python 3.9+.

## 2. Alternatif: ZIP ile kurulum

1. Güncel Release ZIP'ini indirin.
2. ZIP'i çıkarın.
3. Windows'ta `HHC-KUR.cmd`, macOS/Linux'ta `./HHC-KUR.sh` çalıştırın.

Makine kurulumu şu global OpenCode komutlarını ekler:

- `/hhc-install`
- `/hhc-reconfigure`
- `/hhc-update`
- `/hhc-status`

## 3. Hedef projeye kurulum

Projeyi OpenCode'da açın:

```text
/hhc-install
```

### Adım 1 — Çalışma profili

Yalnız üç profil vardır:

- **Basic:** maliyet/bağlam öncelikli; uzman ve paralellik eşiği yüksektir.
- **Standard:** **varsayılan/önerilen** dengeli SMART çalışma.
- **Powerful:** kalite/güvence öncelikli; bağımsız yüksek değerli işlerde daha istekli paralellik ve doğrulama.

Profil rol kadrosu değildir. Üçünde de temel uzman roller erişilebilir kalır.

### Adım 2 — Proje özellikleri otomatik algılanır

Kullanıcıdan Web/Desktop seçimi istenmez. HHC repo sinyallerinden çoklu özellik çıkarır:

`browser_ui`, `desktop_ui`, `backend`, `cli`, `library`, `database`, `wordpress`, `containerized`, `mobile`.

Bir proje aynı anda birden fazla özelliğe sahip olabilir.

### Adım 3 — Scout

Harici/güncel araştırmanın varsayılan native yolu ana ajanın `websearch` + `webfetch` araçlarıdır. Scout profile bağlı değildir ve yalnız çalışma zamanı native `scout` yüzeyini gerçekten keşfederse isteğe bağlı bağlam yalıtımı olarak sorulur; yüzey yoksa kurulum Scout sorusu göstermez ve `--scout disabled` kullanır. HHC `agent.scout` yazarak aynı adlı custom agent üretmez ve Scout modelini override etmez. Resmi docs Scout'u yerleşik alt ajan olarak tanımlasa da test edilen OpenCode Desktop **1.18.15** ve standalone CLI **1.18.15** gerçek agent discovery yüzeylerinde Scout bulunmamıştır.

### Adım 4 — Playwright

Yalnız `browser_ui` doğrulanırsa **Playwright MCP kullanılsın mı?** sorulur. Varsayılan **Hayır**.

Açıldığında Playwright proje-local kurulur; `playwright_*` araçları yalnız `visual-qa` rolüne açılır. Browser UI yoksa normal kurulum bu soruyu göstermez.

### Adım 5 — Modeller

Model keşfi ve `model_advisor.py` kullanılarak kurulu roller için model seçilir. Normal akışta her rolün modeli ayrı seçilir; profile göre otomatik pahalı model yükseltmesi yapılmaz.

Scout açıksa model HHC tarafından ayrıca seçilmez; native Scout hangi çalışma zamanında sunuluyorsa o çalışma zamanının model davranışı kullanılır.

### Normal ana ajan ve ekip davranışı

Yeni normal UX'te **Tek Ana Ajan / Çoklu Ajan** ayrı ana soru değildir. Varsayılan çalışma:

- ana ajan: **Çalışan Yönetici (`working-manager`)**
- arka uç çalışma biçimi: `multi + hands_on`
- bütün temel uzman roller erişilebilir
- hangi uzmanın çağrılacağı SMART tarafından görev bazında belirlenir

Eski `single|multi`, ortak model ve salt orkestratör ana ajan seçenekleri yalnız geçiş/Gelişmiş Yapılandırma amacıyla arka uçta korunur.

## 4. HHC envanteri

### Profiller

| Profil | Öncelik | Uzman çağırma | Paralellik | Bağımsız inceleme |
|---|---|---|---|---|
| **Basic** | Maliyet/bağlam | Yüksek eşik | Muhafazakâr | Yalnız kritik |
| **Standard** | Dengeli | Normal eşik | Yalnız bağımsız işler | Risk bazlı |
| **Powerful** | Kalite/güvence | Daha düşük eşik | Bağımsız yüksek değerli işlerde daha istekli | Önemli/kritik |

### Roller

| Teknik ID | Görev |
|---|---|
| `working-manager` | Küçük/orta işleri doğrudan uygular, gerektiğinde uzman çağırır. |
| `manager` | Salt-okunur orkestrasyon ve kalite kapısı. |
| `architect` | Gerçek mimari kararları planlar. |
| `repository-explorer` | Yerel repo keşfi yapar. |
| `coder` | Uygulamayı yapar ve deterministik kontrolleri çalıştırır. |
| `qa-reviewer` | Diff/test/regresyon incelemesi yapar. |
| `security-reviewer` | Gerçek güvenlik sınırlarını inceler. |
| `visual-qa` | Görsel/tarayıcı doğrulaması yapar. |

### HHC skill'leri

`hhc-task-classification`, `hhc-repository-analysis`, `hhc-implementation-planning`, `hhc-safe-refactoring`, `hhc-test-strategy`, `hhc-code-review`, `hhc-regression-review`, `hhc-security-review`, `hhc-visual-qa`, `hhc-accessibility-review`, `hhc-browser-testing`, `hhc-release-guardrails`, `hhc-changelog-and-documentation`.

### HHC komutları

Buradaki komut sayımı paket envanteridir (4 bootstrap + 2 proje komutu). OpenCode 1.18.15 runtime ayrıca 13 HHC skill'ini `source: skill` olarak command catalog/slash yüzeyinde gösterebilir; bu skill body'lerinin başlangıç context'ine sürekli yüklendiği anlamına gelmez.

**Sistem:** `/hhc-install`, `/hhc-reconfigure`, `/hhc-update`, `/hhc-status`

**Ekip:** `/hhc-team-status`, `/hhc-team-review`

`/hhc-status` HHC yapılandırmasını; `/hhc-team-status` aktif proje/görev çalışma durumunu raporlar. `/hhc-team-review` mevcut değişikliği `qa-reviewer` alt ajanına `subtask: true` ile gönderir.

### Proje özellikleri

`browser_ui`, `desktop_ui`, `backend`, `cli`, `library`, `database`, `wordpress`, `containerized`, `mobile`.

## 5. Gelişmiş Yapılandırma

Eski **Custom** profil artık ana profil değildir.

İleri düzey kullanıcı açıkça isterse:

- uzman havuzunu `--roles` ile daraltabilir,
- ana ajanı `manager`/orkestratör yapabilir,
- tek ortak model kullanabilir,
- proje özelliğine explicit override ekleyebilir.

Bu ayarlar Basic/Standard/Powerful profilinin yerine geçmez.

## 6. Paralellik ve arka planda çalışma

HHC, alt ajanları yalnız kullanılan OpenCode Task araç yüzeyi `background` seçeneğini gerçekten sunuyorsa arka planda çalıştırır. OpenCode 1.18.15 Desktop/CLI doğrulamasında bu yüzey experimental `OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS=true` ile açılır; HHC bu flag'i varsayılan olarak zorla etkinleştirmez. Ana ajanın beklemeden sürdürebileceği, bağımsız ve dosya/durum çakışması üretmeyecek işler paralelleştirilir; yüzey yoksa veya çalışma zamanı reddederse ön plan akışı kullanılır. Arka plan yüzeyi etkin olduğunda gereksiz polling yapılmaz.

**Kullanıcı etkileşimi:** Bir alt ajan OAuth/device code, MFA, izin/onay, credential girişi veya başka bir dış kullanıcı işlemi gerektiren noktaya gelirse kendi oturumunda beklemek veya otomatik retry yapmak yerine `STATUS: USER_ACTION_REQUIRED` ile Manager’a dönmelidir. Manager gerekli güvenli URL/kodu ana ekranda gösterir ve durumu `WAIT_FOR_USER` olarak bekletir; kullanıcı işlemi tamamladıktan sonra mümkünse aynı `task_id` ile child session devam ettirilir. Specialist rollerde OpenCode native `question` permission `deny` edilerek kullanıcıya doğrudan soru sorma yolu parent Manager’a bırakılır. Bash içindeki device-code/OAuth gibi interaktif süreçlerde handoff bir agent instruction sözleşmesidir; HHC OpenCode core dışındaki süreci teknik olarak intercept ettiği iddiasında bulunmaz.

Bağımlı aşamalar ve aynı dosyada edit yapan ajanlar sıralı kalır. Powerful her rolü çalıştırmaz ve aynı rolü varsayılan iki kez çağırmaz.

## 7. Eski profillerden geçiş

- `minimal` → `basic`
- `standard` → `standard`
- `high-assurance` → `powerful`
- `web-development` → `standard` + `browser_ui`
- `desktop-development` → `standard` + `desktop_ui`
- `custom` → `standard` + eski uzman listesi Gelişmiş Yapılandırma olarak korunur

Eski role/model/Scout/Playwright seçimleri geçiş sırasında kaybedilmemelidir.

## 8. Yeniden yapılandırma

```text
/hhc-reconfigure
```

Profil, model atamaları, Scout/Playwright ve Gelişmiş Yapılandırma ayarlarını güvenli biçimde değiştirir.

## 9. Güncelleme

```text
/hhc-update
```

Mevcut durum bilgisini koruyarak yeni HHC sürümüne eşitler.

## 10. Mevcut `opencode.jsonc`

Kullanıcının mevcut yapılandırması sessizce ezilmez. `subagent_depth: 1` korunur.

## 11. Uzak hedef repo

Uzak repo kurulumu için: repoyu `git clone` ile klonlayın, ardından `/hhc-install` çalıştırın.
