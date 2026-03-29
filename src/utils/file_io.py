
import os
import json
import csv
import numpy as np
import cv2

# Try importing pymupdf for pdf support
try:
    import fitz  # pymupdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("pymupdf (fitz) not found. PDF support disabled. Install with: pip install pymupdf")

def load_images_from_file(file_path):
    """
    Returns a list of cv2 images from a file path (Image or PDF).
    """
    print(f"[LOAD] Dosya yükleniyor: {file_path}")
    images = []
    
    if not os.path.exists(file_path):
        print(f"[ERROR] Dosya bulunamadı: {file_path}")
        return []

    ext = os.path.splitext(file_path)[1].lower()
    print(f"[LOAD] Dosya uzantısı: {ext}")
    
    if ext == '.pdf':
        if not PDF_AVAILABLE:
            print("[ERROR] PDF desteği yok - PyMuPDF bulunamadı")
            # In a real app, you might want to raise an exception here to be caught by UI
            raise ImportError("PDF support requires 'pymupdf'. Please run: pip install pymupdf")
            
        try:
            print("[LOAD] PDF açılıyor...")
            doc = fitz.open(file_path)
            print(f"[LOAD] PDF sayfa sayısı: {len(doc)}")
            for i, page in enumerate(doc):
                print(f"[LOAD] PDF sayfa {i+1} işleniyor...")
                pix = page.get_pixmap(dpi=150) # 150 dpi is good enough
                img_data = pix.tobytes("png")
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                images.append(img)
                print(f"[LOAD] Sayfa {i+1} yüklendi - Boyut: {img.shape}")
            print(f"[LOAD] PDF başarıyla yüklendi - Toplam {len(images)} sayfa")
        except Exception as e:
            print(f"[ERROR] PDF yükleme hatası: {e}")
            raise e
    else:
        print("[LOAD] Görsel dosya okunuyor...")
        # cv2.imread doesn't support unicode paths well on Windows sometimes
        # using numpy fromfile workaround is safer for unicode paths
        try:
            # img = cv2.imread(file_path)
            # Unicode safe read
            with open(file_path, "rb") as stream:
                bytes_data = bytearray(stream.read())
            numpyarray = np.asarray(bytes_data, dtype=np.uint8)
            img = cv2.imdecode(numpyarray, cv2.IMREAD_COLOR)
            
            if img is not None:
                images.append(img)
                print(f"[LOAD] Görsel yüklendi - Boyut: {img.shape}")
            else:
                 print(f"[ERROR] Görsel okunamadı: {file_path}")
        except Exception as e:
            print(f"[ERROR] Görsel okuma hatası: {e}")
            
    print(f"[LOAD] Toplam {len(images)} görsel yüklendi")
    return images

def save_template_json(data, file_path):
    """
    Saves the template data dictionary to a JSON file.
    """
    print(f"[SAVE] JSON dosyası yazılıyor: {file_path}")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] JSON kaydetme hatası: {e}")
        raise e

def load_template_json(file_path):
    """
    Loads template data from a JSON file.
    """
    print(f"[TEMPLATE] Şablon dosyası okunuyor: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[ERROR] JSON okuma hatası: {e}")
        raise e

def export_csv_report(session_results, file_path):
    """
    Exports the session results to a CSV file.
    session_results: dict { page_idx: { 'total': score, 'subscales': {} } }
    """

    try:
        print(f"[EXPORT] CSV raporu dışa aktarılıyor: {file_path}")
        # collect all unique subscales
        all_subscales = set()
        for res in session_results.values():
            all_subscales.update(res['subscales'].keys())
        sorted_subscales = sorted(list(all_subscales))
        
        header = ["Sayfa No", "Toplam Puan"] + sorted_subscales
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f: # utf-8-sig for excel
            writer = csv.writer(f, delimiter=';') # semicolon safer for excel in some regions
            writer.writerow(header)
            
            # write page rows
            sorted_indices = sorted(session_results.keys())
            for page_idx in sorted_indices:
                res = session_results[page_idx]
                row = [page_idx + 1, res['total']]
                for sub in sorted_subscales:
                    row.append(res['subscales'].get(sub, 0))
                writer.writerow(row)
                
            # write totals row
            writer.writerow([])
            total_sum = sum(r['total'] for r in session_results.values())
            total_row = ["GENEL TOPLAM", total_sum]
            
            # calculate subscale totals
            sub_totals = {sub: 0 for sub in sorted_subscales}
            for res in session_results.values():
                for sub, val in res['subscales'].items():
                    sub_totals[sub] += val
                    
            for sub in sorted_subscales:
                total_row.append(sub_totals[sub])
                
            writer.writerow(total_row)
            
        print("[EXPORT] CSV dışa aktarma başarılı")
        return True
    except Exception as e:
        print(f"[ERROR] CSV kaydetme hatası: {e}")
        raise e
