---
description: Mevcut HHC çalışma profilini, gelişmiş ayarları ve model dağılımını değiştir
---

# HHC AI Team Kit — Yeniden Yapılandırma

Yeni kurulumla **aynı karar ağacını** kullan; yalnız mevcut durum değerlerini başlangıç seçimi olarak koru ve eski geçiş uygula.

`.opencode/hhc-team.json` dosyasını oku. Yoksa `/hhc-install` öner.

## Geçiş

Eski profile'ları kullanıcıya yeniden seçenek olarak gösterme:
- `minimal` → `basic`
- `standard` → `standard`
- `high-assurance` → `powerful`
- `web-development` → `standard` + `browser_ui` geçiş sinyali
- `desktop-development` → `standard` + `desktop_ui` geçiş sinyali
- `custom` → `standard` + mevcut uzman listesi Gelişmiş Yapılandırma olarak korunur

## Normal akış

1. Profil: **Basic / Standard / Powerful**. Standard varsayılandır.
2. `project_characteristics.py --project-path . --legacy-profile <eski-profil>` ile çoklu proje özelliklerini yeniden çıkar; kullanıcıya proje türü seçtirme.
3. Normal UX'te **Tek Ana Ajan / Çoklu Ajan** sorusu sorma. Mevcut eski state desteklenir; kullanıcı özellikle değiştirmek istemiyorsa model/ana ajan tercihini koru. Yeni normal kurulum davranışı `multi + hands_on`dır.
4. Dış araştırmanın varsayılan yolu native `websearch` + `webfetch`tir. Çalışma zamanı native Scout'u gerçekten keşfetmiyorsa Scout sorusu gösterme ve `--scout disabled` kullan. Native Scout gerçekten çağrılabiliyorsa mevcut `scout_enabled` durumunu göster ve yalnız bağlam yalıtımı için **Native Scout kullanılsın mı? Evet/Hayır** sor. HHC model override/custom Scout üretmez.
5. `browser_ui` doğrulanıyorsa Playwright mevcut durumunu göster ve **Evet/Hayır** sor. Tarayıcı arayüzü yoksa yeni Playwright açma; eski web geçiş ile kanıt varsa korunabilir.
6. Model advisor çalıştır. **Kurulu ekipte N rol varsa N ayrı model kararı alınmalıdır.** Mevcut role model atamalarını başlangıç seçimi olarak koru ve bir rolün modelini diğerine sessizce kopyalama. Kullanıcı istemeden pahalı modele geçme.
7. Normal akışta tüm uzman roller erişilebilir kalır. Rol havuzunu daraltma yalnız Gelişmiş Yapılandırma'dır.
8. Özet + **Uygula / Geri dön / İptal**.

Windows Desktop model keşfinde `opencode.global.dat` içindeki `visibility=show` kayıtları EN İYİ ÇABA; ardından resmî CLI, son çare olarak BELGELENMEMİŞ/EN İYİ ÇABA önbellek akışı kullanılır.

## Gelişmiş Yapılandırma

Eski Custom davranışı burada yaşar. Kullanıcı açıkça isterse `--roles` ile uzman havuzunu sınırla; mevcut custom geçiş'da eski rol listesi kaybolmamalı.

Backend:

`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path . --reconfigure --team-mode multi --manager-mode hands_on --preset <basic|standard|powerful> [--roles <advanced-uzmans>] --model role=provider/model ... --scout <enabled|disabled> --playwright <enabled|disabled> --validate-model-capabilities`

Eski `single`/shared-model state'leri güvenli biçimde korunabilir. Kullanıcı açıkça yeni normal akışa geçmek isterse `multi + hands_on` kullan.
