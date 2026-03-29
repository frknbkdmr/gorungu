"""
Study I/O utilities for Study Mode.

Handles patient folder discovery and multi-format export
(per-patient CSV, combined summary CSV).
"""

import os
import csv

from src.utils import file_io
from src.core import study_engine


# Image extensions accepted from patient folders
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".pdf"}


def load_patient_folders(root_path):
    """
    Discover patient subfolders inside root_path.

    Each immediate subdirectory is treated as one patient. Image files
    inside each subfolder are collected and sorted alphabetically.

    Args:
        root_path: path to the directory containing patient subfolders

    Returns:
        list of dicts sorted by folder name:
        [
            {
                "folder_name": str,
                "folder_path": str,
                "image_paths": list[str]   # sorted alphabetically
            },
            ...
        ]
    """
    print(f"[STUDY_IO] Hasta klasörleri taranıyor: {root_path}")
    entries = []

    try:
        with os.scandir(root_path) as it:
            for entry in it:
                if entry.is_dir():
                    image_paths = _collect_images(entry.path)
                    entries.append({
                        "folder_name": entry.name,
                        "folder_path": entry.path,
                        "image_paths": image_paths
                    })
    except Exception as e:
        print(f"[STUDY_IO] Hata: {e}")
        raise

    entries.sort(key=lambda e: e["folder_name"])
    print(f"[STUDY_IO] {len(entries)} hasta klasörü bulundu")
    return entries


def _collect_images(folder_path):
    """Return sorted list of image file paths inside a folder (non-recursive)."""
    paths = []
    try:
        with os.scandir(folder_path) as it:
            for entry in it:
                if entry.is_file():
                    ext = os.path.splitext(entry.name)[1].lower()
                    if ext in _IMAGE_EXTS:
                        paths.append(entry.path)
    except Exception as e:
        print(f"[STUDY_IO] Klasör okunamadı {folder_path}: {e}")
    paths.sort(key=lambda p: os.path.basename(p))
    return paths


def load_patient_images(image_paths):
    """
    Load all images for a patient from a list of file paths.

    Args:
        image_paths: list of file paths (may include PDFs)

    Returns:
        list of cv2 images in order
    """
    images = []
    for path in image_paths:
        imgs = file_io.load_images_from_file(path)
        images.extend(imgs)
    return images


def export_patient_csv(patient, protocol, file_path):
    """
    Export a single patient's results as a CSV file.

    Rows: one per scale (aggregated across pages).
    Columns: Ölçek Adı, Toplam Puan, <subscale columns...>

    Args:
        patient: patient dict with scale_results
        protocol: list of protocol_entry dicts
        file_path: destination .csv path
    """
    print(f"[STUDY_IO] Hasta CSV dışa aktarılıyor: {file_path}")

    sorted_protocol = sorted(protocol, key=lambda e: e["order"])

    # Collect all unique subscale names
    all_subscales = set()
    for proto in sorted_protocol:
        scale_idx = proto["order"]
        if scale_idx in patient.get("scale_results", {}):
            _, subscales = study_engine.get_scale_total(patient["scale_results"][scale_idx])
            all_subscales.update(subscales.keys())
    sorted_subscales = sorted(list(all_subscales))

    header = ["Ölçek Adı", "Toplam Puan", "Onay"] + sorted_subscales

    try:
        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([f"Hasta {patient['id']} Raporu"])
            writer.writerow(header)

            grand_total = 0
            for proto in sorted_protocol:
                scale_idx = proto["order"]
                scale_name = proto["scale_name"]

                if scale_idx in patient.get("scale_results", {}):
                    scale_res = patient["scale_results"][scale_idx]
                    total, subscales = study_engine.get_scale_total(scale_res)
                    approved = "Evet" if scale_res.get("approved", False) else "Hayır"
                    grand_total += total
                    row = [scale_name, total, approved]
                    for sub in sorted_subscales:
                        row.append(subscales.get(sub, 0))
                else:
                    row = [scale_name, "", "Hayır"] + [""] * len(sorted_subscales)
                writer.writerow(row)

            writer.writerow([])
            writer.writerow(["GENEL TOPLAM", grand_total])

        print(f"[STUDY_IO] Hasta CSV başarıyla yazıldı: {file_path}")
        return True
    except Exception as e:
        print(f"[STUDY_IO] CSV kaydetme hatası: {e}")
        raise


def export_combined_csv(patients, protocol, file_path):
    """
    Export all patients in a single summary CSV.

    Rows: one per patient.
    Columns: Hasta No, {Scale} Toplam, {Scale}_{Subscale}, ...

    Args:
        patients: list of patient dicts
        protocol: list of protocol_entry dicts
        file_path: destination .csv path
    """
    print(f"[STUDY_IO] Birleşik CSV dışa aktarılıyor: {file_path}")

    rows = study_engine.build_combined_table(patients, protocol)

    if not rows:
        print("[STUDY_IO] Dışa aktarılacak veri yok")
        return False

    # Collect ordered column names preserving insertion order
    all_keys = ["Hasta No"]
    seen = set(all_keys)
    for row in rows:
        for key in row:
            if key not in seen:
                all_keys.append(key)
                seen.add(key)

    try:
        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=all_keys, delimiter=";", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

        print(f"[STUDY_IO] Birleşik CSV başarıyla yazıldı: {file_path}")
        return True
    except Exception as e:
        print(f"[STUDY_IO] Birleşik CSV hatası: {e}")
        raise
