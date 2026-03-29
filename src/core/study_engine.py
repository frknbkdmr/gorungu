"""
Study Engine - Batch patient scanning logic for Study Mode.

Handles the assignment of patient images to template pages and
orchestrates scoring across all scales in a protocol.
"""

from src.core import omr_engine


def scan_patient(patient_images, protocol, threshold=0.12):
    """
    Score all scales for a single patient.

    Assigns images from patient_images to template pages in protocol order,
    based on each scale's page count. Calls omr_engine.align_images and
    omr_engine.score_page for each page.

    Args:
        patient_images: list of cv2 images (sorted alphabetically from folder)
        protocol: list of protocol_entry dicts (sorted by 'order')
        threshold: OMR fill ratio threshold

    Returns:
        scale_results dict keyed by protocol order index:
        {
            0: {
                "scale_name": str,
                "pages": {
                    page_index: {
                        "total": float,
                        "subscales": dict,
                        "details": list,
                        "aligned_image": np.array,
                        "rois_def": list
                    }
                },
                "approved": False
            },
            ...
        }
    """
    image_cursor = 0
    scale_results = {}

    for proto in sorted(protocol, key=lambda e: e["order"]):
        scale_idx = proto["order"]
        scale_results[scale_idx] = {
            "scale_name": proto["scale_name"],
            "pages": {},
            "approved": False
        }

        for page_def in proto["template_pages"]:
            if image_cursor >= len(patient_images):
                print(f"[STUDY] Uyarı: Yeterli görsel yok (cursor={image_cursor}, toplam={len(patient_images)})")
                break

            input_img = patient_images[image_cursor]
            ref_img = page_def["image"]

            print(f"[STUDY] Hizalanıyor: ölçek={proto['scale_name']}, sayfa={page_def['page_index']}, görsel={image_cursor}")
            aligned, M = omr_engine.align_images(input_img, ref_img)

            if aligned is not None:
                score, subscales, log, details = omr_engine.score_page(
                    aligned, page_def["rois"], threshold
                )
                scale_results[scale_idx]["pages"][page_def["page_index"]] = {
                    "total": score,
                    "subscales": subscales,
                    "details": details,
                    "aligned_image": aligned,
                    "rois_def": page_def["rois"]
                }
                print(f"[STUDY] Puan: {score} ({proto['scale_name']}, sayfa {page_def['page_index']})")
            else:
                print(f"[STUDY] Hizalama başarısız: ölçek={proto['scale_name']}, sayfa={page_def['page_index']}")

            image_cursor += 1

    return scale_results


def get_scale_total(scale_result):
    """
    Compute the total score for a scale (sum across all pages).

    Args:
        scale_result: single entry from scale_results dict

    Returns:
        (total, combined_subscales) tuple
    """
    total = 0
    combined_subscales = {}
    for page_data in scale_result["pages"].values():
        total += page_data["total"]
        for sub, val in page_data["subscales"].items():
            combined_subscales[sub] = combined_subscales.get(sub, 0) + val
    return total, combined_subscales


def build_combined_table(patients, protocol):
    """
    Build a flat list of dicts for combined CSV export.

    Each dict represents one patient with aggregated scores per scale.

    Args:
        patients: list of patient dicts
        protocol: list of protocol_entry dicts

    Returns:
        list of dicts, one per patient, with keys:
            "Hasta No", "{scale_name} Toplam", "{scale_name}_{subscale}", ...
    """
    rows = []
    sorted_protocol = sorted(protocol, key=lambda e: e["order"])

    for patient in patients:
        row = {"Hasta No": patient["id"]}

        for proto in sorted_protocol:
            scale_idx = proto["order"]
            scale_name = proto["scale_name"]

            if scale_idx in patient.get("scale_results", {}):
                total, subscales = get_scale_total(patient["scale_results"][scale_idx])
                row[f"{scale_name} Toplam"] = total
                for sub, val in subscales.items():
                    row[f"{scale_name}_{sub}"] = val
            else:
                row[f"{scale_name} Toplam"] = ""

        rows.append(row)

    return rows
