# Otomatik Veri Seti Artırma Projesi (UAV Tabanlı)

## 1. Giriş

Makine öğrenmesi ve özellikle derin öğrenme tabanlı nesne tespit modellerinin başarımı,
büyük ve çeşitli veri setlerine doğrudan bağlıdır. Ancak gerçek hayatta, özellikle
İnsansız Hava Araçları (UAV) ile elde edilen görüntülerde veri toplama süreci
zaman alıcı, maliyetli ve zahmetlidir.

Bu projede, UAV videoları kullanılarak **otomatik veri seti artırma** sürecini
gerçekleştiren bir sistem geliştirilmiştir. Amaç; video akışları üzerinden
nesne tespiti yaparak, belirli koşulları sağlayan karelerin otomatik olarak
kaydedilmesi ve bu sayede etiketlenmeye hazır bir veri setinin oluşturulmasıdır.

---

## 2. Projenin Amacı

Bu projenin temel amaçları şunlardır:

- UAV videolarından otomatik olarak anlamlı görüntü kareleri çıkarmak
- Nesne tespiti kullanarak gereksiz kareleri elemek
- Manuel veri toplama ihtiyacını azaltmak
- Nesne tespiti modellerinin eğitimi için daha büyük ve çeşitli veri setleri oluşturmak
- Zaman ve iş gücü maliyetini minimize etmek

---

## 3. Kullanılan Teknolojiler ve Araçlar

Projede aşağıdaki teknolojiler ve kütüphaneler kullanılmıştır:

- **Python**: Ana programlama dili
- **OpenCV (cv2)**: Video işleme ve kare yakalama işlemleri
- **YOLO tabanlı nesne tespit modeli**: UAV görüntülerinde nesne tespiti
- **NumPy**: Matris ve veri işlemleri
- **PyTorch**: Derin öğrenme modeli kullanımı (varsa)

---

## 4. Sistem Mimarisi ve Çalışma Prensibi

Sistem genel olarak aşağıdaki adımlarla çalışmaktadır:

1. UAV videosu sisteme giriş olarak verilir
2. Video belirli aralıklarla karelere ayrılır
3. Her kare üzerinde nesne tespiti yapılır
4. Tespit edilen nesneler belirli eşik koşullarını sağlıyorsa kare kaydedilir
5. Kaydedilen kareler veri seti klasörüne otomatik olarak eklenir

Bu yapı sayesinde, yalnızca hedef nesnelerin bulunduğu kareler veri setine dahil edilir.

---

## 5. Video Kare Yakalama Mekanizması

Video akışı OpenCV kullanılarak işlenmektedir. Sistem, her kareyi tek tek
işlemek yerine belirli bir periyotta kare alarak:

- Gereksiz tekrarları azaltır
- Veri setinde çeşitliliği artırır
- Depolama maliyetini düşürür

Örnek olarak, her **N frame’de bir** görüntü alınmakta ve bu görüntü nesne
tespit modeline gönderilmektedir.

---

## 6. Nesne Tespiti ve Filtreleme Süreci

Her alınan kare üzerinde önceden eğitilmiş nesne tespit modeli çalıştırılır.
Model çıktısına göre:

- Eğer hedef nesne algılanmışsa kare kaydedilir
- Hedef nesne yoksa kare atlanır

Bu yöntem sayesinde:
- Boş veya anlamsız görüntüler elenir
- Veri seti kalitesi artırılır
- Etiketleme süreci daha verimli hale gelir

---

## 7. Veri Seti Artırma Stratejisi

Proje, klasik veri artırma yöntemlerinden (rotation, flip vb.) farklı olarak
**gerçek veriye dayalı otomatik artırma** yaklaşımı sunar.

Avantajları:
- Gerçek dünya senaryolarını daha iyi yansıtır
- UAV açıları ve yükseklik farklarını kapsar
- Modelin genelleme yeteneğini artırır

---

## 8. Çıktılar

Proje çıktısı olarak:

- UAV videolarından otomatik olarak çıkarılmış görüntü kareleri
- Nesne tespiti yapılmış ve filtrelenmiş veri seti
- Eğitim için hazır, daha dengeli bir görüntü koleksiyonu elde edilmiştir

---

## 9. Karşılaşılan Problemler ve Çözümler

### Büyük Dosya Boyutları
UAV videoları yüksek boyutlu olduğu için GitHub’a doğrudan eklenmemiştir.
Bunun yerine, sistemin çalışma mantığı ve örnek çıktılar paylaşılmıştır.

### Yanlış Pozitif Tespitler
Nesne tespit modelinin bazı durumlarda hatalı algılama yaptığı gözlemlenmiştir.
Bu durum, eşik değerleri ve kare alma periyotları ayarlanarak minimize edilmiştir.

---

## 10. Gelecek Çalışmalar

Projenin ilerleyen aşamalarında aşağıdaki geliştirmeler planlanmaktadır:

- Otomatik etiket (annotation) oluşturma
- Farklı UAV senaryoları için model çeşitlendirme
- Gerçek zamanlı veri seti artırma
- Çoklu nesne sınıfı desteği
- GUI tabanlı kullanıcı arayüzü

---

## 11. Sonuç

Bu proje kapsamında, UAV videolarını kullanarak otomatik veri seti artırımı
sağlayan bir sistem geliştirilmiştir. Sistem, manuel veri toplama ihtiyacını
azaltarak nesne tespiti projeleri için verimli, ölçeklenebilir ve pratik bir
çözüm sunmaktadır.

Elde edilen sonuçlar, bu yaklaşımın özellikle UAV tabanlı görüntü işleme
projelerinde etkili bir yöntem olduğunu göstermektedir.
