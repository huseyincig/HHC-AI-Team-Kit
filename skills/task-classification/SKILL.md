---
name: task-classification
description: Belirsiz, çok adımlı veya çoklu ajan gerektirebilecek görevlerde minimum yeterli ekip, doğrulama ve onay ihtiyacını ekonomik biçimde belirlemek için kullanılır.
---

# Görev Sınıflandırma ve Yönlendirme

Amaç en fazla kontrolü değil, **yeterli güveni sağlayan en küçük çalışma setini** seçmektir.

Önce şu filtreden geç:

1. Kullanıcının gerçek amacı ve gözlenebilir kabul ölçütü nedir?
2. Sonucu değiştirecek doğrulanmamış bir bilgi var mı?
   - Kararı değiştirmeyecek bilinmeyeni araştırma.
   - Kararı değiştirecek bilinmeyeni tahmin etme; önce mevcut bağlam, ilgili kaynak kodu, config/docs/tests veya uygun tool ile doğrula. Hâlâ maddiyse kullanıcıya sor.
3. Görev gerçekten ağır repository keşfi, mimari karar, uygulama, QA, güvenlik veya görsel QA gerektiriyor mu?
4. Doğrudan test/build/lint/diff veya etkin ve kullanılabilir OpenCode LSP diagnostic gibi deterministik bir kontrol yeterliyse ikinci bir LLM'ye aynı soruyu sordurma.
5. Geri dönüşü zor veya dış etkili işlem varsa uygulamadan önce kullanıcı onayının gerekip gerekmediğini belirle.

## Minimum routing

Preset'teki roller bir **uzman havuzudur**, sabit pipeline değildir. En küçük yeterli setle başla; yeni bulgu ortaya çıkarsa ekibi genişlet.

- `repository-explorer`: görev alanını bulmak ana context'i ciddi büyütecekse.
- `architect`: yeni subsystem, cross-module sözleşme, public API, veri modeli/schema, migration, büyük bağımlılık veya mimari sınır değişiyorsa.
- `coder`: ayrı uygulama işi gerçekten devredilecekse.
- `qa-reviewer`: anlamlı davranış/regresyon riski veya bağımsız yorum gerekiyorsa; typo ve tamamen deterministik küçük değişikliklerde zorunlu değildir.
- `security-reviewer`: auth/authz, izinler, secrets/credentials, kullanıcı kontrollü girdi, DB/dosya mutasyonu, upload, ağ yüzeyi, dependency/supply-chain, serialization, crypto, production/release veya remote execution gerçekten etkileniyorsa.
- `visual-qa`: UI/CSS/layout/responsive/DOM/template veya görsel etkileşim değişiyorsa.

Bir uzman çağrıldıktan sonra gereksiz olduğunu fark ederse uzun rapor üretmeden kısa gerekçeyle dönsün.

## Döngü kontrolü

Retry sayısını mekanik olarak sayma. Son deneme **yeni bilgi veya gerçek ilerleme** üretmediyse aynı yaklaşımı tekrarlama; strateji değiştir, uygun uzmanı ekle veya gerekiyorsa kullanıcıya yükselt. OpenCode'un native `doom_loop` korumasını aşmaya çalışma.

## Handoff

Alt ajanlardan ham büyük çıktı isteme. Varsayılan olarak kısa sonuç, önemli bulgular, dosya/sembol referansları, doğrulanmayan noktalar ve gerekiyorsa sonraki adım yeterlidir. **Context taşıma; referans taşı.**
