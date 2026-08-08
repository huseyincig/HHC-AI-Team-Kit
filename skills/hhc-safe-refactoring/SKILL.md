---
name: hhc-safe-refactoring
description: Davranışı koruyan yeniden düzenlemelerde kapsamı dar tutmak ve regresyon riskini azaltmak için kullanılır.
---

# Güvenli Yeniden Düzenleme

Davranış değişikliği ile yapısal değişikliği ayır. Önce mevcut testleri çalıştır; küçük adımlarla değiştir; herkese açık sözleşmeleri ve veri biçimlerini gerekmedikçe değiştirme; ardından aynı testleri tekrar çalıştır.
