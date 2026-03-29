"""
Designer Mode - Modern UI for OMR Template Creation

This module handles the template design workflow with a modernized customtkinter interface.
All functional logic (ROI creation, grid tool, saving) remains intact.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk  # Keep ttk.Treeview as CTk doesn't have a replacement
import cv2
import numpy as np
import os
import json
from PIL import Image, ImageTk

from src.utils import file_io
from src.ui import dialogs
from src.ui.styles import Style, create_accent_button, create_secondary_button
from src import config


class DesignerMode:
    """
    Designer mode for creating and editing OMR templates.
    All ROI logic is preserved; only UI presentation is modernized.
    """
    
    def __init__(self, app):
        self.app = app  # Reference to main OMRApp
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
        
        # Get colors from style system
        self.colors = Style.get_theme_colors()

    def setup_ui(self, parent_frame):
        """Setup the designer mode UI with modern CTk widgets."""
        self.colors = Style.get_theme_colors()
        
        # ==========================================================================
        # TOOLBAR
        # ==========================================================================
        toolbar = ctk.CTkFrame(
            parent_frame, 
            fg_color=self.colors["bg_secondary"],
            corner_radius=0,
            height=60
        )
        toolbar.pack(side="top", fill="x", padx=0, pady=0)
        toolbar.pack_propagate(False)
        
        toolbar_content = ctk.CTkFrame(toolbar, fg_color="transparent")
        toolbar_content.pack(fill="both", expand=True, padx=Style.PADDING_MD, pady=Style.PADDING_SM)
        
        # Group 1: File Operations
        grp_file = ctk.CTkFrame(toolbar_content, fg_color="transparent")
        grp_file.pack(side="left", padx=(0, Style.PADDING_XL))  # Increased spacing between groups
        
        ctk.CTkLabel(
            grp_file, 
            text="DOSYA",
            font=Style.FONTS["small_bold"],
            text_color=self.colors["text_muted"]
        ).pack(side="top", anchor="w")
        
        btn_row1 = ctk.CTkFrame(grp_file, fg_color="transparent")
        btn_row1.pack(side="top", pady=(Style.PADDING_XS, 0))
        
        create_secondary_button(
            btn_row1, 
            text="📁 Boş Form Yükle", 
            command=self.load_blank_form
        ).pack(side="left", padx=(0, Style.PADDING_MD))  # Increased button spacing
        
        create_secondary_button(
            btn_row1, 
            text="📂 Şablon Yükle", 
            command=self.load_template_for_editing
        ).pack(side="left", padx=(0, Style.PADDING_MD))
        
        create_accent_button(
            btn_row1, 
            text="💾 Şablonu Kaydet", 
            command=self.save_template
        ).pack(side="left")
        
        # Separator
        ctk.CTkFrame(
            toolbar_content, 
            width=1, 
            fg_color=self.colors["border"]
        ).pack(side="left", fill="y", padx=Style.PADDING_LG)
        
        # Group 2: Edit Tools
        grp_edit = ctk.CTkFrame(toolbar_content, fg_color="transparent")
        grp_edit.pack(side="left", padx=(0, Style.PADDING_XL))
        
        ctk.CTkLabel(
            grp_edit, 
            text="DÜZENLE",
            font=Style.FONTS["small_bold"],
            text_color=self.colors["text_muted"]
        ).pack(side="top", anchor="w")
        
        btn_row2 = ctk.CTkFrame(grp_edit, fg_color="transparent")
        btn_row2.pack(side="top", pady=(Style.PADDING_XS, 0))
        
        create_secondary_button(
            btn_row2, 
            text="🗑️ Sayfayı Temizle", 
            command=self.clear_rois
        ).pack(side="left", padx=(0, Style.PADDING_MD))
        
        self.grid_mode_switch = ctk.CTkSwitch(
            btn_row2,
            text="Grid Aracı",
            variable=self.grid_mode_var,
            font=Style.FONTS["body"],
            text_color=self.colors["text_primary"],
            fg_color=self.colors["bg_tertiary"],
            progress_color=self.colors["accent"],
            button_color=self.colors["text_secondary"],
            button_hover_color=self.colors["text_primary"]
        )
        self.grid_mode_switch.pack(side="left")
        
        # Separator
        ctk.CTkFrame(
            toolbar_content, 
            width=1, 
            fg_color=self.colors["border"]
        ).pack(side="left", fill="y", padx=Style.PADDING_LG)
        
        # Group 3: Navigation
        grp_nav = ctk.CTkFrame(toolbar_content, fg_color="transparent")
        grp_nav.pack(side="left", padx=(0, Style.PADDING_XL))
        
        ctk.CTkLabel(
            grp_nav, 
            text="SAYFA",
            font=Style.FONTS["small_bold"],
            text_color=self.colors["text_muted"]
        ).pack(side="top", anchor="w")
        
        btn_row3 = ctk.CTkFrame(grp_nav, fg_color="transparent")
        btn_row3.pack(side="top", pady=(Style.PADDING_XS, 0))
        
        self.btn_prev = ctk.CTkButton(
            btn_row3,
            text="◀ Önceki",
            command=self.prev_page,
            state="disabled",
            width=100,  # Wider buttons
            height=Style.BUTTON_HEIGHT_SM,
            font=Style.FONTS["button"],
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            corner_radius=Style.CORNER_RADIUS_SM
        )
        self.btn_prev.pack(side="left", padx=(0, Style.PADDING_MD))
        
        self.lbl_page = ctk.CTkLabel(
            btn_row3, 
            text="Sayfa 1/1",
            font=Style.FONTS["body_bold"],
            text_color=self.colors["text_primary"],
            width=100
        )
        self.lbl_page.pack(side="left", padx=Style.PADDING_MD)
        
        self.btn_next = ctk.CTkButton(
            btn_row3,
            text="Sonraki ▶",
            command=self.next_page,
            state="disabled",
            width=100,  # Wider buttons
            height=Style.BUTTON_HEIGHT_SM,
            font=Style.FONTS["button"],
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            corner_radius=Style.CORNER_RADIUS_SM
        )
        self.btn_next.pack(side="left")
        
        # Help button (right side)
        create_secondary_button(
            toolbar_content, 
            text="❓ Yardım", 
            command=self.show_help
        ).pack(side="right")
        
        # ==========================================================================
        # CONTENT AREA (Canvas + ROI Panel)
        # ==========================================================================
        content_area = ctk.CTkFrame(parent_frame, fg_color=self.colors["bg_primary"])
        content_area.pack(fill="both", expand=True)
        
        # Canvas Frame
        self.canvas_frame = ctk.CTkFrame(
            content_area, 
            fg_color=self.colors["bg_primary"],
            corner_radius=0
        )
        self.canvas_frame.pack(side="left", fill="both", expand=True)
        
        # Canvas (still using tk.Canvas for rendering compatibility)
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            bg=self.colors["canvas"], 
            bd=0, 
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # ==========================================================================
        # ROI PANEL (Right)
        # ==========================================================================
        self.roi_panel = ctk.CTkFrame(
            content_area, 
            width=280,
            fg_color=self.colors["bg_secondary"],
            corner_radius=0
        )
        self.roi_panel.pack(side="right", fill="y", padx=0, pady=0)
        self.roi_panel.pack_propagate(False)
        
        panel_content = ctk.CTkFrame(self.roi_panel, fg_color="transparent")
        panel_content.pack(fill="both", expand=True, padx=Style.PADDING_MD, pady=Style.PADDING_MD)
        
        # Section header
        self._create_section_header(panel_content, "BÖLGE LİSTESİ")
        
        # ROI Treeview (keeping ttk.Treeview as it has no CTk equivalent)
        tree_frame = ctk.CTkFrame(panel_content, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True)
        
        # Configure Treeview style
        style = ttk.Style()
        style.configure(
            "Designer.Treeview",
            background=self.colors["input_bg"],
            foreground=self.colors["text_primary"],
            fieldbackground=self.colors["input_bg"],
            borderwidth=0,
            font=Style.FONTS["small"]
        )
        style.configure(
            "Designer.Treeview.Heading",
            background=self.colors["bg_tertiary"],
            foreground=self.colors["text_primary"],
            font=Style.FONTS["small_bold"]
        )
        style.map("Designer.Treeview", background=[("selected", self.colors["accent"])])
        
        columns = ("label", "value", "subscale")
        self.roi_tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show="headings", 
            selectmode="browse",
            style="Designer.Treeview"
        )
        
        self.roi_tree.heading("label", text="Etiket")
        self.roi_tree.heading("value", text="Değer")
        self.roi_tree.heading("subscale", text="Alt Ölçek")
        
        self.roi_tree.column("label", width=70)
        self.roi_tree.column("value", width=50)
        self.roi_tree.column("subscale", width=90)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.roi_tree.yview)
        self.roi_tree.configure(yscroll=scrollbar.set)
        
        self.roi_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Keyboard shortcuts info
        info_frame = ctk.CTkFrame(panel_content, fg_color=self.colors["bg_tertiary"], corner_radius=Style.CORNER_RADIUS_SM)
        info_frame.pack(fill="x", pady=(Style.PADDING_MD, 0))
        
        ctk.CTkLabel(
            info_frame,
            text="⌨️ Kısayollar",
            font=Style.FONTS["small_bold"],
            text_color=self.colors["text_secondary"]
        ).pack(anchor="w", padx=Style.PADDING_SM, pady=(Style.PADDING_SM, 0))
        
        shortcuts_text = "↑↓←→: Hareket | Shift+: Hızlı\nAlt+: Boyut | Del: Sil | Sağ-tık: Geri"
        ctk.CTkLabel(
            info_frame,
            text=shortcuts_text,
            font=Style.FONTS["mono_small"],
            text_color=self.colors["text_muted"],
            justify="left"
        ).pack(anchor="w", padx=Style.PADDING_SM, pady=(0, Style.PADDING_SM))
        
        # ==========================================================================
        # Event Bindings
        # ==========================================================================
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
        
        self.refresh_roi_list()
    
    def _create_section_header(self, parent, text):
        """Create a styled section header with separator."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, Style.PADDING_MD))
        
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

    def load_blank_form(self):
        """Load a blank form image. Logic unchanged."""
        file_path = filedialog.askopenfilename(filetypes=[("Files", "*.jpg *.jpeg *.png *.bmp *.pdf")])
        if not file_path:
            return
        
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
        """Load existing template for editing. Logic unchanged."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file_path:
            return
        
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
        """Save current template. Logic unchanged."""
        print("[SAVE] Şablon kaydetme işlemi başlatıldı")
        if not self.pages:
            messagebox.showwarning("Uyarı", "Yüklü sayfa yok!")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not file_path:
            return
        
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
        """Display current page. Logic unchanged."""
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
        """Refresh canvas display. Logic unchanged."""
        if not self.pages:
            return
        
        page = self.pages[self.current_page_index]
        img = page['image']
        rois = page['rois']
        
        h, w = img.shape[:2]
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
        
        self.redraw_rois(rois)

    def redraw_rois(self, rois):
        """Redraw ROI overlays. Logic unchanged."""
        self.canvas.delete("roi")
        for i, item in enumerate(rois):
            x, y = self.to_canvas_coords(item['x'], item['y'])
            w = item['w'] * self.image_scale * self.zoom_scale
            h = item['h'] * self.image_scale * self.zoom_scale
            
            color = "#22c55e"  # Modern green
            width = 2
            if i == self.selected_roi_index:
                color = "#e94560"  # Accent red
                width = 3
            
            self.canvas.create_rectangle(x, y, x+w, y+h, outline=color, width=width, tags="roi")
            sub = item.get('subscale', 'Genel')
            self.canvas.create_text(
                x, y-5, 
                text=f"{item['label']} ({item['value']}) [{sub}]", 
                fill="#3b82f6",  # Modern blue
                anchor=tk.SW, 
                tags="roi",
                font=Style.FONTS["small"]
            )

    def to_canvas_coords(self, img_x, img_y):
        """Convert image coords to canvas coords. Logic unchanged."""
        x = (img_x * self.image_scale * self.zoom_scale) + self.pan_x
        y = (img_y * self.image_scale * self.zoom_scale) + self.pan_y
        return x, y

    def to_image_coords(self, canvas_x, canvas_y):
        """Convert canvas coords to image coords. Logic unchanged."""
        x = (canvas_x - self.pan_x) / (self.image_scale * self.zoom_scale)
        y = (canvas_y - self.pan_y) / (self.image_scale * self.zoom_scale)
        return int(x), int(y)

    def on_mouse_down(self, event):
        """Handle mouse down. Logic unchanged."""
        self.canvas.focus_set()
        if not self.pages:
            return
        
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
            outline="#e94560", width=2
        )

    def on_mouse_drag(self, event):
        """Handle mouse drag. Logic unchanged."""
        if self.current_rect:
            cur_x = self.canvas.canvasx(event.x)
            cur_y = self.canvas.canvasy(event.y)
            self.canvas.coords(self.current_rect, self.rect_start_x, self.rect_start_y, cur_x, cur_y)

    def on_mouse_up(self, event):
        """Handle mouse up. Logic unchanged."""
        if not self.current_rect:
            return
        if not self.pages:
            return
        
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
        """Handle grid ROI creation. Logic unchanged."""
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
        """Handle single ROI creation. Logic unchanged."""
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
        """Undo last ROI. Logic unchanged."""
        if self.pages and self.pages[self.current_page_index]['rois']:
            print("[DESIGNER] Son ROI geri alındı")
            self.pages[self.current_page_index]['rois'].pop()
            self.refresh_canvas()
            self.refresh_roi_list()
            
    def clear_rois(self):
        """Clear all ROIs on current page. Logic unchanged."""
        if self.pages:
            print("[DESIGNER] Sayfadaki tüm ROI'ler silindi")
            self.pages[self.current_page_index]['rois'] = []
            self.refresh_canvas()
            self.refresh_roi_list()

    def on_zoom(self, event):
        """Handle zoom. Logic unchanged."""
        if not self.tk_image:
            return
        
        if event.num == 5 or event.delta < 0:
            factor = 0.9
        else:
            factor = 1.1
            
        new_zoom = self.zoom_scale * factor
        if new_zoom < 0.1 or new_zoom > 10.0:
            return
            
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)
        
        rel_x = (mouse_x - self.pan_x) / self.zoom_scale
        rel_y = (mouse_y - self.pan_y) / self.zoom_scale
        
        self.zoom_scale = new_zoom
        self.pan_x = mouse_x - (rel_x * self.zoom_scale)
        self.pan_y = mouse_y - (rel_y * self.zoom_scale)
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
            
    def update_nav_buttons(self):
        """Update navigation buttons. Logic unchanged."""
        total = len(self.pages)
        if total == 0:
            self.lbl_page.configure(text="Sayfa Yok")
            self.btn_prev.configure(state="disabled")
            self.btn_next.configure(state="disabled")
            return
        self.lbl_page.configure(text=f"Sayfa {self.current_page_index + 1}/{total}")
        self.btn_prev.configure(state="normal" if self.current_page_index > 0 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page_index < total - 1 else "disabled")

    def prev_page(self):
        """Navigate to previous page. Logic unchanged."""
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.display_current_page()

    def next_page(self):
        """Navigate to next page. Logic unchanged."""
        if self.current_page_index < len(self.pages) - 1:
            self.current_page_index += 1
            self.display_current_page()
            
    def refresh_roi_list(self):
        """Refresh ROI list in treeview. Logic unchanged."""
        if not hasattr(self, 'roi_tree') or not self.roi_tree.winfo_exists():
            return
        for item in self.roi_tree.get_children():
            self.roi_tree.delete(item)
        if not self.pages:
            return
        
        rois = self.pages[self.current_page_index]['rois']
        for i, roi in enumerate(rois):
            self.roi_tree.insert("", "end", iid=str(i), values=(roi['label'], roi['value'], roi.get('subscale', 'Genel')))
            
        if self.selected_roi_index is not None and 0 <= self.selected_roi_index < len(rois):
            self.roi_tree.selection_set(str(self.selected_roi_index))
            self.roi_tree.see(str(self.selected_roi_index))
        else:
            self.selected_roi_index = None

    def on_tree_select(self, event):
        """Handle treeview selection. Logic unchanged."""
        sel = self.roi_tree.selection()
        if not sel:
            self.selected_roi_index = None
        else:
            self.selected_roi_index = int(sel[0])
        self.refresh_canvas()

    def on_roi_list_double_click(self, event):
        """Handle double-click on ROI list. Logic unchanged."""
        if self.selected_roi_index is None:
            return
        rois = self.pages[self.current_page_index]['rois']
        roi = rois[self.selected_roi_index]
        
        d = dialogs.RegionPropertiesDialog(self.app.root, roi['label'], roi.get('subscale', 'Genel'), roi['value'])
        if d.result:
            roi.update(d.result)
            self.refresh_roi_list()
            self.refresh_canvas()
            
    def show_help(self):
        """Show help dialog. Logic unchanged."""
        help_text = """
Kısayollar ve Kullanım:
• Seçim: Tıklama, Liste
• Düzenleme: Çift Tıklama (Liste), Delete (Sil)
• Hareket: Yön Tuşları, Shift+Yön Tuşları
• Boyutlandırma: Alt + Yön Tuşları
• Geri Al: Sağ Tık
"""
        messagebox.showinfo("Yardım", help_text)

    def on_key_press(self, event):
        """Handle keyboard shortcuts. Logic unchanged."""
        if self.selected_roi_index is None:
            return
        if not self.pages:
            return
        
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
            if key == "Left":
                roi['w'] = max(5, roi['w'] - 1)
            elif key == "Right":
                roi['w'] += 1
            elif key == "Up":
                roi['h'] = max(5, roi['h'] - 1)
            elif key == "Down":
                roi['h'] += 1
        else:
            if key == "Left":
                roi['x'] -= step
            elif key == "Right":
                roi['x'] += step
            elif key == "Up":
                roi['y'] -= step
            elif key == "Down":
                roi['y'] += step
            
        self.refresh_canvas()
