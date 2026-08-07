---
name: code-review
description: Anlamlı kod değişikliklerini amaç, diff ve davranış riski açısından bağımsız incelemek için kullanılır.
---

# Kod İncelemesi

Kabul kriteri ve diff'ten başla. İlgili test kanıtını dikkate al; test/build sonucu zaten deterministik olarak doğrulanmışsa aynı sonucu yeniden tahmin etme. Hata yolları, sınır durumları, API/sözleşme değişiklikleri, yanlış abstraction, gereksiz karmaşıklık ve test boşluklarına odaklan. Şüphe varsa yalnız ilgili kaynak alanını genişlet. Bulguları dosya/satır veya sembol referansıyla ver.
