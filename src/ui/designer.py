
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
import os
import json
from PIL import Image, ImageTk

from src.utils import file_io
from src.ui import dialogs
from src import config

class DesignerMode:
    def __init__(self, app):
        self.app = app # Reference to main OMRApp for shared resources like root, status_var
        self.pages = [] 
        self.current_page_index = 0
        self.selected_roi_index = None
        self.grid_mode_var = tk.BooleanVar(value=False)
        
        # Canvas state
        self.canvas = None
        self.tk_image = None
        
        # Interaction state
        self.rect_start_x = None
        self.rect_start_y = None
        self.current_rect = None
        
        # Zoom/Pan state
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.image_scale = 1.0
        
        self.colors = config.THEMES[config.DEFAULT_THEME] # fallback, app should set this

    def setup_ui(self, parent_frame):
        self.colors = self.app.colors
        
        # toolbar
        toolbar = ttk.Frame(parent_frame, style="Panel.TFrame", padding=10)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        # group 1: file operations
        grp_file = ttk.LabelFrame(toolbar, text="Dosya", padding=5)
        grp_file.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(grp_file, text="Boş Form Yükle", command=self.load_blank_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(grp_file, text="Şablon Yükle", command=self.load_template_for_editing).pack(side=tk.LEFT, padx=5)
        ttk.Button(grp_file, text="Şablonu Kaydet", command=self.save_template, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        
        # group 2: edit
        grp_edit = ttk.LabelFrame(toolbar, text="Düzenle", padding=5)
        grp_edit.pack(side=tk.LEFT, padx=5)
        ttk.Button(grp_edit, text="Sayfayı Temizle", command=self.clear_rois).pack(side=tk.LEFT, padx=5)
        
        self.grid_mode_var.set(False)
        ttk.Checkbutton(grp_edit, text="Grid Aracı", variable=self.grid_mode_var, style="Switch.TCheckbutton").pack(side=tk.LEFT, padx=10)
        
        # group 3: navigation
        grp_nav = ttk.LabelFrame(toolbar, text="Navigasyon", padding=5)
        grp_nav.pack(side=tk.LEFT, padx=5)
        
        self.btn_prev = ttk.Button(grp_nav, text="< Önceki", command=self.prev_page, state=tk.DISABLED)
        self.btn_prev.pack(side=tk.LEFT, padx=5)
        
        self.lbl_page = ttk.Label(grp_nav, text="Sayfa 1/1")
        self.lbl_page.pack(side=tk.LEFT, padx=5)
        
        self.btn_next = ttk.Button(grp_nav, text="Sonraki >", command=self.next_page, state=tk.DISABLED)
        self.btn_next.pack(side=tk.LEFT, padx=5)
        
        # help button
        ttk.Button(toolbar, text="Yardım / Kısayollar", command=self.show_help).pack(side=tk.RIGHT, padx=10)

        # Content Area
        content_area = ttk.PanedWindow(parent_frame, orient=tk.HORIZONTAL)
        content_area.pack(fill=tk.BOTH, expand=True)
        
        # Canvas Frame
        self.canvas_frame = ttk.Frame(content_area, style="TFrame")
        content_area.add(self.canvas_frame, weight=3)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg=self.colors["canvas"], bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # ROI Panel
        self.roi_panel = ttk.Frame(content_area, style="Panel.TFrame", padding=5)
        content_area.add(self.roi_panel, weight=1)
        
        ttk.Label(self.roi_panel, text="Bölge Listesi", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        columns = ("label", "value", "subscale")
        self.roi_tree = ttk.Treeview(self.roi_panel, columns=columns, show="headings", selectmode="browse")
        
        self.roi_tree.heading("label", text="Etiket")
        self.roi_tree.heading("value", text="Değer")
        self.roi_tree.heading("subscale", text="Alt Ölçek")
        
        self.roi_tree.column("label", width=60)
        self.roi_tree.column("value", width=40)
        self.roi_tree.column("subscale", width=80)
        
        scrollbar = ttk.Scrollbar(self.roi_panel, orient=tk.VERTICAL, command=self.roi_tree.yview)
        self.roi_tree.configure(yscroll=scrollbar.set)
        
        self.roi_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bindings
        self.roi_tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.roi_tree.bind("<Double-1>", self.on_roi_list_double_click)
        
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Button-3>", self.undo_last_roi)
        
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-4>", self.on_zoom)
        self.canvas.bind("<Button-5>", self.on_zoom)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.do_pan)
        
        # App-level key binding helper required to route keys to active mode
        # handled by app.kwy_handler -> self.on_key_press
        
        self.refresh_roi_list()

    def load_blank_form(self):
        file_path = filedialog.askopenfilename(filetypes=[("Files", "*.jpg *.jpeg *.png *.bmp *.pdf")])
        if not file_path: return
        
        print(f"[DESIGNER] Boş form yükleniyor: {file_path}")
        loaded_imgs = file_io.load_images_from_file(file_path)
        if not loaded_imgs:
            print("[ERROR] Görseller yüklenemedi")
            messagebox.showerror("Error", "Could not load images.")
            return

        self.pages = []
        for img in loaded_imgs:
            self.pages.append({
                'image': img,
                'rois': [],
                'image_path': file_path
            })
            
        self.current_page_index = 0
        self.display_current_page()

    def load_template_for_editing(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file_path: return
        
        print(f"[DESIGNER] Düzenleme için şablon yükleniyor: {file_path}")
        
        try:
            data = file_io.load_template_json(file_path)
            template_dir = os.path.dirname(file_path)
            new_pages = []
            
            for page_data in data.get('pages', []):
                ref_img_name = page_data['ref_image_storage']
                ref_img_path = os.path.join(template_dir, ref_img_name)
                
                if not os.path.exists(ref_img_path):
                    messagebox.showerror("Hata", f"Referans resim bulunamadı:\n{ref_img_path}")
                    return
                    
                img = cv2.imread(ref_img_path)
                if img is None:
                    messagebox.showerror("Hata", f"Resim yüklenemedi:\n{ref_img_path}")
                    return
                    
                new_pages.append({
                    'image': img,
                    'rois': page_data.get('rois', []),
                    'image_path': ref_img_path
                })
                
            if not new_pages:
                messagebox.showwarning("Uyarı", "Şablonda sayfa bulunamadı.")
                return
                
            self.pages = new_pages
            self.current_page_index = 0
            self.display_current_page()
            self.refresh_roi_list()
            messagebox.showinfo("Başarılı", "Şablon düzenleme için yüklendi.")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Şablon yüklenirken hata oluştu:\n{e}")

    def save_template(self):
        print("[SAVE] Şablon kaydetme işlemi başlatıldı")
        if not self.pages:
            messagebox.showwarning("Uyarı", "Yüklü sayfa yok!")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not file_path: return
        
        base_name = os.path.splitext(file_path)[0]
        template_pages_data = []
        
        for idx, page in enumerate(self.pages):
            ref_save_path = f"{base_name}_p{idx}.jpg"
            cv2.imwrite(ref_save_path, page['image'])
            
            template_pages_data.append({
                "page_index": idx,
                "ref_image_storage": os.path.basename(ref_save_path),
                "rois": page['rois']
            })
            
        data = {"version": "2.0", "pages": template_pages_data}
        file_io.save_template_json(data, file_path)
        messagebox.showinfo("Başarılı", f"Şablon kaydedildi: {file_path}")

    def display_current_page(self):
        if not self.pages:
            self.canvas.delete("all")
            return
            
        page = self.pages[self.current_page_index]
        img = page['image']
        
        # Calculate scale
        h, w = img.shape[:2]
        canvas_h = 700
        canvas_w = 1100
        scale_w = canvas_w / w
        scale_h = canvas_h / h
        self.image_scale = min(scale_w, scale_h, 1.0)
        
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        self.refresh_canvas()
        self.refresh_roi_list()
        self.update_nav_buttons()

    def refresh_canvas(self):
        if not self.pages: return
        
        page = self.pages[self.current_page_index]
        img = page['image']
        rois = page['rois']
        
        h, w = img.shape[:2]
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
        
        self.redraw_rois(rois)

    def redraw_rois(self, rois):
        self.canvas.delete("roi")
        for i, item in enumerate(rois):
            x, y = self.to_canvas_coords(item['x'], item['y'])
            w = item['w'] * self.image_scale * self.zoom_scale
            h = item['h'] * self.image_scale * self.zoom_scale
            
            color = "green"
            width = 2
            if i == self.selected_roi_index:
                color = "red"
                width = 3
            
            self.canvas.create_rectangle(x, y, x+w, y+h, outline=color, width=width, tags="roi")
            sub = item.get('subscale', 'Genel')
            self.canvas.create_text(x, y-5, text=f"{item['label']} ({item['value']}) [{sub}]", fill="blue", anchor=tk.SW, tags="roi")

    def to_canvas_coords(self, img_x, img_y):
        x = (img_x * self.image_scale * self.zoom_scale) + self.pan_x
        y = (img_y * self.image_scale * self.zoom_scale) + self.pan_y
        return x, y

    def to_image_coords(self, canvas_x, canvas_y):
        x = (canvas_x - self.pan_x) / (self.image_scale * self.zoom_scale)
        y = (canvas_y - self.pan_y) / (self.image_scale * self.zoom_scale)
        return int(x), int(y)

    def on_mouse_down(self, event):
        self.canvas.focus_set()
        if not self.pages: return
        
        click_x = self.canvas.canvasx(event.x)
        click_y = self.canvas.canvasy(event.y)
        img_x, img_y = self.to_image_coords(click_x, click_y)
        
        print(f"[DESIGNER] Tıklama: Canvas({click_x:.1f}, {click_y:.1f}) -> Resim({img_x}, {img_y})")
        
        rois = self.pages[self.current_page_index]['rois']
        clicked_index = None
        
        for i in range(len(rois)-1, -1, -1):
            r = rois[i]
            if (r['x'] <= img_x <= r['x'] + r['w']) and (r['y'] <= img_y <= r['y'] + r['h']):
                clicked_index = i
                break
        
        if clicked_index is not None:
            self.selected_roi_index = clicked_index
            self.refresh_canvas()
            self.refresh_roi_list()
            return
        else:
            if self.selected_roi_index is not None:
                self.selected_roi_index = None
                self.refresh_canvas()
                self.refresh_roi_list()
        
        self.rect_start_x = click_x
        self.rect_start_y = click_y
        self.current_rect = self.canvas.create_rectangle(
            self.rect_start_x, self.rect_start_y, 
            self.rect_start_x, self.rect_start_y, 
            outline="red", width=2
        )

    def on_mouse_drag(self, event):
        if self.current_rect:
            cur_x = self.canvas.canvasx(event.x)
            cur_y = self.canvas.canvasy(event.y)
            self.canvas.coords(self.current_rect, self.rect_start_x, self.rect_start_y, cur_x, cur_y)

    def on_mouse_up(self, event):
        if not self.current_rect: return
        if not self.pages: return
        
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        
        x1 = min(self.rect_start_x, cur_x)
        y1 = min(self.rect_start_y, cur_y)
        x2 = max(self.rect_start_x, cur_x)
        y2 = max(self.rect_start_y, cur_y)
        
        if (x2 - x1) < 5 or (y2 - y1) < 5:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            return

        # Grid or Single
        if self.grid_mode_var.get():
            self._handle_grid_creation(x1, y1, x2, y2)
        else:
            self._handle_single_roi_creation(x1, y1, x2, y2)

    def _handle_grid_creation(self, x1, y1, x2, y2):
        current_rois = self.pages[self.current_page_index]['rois']
        default_label = f"Q{len(current_rois)+1}"
        
        d = dialogs.GridDialog(self.app.root, default_label)
        if d.result is None:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            return
            
        rows = d.result['rows']
        cols = d.result['cols']
        base_label = d.result['label']
        subscale = d.result['subscale']
        
        orig_x, orig_y = self.to_image_coords(x1, y1)
        orig_x2, orig_y2 = self.to_image_coords(x2, y2)
        
        total_w = orig_x2 - orig_x
        total_h = orig_y2 - orig_y
        cell_w = total_w / cols
        cell_h = total_h / rows
        
        count = 1
        for r in range(rows):
            for c in range(cols):
                cell_x = int(orig_x + (c * cell_w))
                cell_y = int(orig_y + (r * cell_h))
                lbl = f"{base_label}-{count}"
                
                roi_data = {
                    "x": cell_x, "y": cell_y, "w": int(cell_w), "h": int(cell_h),
                    "value": "1", "label": lbl, "subscale": subscale
                }
                self.pages[self.current_page_index]['rois'].append(roi_data)
                count += 1
        
        self.canvas.delete(self.current_rect)
        self.current_rect = None
        self.redraw_rois(self.pages[self.current_page_index]['rois'])
        self.refresh_roi_list()

    def _handle_single_roi_creation(self, x1, y1, x2, y2):
        current_rois = self.pages[self.current_page_index]['rois']
        default_label = f"Madde {len(current_rois)+1}"
        last_subscale = current_rois[-1].get('subscale', "Genel") if current_rois else "Genel"
            
        d = dialogs.RegionPropertiesDialog(self.app.root, default_label, last_subscale)
        if d.result is None:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            return

        orig_x, orig_y = self.to_image_coords(x1, y1)
        orig_x2, orig_y2 = self.to_image_coords(x2, y2)
        
        roi_data = {
            "x": orig_x, "y": orig_y, "w": orig_x2 - orig_x, "h": orig_y2 - orig_y,
            "value": d.result['value'],
            "label": d.result['label'],
            "subscale": d.result['subscale']
        }

        print(f"[DESIGNER] Yeni ROI eklendi: {roi_data}")
        self.pages[self.current_page_index]['rois'].append(roi_data)
        self.canvas.delete(self.current_rect)
        self.current_rect = None
        self.redraw_rois(self.pages[self.current_page_index]['rois'])
        self.refresh_roi_list()

    def undo_last_roi(self, event):
        if self.pages and self.pages[self.current_page_index]['rois']:
            print("[DESIGNER] Son ROI geri alındı")
            self.pages[self.current_page_index]['rois'].pop()
            self.refresh_canvas()
            self.refresh_roi_list()
            
    def clear_rois(self):
        if self.pages:
            print("[DESIGNER] Sayfadaki tüm ROI'ler silindi")
            self.pages[self.current_page_index]['rois'] = []
            self.refresh_canvas()
            self.refresh_roi_list()

    def on_zoom(self, event):
        if not self.tk_image: return
        
        if event.num == 5 or event.delta < 0: factor = 0.9
        else: factor = 1.1
            
        new_zoom = self.zoom_scale * factor
        if new_zoom < 0.1 or new_zoom > 10.0: return
            
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)
        
        rel_x = (mouse_x - self.pan_x) / self.zoom_scale
        rel_y = (mouse_y - self.pan_y) / self.zoom_scale
        
        self.zoom_scale = new_zoom
        self.pan_x = mouse_x - (rel_x * self.zoom_scale)
        self.pan_y = mouse_y - (rel_y * self.zoom_scale)
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
            
    def update_nav_buttons(self):
        total = len(self.pages)
        if total == 0:
            self.lbl_page.config(text="Sayfa Yok")
            self.btn_prev.config(state=tk.DISABLED)
            self.btn_next.config(state=tk.DISABLED)
            return
        self.lbl_page.config(text=f"Sayfa {self.current_page_index + 1}/{total}")
        self.btn_prev.config(state=tk.NORMAL if self.current_page_index > 0 else tk.DISABLED)
        self.btn_next.config(state=tk.NORMAL if self.current_page_index < total - 1 else tk.DISABLED)

    def prev_page(self):
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.display_current_page()

    def next_page(self):
        if self.current_page_index < len(self.pages) - 1:
            self.current_page_index += 1
            self.display_current_page()
            
    def refresh_roi_list(self):
        if not hasattr(self, 'roi_tree') or not self.roi_tree.winfo_exists(): return
        for item in self.roi_tree.get_children(): self.roi_tree.delete(item)
        if not self.pages: return
        
        rois = self.pages[self.current_page_index]['rois']
        for i, roi in enumerate(rois):
            self.roi_tree.insert("", "end", iid=str(i), values=(roi['label'], roi['value'], roi.get('subscale', 'Genel')))
            
        if self.selected_roi_index is not None and 0 <= self.selected_roi_index < len(rois):
            self.roi_tree.selection_set(str(self.selected_roi_index))
            self.roi_tree.see(str(self.selected_roi_index))
        else:
            self.selected_roi_index = None

    def on_tree_select(self, event):
        sel = self.roi_tree.selection()
        if not sel: self.selected_roi_index = None
        else: self.selected_roi_index = int(sel[0])
        self.refresh_canvas()

    def on_roi_list_double_click(self, event):
        if self.selected_roi_index is None: return
        rois = self.pages[self.current_page_index]['rois']
        roi = rois[self.selected_roi_index]
        
        d = dialogs.RegionPropertiesDialog(self.app.root, roi['label'], roi.get('subscale', 'Genel'), roi['value'])
        if d.result:
            roi.update(d.result)
            self.refresh_roi_list()
            self.refresh_canvas()
            
    def show_help(self):
        help_text = """
Kısayollar ve Kullanım:
Seçim: Tıklama, Liste
Düzenleme: Çift Tıklama (Liste), Delete (Sil)
Hareket: Yön Tuşları, Shift+Yön Tuşları
Boyutlandırma: Alt + Yön Tuşları
Geri Al: Sağ Tık
"""
        messagebox.showinfo("Yardım", help_text)

    def on_key_press(self, event):
        """Called by main app key handler"""
        # ... logic for moving/resizing ROIs ...
        if self.selected_roi_index is None: return
        if not self.pages: return
        
        rois = self.pages[self.current_page_index]['rois']
        roi = rois[self.selected_roi_index]
        key = event.keysym
        
        step = 10 if (event.state & 0x0001) else 1
        is_alt = (event.state & 0x20000) or (event.state & 131072)
        
        if key == "Delete":
            rois.pop(self.selected_roi_index)
            self.selected_roi_index = None
            self.refresh_roi_list()
            self.refresh_canvas()
            return
            
        if is_alt:
            if key == "Left": roi['w'] = max(5, roi['w'] - 1)
            elif key == "Right": roi['w'] += 1
            elif key == "Up": roi['h'] = max(5, roi['h'] - 1)
            elif key == "Down": roi['h'] += 1
        else:
            if key == "Left": roi['x'] -= step
            elif key == "Right": roi['x'] += step
            elif key == "Up": roi['y'] -= step
            elif key == "Down": roi['y'] += step
            
        self.refresh_canvas()
