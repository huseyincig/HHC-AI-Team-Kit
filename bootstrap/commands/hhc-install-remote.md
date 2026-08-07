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
5. Model keşfi klonlanan proje dizini için `model_discovery.py --project-path <hedef>` ile yapılır.
6. Tek Ana Ajanda bir model bütün rollere; Çoklu Ajanda doğrudan rol → model.
7. Son özet ve onay.

`Model politikası`, `OpenCode'u devral`, `Hangi roller farklı olsun?` veya `Tam bağımsız tek ajan` sorularını gösterme.

CLI resmî kaynaktır; cache yalnız **UNDOCUMENTED / BEST-EFFORT** ve aktifliği doğrulanabilen provider'larla filtrelenmiş fallback olabilir. Refresh yalnız kullanıcı açıkça isterse bir kez çalıştırılır.

Backend:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/remote_install.py" --repo "$ARGUMENTS" --team-mode <single|multi> --preset <profil> [--manager-mode <mod>] [--roles ...] [--shared-model provider/model | --model role=provider/model ...]`

Kurulum sonucunda `config.action` `preserved-existing-config` ise hedef depodaki mevcut `opencode.jsonc` dosyasının korunduğunu ve HHC'nin bu config değerlerini değiştirmediğini kullanıcıya bildir.
