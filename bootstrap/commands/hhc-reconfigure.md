---
description: Mevcut HHC ekip profilini, çalışma biçimini ve model dağılımını değiştir
---

# HHC AI Team Kit — Yeniden Yapılandırma

`.opencode/hhc-team.json` dosyasını oku. Yoksa `/hhc-install` öner; varsayım yaparak dosya silme.

Yeni kurulumla **aynı karar ağacını** kullan. Eski rc.16 state'inde `solo-agent`, `inherit/shared/per-role` gibi teknik alanlar bulunabilir; bunları okuyabilirsin ama kullanıcıya eski UX'i yeniden gösterme.

## Akış

1. Önce profil: Minimal / Standard / Web Development / Desktop Development / High Assurance / Özel.
2. Yalnız Özel profilde uzman rollerini Türkçe görünen adlarla seçtir. Hazır profilde rol sorusu yok.
3. Çalışma biçimi: **Tek Ana Ajan** veya **Çoklu Ajan Ekibi**.
4. Tek Ana Ajan ise primary otomatik Çalışan Yönetici; yönetici tipi sorma. Çoklu Ajanda Çalışan Yönetici / Orkestratör sor.
5. Mevcut state'teki `scout_enabled` / `scout_model` değerini göster ve **Scout kullanımı: Evet / Hayır** sorusunu sor. Preset Scout'u otomatik açmaz. Hayır ise Scout modeli sorma; Evet ise model keşfinden sonra Scout için ayrı model seç.
6. Model keşfini `{{PYTHON}} "{{KIT_ROOT}}/scripts/model_discovery.py" --project-path .` ile yap. Windows OpenCode Desktop'ta `%APPDATA%\ai.opencode.desktop\opencode.global.dat` içindeki `model.user[]` kayıtlarından `visibility=show` modeller varsa bunlar önceliklidir; yoksa CLI/cache fallback akışı kullanılır.
7. Tek Ana Ajanda bir model seç ve bütün rollere uygula. Çoklu Ajanda kurulu her rol için ayrı model cevabı topla; bütün roller model almadan devam etme.
8. Özet + **Uygula / Geri dön / İptal**.

Normal UX'te şunları SORMA:
- Model politikası
- OpenCode modelini devral
- Tek model tüm ekipte mi
- Hangi roller varsayılandan farklı olsun
- Tam bağımsız tek ajan

Scout = Evet ise **Scout / Dış Araştırma** modeli de bağımsız bir `provider/model` kararıdır. Mevcut Scout modeli varsa başlangıç seçimi olarak göster/koru; kullanıcı değiştirebilir. Scout = Hayır seçilirse HHC-owned Scout override kaldırılır ve diğer config/rol modelleri korunur.

Model keşfi başarısızsa loop'a girme. Kullanıcı açıkça isterse bir kez normal yeniden deneme veya bir kez `model_discovery.py --project-path . --refresh`; yine sonuç yoksa elle tam `provider/model` veya iptal.

Eski `single + solo-agent` state'i reconfigure edilirken sessizce dosya kaybetme. Kullanıcının yeni seçimine göre installer `--reconfigure` ile eski HHC-owned `solo-agent.md` dosyasını kaldırıp yeni `working-manager + profil uzmanları` yapısına güvenle geçsin.

## Çoklu Ajan model eşlemesi — tek geçerli akış

Kurulu ekipte N rol varsa N ayrı model kararı alınmalıdır. Her rol için Türkçe görünen adıyla `Bu rol hangi modeli kullansın?` sorusunu sor. Bir rolün cevabını başka role otomatik uygulama. Manuel giriş de rol bazındadır. Son onaya ancak bütün kurulu rollerin `provider/model` değeri belirlendikten sonra geç. Backend'e kurulu her rol için açık `--model role=provider/model` argümanı gönder.

## Backend

Tek Ana Ajan:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path . --reconfigure --team-mode single --preset <profil> [--roles <custom-uzmanlar>] --shared-model provider/model --scout <enabled|disabled> [--scout-model provider/model]`

Çoklu Ajan:
`{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path . --reconfigure --team-mode multi --preset <profil> --manager-mode <mod> [--roles <custom-uzmanlar>] --model role=provider/model ... --scout <enabled|disabled> [--scout-model provider/model]`

Installer yalnız HHC'nin yönettiği eski dosyaları yeni seçimle uyumlu hale getirir; kullanıcıya ait başka `.opencode` dosyalarına dokunma. `config.action` `preserved-existing-config` ise mevcut `opencode.jsonc` dosyasının korunup HHC config varsayılanlarının bu dosyaya yazılmadığını açıkça bildir.
