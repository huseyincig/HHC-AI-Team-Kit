---
description: Uzak Git kod deposunu klonla ve HHC kurulum asistanını çalıştır
---

# HHC AI Team Kit — Uzak Kod Deposu Kurulumu

Kullanıcıdan Git URL'sini al. Önce erişimi doğrula, sonra güvenli bir hedefe klonla. Credential/token isteme veya loglama.

Klonlama tamamlandıktan sonra yerel `/hhc-install` ile **aynı rc.17 sihirbazını** uygula:
1. Profil ilk soru.
2. Yalnız Özel profilde uzman rol seçimi.
3. Tek Ana Ajan / Çoklu Ajan Ekibi.
4. Tek Ana Ajanda yönetici otomatik Çalışan Yönetici; Çoklu Ajanda yönetici tipi sor.
5. Scout kullanımı: Evet / Hayır. Hayır varsayılandır; Evet ise model keşfinden sonra Scout / Dış Araştırma için ayrıca model seç.
6. Profil Web Development ise Playwright MCP: Evet / Hayır sor; varsayılan Hayır. Web dışı profilde sorma.
7. Model keşfi + capability/context/maliyet danışmanı klonlanan proje dizini için `model_advisor.py --project-path <hedef> --role <kurulu-role> ... [--role scout]` ile yapılır.
8. `INCOMPATIBLE` model seçilmez; `WARNING`/UNKNOWN için explicit kullanıcı onayı alınır. Metadata yoksa kurulum kırılmaz.
9. Tek Ana Ajanda bir model bütün rollere; Çoklu Ajanda doğrudan rol → model.
10. Son özet ve onay.

`Model politikası`, `OpenCode'u devral`, `Hangi roller farklı olsun?` veya `Tam bağımsız tek ajan` sorularını gösterme.

CLI resmî kaynaktır; cache yalnız **UNDOCUMENTED / BEST-EFFORT** ve aktifliği doğrulanabilen provider'larla filtrelenmiş fallback olabilir. Refresh yalnız kullanıcı açıkça isterse bir kez çalıştırılır.

Backend:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/remote_install.py" --repo "$ARGUMENTS" --team-mode <single|multi> --preset <profil> [--manager-mode <mod>] [--roles ...] [--shared-model provider/model | --model role=provider/model ...] --scout <enabled|disabled> [--scout-model provider/model] --playwright <enabled|disabled> --validate-model-capabilities`

Kurulum sonucunda `config.action` `preserved-existing-config` ise hedef depodaki mevcut `opencode.jsonc` dosyasının korunduğunu ve HHC'nin bu config değerlerini değiştirmediğini kullanıcıya bildir.
