---
description: Mevcut HHC çalışma profilini, gelişmiş ayarları ve model dağılımını değiştir
---

# HHC AI Team Kit — Yeniden Yapılandırma

Yeni kurulumla **aynı karar ağacını** kullan; yalnız mevcut state değerlerini başlangıç seçimi olarak koru ve legacy migration uygula.

`.opencode/hhc-team.json` dosyasını oku. Yoksa `/hhc-install` öner.

## Migration

Legacy profile'ları kullanıcıya yeniden seçenek olarak gösterme:
- `minimal` → `basic`
- `standard` → `standard`
- `high-assurance` → `powerful`
- `web-development` → `standard` + `browser_ui` migration sinyali
- `desktop-development` → `standard` + `desktop_ui` migration sinyali
- `custom` → `standard` + mevcut specialist listesi Advanced Configuration olarak korunur

## Normal akış

1. Profil: **Basic / Standard / Powerful**. Standard varsayılandır.
2. `project_characteristics.py --project-path . --legacy-profile <eski-profil>` ile çoklu proje özelliklerini yeniden çıkar; kullanıcıya proje türü seçtirme.
3. Normal UX'te **Tek Ana Ajan / Çoklu Ajan** sorusu sorma. Mevcut legacy state desteklenir; kullanıcı özellikle değiştirmek istemiyorsa model/primary tercihini koru. Yeni normal kurulum davranışı `multi + hands_on`dır.
4. Mevcut `scout_enabled` / `scout_model` durumunu göster ve **Scout / Dış Araştırma: Evet/Hayır** sor. Scout profile bağlı değildir.
5. `browser_ui` doğrulanıyorsa Playwright mevcut durumunu göster ve **Evet/Hayır** sor. Browser UI yoksa yeni Playwright açma; legacy web migration ile kanıt varsa korunabilir.
6. Model advisor çalıştır. **Kurulu ekipte N rol varsa N ayrı model kararı alınmalıdır.** Mevcut role model atamalarını başlangıç seçimi olarak koru ve bir rolün modelini diğerine sessizce kopyalama. Kullanıcı istemeden pahalı modele geçme.
7. Normal akışta tüm specialist roller erişilebilir kalır. Rol havuzunu daraltma yalnız Advanced Configuration'dır.
8. Özet + **Uygula / Geri dön / İptal**.

Windows Desktop model keşfinde `opencode.global.dat` içindeki `visibility=show` kayıtları BEST-EFFORT; ardından resmî CLI, son çare olarak UNDOCUMENTED/BEST-EFFORT cache akışı kullanılır.

## Advanced Configuration

Eski Custom davranışı burada yaşar. Kullanıcı açıkça isterse `--roles` ile specialist havuzunu sınırla; mevcut custom migration'da eski rol listesi kaybolmamalı.

Backend:

`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path . --reconfigure --team-mode multi --manager-mode hands_on --preset <basic|standard|powerful> [--roles <advanced-specialists>] --model role=provider/model ... --scout <enabled|disabled> [--scout-model provider/model] --playwright <enabled|disabled> --validate-model-capabilities`

Legacy `single`/shared-model state'leri güvenli biçimde korunabilir. Kullanıcı açıkça yeni normal akışa geçmek isterse `multi + hands_on` kullan.
