"""
Scanner Mode - Modern UI for OMR Scanning and Scoring

This module handles the scanning workflow with a modernized customtkinter interface.
All functional logic (scoring, alignment, threshold calculations) remains intact.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
import os
import json
from PIL import Image, ImageTk

from src.utils import file_io
from src.core import omr_engine
from src.ui import dialogs
from src.ui.styles import Style, create_section_header, create_accent_button, create_secondary_button
from src import config


class ScannerMode:
    """
    Scanner mode for loading templates and scoring filled forms.
    All scoring logic is preserved; only UI presentation is modernized.
    """
    
    def __init__(self, app):
        self.app = app
        
        # Data state (unchanged)
        self.template_pages = []
        self.input_images = []
        self.current_input_index = 0
        self.session_results = {}  # {input_index: {total, subscales, details, aligned_image}}
        self.dynamic_threshold = 0.12
        self.edit_mode = False
        
        # Canvas state
        self.canvas = None
        self.tk_image = None
        
        # Zoom/Pan state
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.image_scale = 1.0
        
        # Get colors from style system
        self.colors = Style.get_theme_colors()

    def setup_ui(self, parent_frame):
        """Setup the scanner mode UI with modern CTk widgets."""
        self.colors = Style.get_theme_colors()
        
        # ==========================================================================
        # LEFT PANEL - Controls
        # ==========================================================================
        panel = ctk.CTkFrame(
            parent_frame, 
            width=Style.PANEL_WIDTH_MD,
            fg_color=self.colors["bg_secondary"],
            corner_radius=0
        )
        panel.pack(side="left", fill="y", padx=0, pady=0)
        panel.pack_propagate(False)
        
        # Scrollable content
        panel_content = ctk.CTkScrollableFrame(
            panel,
            fg_color="transparent"
        )
        panel_content.pack(fill="both", expand=True, padx=Style.PADDING_MD, pady=Style.PADDING_MD)
        
        # --- Section 1: Setup ---
        self._create_section_header(panel_content, "1. KURULUM")
        
        frm_setup = ctk.CTkFrame(panel_content, fg_color="transparent")
        frm_setup.pack(fill="x", pady=(0, Style.PADDING_LG))
        
        self.btn_load_template = create_secondary_button(
            frm_setup, 
            text="📁 Şablon Yükle (JSON)", 
            command=self.load_template
        )
        self.btn_load_template.pack(fill="x", pady=Style.PADDING_XS)
        
        self.lbl_template = ctk.CTkLabel(
            frm_setup, 
            text="⚠️ Şablon yüklenmedi",
            font=Style.FONTS["small"],
            text_color=self.colors["error"]
        )
        self.lbl_template.pack(pady=(Style.PADDING_XS, Style.PADDING_SM), anchor="w")
        
        create_secondary_button(
            frm_setup, 
            text="🖼️ Resimleri Yükle", 
            command=self.load_filled_form
        ).pack(fill="x", pady=Style.PADDING_XS)
        
        create_secondary_button(
            frm_setup, 
            text="📂 Klasör Yükle", 
            command=self.load_filled_folder
        ).pack(fill="x", pady=Style.PADDING_XS)
        
        # --- Section 2: Navigation ---
        self._create_section_header(panel_content, "2. GÖRÜNTÜ")
        
        frm_nav = ctk.CTkFrame(panel_content, fg_color="transparent")
        frm_nav.pack(fill="x", pady=(0, Style.PADDING_LG))
        
        nav_inner = ctk.CTkFrame(frm_nav, fg_color="transparent")
        nav_inner.pack(fill="x", pady=(0, Style.PADDING_SM))
        
        self.btn_scan_prev = ctk.CTkButton(
            nav_inner, 
            text="◀", 
            command=self.scan_prev_page,
            state="disabled",
            width=50,
            height=Style.BUTTON_HEIGHT_SM,
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            corner_radius=Style.CORNER_RADIUS_SM
        )
        self.btn_scan_prev.pack(side="left", padx=(0, Style.PADDING_SM))
        
        self.lbl_scan_page = ctk.CTkLabel(
            nav_inner, 
            text="0 / 0",
            font=Style.FONTS["body_bold"],
            text_color=self.colors["text_primary"]
        )
        self.lbl_scan_page.pack(side="left", expand=True)
        
        self.btn_scan_next = ctk.CTkButton(
            nav_inner, 
            text="▶", 
            command=self.scan_next_page,
            state="disabled",
            width=50,
            height=Style.BUTTON_HEIGHT_SM,
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            corner_radius=Style.CORNER_RADIUS_SM
        )
        self.btn_scan_next.pack(side="left", padx=(Style.PADDING_SM, 0))
        
        create_secondary_button(
            frm_nav, 
            text="✂️ Otomatik Kırp", 
            command=self.auto_crop_current_page
        ).pack(fill="x", pady=(Style.PADDING_SM, Style.PADDING_XS))
        
        create_secondary_button(
            frm_nav, 
            text="📐 Manuel Kırp/Düzelt", 
            command=self.open_corner_correction
        ).pack(fill="x", pady=Style.PADDING_XS)
        
        # --- Section 3: Scoring ---
        self._create_section_header(panel_content, "3. İŞLEM")
        
        frm_score = ctk.CTkFrame(panel_content, fg_color="transparent")
        frm_score.pack(fill="x", pady=(0, Style.PADDING_MD))
        
        ctk.CTkLabel(
            frm_score, 
            text="Şablon Sayfası:",
            font=Style.FONTS["small_bold"],
            text_color=self.colors["text_secondary"]
        ).pack(anchor="w")
        
        self.cmb_template_page = ctk.CTkOptionMenu(
            frm_score,
            values=["Şablon yüklenmedi"],
            fg_color=self.colors["input_bg"],
            button_color=self.colors["bg_tertiary"],
            button_hover_color=self.colors["border"],
            dropdown_fg_color=self.colors["bg_secondary"],
            dropdown_hover_color=self.colors["bg_tertiary"],
            text_color=self.colors["text_primary"],
            font=Style.FONTS["body"],
            corner_radius=Style.CORNER_RADIUS_SM,
            height=Style.INPUT_HEIGHT
        )
        self.cmb_template_page.pack(fill="x", pady=(Style.PADDING_XS, Style.PADDING_MD))
        
        # Threshold control
        thresh_header = ctk.CTkFrame(frm_score, fg_color="transparent")
        thresh_header.pack(fill="x")
        
        ctk.CTkLabel(
            thresh_header, 
            text="Hassasiyet (Eşik):",
            font=Style.FONTS["small_bold"],
            text_color=self.colors["text_secondary"]
        ).pack(side="left")
        
        self.lbl_threshold_value = ctk.CTkLabel(
            thresh_header, 
            text=f"{self.dynamic_threshold:.2f}",
            font=Style.FONTS["mono"],
            text_color=self.colors["accent"]
        )
        self.lbl_threshold_value.pack(side="right")
        
        self.threshold_slider = ctk.CTkSlider(
            frm_score,
            from_=0.01,
            to=0.50,
            number_of_steps=49,
            command=self.on_threshold_change,
            fg_color=self.colors["bg_tertiary"],
            progress_color=self.colors["accent"],
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            height=16
        )
        self.threshold_slider.set(self.dynamic_threshold)
        self.threshold_slider.pack(fill="x", pady=(Style.PADDING_SM, Style.PADDING_LG))
        
        # Progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(
            frm_score,
            fg_color=self.colors["bg_tertiary"],
            progress_color=self.colors["accent"],
            height=6,
            corner_radius=3
        )
        self.progress_bar.set(0)
        # Will be shown during processing
        
        create_accent_button(
            frm_score, 
            text="⚡ Sayfayı Puanla", 
            command=self.score_current_page
        ).pack(fill="x", pady=(0, Style.PADDING_SM))
        
        self.btn_edit_mode = ctk.CTkButton(
            frm_score,
            text="✎ Veri Düzenleme: Kapalı",
            command=self.toggle_edit_mode,
            font=Style.FONTS["button"],
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            height=Style.BUTTON_HEIGHT_SM,
            corner_radius=Style.CORNER_RADIUS_MD
        )
        self.btn_edit_mode.pack(fill="x", pady=Style.PADDING_XS)
        
        # Spacer
        ctk.CTkFrame(panel_content, fg_color="transparent", height=20).pack(fill="x")
        
        # --- Footer: Score Display ---
        frm_footer = ctk.CTkFrame(panel_content, fg_color="transparent")
        frm_footer.pack(fill="x", side="bottom", pady=Style.PADDING_MD)
        
        ctk.CTkLabel(
            frm_footer, 
            text="TOPLAM PUAN",
            font=Style.FONTS["small_bold"],
            text_color=self.colors["text_muted"]
        ).pack(anchor="e")
        
        self.lbl_total_score = ctk.CTkLabel(
            frm_footer,
            text="0",
            font=Style.FONTS["score_display"],
            text_color=self.colors["accent"]
        )
        self.lbl_total_score.pack(anchor="e", pady=(0, Style.PADDING_MD))
        
        create_secondary_button(
            frm_footer, 
            text="📊 Raporu Görüntüle", 
            command=self.show_session_report
        ).pack(fill="x")
        
        # ==========================================================================
        # CENTER - Canvas
        # ==========================================================================
        center_frame = ctk.CTkFrame(
            parent_frame, 
            fg_color=self.colors["bg_primary"],
            corner_radius=0
        )
        center_frame.pack(side="left", fill="both", expand=True, padx=0, pady=0)
        
        # Canvas (still using tk.Canvas for image rendering compatibility)
        self.canvas = tk.Canvas(
            center_frame, 
            bg=self.colors["canvas"], 
            bd=0, 
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # ==========================================================================
        # RIGHT PANEL - Results
        # ==========================================================================
        details_panel = ctk.CTkFrame(
            parent_frame, 
            width=300,
            fg_color=self.colors["bg_secondary"],
            corner_radius=0
        )
        details_panel.pack(side="right", fill="y", padx=0, pady=0)
        details_panel.pack_propagate(False)
        
        details_content = ctk.CTkFrame(details_panel, fg_color="transparent")
        details_content.pack(fill="both", expand=True, padx=Style.PADDING_MD, pady=Style.PADDING_MD)
        
        self._create_section_header(details_content, "SONUÇLAR")
        
        self.txt_results = ctk.CTkTextbox(
            details_content,
            font=Style.FONTS["mono"],
            fg_color=self.colors["input_bg"],
            text_color=self.colors["text_primary"],
            border_width=0,
            corner_radius=Style.CORNER_RADIUS_SM,
            wrap="word"
        )
        self.txt_results.pack(fill="both", expand=True)
        
        # ==========================================================================
        # Event Bindings
        # ==========================================================================
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-4>", self.on_zoom)
        self.canvas.bind("<Button-5>", self.on_zoom)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.do_pan)
    
    def _create_section_header(self, parent, text):
        """Create a styled section header with separator."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(Style.PADDING_SM, Style.PADDING_MD))
        
        lbl = ctk.CTkLabel(
            frame, 
            text=text,
            font=Style.FONTS["small_bold"],
            text_color=self.colors["text_muted"]
        )
        lbl.pack(side="left")
        
        sep = ctk.CTkFrame(
            frame, 
            height=1, 
            fg_color=self.colors["border"]
        )
        sep.pack(side="left", fill="x", expand=True, padx=(Style.PADDING_SM, 0))

    # ==========================================================================
    # FUNCTIONAL LOGIC (UNCHANGED)
    # All methods below preserve the original algorithm logic
    # ==========================================================================
    
    def load_template(self):
        """Load a template JSON file. Logic unchanged."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file_path:
            return
        
        print(f"[SCANNER] Şablon yükleniyor: {file_path}")
        try:
            data = file_io.load_template_json(file_path)
            base_dir = os.path.dirname(file_path)
            self.template_pages = []
            
            if "pages" in data:
                for i, p_data in enumerate(data["pages"]):
                    ref_name = p_data["ref_image_storage"]
                    ref_path = os.path.join(base_dir, ref_name)
                    if os.path.exists(ref_path):
                        img = cv2.imread(ref_path)
                        self.template_pages.append({
                            "image": img, "rois": p_data["rois"], "page_index": p_data["page_index"]
                        })
            else:
                # legacy format
                ref_name = data.get("ref_image_storage", "") or data.get("ref_image_path", "")
                ref_path = os.path.join(base_dir, ref_name)
                if os.path.exists(ref_path):
                    img = cv2.imread(ref_path)
                    self.template_pages.append({
                        "image": img, "rois": data["rois"], "page_index": 0
                    })
                    
            if self.template_pages:
                self.lbl_template.configure(
                    text=f"✓ {os.path.basename(file_path)} ({len(self.template_pages)} sayfa)",
                    text_color=self.colors["success"]
                )
                page_values = [f"Sayfa {i+1}" for i in range(len(self.template_pages))]
                self.cmb_template_page.configure(values=page_values)
                self.cmb_template_page.set(page_values[0])
            else:
                messagebox.showerror("Hata", "Referans görselleri yüklenemedi.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def load_filled_form(self):
        """Load filled form images. Logic unchanged."""
        file_paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")])
        if file_paths:
            print(f"[SCANNER] {len(file_paths)} adet form görseli seçildi")
            self._load_inputs(file_paths)

    def load_filled_folder(self):
        """Load images from a folder. Logic unchanged."""
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        valid_exts = {'.jpg', '.jpeg', '.png', '.bmp'}
        paths = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if os.path.splitext(file)[1].lower() in valid_exts:
                    paths.append(os.path.join(root, file))
        self._load_inputs(paths)
        
    def _load_inputs(self, file_paths):
        """Internal method to load input images. Logic unchanged."""
        print(f"[SCANNER] Görseller yükleniyor...")
        self.input_images = []
        for path in file_paths:
            imgs = file_io.load_images_from_file(path)
            self.input_images.extend(imgs)
            
        if self.input_images:
            self.current_input_index = 0
            self.session_results = {}
            self.update_scanner_ui()
            messagebox.showinfo("Yüklendi", f"{len(self.input_images)} resim yüklendi.")
        else:
            messagebox.showwarning("Uyarı", "Görsel yüklenemedi.")

    def update_scanner_ui(self):
        """Update UI state based on loaded images. Logic unchanged."""
        start_state = "normal" if self.input_images else "disabled"
        self.btn_scan_prev.configure(state=start_state)
        self.btn_scan_next.configure(state=start_state)
        
        if not self.input_images:
            self.lbl_scan_page.configure(text="0 / 0")
            self.canvas.delete("all")
            return
            
        total = len(self.input_images)
        self.lbl_scan_page.configure(text=f"{self.current_input_index + 1} / {total}")
        self.btn_scan_prev.configure(state="normal" if self.current_input_index > 0 else "disabled")
        self.btn_scan_next.configure(state="normal" if self.current_input_index < total - 1 else "disabled")
        
        self.refresh_canvas()
        
        if self.template_pages and self.current_input_index < len(self.template_pages):
            page_values = self.cmb_template_page.cget("values")
            if page_values and len(page_values) > self.current_input_index:
                self.cmb_template_page.set(page_values[self.current_input_index])

    def scan_prev_page(self):
        """Navigate to previous page. Logic unchanged."""
        if self.current_input_index > 0:
            print(f"[SCANNER] Önceki sayfaya gidiliyor ({self.current_input_index} -> {self.current_input_index-1})")
            self.current_input_index -= 1
            self.update_scanner_ui()
            
    def scan_next_page(self):
        """Navigate to next page. Logic unchanged."""
        if self.current_input_index < len(self.input_images) - 1:
            print(f"[SCANNER] Sonraki sayfaya gidiliyor ({self.current_input_index} -> {self.current_input_index+1})")
            self.current_input_index += 1
            self.update_scanner_ui()

    def refresh_canvas(self):
        """Refresh the canvas display. Logic unchanged."""
        if not self.input_images:
            return
        
        # Display aligned image if scored, else raw
        if self.current_input_index in self.session_results:
            img = self.session_results[self.current_input_index]['aligned_image']
        else:
            img = self.input_images[self.current_input_index]
            
        h, w = img.shape[:2]
        canvas_h = 700
        canvas_w = 1100
        scale_w = canvas_w / w
        scale_h = canvas_h / h
        self.image_scale = min(scale_w, scale_h, 1.0)
        
        final_scale = self.image_scale * self.zoom_scale
        new_w = int(w * final_scale)
        new_h = int(h * final_scale)
        
        if new_w < 1 or new_h < 1:
            return
        
        resized = cv2.resize(img, (new_w, new_h))
        rgb_img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
        self.tk_image = ImageTk.PhotoImage(pil_img)
        
        self.canvas.delete("all")
        self.canvas.create_image(self.pan_x, self.pan_y, anchor=tk.NW, image=self.tk_image)
        
        if self.current_input_index in self.session_results:
            self.draw_scanner_rois(self.session_results[self.current_input_index]['details'])

    def score_current_page(self):
        """Score the current page. Core algorithm unchanged."""
        if not self.template_pages or not self.input_images:
            return
        
        # Get selected template page index
        current_value = self.cmb_template_page.get()
        t_idx = 0
        try:
            t_idx = int(current_value.split()[-1]) - 1
        except:
            pass
            
        if t_idx < 0 or t_idx >= len(self.template_pages):
            return
        
        t_page = self.template_pages[t_idx]
        input_img = self.input_images[self.current_input_index]
        
        print(f"[SCANNER] Sayfa puanlanıyor (Giriş: {self.current_input_index}, Şablon: Sayfa {t_idx})")
        
        try:
            # Show progress
            self.progress_bar.pack(fill="x", pady=(0, Style.PADDING_SM))
            self.progress_bar.set(0.2)
            self.txt_results.delete("1.0", "end")
            self.txt_results.insert("end", "Hizalanıyor...\n")
            self.app.root.update()
            
            aligned, M = omr_engine.align_images(input_img, t_page['image'])
            self.progress_bar.set(0.5)
            self.app.root.update()
            
            if aligned is None:
                self.txt_results.insert("end", "Hizalama BAŞARISIZ.\n")
                messagebox.showwarning("Hata", "Hizalama başarısız.")
                self.progress_bar.pack_forget()
                return
            
            self.progress_bar.set(0.8)
            self.app.root.update()
                
            score, subscales, log, details = omr_engine.score_page(aligned, t_page['rois'], self.dynamic_threshold)
            
            self.session_results[self.current_input_index] = {
                "total": score, "subscales": subscales, "details": details,
                "aligned_image": aligned, "rois_def": t_page['rois']
            }
            
            self.progress_bar.set(1.0)
            self.app.root.update()
            
            self.update_results_display(score, log)
            self.update_total_score()
            self.refresh_canvas()
            
            # Hide progress bar after completion
            self.progress_bar.pack_forget()
            
        except Exception as e:
            self.progress_bar.pack_forget()
            messagebox.showerror("Hata", str(e))

    def update_results_display(self, score, log):
        """Update the results text display. Logic unchanged."""
        self.txt_results.delete("1.0", "end")
        self.txt_results.insert("end", f"Puan: {score}\n\n")
        for line in log:
            self.txt_results.insert("end", line + "\n")
        
    def update_total_score(self):
        """Update the total score display. Logic unchanged."""
        total = sum(r['total'] for r in self.session_results.values())
        self.lbl_total_score.configure(text=f"{total}")

    def draw_scanner_rois(self, details):
        """Draw ROI overlays on canvas. Logic unchanged."""
        self.canvas.delete("scanner_roi")
        for idx, item in enumerate(details):
            roi = item['roi_def']
            x, y = self.to_canvas_coords(roi['x'], roi['y'])
            w = roi['w'] * self.image_scale * self.zoom_scale
            h = roi['h'] * self.image_scale * self.zoom_scale
            
            color = "#22c55e" if item['is_marked'] else "#ef4444"
            self.canvas.create_rectangle(x, y, x+w, y+h, outline=color, width=2, tags=("scanner_roi", f"roi_{idx}"))

    def to_canvas_coords(self, img_x, img_y):
        """Convert image coords to canvas coords. Logic unchanged."""
        x = (img_x * self.image_scale * self.zoom_scale) + self.pan_x
        y = (img_y * self.image_scale * self.zoom_scale) + self.pan_y
        return x, y

    def to_image_coords(self, canvas_x, canvas_y):
        """Convert canvas coords to image coords."""
        x = (canvas_x - self.pan_x) / (self.image_scale * self.zoom_scale)
        y = (canvas_y - self.pan_y) / (self.image_scale * self.zoom_scale)
        return int(x), int(y)

    def open_corner_correction(self):
        """Open corner correction dialog. Logic unchanged."""
        if not self.input_images:
            return
        current_img = self.input_images[self.current_input_index]
        
        d = dialogs.CornerCorrectionDialog(self.app.root, current_img)
        if d.result_image is not None:
            self.input_images[self.current_input_index] = d.result_image
            if self.current_input_index in self.session_results:
                del self.session_results[self.current_input_index]
                self.txt_results.delete("1.0", "end")
            self.update_scanner_ui()

    def auto_crop_current_page(self):
        """Auto crop the current page. Logic unchanged."""
        if not self.input_images:
            return
        
        print("[SCANNER] Otomatik kırpma isteği başlatıldı")
        try:
            current_img = self.input_images[self.current_input_index]
            found, corners = omr_engine.detect_corners(current_img)
            
            if found:
                warped = omr_engine.get_four_point_transform(current_img, corners)
                self.input_images[self.current_input_index] = warped
                
                # Clear results for this page as image changed
                if self.current_input_index in self.session_results:
                    del self.session_results[self.current_input_index]
                    self.txt_results.delete("1.0", "end")
                
                self.update_scanner_ui()
            else:
                messagebox.showwarning("Başarısız", "Otomatik köşe tespiti başarısız oldu. Manuel kırpma kullanın.")
                
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def toggle_edit_mode(self):
        """Toggle edit mode for manual ROI adjustment. Logic unchanged."""
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
            self.btn_edit_mode.configure(
                text="✎ Veri Düzenleme: AÇIK",
                fg_color=self.colors["accent"],
                hover_color=self.colors["accent_hover"],
                text_color="#ffffff"
            )
            self.canvas.bind("<Button-1>", self.on_scanner_roi_click)
        else:
            self.btn_edit_mode.configure(
                text="✎ Veri Düzenleme: Kapalı",
                fg_color=self.colors["bg_tertiary"],
                hover_color=self.colors["border"],
                text_color=self.colors["text_primary"]
            )
            self.canvas.bind("<Button-1>", self.on_mouse_down)

    def on_scanner_roi_click(self, event):
        """Handle ROI click in edit mode using geometric hit testing."""
        if not self.edit_mode:
            return
        if self.current_input_index not in self.session_results:
            return
        
        # Convert click to image coords
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        img_x, img_y = self.to_image_coords(cx, cy)
        
        res = self.session_results[self.current_input_index]
        details = res['details']
        
        roi_idx = -1
        # Check geometric intersection
        for idx, item in enumerate(details):
            roi = item['roi_def']
            if (roi['x'] <= img_x <= roi['x'] + roi['w']) and \
               (roi['y'] <= img_y <= roi['y'] + roi['h']):
                roi_idx = idx
                break
                
        if roi_idx == -1:
            return
        
        res = self.session_results[self.current_input_index]
        details = res['details']
        was_marked = details[roi_idx]['is_marked']
        current_fill = details[roi_idx]['fill_ratio']
        
        details[roi_idx]['is_marked'] = not was_marked
        self.update_threshold_from_manual_input(not was_marked, current_fill)
        
        # Recalc this page score locally
        self.recalculate_page_score(self.current_input_index)
        self.draw_scanner_rois(details)

    def update_threshold_from_manual_input(self, is_now_marked, fill_ratio):
        """Update threshold based on manual input. Logic unchanged."""
        margin = 0.01
        changed = False
        if is_now_marked:
            if self.dynamic_threshold > fill_ratio:
                self.dynamic_threshold = max(0.01, fill_ratio - margin)
                changed = True
        else:
            if self.dynamic_threshold < fill_ratio:
                self.dynamic_threshold = min(0.90, fill_ratio + margin)
                changed = True
        
        if changed:
            self.threshold_slider.set(self.dynamic_threshold)
            self.lbl_threshold_value.configure(text=f"{self.dynamic_threshold:.3f}")

    def recalculate_page_score(self, input_idx):
        """Recalculate page score after manual edits. Logic unchanged."""
        res = self.session_results[input_idx]
        details = res['details']
        p_score = 0
        p_subscales = {}
        p_log = []
        
        for item in details:
            is_marked = item['is_marked']
            val = item['roi_def']['value']
            sub = item['roi_def'].get('subscale', 'Genel')
            label = item['roi_def']['label']
            status = "✓" if is_marked else "✗"
            
            if is_marked:
                try:
                    s = float(val)
                    p_score += s
                    p_subscales[sub] = p_subscales.get(sub, 0) + s
                except:
                    pass
            p_log.append(f"{status} {label} [{sub}]: {val if is_marked else '0'} (Manuel)")
            
        print(f"[SCANNER] Manuel düzenleme sonrası yeni puan: {p_score}")
        res['total'] = p_score
        res['subscales'] = p_subscales
        
        if input_idx == self.current_input_index:
            self.update_results_display(p_score, p_log)
            self.update_total_score()

    def show_session_report(self):
        """Show session report dialog. Logic unchanged."""
        if not self.session_results:
            return
        
        total_score = sum(r['total'] for r in self.session_results.values())
        report = f"=== OTURUM RAPORU ===\nToplam Puan: {total_score}\n"
        
        top = ctk.CTkToplevel(self.app.root)
        top.title("Rapor")
        top.geometry("500x400")
        top.configure(fg_color=self.colors["bg_primary"])
        
        txt = ctk.CTkTextbox(
            top,
            font=Style.FONTS["mono"],
            fg_color=self.colors["input_bg"],
            text_color=self.colors["text_primary"]
        )
        txt.pack(fill="both", expand=True, padx=Style.PADDING_MD, pady=Style.PADDING_MD)
        txt.insert("end", report)
        
        def export_csv():
            path = filedialog.asksaveasfilename(defaultextension=".csv")
            if path:
                file_io.export_csv_report(self.session_results, path)
        
        create_accent_button(
            top, 
            text="📁 Dışa Aktar CSV", 
            command=export_csv
        ).pack(pady=Style.PADDING_MD)

    def on_threshold_change(self, value):
        """Handle threshold slider change. Logic unchanged."""
        self.dynamic_threshold = float(value)
        self.lbl_threshold_value.configure(text=f"{self.dynamic_threshold:.3f}")

    # ==========================================================================
    # Zoom/Pan Methods (Logic unchanged)
    # ==========================================================================
    
    def on_zoom(self, event):
        """Handle zoom events. Logic unchanged."""
        if not self.tk_image:
            return
        if event.num == 5 or event.delta < 0:
            factor = 0.9
        else:
            factor = 1.1
        self.zoom_scale *= factor
        self.refresh_canvas()

    def start_pan(self, event):
        """Start panning. Logic unchanged."""
        self.canvas.scan_mark(event.x, event.y)
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def do_pan(self, event):
        """Continue panning. Logic unchanged."""
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        self.pan_x += dx
        self.pan_y += dy
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.refresh_canvas()

    def on_mouse_down(self, event):
        """Handle mouse down. Logic unchanged."""
        self.start_pan(event)

    def on_mouse_drag(self, event):
        """Handle mouse drag. Logic unchanged."""
        self.do_pan(event)

    def on_mouse_up(self, event):
        """Handle mouse up. Logic unchanged."""
        pass
