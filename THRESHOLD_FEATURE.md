# Dinamik Eşik Kontrolü - Eklenen Özellik

## Özet

Tarayıcı modu penceresine, kullanıcının ROI (Region of Interest) işaretlenme eşiğini dinamik olarak ayarlayabilmesini sağlayan bir kullanıcı arayüzü (UI) elemanı eklendi.

## Eklenen Özellikler

### 1. Eşik Kontrolü Slider'ı (Threshold Slider)

**Konum**: Tarayıcı Modu → "3. Puanlama" bölümü → "İşlem" çerçevesi içinde

**Özellikler**:
- **Aralık**: 0.01 ile 0.50 arasında
- **Varsayılan Değer**: 0.12
- **Hassasiyet**: 0.01 adımlarla ayarlanabilir
- **Görsel Geri Bildirim**: Mevcut eşik değerini gösteren bir etiket

**Kullanım**:
1. Tarayıcı moduna geçin (Menü → Mod → Tarayıcı Modu)
2. "3. Puanlama" bölümünde "İşaretlenme Eşiği (Threshold)" başlığını bulun
3. Slider'ı sağa veya sola kaydırarak eşik değerini ayarlayın
4. Sağ tarafta güncel eşik değeri gösterilir (örn: 0.12)

### 2. Yeni Fonksiyon: `on_threshold_change()`

Bu callback fonksiyonu, slider hareket ettirildiğinde otomatik olarak çağrılır ve:
- `dynamic_threshold` değişkenini günceller
- Eşik değer etiketini günceller

## Teknik Detaylar

### Değişiklikler

#### Dosya: `gorungu.py`

**1. Scanner Mode UI Setup (satır ~1087-1139)**
```python
# Threshold Control
ttk.Label(frm_score, text="İşaretlenme Eşiği (Threshold):").pack(anchor=tk.W, pady=(5, 0))

# Frame for threshold slider and value label
threshold_frame = ttk.Frame(frm_score)
threshold_frame.pack(fill=tk.X, pady=(2, 10))

# Initialize dynamic_threshold if not exists
if not hasattr(self, 'dynamic_threshold'):
    self.dynamic_threshold = 0.12

# Threshold value label
self.lbl_threshold_value = ttk.Label(threshold_frame, text=f"{self.dynamic_threshold:.2f}", width=5)
self.lbl_threshold_value.pack(side=tk.RIGHT)

# Threshold slider
self.threshold_slider = tk.Scale(
    threshold_frame,
    from_=0.01,
    to=0.50,
    resolution=0.01,
    orient=tk.HORIZONTAL,
    command=self.on_threshold_change,
    showvalue=0,
    bg=self.colors["panel_bg"],
    fg=self.colors["text"],
    highlightthickness=0,
    troughcolor=self.colors["canvas"]
)
self.threshold_slider.set(self.dynamic_threshold)
self.threshold_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
```

**2. Callback Function (satır ~1434-1439)**
```python
def on_threshold_change(self, value):
    """Callback for threshold slider change"""
    self.dynamic_threshold = float(value)
    # Update the label to show current threshold value
    if hasattr(self, 'lbl_threshold_value'):
        self.lbl_threshold_value.config(text=f"{self.dynamic_threshold:.2f}")
```

**3. Updated Learning Function (satır ~1481-1519)**
```python
def update_threshold_from_manual_input(self, is_now_marked, fill_ratio):
    """
    Adapts the dynamic threshold based on user's manual correction.
    """
    if not hasattr(self, 'dynamic_threshold'):
        self.dynamic_threshold = 0.12
        
    # Learning Rate or "Safety Margin"
    margin = 0.01
    
    threshold_changed = False
    
    if is_now_marked:
        # User says this SHOULD be marked.
        if self.dynamic_threshold > fill_ratio:
            self.dynamic_threshold = max(0.01, fill_ratio - margin)
            threshold_changed = True
    else:
        # User says this SHOULD NOT be marked.
        if self.dynamic_threshold < fill_ratio:
            self.dynamic_threshold = min(0.90, fill_ratio + margin)
            threshold_changed = True
    
    # Update UI elements if threshold was changed
    if threshold_changed:
        # Update slider position if it exists
        if hasattr(self, 'threshold_slider') and self.threshold_slider.winfo_exists():
            self.threshold_slider.set(self.dynamic_threshold)
        
        # Update threshold value label if it exists
        if hasattr(self, 'lbl_threshold_value') and self.lbl_threshold_value.winfo_exists():
            self.lbl_threshold_value.config(text=f"{self.dynamic_threshold:.2f}")
        
        # Update status bar to inform user
        self.status_var.set(f"Eşik değeri otomatik olarak {self.dynamic_threshold:.2f} değerine güncellendi.")
```

