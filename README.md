
# GÖRÜNGÜ (OMR Application) - Powered by Thoth Engine

GÖRÜNGÜ, Python ve OpenCV tabanlı, modern arayüze sahip bir Optik Form Okuma ve Değerlendirme (OMR) uygulamasıdır. Psikiyatri ölçekleri ve anket formlarını dijitalleştirmek, otomatik olarak puanlamak ve analiz etmek için geliştirilmiştir.

## Özellikler

*   **Tasarımcı Modu:** Formlar üzerinde etkileşimli olarak ROI (İlgi Alanı) belirleme ve şablon oluşturma.
*   **Tarayıcı Modu:** Taranmış formları veya fotoğrafları yükleyip, şablon bazlı otomatik puanlama yapma.
*   **Dinamik Eşik (Dynamic Threshold):** Kullanıcı işaretlemelerini algılama hassasiyetini, kaydırıcı (slider) ile gerçek zamanlı ayarlama ve öğrenme yeteneği.
*   **Otomatik Hizalama:** Fotoğraflardaki kayma ve dönmeleri referans görsele göre otomatik düzeltme (SIFT/ORB).
*   **Raporlama:** Sonuçları CSV (Excel uyumlu) formatında dışa aktarma.
*   **Modern UI:** Tkinter tabanlı, özel temalı (Nil Deltası) kullanıcı dostu arayüz.

## Gereksinimler

*   Python 3.8+
*   Kütüphaneler:
    *   `opencv-python`
    *   `numpy`
    *   `Pillow` (PIL)
    *   `pymupdf` (PDF desteği için)

## Kurulum

1.  Bu depoyu klonlayın veya indirin.
2.  Gerekli bağımlılıkları yükleyin:

```bash
pip install -r requirements.txt
```

## Kullanım

Uygulamayı başlatmak için ana dizinde komut satırını açın ve aşağıdaki komutu çalıştırın:

```bash
python gorungu.py
```

### 1. Şablon Oluşturma (Tasarımcı Modu)

1.  Uygulama açılışta Tasarımcı Modunda başlar.
2.  "Boş Form Yükle" butonu ile işaretlenmemiş, temiz bir form görseli seçin.
3.  Form üzerindeki kutucukları (işaretleme alanlarını) farenizle seçin.
4.  Her kutucuk için bir etiket ve puan değeri girin.
5.  İşlemi tamamladığınızda "Şablonu Kaydet" butonu ile çalışmanızı `.json` formatında kaydedin.

### 2. Form Okuma (Tarayıcı Modu)

1.  "Mod" menüsünden "Tarayıcı Modu"na geçin.
2.  "Şablon Yükle" butonu ile daha önce kaydettiğiniz `.json` dosyasını seçin.
3.  "Resimleri Yükle" veya "Klasör Yükle" butonları ile doldurulmuş formların görsellerini yükleyin.
4.  "Bu Sayfayı Puanla" butonu ile o anki sayfayı değerlendirin veya manuel kontrollerinizi yapın.
5.  Tüm formlar bittiğinde "Raporu Görüntüle" ve ardından "Excel'e Aktar" seçenekleri ile sonuçları alın.

## Lisans

Bu proje MIT Lisansı ile lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakabilirsiniz.

## Geliştirici

**Dr. Furkan BEKDEMİR**
