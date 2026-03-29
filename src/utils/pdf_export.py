"""
PDF Export for Study Mode.

Generates per-patient PDF reports using PyMuPDF (fitz).
Each scale gets its own page with a title, total score, subscale table,
and an optional thumbnail of the scanned form.
"""

import os
import io
from datetime import date

import cv2
import numpy as np

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("[PDF] PyMuPDF bulunamadı. PDF dışa aktarma devre dışı.")

from src.core import study_engine


# A4 dimensions in points (1 pt = 1/72 inch)
_PAGE_W = 595
_PAGE_H = 842
_MARGIN = 50
_LINE_HEIGHT = 18


def _get_font(doc):
    """
    Return (fontname, fontfile) for Turkish-safe rendering.
    Uses Segoe UI if available on Windows, falls back to built-in Helvetica.
    """
    segoe_path = "C:/Windows/Fonts/segoeui.ttf"
    if os.path.exists(segoe_path):
        return "segoeui", segoe_path
    return "helv", None


def _insert_text(page, x, y, text, fontname, fontfile, size=12, color=(0, 0, 0)):
    """Helper to insert text with optional fontfile."""
    if fontfile:
        page.insert_text(
            (x, y), text,
            fontname=fontname,
            fontfile=fontfile,
            fontsize=size,
            color=color
        )
    else:
        page.insert_text(
            (x, y), text,
            fontname=fontname,
            fontsize=size,
            color=color
        )


def _draw_separator(page, y, color=(0.8, 0.8, 0.8)):
    page.draw_line((_MARGIN, y), (_PAGE_W - _MARGIN, y), color=color, width=0.5)


def _image_to_png_bytes(cv2_img):
    """Convert a cv2 BGR image to PNG bytes."""
    _, buf = cv2.imencode(".png", cv2_img)
    return bytes(buf)