## Eşik Değerinin Kullanımı

Ayarlanan `dynamic_threshold` değeri, `score_page()` fonksiyonunda (satır 1600) ROI'ların işaretli olup olmadığını belirlemek için kullanılır:

```python
is_marked = fill_ratio > self.dynamic_threshold
```

**Nasıl Çalışır**:
- **Düşük Eşik (örn. 0.05)**: Daha hassas, hafif işaretleri de algılar
- **Yüksek Eşik (örn. 0.30)**: Daha katı, sadece yoğun işaretleri algılar
- **Varsayılan (0.12)**: Dengeli yaklaşım

### 🎓 Otomatik Öğrenme (Learning Mode)

Veri düzenleme modu açıkken, kullanıcı manuel olarak bir ROI'nın durumunu değiştirdiğinde:

1. Sistem otomatik olarak threshold değerini ayarlar
2. **YENİ**: Slider otomatik olarak yeni pozisyona kayar
3. **YENİ**: Değer etiketi güncellenir
4. **YENİ**: Durum çubuğunda bilgilendirme mesajı gösterilir

**Örnek**:
- Kullanıcı fill_ratio 0.08 olan bir ROI'yı "işaretli" olarak değiştirirse
- Sistem threshold'u 0.08 - 0.01 = 0.07'ye düşürür
- Slider ve etiket otomatik olarak 0.07 değerini gösterir
- Durum çubuğu: "Eşik değeri otomatik olarak 0.07 değerine güncellendi."

## Kullanıcı Deneyimi

### Öncesi
Kullanıcı eşik değerini değiştirmek için kod düzenlemesi yapması gerekirdi.

### Sonrası  
Kullanıcı tarayıcı modunda slider ile eşik değerini gerçek zamanlı olarak ayarlayabilir ve farklı değerlerle test edebilir.

## Test Önerileri

1. Uygulamayı başlatın
2. Tarayıcı moduna geçin
3. Bir şablon ve test görüntüleri yükleyin

**Manuel Eşik Testi**:
4. Eşik slider'ını farklı değerlere ayarlayın
5. "Bu Sayfayı Puanla" butonuna tıklayarak sonuçları gözlemleyin
6. Farklı eşik değerlerinin işaretlenme algılama üzerindeki etkisini değerlendirin

**Otomatik Öğrenme Testi**:
7. "Veri Düzenleme: Kapalı" butonuna tıklayarak düzenleme modunu açın
8. Canvas üzerindeki bir ROI kutusuna tıklayarak durumunu değiştirin
9. Slider'ın otomatik olarak yeni eşik değerine kaydığını gözlemleyin
10. Durum çubuğundaki bilgilendirme mesajını kontrol edin

## Notlar

- **Manuel Ayar**: Kullanıcı slider'ı sürüklediğinde eşik değeri anında güncellenir
- **Otomatik Öğrenme**: Veri düzenleme modunda ROI durumu değiştirildiğinde:
  - `update_threshold_from_manual_input()` fonksiyonu devreye girer
  - Eşik değeri otomatik olarak ayarlanır
  - **Slider otomatik olarak yeni pozisyona kayar**
  - **Değer etiketi güncellenir**
  - **Durum çubuğunda bilgilendirme gösterilir**
- Slider değeri ve otomatik öğrenme **senkronize** çalışır
- İki mod (manuel/otomatik) birbirini tamamlar ve aynı UI elemanlarını günceller

