---
description: Mevcut HHC yapılandırma durumunu göster (sürüm, roller, modeller, Scout, Playwright, MCP)
---

# HHC AI Team Kit — Yapılandırma Durumu

Salt-okunur durum raporu. Yapılandırma değişikliği yapmaz.

1. `.opencode/hhc-team.json` yoksa → "Bu projede HHC kurulu değil. `/hhc-install` kullanın." dur.
2. Backend: `{{PYTHON}} "{{KIT_ROOT}}/scripts/install.py" --project-path . --status`
3. Çıktıyı kullanıcıya göster. Sorular olursa açıkla (rol/model/scout/MCP).
4. Son not: değişiklik için `/hhc-reconfigure`, güncelleme için `/hhc-update`.
