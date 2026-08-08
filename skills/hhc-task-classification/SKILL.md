---
name: hhc-task-classification
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
6. OAuth/device login, MFA, izin/onay, credential girişi veya başka kullanıcı etkileşimi çıkma ihtimali varsa bunu erken işaretle. Böyle bir durum çalışma sırasında beklenmedik biçimde ortaya çıkarsa alt ajan beklemek/retry etmek yerine `USER_ACTION_REQUIRED` handoff ile Manager'a dönsün.

## Minimum yönlendirme

Çalışma profili bir **ajan kadrosu değildir**; maliyet, paralellik ve doğrulama yoğunluğu politikasıdır. Erişilebilir uzmanlar arasından en küçük yeterli setle başla; yeni bulgu ortaya çıkarsa ekibi genişlet.

- `repository-explorer`: görev alanını bulmak ana bağlamı ciddi büyütecekse.
- `architect`: yeni alt sistem, modüller arası sözleşme, genel API, veri modeli/şema, geçiş, büyük bağımlılık veya mimari sınır değişiyorsa.
- `coder`: ayrı uygulama işi gerçekten devredilecekse.
- `qa-reviewer`: anlamlı davranış/regresyon riski veya bağımsız yorum gerekiyorsa; typo ve tamamen deterministik küçük değişikliklerde zorunlu değildir.
- `security-reviewer`: auth/authz, izinler, secrets/credentials, kullanıcı kontrollü girdi, DB/dosya mutasyonu, dosya yükleme, ağ yüzeyi, bağımlılık/tedarik zinciri, serileştirme, crypto, üretim/sürüm veya uzaktan çalıştırma gerçekten etkileniyorsa.
- `visual-qa`: arayüz/CSS/yerleşim/farklı ekran boyutlarına uyum/DOM/şablon veya görsel etkileşim değişiyorsa.

Bir uzman çağrıldıktan sonra gereksiz olduğunu fark ederse uzun rapor üretmeden kısa gerekçeyle dönsün.

## Döngü kontrolü

Yeniden deneme sayısını mekanik olarak sayma. Son deneme **yeni bilgi veya gerçek ilerleme** üretmediyse aynı yaklaşımı tekrarlama; strateji değiştir, uygun uzmanı ekle veya gerekiyorsa kullanıcıya yükselt. `USER_ACTION_REQUIRED` / auth / MFA / permission / confirmation bekleme durumlarını hata sayıp otomatik retry etme; `WAIT_FOR_USER` olarak kullanıcıya yükselt. OpenCode'un yerleşik `doom_loop` korumasını aşmaya çalışma.

## Handoff

Alt ajanlardan ham büyük çıktı isteme. Varsayılan olarak kısa sonuç, önemli bulgular, dosya/sembol referansları, doğrulanmayan noktalar ve gerekiyorsa sonraki adım yeterlidir. **Bağlam taşıma; referans taşı.**
