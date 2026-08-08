---
description: Uzak Git deposunu klonlayıp HHC AI Team Kit'i kur
---

# HHC AI Team Kit — Uzak Projeye Kurulum

Repo URL'sini doğrula ve `remote_install.py` ile klonlandıktan sonra normal SMART kurulum karar ağacını uygula.

1. Profil: **Basic / Standard / Powerful** (Standard varsayılan).
2. Team mode normal kullanıcıya sorulmaz; `multi + hands_on` kullanılır. Legacy/Advanced seçenekler korunur.
3. Repo klonlandıktan sonra proje özellikleri otomatik algılanır; Web/Desktop profile sorulmaz.
4. Scout: Evet/Hayır, default Hayır.
5. `browser_ui` doğrulanmışsa Playwright: Evet/Hayır, default Hayır.
6. Model advisor ile bütün kurulu roller için model kararlarını al; Scout açıksa ayrı Scout modeli seç.
7. Son özet + onay.

Backend örneği:

`{{PYTHON}} "{{KIT_ROOT}}/scripts/remote_install.py" --repo "$ARGUMENTS" --team-mode multi --manager-mode hands_on --preset <basic|standard|powerful> --model role=provider/model ... --scout <enabled|disabled> [--scout-model provider/model] --playwright <enabled|disabled> --validate-model-capabilities`

Playwright profile bağlı değildir; klonlanan repo `browser_ui` özelliğini doğrulamıyorsa backend açmayı reddeder. Gelişmiş explicit override gerektiğinde `--project-characteristic browser_ui` kullanılabilir.
