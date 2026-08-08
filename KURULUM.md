# Kurulum

[README](README.md) | [English installation guide](INSTALLATION.md)

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
- `/hhc-install-remote`
- `/hhc-reconfigure`
- `/hhc-update`

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

Profil rol kadrosu değildir. Üçünde de temel specialist roller erişilebilir kalır.

### Adım 2 — Proje özellikleri otomatik algılanır

Kullanıcıdan Web/Desktop seçimi istenmez. HHC repo sinyallerinden çoklu özellik çıkarır:

`browser_ui`, `desktop_ui`, `backend`, `cli`, `library`, `database`, `wordpress`, `containerized`, `mobile`.

Bir proje aynı anda birden fazla özelliğe sahip olabilir.

### Adım 3 — Scout

**OpenCode Scout kullanılsın mı?** Varsayılan **Hayır**.

Scout profile bağlı değildir. Harici/güncel dokümantasyon ve dependency/upstream araştırması için kullanılır; yerel repo keşfi `repository-explorer` ile yapılır. Açılırsa Scout modeli ayrıca seçilir.

### Adım 4 — Playwright

Yalnız `browser_ui` doğrulanırsa **Playwright MCP kullanılsın mı?** sorulur. Varsayılan **Hayır**.

Açıldığında Playwright proje-local kurulur; `playwright_*` araçları yalnız `visual-qa` rolüne açılır. Browser UI yoksa normal kurulum bu soruyu göstermez.

### Adım 5 — Modeller

Model keşfi ve `model_advisor.py` kullanılarak kurulu roller için model seçilir. Normal akışta her rolün modeli ayrı seçilir; profile göre otomatik pahalı model yükseltmesi yapılmaz.

Scout açıksa Scout modeli ayrıca seçilir.

### Normal primary ve ekip davranışı

Yeni normal UX'te **Tek Ana Ajan / Çoklu Ajan** ayrı ana soru değildir. Varsayılan çalışma:

- primary: **Çalışan Yönetici (`working-manager`)**
- backend: `multi + hands_on`
- bütün temel specialist roller erişilebilir
- hangi specialist'in çağrılacağı SMART tarafından görev bazında belirlenir

Eski `single|multi`, shared model ve salt orkestratör primary seçenekleri yalnız migration/Advanced Configuration amacıyla backend'de korunur.

## 4. Advanced Configuration

Eski **Custom** profil artık ana profil değildir.

İleri düzey kullanıcı açıkça isterse:

- specialist havuzunu `--roles` ile daraltabilir,
- primary'ı `manager`/orkestratör yapabilir,
- tek ortak model kullanabilir,
- proje özelliğine explicit override ekleyebilir.

Bu ayarlar Basic/Standard/Powerful profilinin yerine geçmez.

## 5. Parallelism ve background

HHC background subagent kullanımını desteklenen çalışma davranışı kabul eder. Yalnız parent'ın beklemeden sürdürebileceği, bağımsız ve file/state çakışması üretmeyecek işler paralelleştirilir.

Bağımlı aşamalar ve aynı dosyada edit yapan ajanlar sıralı kalır. Powerful her rolü çalıştırmaz ve aynı rolü varsayılan iki kez çağırmaz.

## 6. Legacy profile migration

- `minimal` → `basic`
- `standard` → `standard`
- `high-assurance` → `powerful`
- `web-development` → `standard` + `browser_ui`
- `desktop-development` → `standard` + `desktop_ui`
- `custom` → `standard` + eski specialist listesi Advanced Configuration olarak korunur

Eski role/model/Scout/Playwright seçimleri migration sırasında kaybedilmemelidir.

## 7. Yeniden yapılandırma

```text
/hhc-reconfigure
```

Profil, model atamaları, Scout/Playwright ve Advanced Configuration ayarlarını güvenli biçimde değiştirir.

## 8. Güncelleme

```text
/hhc-update
```

Mevcut state'i koruyarak yeni HHC sürümüne eşitler.

## 9. Mevcut `opencode.jsonc`

Kullanıcının mevcut yapılandırması sessizce ezilmez. `subagent_depth: 1` korunur.

## 10. Uzak hedef repo

```text
/hhc-install-remote <git-url>
```

Bu komut hedef Git reposunu klonlar ve aynı Basic/Standard/Powerful SMART kurulum akışını uygular.
