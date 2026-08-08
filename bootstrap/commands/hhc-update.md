---
description: HHC proje dosyalarını ve global kit'i otomatik güncelle
---

# HHC AI Team Kit — Güncelleme (Sessiz Senkron + Global Self-Update)

1. `.opencode/hhc-team.json` yoksa → "Bu projede HHC kurulu değil. `/hhc-install` kullanın." dur.
2. `{{KIT_ROOT}}/VERSION` yoksa → "Global kit bulunamadı. HHC-KUR çalıştırın." dur.
3. Global kit self-update: `{{PYTHON}} "{{KIT_ROOT}}/scripts/update_global.py" $ARGUMENTS`
   - JSON `status` alanına göre raporla:
     - `UPDATED` = "Global kit güncellendi: eski → yeni"
     - `UP_TO_DATE` = "Global kit güncel (x.x.x)"
     - `OFFLINE` / `NO_RELEASES` / `RATE_LIMITED` = soft-notice "Uzak kontrol atlandı: <neden>. Yerel senkron devam."
     - `ERROR` = yüksek uyarı "Bütünlük/doğrulama hatası, global kit dokunulmadı"
     - `LOCAL_ONLY` (`--no-remote`) = "Uzak kontrol atlandı (--no-remote)"
4. Backend proje senkronu (sessiz): `{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path . --update`
5. JSON `status` alanına göre raporla:
   - `UP_TO_DATE` → "HHC güncel. Kit sürümü: x.x.x"
   - `UPDATED` → "Güncellendi: x.x.x → y.y.y" + `written` / `removed` özeti (kaç dosya yazıldı, kaçı kaldırıldı).
6. `config.action` == `preserved-existing-config` ise mevcut `opencode.jsonc` korunduğunu bildir (HHC config varsayılanlarını değiştirmedi).
7. Hata alınırsa → "Güncelleme başarısız. `/hhc-reconfigure` ile yeniden yapılandırmayı deneyin." öner.
8. Son not: Global kit `/hhc-update` ile otomatik güncellenir (GitHub releases). `--no-remote` ile yalnız yerel senkron. Network yoksa yerel senkron yine de çalışır. Proje dosyaları her zaman `/hhc-update` ile güncel tutulur.
