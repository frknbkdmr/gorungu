"""
Study Mode - Batch patient scanning with supervision and export.

Workflow:
  Phase 1 (Setup)  - Load protocol templates, select patient root folder
  Phase 2 (Review) - Navigate patients/scales, score pages, approve results
  Phase 3 (Export) - Export per-patient CSV, combined CSV, and PDF reports
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import cv2
import numpy as np
from PIL import Image, ImageTk

from src.utils import file_io, study_io
from src.utils import pdf_export
from src.core import omr_engine, study_engine
from src.ui.styles import Style, Tooltip, create_accent_button, create_secondary_button
from src.ui import dialogs


class StudyMode:
    def __init__(self, app):
        self.app = app

        # Protocol: list of protocol_entry dicts
        self.protocol = []

        # Patients: list of patient dicts
        self.patients = []

        # Navigation state
        self.current_patient_idx = 0
        self.current_scale_idx = 0
        self.current_page_idx = 0

        # Canvas / zoom / pan state
        self.canvas = None
        self.tk_image = None
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.image_scale = 1.0

        self.dynamic_threshold = 0.12
        self.edit_mode = False
        self.phase = "setup"  # "setup" | "review" | "export"

        self.parent_frame = None
        self.colors = Style.get_theme_colors()

    # ==========================================================================
    # Phase management
    # ==========================================================================

    def setup_ui(self, parent_frame):
        self.parent_frame = parent_frame
        self.colors = Style.get_theme_colors()
        self._show_phase_setup()

    def _clear_phase(self):
        """Destroy all widgets and reset canvas refs."""
        self.canvas = None
        self.tk_image = None
        for w in self.parent_frame.winfo_children():
            w.destroy()

    # ==========================================================================
    # Phase 1 – Setup
    # ==========================================================================

    def _show_phase_setup(self):
        self.phase = "setup"
        self._clear_phase()
        self.app.status_var.set("Çalışma Modu — Protokol ve hasta klasörü yükleyin.")

        outer = ctk.CTkFrame(self.parent_frame, fg_color=self.colors["bg_primary"], corner_radius=0)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=2)
        outer.columnconfigure(2, weight=1)
        outer.rowconfigure(0, weight=1)

        # --- Left: Protocol ---
        left = ctk.CTkFrame(outer, fg_color=self.colors["bg_secondary"], corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 1), pady=0)

        lc = ctk.CTkScrollableFrame(left, fg_color="transparent")
        lc.pack(fill="both", expand=True, padx=Style.PADDING_MD, pady=Style.PADDING_MD)

        self._section(lc, "1. PROTOKOL (ŞABLONLAR)")

        create_secondary_button(lc, text="➕ Şablon Ekle", command=self._add_template).pack(
            fill="x", pady=(0, Style.PADDING_MD))

        self._protocol_cards_frame = ctk.CTkFrame(lc, fg_color="transparent")
        self._protocol_cards_frame.pack(fill="x")
        self._rebuild_protocol_cards()

        # --- Middle: Patients ---
        mid = ctk.CTkFrame(outer, fg_color=self.colors["bg_primary"], corner_radius=0)
        mid.grid(row=0, column=1, sticky="nsew", padx=1, pady=0)

        mc = ctk.CTkFrame(mid, fg_color="transparent")
        mc.pack(fill="both", expand=True, padx=Style.PADDING_LG, pady=Style.PADDING_MD)

        self._section(mc, "2. HASTA KÖK KLASÖRÜ")

        folder_row = ctk.CTkFrame(mc, fg_color="transparent")
        folder_row.pack(fill="x", pady=(0, Style.PADDING_MD))

        self._lbl_root_folder = ctk.CTkLabel(
            folder_row,
            text="Klasör seçilmedi",
            font=Style.FONTS["small"],
            text_color=self.colors["text_muted"],
            anchor="w"
        )
        self._lbl_root_folder.pack(side="left", fill="x", expand=True)

        create_secondary_button(folder_row, text="📂 Seç", command=self._select_root_folder, width=80).pack(side="right")

        self._section(mc, "HASTALAR")

        self._patient_list_frame = ctk.CTkScrollableFrame(
            mc,
            fg_color=self.colors["input_bg"],
            corner_radius=Style.CORNER_RADIUS_SM
        )
        self._patient_list_frame.pack(fill="both", expand=True, pady=(0, Style.PADDING_MD))

        self._lbl_no_patients = ctk.CTkLabel(
            self._patient_list_frame,
            text="Henüz hasta klasörü yüklenmedi.",
            font=Style.FONTS["small"],
            text_color=self.colors["text_muted"]
        )
        self._lbl_no_patients.pack(pady=Style.PADDING_LG)

        btn_start = create_accent_button(mc, text="▶  Taramayı Başlat", command=self._start_review)
        btn_start.pack(fill="x")
        self._btn_start = btn_start

        # --- Right: Validation ---
        right = ctk.CTkFrame(outer, fg_color=self.colors["bg_secondary"], corner_radius=0)
        right.grid(row=0, column=2, sticky="nsew", padx=(1, 0), pady=0)

        rc = ctk.CTkScrollableFrame(right, fg_color="transparent")
        rc.pack(fill="both", expand=True, padx=Style.PADDING_MD, pady=Style.PADDING_MD)

        self._section(rc, "DOĞRULAMA")

        self._validation_frame = ctk.CTkFrame(rc, fg_color="transparent")
        self._validation_frame.pack(fill="x")
        self._refresh_validation()

    def _section(self, parent, text):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=(Style.PADDING_SM, Style.PADDING_MD))
        ctk.CTkLabel(f, text=text, font=Style.FONTS["small_bold"],
                     text_color=self.colors["text_muted"]).pack(side="left")
        ctk.CTkFrame(f, height=1, fg_color=self.colors["border"]).pack(
            side="left", fill="x", expand=True, padx=(Style.PADDING_SM, 0))

    def _rebuild_protocol_cards(self):
        for w in self._protocol_cards_frame.winfo_children():
            w.destroy()

        if not self.protocol:
            ctk.CTkLabel(
                self._protocol_cards_frame,
                text="Henüz şablon eklenmedi.",
                font=Style.FONTS["small"],
                text_color=self.colors["text_muted"]
            ).pack(pady=Style.PADDING_MD)
            return

        for i, entry in enumerate(self.protocol):
            card = ctk.CTkFrame(
                self._protocol_cards_frame,
                fg_color=self.colors["bg_tertiary"],
                corner_radius=Style.CORNER_RADIUS_SM
            )
            card.pack(fill="x", pady=2)

            ctk.CTkLabel(
                card,
                text=f"{i + 1}.",
                font=Style.FONTS["body_bold"],
                text_color=self.colors["accent"],
                width=28
            ).pack(side="left", padx=(Style.PADDING_SM, 0), pady=Style.PADDING_SM)

            ctk.CTkLabel(
                card,
                text=entry["scale_name"],
                font=Style.FONTS["body"],
                text_color=self.colors["text_primary"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=Style.PADDING_SM)

            ctk.CTkLabel(
                card,
                text=f"{entry['page_count']}s",
                font=Style.FONTS["small"],
                text_color=self.colors["text_muted"],
                width=24
            ).pack(side="left")

            ctk.CTkButton(
                card, text="↑", width=28, height=28,
                fg_color="transparent", hover_color=self.colors["border"],
                text_color=self.colors["text_secondary"], font=Style.FONTS["body_bold"],
                corner_radius=Style.CORNER_RADIUS_SM,
                command=lambda idx=i: self._move_protocol_entry(idx, -1)
            ).pack(side="left", padx=2, pady=4)

            ctk.CTkButton(
                card, text="↓", width=28, height=28,
                fg_color="transparent", hover_color=self.colors["border"],
                text_color=self.colors["text_secondary"], font=Style.FONTS["body_bold"],
                corner_radius=Style.CORNER_RADIUS_SM,
                command=lambda idx=i: self._move_protocol_entry(idx, 1)
            ).pack(side="left", padx=2, pady=4)

            ctk.CTkButton(
                card, text="✕", width=28, height=28,
                fg_color="transparent", hover_color=self.colors["error"],
                text_color=self.colors["text_muted"], font=Style.FONTS["small_bold"],
                corner_radius=Style.CORNER_RADIUS_SM,
                command=lambda idx=i: self._remove_protocol_entry(idx)
            ).pack(side="left", padx=(0, Style.PADDING_SM), pady=4)

    def _add_template(self):
        paths = filedialog.askopenfilenames(filetypes=[("JSON Şablonu", "*.json")])
        if not paths:
            return
        for path in paths:
            try:
                data = file_io.load_template_json(path)
                base_dir = os.path.dirname(path)
                template_pages = []
                if "pages" in data:
                    for p_data in data["pages"]:
                        ref_path = os.path.join(base_dir, p_data["ref_image_storage"])
                        if os.path.exists(ref_path):
                            img = cv2.imread(ref_path)
                            template_pages.append({
                                "image": img,
                                "rois": p_data["rois"],
                                "page_index": p_data["page_index"]
                            })
                else:
                    ref_name = data.get("ref_image_storage", "") or data.get("ref_image_path", "")
                    ref_path = os.path.join(base_dir, ref_name)
                    if os.path.exists(ref_path):
                        img = cv2.imread(ref_path)
                        template_pages.append({"image": img, "rois": data["rois"], "page_index": 0})

                if not template_pages:
                    messagebox.showwarning("Uyarı", f"Referans görseller bulunamadı:\n{path}")
                    continue

                scale_name = os.path.splitext(os.path.basename(path))[0]
                self.protocol.append({
                    "order": len(self.protocol),
                    "template_path": path,
                    "scale_name": scale_name,
                    "page_count": len(template_pages),
                    "template_pages": template_pages
                })
                print(f"[STUDY] Şablon eklendi: {scale_name} ({len(template_pages)} sayfa)")
            except Exception as e:
                messagebox.showerror("Hata", f"Şablon yüklenemedi:\n{path}\n\n{e}")

        self._rebuild_protocol_cards()
        self._refresh_validation()

    def _move_protocol_entry(self, idx, direction):
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self.protocol):
            return
        self.protocol[idx], self.protocol[new_idx] = self.protocol[new_idx], self.protocol[idx]
        for i, e in enumerate(self.protocol):
            e["order"] = i
        self._rebuild_protocol_cards()
        self._refresh_validation()

    def _remove_protocol_entry(self, idx):
        self.protocol.pop(idx)
        for i, e in enumerate(self.protocol):
            e["order"] = i
        self._rebuild_protocol_cards()
        self._refresh_validation()

    def _select_root_folder(self):
        folder = filedialog.askdirectory(title="Hasta Klasörlerini İçeren Kök Klasörü Seçin")
        if not folder:
            return

        try:
            entries = study_io.load_patient_folders(folder)
        except Exception as e:
            messagebox.showerror("Hata", str(e))
            return

        if not entries:
            messagebox.showwarning("Uyarı", "Bu klasörde hasta alt klasörü bulunamadı.")
            return

        self._lbl_root_folder.configure(
            text=os.path.basename(folder),
            text_color=self.colors["success"]
        )

        # Build patient list
        self.patients = []
        for i, entry in enumerate(entries):
            self.patients.append({
                "id": i + 1,
                "folder_name": entry["folder_name"],
                "folder_path": entry["folder_path"],
                "image_paths": entry["image_paths"],
                "images": [],  # loaded on demand
                "scale_results": {},
                "status": "pending"
            })

        self._rebuild_patient_list()
        self._refresh_validation()

    def _rebuild_patient_list(self):
        for w in self._patient_list_frame.winfo_children():
            w.destroy()

        if not self.patients:
            ctk.CTkLabel(
                self._patient_list_frame,
                text="Henüz hasta klasörü yüklenmedi.",
                font=Style.FONTS["small"],
                text_color=self.colors["text_muted"]
            ).pack(pady=Style.PADDING_LG)
            return

        expected_pages = sum(e["page_count"] for e in self.protocol)

        for patient in self.patients:
            found = sum(
                1 for p in patient["image_paths"]
                if os.path.splitext(p)[1].lower() in {".jpg", ".jpeg", ".png", ".bmp"}
            )
            # count PDFs as potentially multi-page (shown as ?)
            pdf_count = sum(1 for p in patient["image_paths"] if p.lower().endswith(".pdf"))
            ok = (found + pdf_count) >= 1  # basic check

            status_color = self.colors["success"] if ok else self.colors["warning"]
            badge = "✓" if ok else "⚠"

            row = ctk.CTkFrame(self._patient_list_frame, fg_color="transparent")
            row.pack(fill="x", padx=Style.PADDING_SM, pady=1)

            ctk.CTkLabel(row, text=f"Hasta {patient['id']}", font=Style.FONTS["small"],
                         text_color=self.colors["text_primary"], width=70, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=patient["folder_name"], font=Style.FONTS["small"],
                         text_color=self.colors["text_secondary"], anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(row, text=f"{len(patient['image_paths'])} dosya", font=Style.FONTS["small"],
                         text_color=self.colors["text_muted"], width=60).pack(side="left")
            ctk.CTkLabel(row, text=badge, font=Style.FONTS["body_bold"],
                         text_color=status_color, width=20).pack(side="right")

    def _refresh_validation(self):
        for w in self._validation_frame.winfo_children():
            w.destroy()

        total_pages = sum(e["page_count"] for e in self.protocol)
        ctk.CTkLabel(
            self._validation_frame,
            text=f"Şablonlar: {len(self.protocol)}   Toplam sayfa: {total_pages}",
            font=Style.FONTS["small"],
            text_color=self.colors["text_secondary"],
            anchor="w"
        ).pack(anchor="w", pady=(0, Style.PADDING_SM))

        ctk.CTkLabel(
            self._validation_frame,
            text=f"Hastalar: {len(self.patients)}",
            font=Style.FONTS["small"],
            text_color=self.colors["text_secondary"],
            anchor="w"
        ).pack(anchor="w", pady=(0, Style.PADDING_MD))

        if not self.protocol:
            self._warn("En az 1 şablon ekleyin.")
        if not self.patients:
            self._warn("Hasta klasörü seçin.")

        if self.protocol and self.patients and total_pages > 0:
            for patient in self.patients:
                n = len(patient["image_paths"])
                if n < total_pages:
                    self._warn(f"Hasta {patient['id']}: {total_pages} bekleniyor, {n} bulundu")

    def _warn(self, text):
        ctk.CTkLabel(
            self._validation_frame,
            text=f"⚠ {text}",
            font=Style.FONTS["small"],
            text_color=self.colors["warning"],
            anchor="w",
            wraplength=200
        ).pack(anchor="w", pady=2)

    def _start_review(self):
        if not self.protocol:
            messagebox.showwarning("Uyarı", "En az 1 şablon ekleyin.")
            return
        if not self.patients:
            messagebox.showwarning("Uyarı", "Hasta klasörü seçin.")
            return

        self.current_patient_idx = 0
        self.current_scale_idx = 0
        self.current_page_idx = 0
        self._show_phase_review()

    # ==========================================================================
    # Phase 2 – Review
    # ==========================================================================

    def _show_phase_review(self):
        self.phase = "review"
        self._clear_phase()
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0

        self._update_status_bar()

        # --- Left panel ---
        left = ctk.CTkFrame(
            self.parent_frame,
            width=Style.PANEL_WIDTH_MD,
            fg_color=self.colors["bg_secondary"],
            corner_radius=0
        )
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        lc = ctk.CTkScrollableFrame(left, fg_color="transparent")
        lc.pack(fill="both", expand=True, padx=Style.PADDING_MD, pady=Style.PADDING_MD)

        # Patient navigation
        self._section(lc, "HASTA")
        nav_p = ctk.CTkFrame(lc, fg_color="transparent")
        nav_p.pack(fill="x", pady=(0, Style.PADDING_SM))

        ctk.CTkButton(nav_p, text="◀", width=40, height=Style.BUTTON_HEIGHT_SM,
                      fg_color=self.colors["bg_tertiary"], hover_color=self.colors["border"],
                      text_color=self.colors["text_primary"], corner_radius=Style.CORNER_RADIUS_SM,
                      command=self._prev_patient).pack(side="left")

        self._lbl_patient = ctk.CTkLabel(nav_p, text="", font=Style.FONTS["body_bold"],
                                          text_color=self.colors["text_primary"])
        self._lbl_patient.pack(side="left", expand=True)

        ctk.CTkButton(nav_p, text="▶", width=40, height=Style.BUTTON_HEIGHT_SM,
                      fg_color=self.colors["bg_tertiary"], hover_color=self.colors["border"],
                      text_color=self.colors["text_primary"], corner_radius=Style.CORNER_RADIUS_SM,
                      command=self._next_patient).pack(side="right")

        self._lbl_patient_name = ctk.CTkLabel(lc, text="", font=Style.FONTS["small"],
                                               text_color=self.colors["text_muted"], anchor="w")
        self._lbl_patient_name.pack(anchor="w", pady=(0, Style.PADDING_SM))

        # Scale navigation
        self._section(lc, "ÖLÇEK")
        nav_s = ctk.CTkFrame(lc, fg_color="transparent")
        nav_s.pack(fill="x", pady=(0, Style.PADDING_SM))

        ctk.CTkButton(nav_s, text="◀", width=40, height=Style.BUTTON_HEIGHT_SM,
                      fg_color=self.colors["bg_tertiary"], hover_color=self.colors["border"],
                      text_color=self.colors["text_primary"], corner_radius=Style.CORNER_RADIUS_SM,
                      command=self._prev_scale).pack(side="left")

        self._lbl_scale = ctk.CTkLabel(nav_s, text="", font=Style.FONTS["body_bold"],
                                        text_color=self.colors["text_primary"])
        self._lbl_scale.pack(side="left", expand=True)

        ctk.CTkButton(nav_s, text="▶", width=40, height=Style.BUTTON_HEIGHT_SM,
                      fg_color=self.colors["bg_tertiary"], hover_color=self.colors["border"],
                      text_color=self.colors["text_primary"], corner_radius=Style.CORNER_RADIUS_SM,
                      command=self._next_scale).pack(side="right")

        # Page navigation
        self._section(lc, "SAYFA")
        nav_pg = ctk.CTkFrame(lc, fg_color="transparent")
        nav_pg.pack(fill="x", pady=(0, Style.PADDING_MD))

        ctk.CTkButton(nav_pg, text="◀", width=40, height=Style.BUTTON_HEIGHT_SM,
                      fg_color=self.colors["bg_tertiary"], hover_color=self.colors["border"],
                      text_color=self.colors["text_primary"], corner_radius=Style.CORNER_RADIUS_SM,
                      command=self._prev_page).pack(side="left")

        self._lbl_page = ctk.CTkLabel(nav_pg, text="", font=Style.FONTS["body"],
                                       text_color=self.colors["text_primary"])
        self._lbl_page.pack(side="left", expand=True)

        ctk.CTkButton(nav_pg, text="▶", width=40, height=Style.BUTTON_HEIGHT_SM,
                      fg_color=self.colors["bg_tertiary"], hover_color=self.colors["border"],
                      text_color=self.colors["text_primary"], corner_radius=Style.CORNER_RADIUS_SM,
                      command=self._next_page).pack(side="right")

        # Threshold
        self._section(lc, "HASSASİYET")
        thresh_row = ctk.CTkFrame(lc, fg_color="transparent")
        thresh_row.pack(fill="x")
        ctk.CTkLabel(thresh_row, text="Eşik:", font=Style.FONTS["small"],
                     text_color=self.colors["text_secondary"]).pack(side="left")
        self._lbl_threshold = ctk.CTkLabel(thresh_row, text=f"{self.dynamic_threshold:.2f}",
                                            font=Style.FONTS["mono"], text_color=self.colors["accent"])
        self._lbl_threshold.pack(side="right")

        self._threshold_slider = ctk.CTkSlider(
            lc, from_=0.01, to=0.50, number_of_steps=49,
            command=self._on_threshold_change,
            fg_color=self.colors["bg_tertiary"],
            progress_color=self.colors["accent"],
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            height=16
        )
        self._threshold_slider.set(self.dynamic_threshold)
        self._threshold_slider.pack(fill="x", pady=(Style.PADDING_SM, Style.PADDING_LG))

        # Crop section
        self._section(lc, "KIRPMA")
        create_secondary_button(lc, text="✂️ Otomatik Kırp",
                                command=self._auto_crop_current_page).pack(
            fill="x", pady=(0, Style.PADDING_XS))
        create_secondary_button(lc, text="📐 Manuel Kırp/Düzelt",
                                command=self._open_corner_correction).pack(
            fill="x", pady=(0, Style.PADDING_LG))

        # Action buttons
        self._progress_bar = ctk.CTkProgressBar(
            lc, fg_color=self.colors["bg_tertiary"],
            progress_color=self.colors["accent"], height=6, corner_radius=3
        )
        self._progress_bar.set(0)

        _b = create_accent_button(lc, text="⚡ Sayfayı Puanla", command=self._score_current_view)
        _b.pack(fill="x", pady=(0, Style.PADDING_XS))
        Tooltip(_b, "Mevcut sayfayı şablona hizalayıp puanla.")

        self._lbl_align_quality = ctk.CTkLabel(
            lc, text="Hizalama: —",
            font=Style.FONTS["small"],
            text_color=self.colors["text_muted"],
            anchor="w"
        )
        self._lbl_align_quality.pack(fill="x", pady=(0, Style.PADDING_SM))

        _b = create_secondary_button(lc, text="🔄 Tüm Hastaları Tara", command=self._batch_scan_all)
        _b.pack(fill="x", pady=(0, Style.PADDING_SM))
        Tooltip(_b, "Tüm hastaları otomatik olarak tara. Mevcut manuel düzeltmeler korunmaz.")

        self._btn_edit = ctk.CTkButton(
            lc, text="✎ Veri Düzenleme: Kapalı",
            command=self._toggle_edit_mode,
            font=Style.FONTS["button"],
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            height=Style.BUTTON_HEIGHT_SM,
            corner_radius=Style.CORNER_RADIUS_MD
        )
        self._btn_edit.pack(fill="x", pady=Style.PADDING_XS)

        # Approve button
        ctk.CTkFrame(lc, fg_color="transparent", height=10).pack(fill="x")
        self._btn_approve = ctk.CTkButton(
            lc, text="✔  ONAYLA",
            command=self._approve_current_scale,
            font=Style.FONTS["body_bold"],
            fg_color=self.colors["success"],
            hover_color="#16a34a",
            text_color="#ffffff",
            height=Style.BUTTON_HEIGHT,
            corner_radius=Style.CORNER_RADIUS_MD
        )
        self._btn_approve.pack(fill="x", pady=Style.PADDING_XS)

        # Finish session
        ctk.CTkFrame(lc, fg_color="transparent", height=20).pack(fill="x")
        create_secondary_button(lc, text="📊 Oturumu Bitir / Dışa Aktar",
                                command=self._show_phase_export).pack(fill="x")

        # --- Center canvas ---
        center = ctk.CTkFrame(self.parent_frame, fg_color=self.colors["bg_primary"], corner_radius=0)
        center.pack(side="left", fill="both", expand=True)

        # Breadcrumb
        self._lbl_breadcrumb = ctk.CTkLabel(
            center, text="", font=Style.FONTS["small"],
            text_color=self.colors["text_muted"], anchor="w"
        )
        self._lbl_breadcrumb.pack(fill="x", padx=Style.PADDING_MD, pady=(Style.PADDING_SM, 0))

        self.canvas = tk.Canvas(center, bg=self.colors["canvas"], bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<MouseWheel>", self._on_zoom)
        self.canvas.bind("<Button-4>", self._on_zoom)
        self.canvas.bind("<Button-5>", self._on_zoom)
        self.canvas.bind("<ButtonPress-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._do_pan)
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_left_press)
        self.canvas.bind("<B1-Motion>", self._do_pan)

        # --- Right panel ---
        right = ctk.CTkFrame(self.parent_frame, width=300,
                             fg_color=self.colors["bg_secondary"], corner_radius=0)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        rc = ctk.CTkFrame(right, fg_color="transparent")
        rc.pack(fill="both", expand=True, padx=Style.PADDING_MD, pady=Style.PADDING_MD)

        self._section(rc, "SONUÇLAR")

        self._lbl_total_score = ctk.CTkLabel(
            rc, text="0",
            font=Style.FONTS["score_display"],
            text_color=self.colors["accent"]
        )
        self._lbl_total_score.pack(anchor="e", pady=(0, Style.PADDING_SM))

        self._txt_results = ctk.CTkTextbox(
            rc, font=Style.FONTS["mono"],
            fg_color=self.colors["input_bg"],
            text_color=self.colors["text_primary"],
            border_width=0, corner_radius=Style.CORNER_RADIUS_SM,
            wrap="word"
        )
        self._txt_results.pack(fill="both", expand=True)

        # Initialize display
        self._refresh_review_ui()

    def _refresh_review_ui(self):
        """Update all labels, canvas, and results for current patient/scale/page."""
        if not self.protocol or not self.patients:
            return

        p = self.patients[self.current_patient_idx]
        proto = self.protocol[self.current_scale_idx]
        total_pages = proto["page_count"]

        # Labels
        self._lbl_patient.configure(
            text=f"Hasta {self.current_patient_idx + 1} / {len(self.patients)}")
        self._lbl_patient_name.configure(text=p["folder_name"])
        self._lbl_scale.configure(
            text=f"{proto['scale_name']} ({self.current_scale_idx + 1}/{len(self.protocol)})")
        self._lbl_page.configure(
            text=f"{self.current_page_idx + 1} / {total_pages}")
        self._lbl_breadcrumb.configure(
            text=f"Hasta {p['id']}  ›  {proto['scale_name']}  ›  Sayfa {self.current_page_idx + 1}")
        self.app.root.title(
            f"GÖRÜNGÜ — Hasta {p['id']}: {p['folder_name']}  ›  {proto['scale_name']}  ›  Sayfa {self.current_page_idx + 1}"
        )

        # Approve button state
        scale_res = p.get("scale_results", {}).get(self.current_scale_idx)
        if scale_res and scale_res.get("approved"):
            self._btn_approve.configure(
                text="✔  ONAYLANDI", fg_color=self.colors["text_muted"],
                hover_color=self.colors["text_muted"])
        else:
            self._btn_approve.configure(
                text="✔  ONAYLA", fg_color=self.colors["success"], hover_color="#16a34a")

        self._update_results_panel()
        self._refresh_canvas()

    def _get_current_image(self):
        """Get the cv2 image for current patient/scale/page position."""
        patient = self.patients[self.current_patient_idx]

        # Load images if not yet loaded
        if not patient["images"]:
            try:
                patient["images"] = study_io.load_patient_images(patient["image_paths"])
            except Exception as e:
                print(f"[STUDY] Görsel yükleme hatası: {e}")
                return None

        # Calculate global image index for this scale+page
        image_offset = 0
        for i in range(self.current_scale_idx):
            image_offset += self.protocol[i]["page_count"]
        image_offset += self.current_page_idx

        if image_offset < len(patient["images"]):
            return patient["images"][image_offset]
        return None

    def _set_current_image(self, img):
        """Replace the cv2 image for current patient/scale/page position."""
        patient = self.patients[self.current_patient_idx]
        if not patient["images"]:
            return
        image_offset = 0
        for i in range(self.current_scale_idx):
            image_offset += self.protocol[i]["page_count"]
        image_offset += self.current_page_idx
        if image_offset < len(patient["images"]):
            patient["images"][image_offset] = img
            # Invalidate cached result for this page since image changed
            scale_res = patient.get("scale_results", {}).get(self.current_scale_idx)
            if scale_res and self.current_page_idx in scale_res.get("pages", {}):
                del scale_res["pages"][self.current_page_idx]

    def _auto_crop_current_page(self):
        """Auto-detect corners and warp the current page image."""
        if not self.patients:
            return
        img = self._get_current_image()
        if img is None:
            return
        try:
            found, corners = omr_engine.detect_corners(img)
            if found:
                warped = omr_engine.get_four_point_transform(img, corners)
                self._set_current_image(warped)
                self._refresh_canvas()
                self.app.status_var.set("Otomatik kırpma uygulandı.")
            else:
                messagebox.showwarning("Başarısız", "Otomatik köşe tespiti başarısız oldu. Manuel kırpma kullanın.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _open_corner_correction(self):
        """Open the corner correction dialog for the current page image."""
        if not self.patients:
            return
        img = self._get_current_image()
        if img is None:
            return
        d = dialogs.CornerCorrectionDialog(self.app.root, img)
        if d.result_image is not None:
            self._set_current_image(d.result_image)
            self._refresh_canvas()
            self.app.status_var.set("Manuel kırpma uygulandı.")

    def _get_current_page_result(self):
        """Return the page result dict for current patient/scale/page, or None."""
        patient = self.patients[self.current_patient_idx]
        scale_res = patient.get("scale_results", {}).get(self.current_scale_idx)
        if scale_res:
            return scale_res["pages"].get(self.current_page_idx)
        return None

    def _refresh_canvas(self):
        if self.canvas is None:
            return

        page_result = self._get_current_page_result()

        if page_result is not None and page_result.get("aligned_image") is not None:
            img = page_result["aligned_image"]
        else:
            img = self._get_current_image()

        if img is None:
            self.canvas.delete("all")
            self.canvas.create_text(
                400, 300, text="Görsel bulunamadı",
                fill=self.colors["text_muted"], font=("Segoe UI", 14)
            )
            return

        h, w = img.shape[:2]
        canvas_h, canvas_w = 700, 1100
        self.image_scale = min(canvas_w / w, canvas_h / h, 1.0)
        final_scale = self.image_scale * self.zoom_scale
        new_w, new_h = int(w * final_scale), int(h * final_scale)
        if new_w < 1 or new_h < 1:
            return

        resized = cv2.resize(img, (new_w, new_h))
        rgb_img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
        self.tk_image = ImageTk.PhotoImage(pil_img)

        self.canvas.delete("all")
        self.canvas.create_image(self.pan_x, self.pan_y, anchor=tk.NW, image=self.tk_image)

        if page_result is not None and page_result.get("details"):
            self._draw_rois(page_result["details"])

    def _draw_rois(self, details):
        self.canvas.delete("study_roi")
        for idx, item in enumerate(details):
            roi = item["roi_def"]
            x, y = self._to_canvas(roi["x"], roi["y"])
            w = roi["w"] * self.image_scale * self.zoom_scale
            h = roi["h"] * self.image_scale * self.zoom_scale
            color = "#22c55e" if item["is_marked"] else "#ef4444"
            self.canvas.create_rectangle(x, y, x + w, y + h, outline=color, width=2,
                                          tags=("study_roi", f"roi_{idx}"))

    def _to_canvas(self, img_x, img_y):
        x = (img_x * self.image_scale * self.zoom_scale) + self.pan_x
        y = (img_y * self.image_scale * self.zoom_scale) + self.pan_y
        return x, y

    def _to_image(self, cx, cy):
        x = (cx - self.pan_x) / (self.image_scale * self.zoom_scale)
        y = (cy - self.pan_y) / (self.image_scale * self.zoom_scale)
        return int(x), int(y)

    def _update_results_panel(self):
        self._txt_results.delete("1.0", "end")
        patient = self.patients[self.current_patient_idx]
        scale_res = patient.get("scale_results", {}).get(self.current_scale_idx)

        if scale_res is None:
            self._lbl_total_score.configure(text="—")
            self._txt_results.insert("end", "Henüz puanlanmadı.\n")
            return

        total, subscales = study_engine.get_scale_total(scale_res)
        self._lbl_total_score.configure(text=str(int(total)))

        proto = self.protocol[self.current_scale_idx]
        self._txt_results.insert("end", f"{proto['scale_name']}\n")
        self._txt_results.insert("end", f"Toplam: {int(total)}\n\n")

        if subscales:
            self._txt_results.insert("end", "Alt Ölçekler:\n")
            for sub, val in sorted(subscales.items()):
                self._txt_results.insert("end", f"  {sub}: {int(val)}\n")

        # Show approval status
        approved = scale_res.get("approved", False)
        self._txt_results.insert("end", f"\nDurum: {'✔ Onaylandı' if approved else '⏳ Onay bekliyor'}\n")

        # Current page details
        page_result = self._get_current_page_result()
        if page_result and page_result.get("details"):
            self._txt_results.insert("end", "\n--- Sayfa Detayları ---\n")
            for item in page_result["details"]:
                status = "✓" if item["is_marked"] else "✗"
                label = item["roi_def"]["label"]
                fill = item.get("fill_ratio", 0)
                self._txt_results.insert("end", f"{status} {label} ({fill:.2f})\n")

    # Navigation
    def _prev_patient(self):
        if self.current_patient_idx > 0:
            self.current_patient_idx -= 1
            self.current_scale_idx = 0
            self.current_page_idx = 0
            self.zoom_scale = 1.0
            self.pan_x = self.pan_y = 0
            self._refresh_review_ui()

    def _next_patient(self):
        if self.current_patient_idx < len(self.patients) - 1:
            self.current_patient_idx += 1
            self.current_scale_idx = 0
            self.current_page_idx = 0
            self.zoom_scale = 1.0
            self.pan_x = self.pan_y = 0
            self._refresh_review_ui()

    def _prev_scale(self):
        if self.current_scale_idx > 0:
            self.current_scale_idx -= 1
            self.current_page_idx = 0
            self._refresh_review_ui()

    def _next_scale(self):
        if self.current_scale_idx < len(self.protocol) - 1:
            self.current_scale_idx += 1
            self.current_page_idx = 0
            self._refresh_review_ui()

    def _prev_page(self):
        if self.current_page_idx > 0:
            self.current_page_idx -= 1
            self._refresh_review_ui()

    def _next_page(self):
        total_pages = self.protocol[self.current_scale_idx]["page_count"]
        if self.current_page_idx < total_pages - 1:
            self.current_page_idx += 1
            self._refresh_review_ui()

    def _score_current_view(self):
        """Score the current patient/scale/page."""
        proto = self.protocol[self.current_scale_idx]
        page_def = proto["template_pages"][self.current_page_idx]
        input_img = self._get_current_image()

        if input_img is None:
            messagebox.showwarning("Uyarı", "Görsel bulunamadı.")
            return

        try:
            self._progress_bar.pack(fill="x", pady=(0, Style.PADDING_SM))
            self._progress_bar.set(0.2)
            self.app.root.update()

            aligned, M = omr_engine.align_images(input_img, page_def["image"])
            self._progress_bar.set(0.6)
            self.app.root.update()

            if aligned is None:
                self._lbl_align_quality.configure(text="Hizalama: Başarısız ✗", text_color=self.colors["error"])
                messagebox.showwarning("Hata", "Hizalama başarısız.")
                self._progress_bar.pack_forget()
                return

            # Alignment quality from homography determinant
            if M is not None:
                try:
                    det = float(M[0, 0] * M[1, 1] - M[0, 1] * M[1, 0])
                    if 0.5 < abs(det) < 2.0:
                        self._lbl_align_quality.configure(text="Hizalama: İyi ✓", text_color=self.colors["success"])
                    else:
                        self._lbl_align_quality.configure(text="Hizalama: Zayıf ⚠", text_color=self.colors["warning"])
                except Exception:
                    self._lbl_align_quality.configure(text="Hizalama: Belirsiz", text_color=self.colors["text_muted"])
            else:
                self._lbl_align_quality.configure(text="Hizalama: İyi ✓", text_color=self.colors["success"])

            score, subscales, log, details = omr_engine.score_page(
                aligned, page_def["rois"], self.dynamic_threshold)

            self._progress_bar.set(1.0)
            self.app.root.update()

            patient = self.patients[self.current_patient_idx]
            scale_idx = self.current_scale_idx

            if scale_idx not in patient["scale_results"]:
                patient["scale_results"][scale_idx] = {
                    "scale_name": proto["scale_name"],
                    "pages": {},
                    "approved": False
                }

            patient["scale_results"][scale_idx]["pages"][self.current_page_idx] = {
                "total": score, "subscales": subscales,
                "details": details, "aligned_image": aligned,
                "rois_def": page_def["rois"]
            }

            self._progress_bar.pack_forget()
            self._refresh_review_ui()

        except Exception as e:
            self._progress_bar.pack_forget()
            messagebox.showerror("Hata", str(e))

    def _batch_scan_all(self):
        """Scan all patients for all scales."""
        if not self.protocol:
            return

        total = len(self.patients)
        if total == 0:
            return

        confirm = messagebox.askyesno(
            "Toplu Tarama",
            f"{total} hasta için tüm ölçekler otomatik taranacak.\nDevam edilsin mi?"
        )
        if not confirm:
            return

        self._progress_bar.pack(fill="x", pady=(0, Style.PADDING_SM))
        errors = []

        for i, patient in enumerate(self.patients):
            self._progress_bar.set((i + 1) / total)
            self.app.root.update()

            try:
                if not patient["images"]:
                    patient["images"] = study_io.load_patient_images(patient["image_paths"])
                results = study_engine.scan_patient(
                    patient["images"], self.protocol, self.dynamic_threshold)
                patient["scale_results"] = results
                patient["status"] = "in_progress"
            except Exception as e:
                errors.append(f"Hasta {patient['id']}: {e}")

        self._progress_bar.pack_forget()

        if errors:
            messagebox.showwarning("Bazı Hatalar", "\n".join(errors[:5]))
        else:
            messagebox.showinfo("Tamamlandı", f"{total} hasta başarıyla tarandı.")

        self._refresh_review_ui()

    def _flash_approve_button(self):
        """Briefly flash the approve button bright green as visual confirmation."""
        if not hasattr(self, '_btn_approve') or not self._btn_approve.winfo_exists():
            return
        orig_color = self._btn_approve.cget("fg_color")
        self._btn_approve.configure(fg_color="#16a34a", text="✔  ONAYLANDI ✓")
        self.app.root.after(600, lambda: (
            self._btn_approve.configure(fg_color=orig_color) if self._btn_approve.winfo_exists() else None
        ))

    def _approve_current_scale(self):
        """Mark current scale as approved for current patient."""
        patient = self.patients[self.current_patient_idx]
        scale_idx = self.current_scale_idx
        scale_res = patient["scale_results"].get(scale_idx)

        if scale_res is None:
            messagebox.showwarning("Uyarı", "Önce sayfayı puanlayın.")
            return

        scale_res["approved"] = True
        patient["status"] = "in_progress"
        self._flash_approve_button()

        # Check if all scales approved for this patient
        all_approved = all(
            patient["scale_results"].get(i, {}).get("approved", False)
            for i in range(len(self.protocol))
        )
        if all_approved:
            patient["status"] = "approved"

        print(f"[STUDY] Onaylandı: Hasta {patient['id']}, {scale_res['scale_name']}")

        # Auto-advance to next unapproved scale
        advanced = False
        for j in range(len(self.protocol)):
            next_scale = (scale_idx + 1 + j) % len(self.protocol)
            sr = patient["scale_results"].get(next_scale, {})
            if not sr.get("approved", False):
                self.current_scale_idx = next_scale
                self.current_page_idx = 0
                advanced = True
                break

        if not advanced and self.current_patient_idx < len(self.patients) - 1:
            self.current_patient_idx += 1
            self.current_scale_idx = 0
            self.current_page_idx = 0

        self._refresh_review_ui()

    def _toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
            self._btn_edit.configure(
                text="✎ Veri Düzenleme: AÇIK",
                fg_color=self.colors["accent"],
                hover_color=self.colors["accent_hover"],
                text_color="#ffffff"
            )
        else:
            self._btn_edit.configure(
                text="✎ Veri Düzenleme: Kapalı",
                fg_color=self.colors["bg_tertiary"],
                hover_color=self.colors["border"],
                text_color=self.colors["text_primary"]
            )

    def _on_canvas_left_press(self, event):
        if self.edit_mode:
            self._on_roi_click(event)
        else:
            self._start_pan(event)

    def _on_roi_click(self, event):
        page_result = self._get_current_page_result()
        if page_result is None:
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        img_x, img_y = self._to_image(cx, cy)

        details = page_result["details"]
        for idx, item in enumerate(details):
            roi = item["roi_def"]
            if (roi["x"] <= img_x <= roi["x"] + roi["w"] and
                    roi["y"] <= img_y <= roi["y"] + roi["h"]):
                was_marked = item["is_marked"]
                fill = item.get("fill_ratio", 0)
                details[idx]["is_marked"] = not was_marked
                self._auto_update_threshold(not was_marked, fill)
                self._recalculate_scale_score()
                self._draw_rois(details)
                break

    def _auto_update_threshold(self, is_now_marked, fill_ratio):
        margin = 0.01
        changed = False
        if is_now_marked and self.dynamic_threshold > fill_ratio:
            self.dynamic_threshold = max(0.01, fill_ratio - margin)
            changed = True
        elif not is_now_marked and self.dynamic_threshold < fill_ratio:
            self.dynamic_threshold = min(0.90, fill_ratio + margin)
            changed = True
        if changed:
            self._threshold_slider.set(self.dynamic_threshold)
            self._lbl_threshold.configure(text=f"{self.dynamic_threshold:.3f}")

    def _recalculate_scale_score(self):
        page_result = self._get_current_page_result()
        if page_result is None:
            return

        p_score = 0
        p_subscales = {}
        for item in page_result["details"]:
            if item["is_marked"]:
                try:
                    s = float(item["roi_def"]["value"])
                    sub = item["roi_def"].get("subscale", "Genel")
                    p_score += s
                    p_subscales[sub] = p_subscales.get(sub, 0) + s
                except Exception:
                    pass

        page_result["total"] = p_score
        page_result["subscales"] = p_subscales
        self._update_results_panel()

    def _on_threshold_change(self, value):
        self.dynamic_threshold = float(value)
        self._lbl_threshold.configure(text=f"{self.dynamic_threshold:.3f}")
        # Debounced live preview
        if hasattr(self, '_threshold_after_id'):
            self.app.root.after_cancel(self._threshold_after_id)
        self._threshold_after_id = self.app.root.after(40, self._apply_live_threshold)

    def _apply_live_threshold(self):
        """Re-classify ROIs at current threshold and redraw — no re-scoring."""
        page_result = self._get_current_page_result()
        if not page_result or not page_result.get("details"):
            return
        for item in page_result["details"]:
            item["is_marked"] = item.get("fill_ratio", 0) >= self.dynamic_threshold
        self._draw_rois(page_result["details"])
        self._recalculate_scale_score()

    def _on_zoom(self, event):
        if not self.tk_image:
            return
        factor = 0.9 if (event.num == 5 or event.delta < 0) else 1.1
        self.zoom_scale *= factor
        self._refresh_canvas()

    def _start_pan(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def _do_pan(self, event):
        self.pan_x += event.x - self.pan_start_x
        self.pan_y += event.y - self.pan_start_y
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self._refresh_canvas()

    def _update_status_bar(self):
        p = self.patients[self.current_patient_idx]
        proto = self.protocol[self.current_scale_idx]
        self.app.status_var.set(
            f"Çalışma Modu — Hasta {p['id']}/{len(self.patients)}  |  {proto['scale_name']}"
        )

    # ==========================================================================
    # Phase 3 – Export
    # ==========================================================================

    def _show_phase_export(self):
        self.phase = "export"
        self._clear_phase()
        self.app.status_var.set("Çalışma Modu — Dışa Aktarma")

        outer = ctk.CTkScrollableFrame(
            self.parent_frame,
            fg_color=self.colors["bg_primary"],
            corner_radius=0
        )
        outer.pack(fill="both", expand=True)

        content = ctk.CTkFrame(outer, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=Style.PADDING_XL, pady=Style.PADDING_XL)

        # Title
        ctk.CTkLabel(content, text="Dışa Aktarma", font=Style.FONTS["header_lg"],
                     text_color=self.colors["text_primary"]).pack(anchor="w", pady=(0, Style.PADDING_LG))

        # Summary table
        self._section(content, "HASTA ÖZETİ")
        summary_frame = ctk.CTkFrame(content, fg_color=self.colors["bg_secondary"],
                                      corner_radius=Style.CORNER_RADIUS_SM)
        summary_frame.pack(fill="x", pady=(0, Style.PADDING_LG))

        # Header row
        hdr = ctk.CTkFrame(summary_frame, fg_color=self.colors["bg_tertiary"],
                            corner_radius=0)
        hdr.pack(fill="x", padx=1, pady=(1, 0))

        ctk.CTkLabel(hdr, text="Hasta", font=Style.FONTS["small_bold"],
                     text_color=self.colors["text_muted"], width=80).pack(side="left", padx=Style.PADDING_SM, pady=Style.PADDING_XS)
        for proto in self.protocol:
            ctk.CTkLabel(hdr, text=proto["scale_name"], font=Style.FONTS["small_bold"],
                         text_color=self.colors["text_muted"], width=90).pack(side="left")
        ctk.CTkLabel(hdr, text="Durum", font=Style.FONTS["small_bold"],
                     text_color=self.colors["text_muted"], width=80).pack(side="left")

        for patient in self.patients:
            row = ctk.CTkFrame(summary_frame, fg_color="transparent")
            row.pack(fill="x", padx=1, pady=0)

            ctk.CTkLabel(row, text=f"Hasta {patient['id']}", font=Style.FONTS["small"],
                         text_color=self.colors["text_primary"], width=80).pack(side="left", padx=Style.PADDING_SM, pady=2)

            for proto in self.protocol:
                scale_res = patient.get("scale_results", {}).get(proto["order"])
                if scale_res:
                    total, _ = study_engine.get_scale_total(scale_res)
                    approved = "✔" if scale_res.get("approved") else "·"
                    txt = f"{int(total)} {approved}"
                    color = self.colors["text_primary"]
                else:
                    txt = "—"
                    color = self.colors["text_muted"]
                ctk.CTkLabel(row, text=txt, font=Style.FONTS["small"],
                             text_color=color, width=90).pack(side="left")

            status_map = {
                "pending": ("Bekleniyor", self.colors["text_muted"]),
                "in_progress": ("Kısmi", self.colors["warning"]),
                "approved": ("Onaylandı", self.colors["success"])
            }
            st, sc = status_map.get(patient["status"], ("?", self.colors["text_muted"]))
            ctk.CTkLabel(row, text=st, font=Style.FONTS["small"], text_color=sc, width=80).pack(side="left")

        # Export options
        self._section(content, "DIŞA AKTAR")

        # Progress bar for exports
        self._export_progress = ctk.CTkProgressBar(
            content, fg_color=self.colors["bg_tertiary"],
            progress_color=self.colors["accent"], height=6, corner_radius=3
        )
        self._export_progress.set(0)

        # 1. Per-patient CSV
        opt1 = ctk.CTkFrame(content, fg_color=self.colors["bg_secondary"],
                             corner_radius=Style.CORNER_RADIUS_SM)
        opt1.pack(fill="x", pady=Style.PADDING_SM)
        ctk.CTkLabel(opt1, text="Hasta Başına CSV", font=Style.FONTS["body_bold"],
                     text_color=self.colors["text_primary"]).pack(side="left", padx=Style.PADDING_MD, pady=Style.PADDING_MD)
        ctk.CTkLabel(opt1, text="Her hasta için ayrı dosya", font=Style.FONTS["small"],
                     text_color=self.colors["text_muted"]).pack(side="left", expand=True)
        create_secondary_button(opt1, text="📁 Klasör Seç", command=self._export_per_patient_csv, width=130).pack(
            side="right", padx=Style.PADDING_MD, pady=Style.PADDING_SM)

        # 2. Combined CSV
        opt2 = ctk.CTkFrame(content, fg_color=self.colors["bg_secondary"],
                             corner_radius=Style.CORNER_RADIUS_SM)
        opt2.pack(fill="x", pady=Style.PADDING_SM)
        ctk.CTkLabel(opt2, text="Birleşik Özet CSV", font=Style.FONTS["body_bold"],
                     text_color=self.colors["text_primary"]).pack(side="left", padx=Style.PADDING_MD, pady=Style.PADDING_MD)
        ctk.CTkLabel(opt2, text="Tüm hastalar tek tabloda", font=Style.FONTS["small"],
                     text_color=self.colors["text_muted"]).pack(side="left", expand=True)
        create_secondary_button(opt2, text="💾 Kaydet", command=self._export_combined_csv, width=130).pack(
            side="right", padx=Style.PADDING_MD, pady=Style.PADDING_SM)

        # 3. PDF
        opt3 = ctk.CTkFrame(content, fg_color=self.colors["bg_secondary"],
                             corner_radius=Style.CORNER_RADIUS_SM)
        opt3.pack(fill="x", pady=Style.PADDING_SM)
        ctk.CTkLabel(opt3, text="PDF Rapor (Hasta Başına)", font=Style.FONTS["body_bold"],
                     text_color=self.colors["text_primary"]).pack(side="left", padx=Style.PADDING_MD, pady=Style.PADDING_MD)
        ctk.CTkLabel(opt3, text="Her hasta için detaylı PDF", font=Style.FONTS["small"],
                     text_color=self.colors["text_muted"]).pack(side="left", expand=True)
        create_secondary_button(opt3, text="📁 Klasör Seç", command=self._export_pdf_reports, width=130).pack(
            side="right", padx=Style.PADDING_MD, pady=Style.PADDING_SM)

        # Bottom buttons
        ctk.CTkFrame(content, fg_color="transparent", height=20).pack(fill="x")
        btns = ctk.CTkFrame(content, fg_color="transparent")
        btns.pack(fill="x")

        create_secondary_button(btns, text="◀ İncelemeye Dön",
                                command=self._show_phase_review).pack(side="left")
        create_secondary_button(btns, text="🔄 Yeni Çalışma",
                                command=self._new_study).pack(side="right")

    def _export_per_patient_csv(self):
        folder = filedialog.askdirectory(title="CSV Dosyalarının Kaydedileceği Klasörü Seçin")
        if not folder:
            return

        self._export_progress.pack(fill="x", pady=(Style.PADDING_SM, 0))
        errors = []
        for i, patient in enumerate(self.patients):
            self._export_progress.set((i + 1) / len(self.patients))
            self.app.root.update()
            path = os.path.join(folder, f"hasta_{patient['id']}_rapor.csv")
            try:
                study_io.export_patient_csv(patient, self.protocol, path)
            except Exception as e:
                errors.append(f"Hasta {patient['id']}: {e}")

        self._export_progress.pack_forget()
        if errors:
            messagebox.showwarning("Hatalar", "\n".join(errors[:5]))
        else:
            messagebox.showinfo("Tamamlandı", f"{len(self.patients)} CSV dosyası kaydedildi:\n{folder}")

    def _export_combined_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="calisma_ozet.csv",
            title="Birleşik CSV Kaydet"
        )
        if not path:
            return
        try:
            study_io.export_combined_csv(self.patients, self.protocol, path)
            messagebox.showinfo("Tamamlandı", f"Birleşik CSV kaydedildi:\n{path}")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _export_pdf_reports(self):
        if not pdf_export.PDF_AVAILABLE:
            messagebox.showerror("Hata", "PyMuPDF bulunamadı.\npip install pymupdf")
            return

        folder = filedialog.askdirectory(title="PDF Dosyalarının Kaydedileceği Klasörü Seçin")
        if not folder:
            return

        self._export_progress.pack(fill="x", pady=(Style.PADDING_SM, 0))
        errors = []
        for i, patient in enumerate(self.patients):
            self._export_progress.set((i + 1) / len(self.patients))
            self.app.root.update()
            path = os.path.join(folder, f"hasta_{patient['id']}_rapor.pdf")
            try:
                pdf_export.export_patient_pdf(patient, self.protocol, path)
            except Exception as e:
                errors.append(f"Hasta {patient['id']}: {e}")

        self._export_progress.pack_forget()
        if errors:
            messagebox.showwarning("Hatalar", "\n".join(errors[:5]))
        else:
            messagebox.showinfo("Tamamlandı", f"{len(self.patients)} PDF kaydedildi:\n{folder}")

    def _new_study(self):
        """Reset all state and return to setup."""
        self.protocol = []
        self.patients = []
        self.current_patient_idx = 0
        self.current_scale_idx = 0
        self.current_page_idx = 0
        self.zoom_scale = 1.0
        self.pan_x = self.pan_y = 0
        self._show_phase_setup()
