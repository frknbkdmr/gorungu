
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
import os
import json
from PIL import Image, ImageTk

from src.utils import file_io
from src.core import omr_engine
from src.ui import dialogs
from src import config

class ScannerMode:
    def __init__(self, app):
        self.app = app
        
        self.template_pages = []
        self.input_images = []
        self.current_input_index = 0
        self.session_results = {} # {input_index: {total, subscales, details, aligned_image}}
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
        
        self.colors = config.THEMES[config.DEFAULT_THEME]

    def setup_ui(self, parent_frame):
        self.colors = self.app.colors
        
        # Control Panel
        panel = ttk.Frame(parent_frame, width=320, style="Panel.TFrame", padding=20)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 0))
        panel.pack_propagate(False)
        
        # --- Section 1: Setup ---
        self._create_section_header(panel, "1. KURULUM")
        
        frm_setup = ttk.Frame(panel, style="Panel.TFrame")
        frm_setup.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Button(frm_setup, text="Şablon Yükle (JSON)", command=self.load_template).pack(fill=tk.X, pady=2)
        self.lbl_template = ttk.Label(frm_setup, text="Şablon yüklenmedi", foreground=self.colors["error"], font=("Segoe UI", 8))
        self.lbl_template.pack(pady=(2, 5), anchor=tk.W)
        
        ttk.Button(frm_setup, text="Resimleri Yükle", command=self.load_filled_form).pack(fill=tk.X, pady=2)
        ttk.Button(frm_setup, text="Klasör Yükle", command=self.load_filled_folder).pack(fill=tk.X, pady=2)
        
        # --- Section 2: Navigation ---
        self._create_section_header(panel, "2. GÖRÜNTÜ")
        
        frm_nav = ttk.Frame(panel, style="Panel.TFrame")
        frm_nav.pack(fill=tk.X, pady=(0, 20))
        
        nav_inner = ttk.Frame(frm_nav, style="Panel.TFrame")
        nav_inner.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_scan_prev = ttk.Button(nav_inner, text="◄", command=self.scan_prev_page, state=tk.DISABLED, width=5)
        self.btn_scan_prev.pack(side=tk.LEFT, padx=(0, 5))
        
        self.lbl_scan_page = ttk.Label(nav_inner, text="0 / 0", anchor=tk.CENTER, font=("Segoe UI", 10, "bold"))
        self.lbl_scan_page.pack(side=tk.LEFT, expand=True)
        
        self.btn_scan_next = ttk.Button(nav_inner, text="►", command=self.scan_next_page, state=tk.DISABLED, width=5)
        self.btn_scan_next.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(frm_nav, text="Otomatik Kırp", command=self.auto_crop_current_page).pack(fill=tk.X, pady=(5, 2))
        ttk.Button(frm_nav, text="Manuel Kırp/Düzelt", command=self.open_corner_correction).pack(fill=tk.X, pady=2)
        
        # --- Section 3: Scoring ---
        self._create_section_header(panel, "3. İŞLEM")
        
        frm_score = ttk.Frame(panel, style="Panel.TFrame")
        frm_score.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frm_score, text="Şablon Sayfası:", style="Panel.TLabel", font=("Segoe UI", 9)).pack(anchor=tk.W)
        self.cmb_template_page = ttk.Combobox(frm_score, state="readonly")
        self.cmb_template_page.pack(fill=tk.X, pady=(2, 10))
        
        # Threshold control
        thresh_header = ttk.Frame(frm_score, style="Panel.TFrame")
        thresh_header.pack(fill=tk.X)
        ttk.Label(thresh_header, text="Hassasiyet (Eşik):", style="Panel.TLabel", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.lbl_threshold_value = ttk.Label(thresh_header, text=f"{self.dynamic_threshold:.2f}", font=("Consolas", 9, "bold"))
        self.lbl_threshold_value.pack(side=tk.RIGHT)
        
        self.threshold_slider = tk.Scale(
            frm_score, from_=0.01, to=0.50, resolution=0.01,
            orient=tk.HORIZONTAL, command=self.on_threshold_change, showvalue=0,
            bg=self.colors["panel_bg"], fg=self.colors["accent"],
            troughcolor=self.colors["canvas"], activebackground=self.colors["accent"],
            bd=0, highlightthickness=0
        )
        self.threshold_slider.set(self.dynamic_threshold)
        self.threshold_slider.pack(fill=tk.X, pady=(2, 15))
        
        ttk.Button(frm_score, text="Sayfayı Puanla", command=self.score_current_page, style="Accent.TButton").pack(fill=tk.X, pady=(0, 5), ipady=5)
        
        self.btn_edit_mode = ttk.Button(frm_score, text="✎ Veri Düzenleme: Kapalı", command=self.toggle_edit_mode)
        self.btn_edit_mode.pack(fill=tk.X, pady=2)
        
        # Footer / Session Score (Push to bottom if possible, or just below)
        ttk.Frame(panel, style="Panel.TFrame").pack(fill=tk.Y, expand=True) # Spacer
        
        frm_footer = ttk.Frame(panel, style="Panel.TFrame")
        frm_footer.pack(fill=tk.X, side=tk.BOTTOM, pady=10)

        # Style for total card
        self.lbl_total_score = ttk.Label(
            frm_footer, 
            text="0", 
            font=("Segoe UI", 24, "bold"), 
            foreground=self.colors["accent"],
            anchor=tk.E,
            background=self.colors["panel_bg"]
        )
        ttk.Label(frm_footer, text="TOPLAM PUAN", font=("Segoe UI", 8, "bold"), foreground="gray").pack(anchor=tk.E)
        self.lbl_total_score.pack(anchor=tk.E, pady=(0, 10))
        
        ttk.Button(frm_footer, text="Raporu Görüntüle", command=self.show_session_report).pack(fill=tk.X)
        
        # Center Area: Canvas
        center_frame = ttk.Frame(parent_frame, style="TFrame")
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0) # Remove padding for seamless look
        
        self.canvas = tk.Canvas(center_frame, bg=self.colors["canvas"], bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Right Panel: Results
        details_panel = ttk.Frame(parent_frame, width=300, style="Panel.TFrame", padding=20)
        details_panel.pack(side=tk.RIGHT, fill=tk.Y)
        details_panel.pack_propagate(False)
        
        self._create_section_header(details_panel, "SONUÇLAR")
        
        results_frame = ttk.Frame(details_panel, style="Panel.TFrame")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.txt_results = tk.Text(
            results_frame, font=("Consolas", 10), relief=tk.FLAT,
            bg=self.colors["panel_bg"], # Blend with panel
            fg=self.colors["text"],
            wrap=tk.WORD, yscrollcommand=scrollbar.set,
            padx=5, pady=5,
            bd=0
        )
        self.txt_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.txt_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.txt_results.yview)
        
        # Bindings
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-4>", self.on_zoom)
        self.canvas.bind("<Button-5>", self.on_zoom)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.do_pan)
        
    def _create_section_header(self, parent, text):
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.pack(fill=tk.X, pady=(5, 10))
        
        lbl = ttk.Label(frame, text=text, font=("Segoe UI", 9, "bold"), foreground="gray")
        lbl.pack(side=tk.LEFT)
        
        sep = ttk.Separator(frame, orient='horizontal')
        sep.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0), pady=7)

        sep = ttk.Separator(frame, orient='horizontal')
        sep.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0), pady=7)
        
    def load_template(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file_path: return
        
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
                # legacy
                ref_name = data.get("ref_image_storage", "") or data.get("ref_image_path", "")
                ref_path = os.path.join(base_dir, ref_name)
                if os.path.exists(ref_path):
                    img = cv2.imread(ref_path)
                    self.template_pages.append({
                        "image": img, "rois": data["rois"], "page_index": 0
                    })
                    
            if self.template_pages:
                self.lbl_template.config(text=f"{os.path.basename(file_path)} ({len(self.template_pages)} sayfa)", foreground=self.colors["success"])
                self.cmb_template_page['values'] = [f"Sayfa {i+1}" for i in range(len(self.template_pages))]
                self.cmb_template_page.current(0)
            else:
                 messagebox.showerror("Hata", "Referans görselleri yüklenemedi.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def load_filled_form(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")])
        if file_paths:
            print(f"[SCANNER] {len(file_paths)} adet form görseli seçildi")
            self._load_inputs(file_paths)

    def load_filled_folder(self):
        folder_path = filedialog.askdirectory()
        if not folder_path: return
        valid_exts = {'.jpg', '.jpeg', '.png', '.bmp'}
        paths = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if os.path.splitext(file)[1].lower() in valid_exts:
                    paths.append(os.path.join(root, file))
        self._load_inputs(paths)
        
    def _load_inputs(self, file_paths):
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
        start_state = tk.NORMAL if self.input_images else tk.DISABLED
        self.btn_scan_prev.config(state=start_state)
        self.btn_scan_next.config(state=start_state)
        
        if not self.input_images:
            self.lbl_scan_page.config(text="0/0")
            self.canvas.delete("all")
            return
            
        total = len(self.input_images)
        self.lbl_scan_page.config(text=f"{self.current_input_index + 1}/{total}")
        self.btn_scan_prev.config(state=tk.NORMAL if self.current_input_index > 0 else tk.DISABLED)
        self.btn_scan_next.config(state=tk.NORMAL if self.current_input_index < total - 1 else tk.DISABLED)
        
        self.refresh_canvas()
        
        if self.template_pages and self.current_input_index < len(self.template_pages):
            self.cmb_template_page.current(self.current_input_index)

    def scan_prev_page(self):
        if self.current_input_index > 0:
            print(f"[SCANNER] Önceki sayfaya gidiliyor ({self.current_input_index} -> {self.current_input_index-1})")
            self.current_input_index -= 1
            self.update_scanner_ui()
            
    def scan_next_page(self):
        if self.current_input_index < len(self.input_images) - 1:
            print(f"[SCANNER] Sonraki sayfaya gidiliyor ({self.current_input_index} -> {self.current_input_index+1})")
            self.current_input_index += 1
            self.update_scanner_ui()

    def refresh_canvas(self):
        if not self.input_images: return
        
        # Display aligned image if scored, else raw
        if self.current_input_index in self.session_results:
            img = self.session_results[self.current_input_index]['aligned_image']
        else:
            img = self.input_images[self.current_input_index]
            
        h, w = img.shape[:2]
        # Recalc scale on every refresh or just cache it?
        canvas_h = 700
        canvas_w = 1100 # Approx
        scale_w = canvas_w / w
        scale_h = canvas_h / h
        self.image_scale = min(scale_w, scale_h, 1.0)
        
        final_scale = self.image_scale * self.zoom_scale
        new_w = int(w * final_scale)
        new_h = int(h * final_scale)
        
        if new_w < 1 or new_h < 1: return
        
        resized = cv2.resize(img, (new_w, new_h))
        rgb_img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
        self.tk_image = ImageTk.PhotoImage(pil_img)
        
        self.canvas.delete("all")
        self.canvas.create_image(self.pan_x, self.pan_y, anchor=tk.NW, image=self.tk_image)
        
        if self.current_input_index in self.session_results:
            self.draw_scanner_rois(self.session_results[self.current_input_index]['details'])

    def score_current_page(self):
        if not self.template_pages or not self.input_images: return
        
        t_idx = self.cmb_template_page.current()
        if t_idx == -1: return
        
        t_page = self.template_pages[t_idx]
        input_img = self.input_images[self.current_input_index]
        
        print(f"[SCANNER] Sayfa puanlanıyor (Giriş: {self.current_input_index}, Şablon: Sayfa {t_idx})")
        
        try:
            self.txt_results.delete(1.0, tk.END)
            self.txt_results.insert(tk.END, "Hizalanıyor...\n")
            self.app.root.update()
            
            aligned, M = omr_engine.align_images(input_img, t_page['image'])
            if aligned is None:
                self.txt_results.insert(tk.END, "Hizalama BAŞARISIZ.\n")
                messagebox.showwarning("Hata", "Hizalama başarısız.")
                return
                
            score, subscales, log, details = omr_engine.score_page(aligned, t_page['rois'], self.dynamic_threshold)
            
            self.session_results[self.current_input_index] = {
                "total": score, "subscales": subscales, "details": details,
                "aligned_image": aligned, "rois_def": t_page['rois']
            }
            
            self.update_results_display(score, log)
            self.update_total_score()
            self.refresh_canvas() # Shows aligned image + ROIs
            
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def update_results_display(self, score, log):
        self.txt_results.delete(1.0, tk.END)
        self.txt_results.insert(tk.END, f"Puan: {score}\n\n")
        for line in log: self.txt_results.insert(tk.END, line + "\n")
        
    def update_total_score(self):
        total = sum(r['total'] for r in self.session_results.values())
        self.lbl_total_score.config(text=f"{total}")

    def draw_scanner_rois(self, details):
        self.canvas.delete("scanner_roi")
        for idx, item in enumerate(details):
            roi = item['roi_def']
            x, y = self.to_canvas_coords(roi['x'], roi['y'])
            w = roi['w'] * self.image_scale * self.zoom_scale
            h = roi['h'] * self.image_scale * self.zoom_scale
            
            color = "green" if item['is_marked'] else "red"
            self.canvas.create_rectangle(x, y, x+w, y+h, outline=color, width=2, tags=("scanner_roi", f"roi_{idx}"))

    def to_canvas_coords(self, img_x, img_y):
        x = (img_x * self.image_scale * self.zoom_scale) + self.pan_x
        y = (img_y * self.image_scale * self.zoom_scale) + self.pan_y
        return x, y

    def open_corner_correction(self):
        if not self.input_images: return
        current_img = self.input_images[self.current_input_index]
        
        d = dialogs.CornerCorrectionDialog(self.app.root, current_img)
        if d.result_image is not None:
             self.input_images[self.current_input_index] = d.result_image
             if self.current_input_index in self.session_results:
                 del self.session_results[self.current_input_index]
                 self.txt_results.delete(1.0, tk.END)
             self.update_scanner_ui()

    def auto_crop_current_page(self):
        if not self.input_images: return
        
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
                    self.txt_results.delete(1.0, tk.END)
                
                self.update_scanner_ui()
                # messagebox.showinfo("Başarılı", "Otomatik kırpma uygulandı.") # Optional feedback
            else:
                messagebox.showwarning("Başarısız", "Otomatik köşe tespiti başarısız oldu. Manuel kırpma kullanın.")
                
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
            self.btn_edit_mode.config(text="✎ Veri Düzenleme: AÇIK", style="Accent.TButton")
            self.canvas.bind("<Button-1>", self.on_scanner_roi_click)
        else:
            self.btn_edit_mode.config(text="✎ Veri Düzenleme: Kapalı", style="TButton")
            self.canvas.bind("<Button-1>", self.on_mouse_down)

    def on_scanner_roi_click(self, event):
        if not self.edit_mode: return
        if self.current_input_index not in self.session_results: return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        item = self.canvas.find_closest(x, y)
        tags = self.canvas.gettags(item)
        
        roi_idx = -1
        for tag in tags:
            if tag.startswith("roi_"):
                roi_idx = int(tag.split("_")[1])
                break
        if roi_idx == -1: return
        
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
            self.lbl_threshold_value.config(text=f"{self.dynamic_threshold:.3f}")

    def recalculate_page_score(self, input_idx):
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
            
            if is_marked:
                try:
                    s = float(val)
                    p_score += s
                    p_subscales[sub] = p_subscales.get(sub, 0) + s
                except: pass
            p_log.append(f"{status} {label} [{sub}]: {val if is_marked else '0'} (Manuel)")
            
        print(f"[SCANNER] Manuel düzenleme sonrası yeni puan: {p_score}")
        res['total'] = p_score
        res['subscales'] = p_subscales
        
        if input_idx == self.current_input_index:
            self.update_results_display(p_score, p_log)
            self.update_total_score()

    def show_session_report(self):
        if not self.session_results: return
        
        total_score = sum(r['total'] for r in self.session_results.values())
        report = f"=== OTURUM RAPORU ===\nToplam Puan: {total_score}\n"
        
        top = tk.Toplevel(self.app.root)
        top.title("Rapor")
        txt = tk.Text(top)
        txt.pack()
        txt.insert(tk.END, report)
        
        ttk.Button(top, text="Dışa Aktar CSV", command=lambda: file_io.export_csv_report(self.session_results, filedialog.asksaveasfilename(defaultextension=".csv"))).pack()

    def on_threshold_change(self, value):
        self.dynamic_threshold = float(value)
        self.lbl_threshold_value.config(text=f"{self.dynamic_threshold:.3f}")

    # Zoom/Pan (shared logic usually, duplicated here for independence or could be in utils)
    def on_zoom(self, event):
        if not self.tk_image: return
        if event.num == 5 or event.delta < 0: factor = 0.9
        else: factor = 1.1
        self.zoom_scale *= factor
        self.refresh_canvas()

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def do_pan(self, event):
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        self.pan_x += dx
        self.pan_y += dy
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.refresh_canvas()

    def on_mouse_down(self, event):
        self.start_pan(event) # Fallback to pan? Scanner doesn't usually draw boxes manually.
        pass # Scanner mode usually just pans.

    def on_mouse_drag(self, event):
        self.do_pan(event)

    def on_mouse_up(self, event):
        pass
