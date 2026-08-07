# Kurulum

## 1. Makineye bir kez kur

Windows: `HHC-KUR.cmd`  
macOS/Linux: `./HHC-KUR.sh`

Global komutlar:
- `/hhc-install`
- `/hhc-install-remote`
- `/hhc-reconfigure`

## 2. Yeni projeye kur

OpenCode'da projeyi aç ve `/hhc-install` çalıştır.

### Adım 1 — Profil

İlk soru her zaman profildir: Minimal, Standard, Web Development, Desktop Development, High Assurance veya Özel. Hazır profil kendi rol havuzunu belirlediği için ayrıca rol sorulmaz. Yalnız Özel profilde uzmanlar seçilir.

### Adım 2 — Çalışma biçimi

Yalnız iki seçenek vardır:

- **Tek Ana Ajan:** primary otomatik **Çalışan Yönetici** olur; profil uzmanları yine kurulur ve gerektiğinde subagent olarak kullanılabilir.
- **Çoklu Ajan Ekibi:** yönetici tipi Çalışan Yönetici veya Orkestratör seçilir.

Tam bağımsız/alt ajanları kapatan üçüncü bir solo seçenek yoktur.

### Adım 3 — Modeller

`scripts/model_discovery.py --project-path <proje>` Windows OpenCode Desktop state'i bulunursa önce `%APPDATA%\ai.opencode.desktop\opencode.global.dat` içindeki `model.user[]` kayıtlarını okur ve yalnız `visibility == "show"` olan `providerID/modelID` çiftlerini gösterir. Bu dosya OpenCode'un public/stable API'si olmadığı için salt-okunur **BEST-EFFORT** kaynak kabul edilir. Desktop state yoksa/boşsa resmî `opencode models` komutuna geçilir. CLI başarısızsa yerel cache yine **UNDOCUMENTED / BEST-EFFORT** fallback'tir; cache'de bulunmak tek başına kullanılabilirlik kanıtı değildir ve yalnız config veya resmî auth görünümüyle aktifliği doğrulanabilen provider'lar kullanılır.

Kullanıcı isterse bir kez `opencode models --refresh` denenebilir; otomatik çalışmaz.

- **Tek Ana Ajan:** bir model seçilir, bütün kurulu HHC rolleri aynı modeli kullanır.
- **Çoklu Ajan:** doğrudan her kurulu role model seçilir.

Ayrı `model politikası`, `OpenCode'u devral`, ekip varsayılan modeli veya “hangi roller farklı olsun?” adımı yoktur.

### Türkçe rol adları

Wizard teknik ID yerine şu görünen adları kullanır: Çalışan Yönetici, Orkestratör, Mimar, Depo Gezgini, Kodlayıcı, Kalite İnceleyici, Görsel QA, Güvenlik İnceleyici.

## 3. Özel profil davranışı

Seçilmeyen uzman rol, ilgili işin yapılamayacağı anlamına gelmez. Manager önce mevcut agent ve native araçlarla görevin güvenilir biçimde tamamlanıp tamamlanamayacağını değerlendirir. Basit dosya araması için Depo Gezgini, basit UI kontrolü için Görsel QA veya küçük test için bağımsız QA otomatik zorunlu değildir.

Uzman gerçekten gerekli ve mevcut ekip güvenilir sonuç üretemiyorsa `/hhc-reconfigure` ile rol eklenmesi önerilebilir.

## 4. Yeniden yapılandırma

```text
/hhc-reconfigure
```

Yeni kurulumla aynı sıra kullanılır: Profil → yalnız Custom ise roller → Tek Ana/Çoklu → gerekirse yönetici → modeller. Eski rc.16 solo state'i yeniden yapılandırılırken HHC-owned dosyalar güvenli biçimde yeni yapıya taşınır.

## 5. Mevcut `opencode.jsonc`

Mevcut config sessizce ezilmez. Config yoksa HHC `default_agent`, `subagent_depth: 1` ve `compaction.auto/prune` içeren küçük config oluşturur; `reserved` eklemez.

## 6. Windows, Desktop ve WSL

Native Windows/OpenCode Desktop ile WSL içinde çalışan OpenCode backend'i farklı kullanıcı ortamlarıdır. Desktop WSL içindeki `opencode serve` backend'ine bağlanıyorsa HHC global bootstrap WSL içinde de ayrıca kurulmalıdır. Linux/container testi native Windows Desktop PASS sayılmaz.

## 7. Uzak kod deposu

```text
/hhc-install-remote <git-url>
```

Uzak kurulum klonlamadan sonra aynı rc.17 wizard karar ağacını kullanır.

## Çoklu ajan model seçimi

Çoklu Ajan Ekibinde kurulu her rol için model ayrı seçilir. Bir rolün modeli diğer rollere otomatik uygulanmaz ve bütün rol-model eşlemeleri tamamlanmadan kurulum onayına geçilmez.
