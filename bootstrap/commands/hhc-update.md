---
description: HHC proje dosyalarını global kit'in yeni sürümüyle sessizce yenile
---

# HHC AI Team Kit — Güncelleme (Sessiz Senkron)

1. `.opencode/hhc-team.json` yoksa → "Bu projede HHC kurulu değil. `/hhc-install` kullanın." dur.
2. `{{KIT_ROOT}}/VERSION` yoksa → "Global kit bulunamadı. HHC-KUR çalıştırın." dur.
3. Backend: `{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path . --update`
4. JSON `status` alanına göre raporla:
   - `UP_TO_DATE` → "HHC güncel. Kit sürümü: x.x.x"
   - `UPDATED` → "Güncellendi: x.x.x → y.y.y" + `written` / `removed` özeti (kaç dosya yazıldı, kaçı kaldırıldı).
5. `config.action` == `preserved-existing-config` ise mevcut `opencode.jsonc` korunduğunu bildir (HHC config varsayılanlarını değiştirmedi).
6. Hata alınırsa → "Güncelleme başarısız. `/hhc-reconfigure` ile yeniden yapılandırmayı deneyin." öner.
7. Son not: Global kit'i güncellemek için HHC-KUR'u yeniden çalıştırın, ardından her projede `/hhc-update`. `--update` sessizdir ve mevcut state'i korur; `--reconfigure` interaktiftir ve state'i değiştirebilir.