def export_patient_pdf(patient, protocol, file_path):
    """
    Generate a PDF report for a single patient.

    One page per scale. Each page contains:
      - Header with patient ID and date
      - Scale name and total score
      - Subscale breakdown table
      - Thumbnail of the first page's aligned image (if available)
      - Approval status

    Args:
        patient: patient dict with scale_results
        protocol: list of protocol_entry dicts
        file_path: destination .pdf path
    """
    if not PDF_AVAILABLE:
        raise ImportError("PyMuPDF bulunamadı. Lütfen 'pip install pymupdf' çalıştırın.")

    print(f"[PDF] Hasta PDF oluşturuluyor: {file_path}")

    doc = fitz.open()
    sorted_protocol = sorted(protocol, key=lambda e: e["order"])
    today = date.today().strftime("%d.%m.%Y")

    for proto in sorted_protocol:
        scale_idx = proto["order"]
        scale_name = proto["scale_name"]

        page = doc.new_page(width=_PAGE_W, height=_PAGE_H)
        fontname, fontfile = _get_font(doc)

        y = _MARGIN

        # --- Header ---
        _insert_text(page, _MARGIN, y, f"GÖRÜNGÜ - Hasta Raporu", fontname, fontfile, size=16, color=(0.05, 0.28, 0.63))
        y += 24
        _insert_text(page, _MARGIN, y, f"Hasta No: {patient['id']}    Tarih: {today}", fontname, fontfile, size=11, color=(0.33, 0.43, 0.48))
        y += 20
        _draw_separator(page, y)
        y += 14

        # --- Scale Title ---
        _insert_text(page, _MARGIN, y, scale_name, fontname, fontfile, size=18, color=(0.05, 0.28, 0.63))
        y += 28

        # --- Score and Approval ---
        scale_data = patient.get("scale_results", {}).get(scale_idx)
        if scale_data is None:
            _insert_text(page, _MARGIN, y, "Bu ölçek için sonuç bulunamadı.", fontname, fontfile, size=12, color=(0.6, 0.6, 0.6))
            doc.save(file_path)
            continue

        total, subscales = study_engine.get_scale_total(scale_data)
        approved = scale_data.get("approved", False)
        approval_color = (0.13, 0.55, 0.13) if approved else (0.83, 0.18, 0.18)
        approval_text = "Onaylandı" if approved else "Onay Bekliyor"

        _insert_text(page, _MARGIN, y, f"TOPLAM PUAN", fontname, fontfile, size=11, color=(0.55, 0.55, 0.55))
        y += 18
        _insert_text(page, _MARGIN, y, str(int(total)), fontname, fontfile, size=40, color=(0.05, 0.28, 0.63))
        y += 50
        _insert_text(page, _MARGIN, y, f"Durum: {approval_text}", fontname, fontfile, size=12, color=approval_color)
        y += 24
        _draw_separator(page, y)
        y += 14

        # --- Subscale Table ---
        if subscales:
            _insert_text(page, _MARGIN, y, "ALT ÖLÇEKLER", fontname, fontfile, size=11, color=(0.55, 0.55, 0.55))
            y += 20

            col1_x = _MARGIN
            col2_x = _PAGE_W - _MARGIN - 80
            row_h = 22
            table_w = _PAGE_W - 2 * _MARGIN

            # Table header background
            page.draw_rect(fitz.Rect(col1_x, y - 14, col1_x + table_w, y + 6), color=None, fill=(0.93, 0.95, 0.98))
            _insert_text(page, col1_x + 4, y, "Alt Ölçek", fontname, fontfile, size=11, color=(0.2, 0.2, 0.2))
            _insert_text(page, col2_x, y, "Puan", fontname, fontfile, size=11, color=(0.2, 0.2, 0.2))
            y += row_h

            for i, (sub, val) in enumerate(sorted(subscales.items())):
                bg = (0.97, 0.97, 0.97) if i % 2 == 0 else None
                if bg:
                    page.draw_rect(fitz.Rect(col1_x, y - 14, col1_x + table_w, y + 6), color=None, fill=bg)
                _insert_text(page, col1_x + 4, y, sub, fontname, fontfile, size=11, color=(0.1, 0.1, 0.1))
                _insert_text(page, col2_x, y, str(int(val)), fontname, fontfile, size=11, color=(0.05, 0.28, 0.63))
                y += row_h

            y += 10
        else:
            _insert_text(page, _MARGIN, y, "Alt ölçek tanımlı değil.", fontname, fontfile, size=11, color=(0.6, 0.6, 0.6))
            y += 20

        _draw_separator(page, y)
        y += 14

        # --- Thumbnail of first page's aligned image ---
        first_page_data = scale_data["pages"].get(0)
        if first_page_data is not None and first_page_data.get("aligned_image") is not None:
            try:
                aligned = first_page_data["aligned_image"]
                h, w = aligned.shape[:2]
                max_thumb_w = _PAGE_W - 2 * _MARGIN
                max_thumb_h = _PAGE_H - y - _MARGIN - 30
                scale_ratio = min(max_thumb_w / w, max_thumb_h / h, 0.5)
                thumb_w = int(w * scale_ratio)
                thumb_h = int(h * scale_ratio)

                if thumb_w > 10 and thumb_h > 10:
                    thumb = cv2.resize(aligned, (thumb_w, thumb_h))
                    png_bytes = _image_to_png_bytes(thumb)
                    img_rect = fitz.Rect(_MARGIN, y, _MARGIN + thumb_w, y + thumb_h)
                    page.insert_image(img_rect, stream=png_bytes)
                    y += thumb_h + 10
            except Exception as e:
                print(f"[PDF] Küçük resim eklenemedi: {e}")

        # --- Footer ---
        page_num_text = f"Sayfa {sorted_protocol.index(proto) + 1} / {len(sorted_protocol)}"
        _insert_text(page, _PAGE_W - _MARGIN - 80, _PAGE_H - 30, page_num_text, fontname, fontfile, size=9, color=(0.6, 0.6, 0.6))

    doc.save(file_path)
    doc.close()
    print(f"[PDF] PDF başarıyla kaydedildi: {file_path}")
    return True
