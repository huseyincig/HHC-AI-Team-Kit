# Güvenlik

- HHC API anahtarı veya sağlayıcı kimlik bilgisini saklamaz.
- Uzak Git erişiminde mevcut Git/SSH/Credential Manager yapılandırmasını kullanır; etkileşimli kimlik bilgisi toplamaz.
- Kullanıcı istemeden push, tag, publish veya release yapılmaz.
- Ajan izinleri role göre sınırlıdır; inceleyici roller salt okunurdur.
- MCP varsayılan olarak kurulmaz veya etkinleştirilmez.
- Mevcut proje dosyalarının üzerine `--force` verilmeden yazılmaz.

Güvenlik açığı bildirirken gizli bilgi veya özel kod deposu içeriğini paylaşmayın.
