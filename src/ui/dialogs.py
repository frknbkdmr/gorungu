"""
Dialogs Module - Modern CTk-based dialogs for GÖRÜNGÜ

All dialogs modernized with customtkinter while preserving functional logic.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk

from src.core import omr_engine
from src.ui.styles import Style


class RegionPropertiesDialog(ctk.CTkToplevel):
    """Dialog for editing ROI properties."""
    
    def __init__(self, parent, default_label="", default_subscale="General", default_value=""):
        super().__init__(parent)
        self.title("Bölge Özellikleri")
        
        colors = Style.get_theme_colors()
        
        # Window setup
        window_width = 360
        window_height = 380
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.configure(fg_color=colors["bg_primary"])
        
        self.result = None
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=Style.PADDING_LG, pady=Style.PADDING_LG)
        
        # Header
        ctk.CTkLabel(
            content,
            text="📝 Bölge Özellikleri",
            font=Style.FONTS["header_md"],
            text_color=colors["text_primary"]
        ).pack(anchor="w", pady=(0, Style.PADDING_LG))
        
        # Label field
        ctk.CTkLabel(
            content,
            text="Etiket (Örn: S1-A):",
            font=Style.FONTS["small_bold"],
            text_color=colors["text_secondary"]
        ).pack(anchor="w")
        
        self.ent_label = ctk.CTkEntry(
            content,
            font=Style.FONTS["body"],
            fg_color=colors["input_bg"],
            border_color=colors["border"],
            text_color=colors["text_primary"],
            height=Style.INPUT_HEIGHT
        )
        self.ent_label.insert(0, default_label)
        self.ent_label.pack(fill="x", pady=(Style.PADDING_XS, Style.PADDING_MD))
        
        # Value field
        ctk.CTkLabel(
            content,
            text="Değer/Puan (Örn: 1, 5, A):",
            font=Style.FONTS["small_bold"],
            text_color=colors["text_secondary"]
        ).pack(anchor="w")
        
        self.ent_value = ctk.CTkEntry(
            content,
            font=Style.FONTS["body"],
            fg_color=colors["input_bg"],
            border_color=colors["border"],
            text_color=colors["text_primary"],
            height=Style.INPUT_HEIGHT
        )
        self.ent_value.insert(0, default_value)
        self.ent_value.pack(fill="x", pady=(Style.PADDING_XS, Style.PADDING_MD))
        self.ent_value.focus_set()
        
        # Subscale field
        ctk.CTkLabel(
            content,
            text="Alt Ölçek (Örn: Depresyon):",
            font=Style.FONTS["small_bold"],
            text_color=colors["text_secondary"]
        ).pack(anchor="w")
        
        self.ent_subscale = ctk.CTkEntry(
            content,
            font=Style.FONTS["body"],
            fg_color=colors["input_bg"],
            border_color=colors["border"],
            text_color=colors["text_primary"],
            height=Style.INPUT_HEIGHT
        )
        self.ent_subscale.insert(0, default_subscale)
        self.ent_subscale.pack(fill="x", pady=(Style.PADDING_XS, Style.PADDING_MD))
        
        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(Style.PADDING_MD, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="✓ Tamam",
            command=self.on_ok,
            font=Style.FONTS["button"],
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            height=Style.BUTTON_HEIGHT,
            width=100
        ).pack(side="left", padx=(0, Style.PADDING_SM))
        
        ctk.CTkButton(
            btn_frame,
            text="İptal",
            command=self.destroy,
            font=Style.FONTS["button"],
            fg_color=colors["bg_tertiary"],
            hover_color=colors["border"],
            text_color=colors["text_primary"],
            height=Style.BUTTON_HEIGHT,
            width=100
        ).pack(side="left")
        
        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.wait_window(self)

    def on_ok(self):
        """Handle OK button click. Logic unchanged."""
        val = self.ent_value.get().strip()
        lbl = self.ent_label.get().strip()
        sub = self.ent_subscale.get().strip()
        
        if not val:
            messagebox.showwarning("Eksik Giriş", "Lütfen bir değer giriniz.", parent=self)
            return
        if not lbl:
            lbl = "Madde"
        if not sub:
            sub = "Genel"
            
        self.result = {"value": val, "label": lbl, "subscale": sub}
        self.destroy()


class GridDialog(ctk.CTkToplevel):
    """Dialog for creating grid of ROIs."""
    
    def __init__(self, parent, default_label="Q1", default_rows=1, default_cols=5):
        super().__init__(parent)
        self.title("Grid Oluştur")
        
        self.default_rows = default_rows
        self.default_cols = default_cols
        
        colors = Style.get_theme_colors()
        
        # Window setup
        window_width = 360
        window_height = 510
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.configure(fg_color=colors["bg_primary"])
        
        self.result = None
        
        self.transient(parent)
        self.grab_set()
        
        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=Style.PADDING_LG, pady=Style.PADDING_LG)
        
        # Header
        ctk.CTkLabel(
            content,
            text="⊞ Grid Oluştur",
            font=Style.FONTS["header_md"],
            text_color=colors["text_primary"]
        ).pack(anchor="w", pady=(0, Style.PADDING_LG))
        
        # Rows field
        ctk.CTkLabel(
            content,
            text="Satır Sayısı:",
            font=Style.FONTS["small_bold"],
            text_color=colors["text_secondary"]
        ).pack(anchor="w")
        
        self.ent_rows = ctk.CTkEntry(
            content,
            font=Style.FONTS["body"],
            fg_color=colors["input_bg"],
            border_color=colors["border"],
            text_color=colors["text_primary"],
            height=Style.INPUT_HEIGHT
        )
        self.ent_rows.insert(0, str(self.default_rows))
        self.ent_rows.pack(fill="x", pady=(Style.PADDING_XS, Style.PADDING_SM))
        
        # Columns field
        ctk.CTkLabel(
            content,
            text="Sütun Sayısı:",
            font=Style.FONTS["small_bold"],
            text_color=colors["text_secondary"]
        ).pack(anchor="w")
        
        self.ent_cols = ctk.CTkEntry(
            content,
            font=Style.FONTS["body"],
            fg_color=colors["input_bg"],
            border_color=colors["border"],
            text_color=colors["text_primary"],
            height=Style.INPUT_HEIGHT
        )
        self.ent_cols.insert(0, str(self.default_cols))
        self.ent_cols.pack(fill="x", pady=(Style.PADDING_XS, Style.PADDING_SM))
        
        # Label field
        ctk.CTkLabel(
            content,
            text="Başlangıç Etiketi (Örn: S1):",
            font=Style.FONTS["small_bold"],
            text_color=colors["text_secondary"]
        ).pack(anchor="w")
        
        self.ent_label = ctk.CTkEntry(
            content,
            font=Style.FONTS["body"],
            fg_color=colors["input_bg"],
            border_color=colors["border"],
            text_color=colors["text_primary"],
            height=Style.INPUT_HEIGHT
        )
        self.ent_label.insert(0, default_label)
        self.ent_label.pack(fill="x", pady=(Style.PADDING_XS, Style.PADDING_SM))
        
        # Subscale field
        ctk.CTkLabel(
            content,
            text="Alt Ölçek:",
            font=Style.FONTS["small_bold"],
            text_color=colors["text_secondary"]
        ).pack(anchor="w")
        
        self.ent_subscale = ctk.CTkEntry(
            content,
            font=Style.FONTS["body"],
            fg_color=colors["input_bg"],
            border_color=colors["border"],
            text_color=colors["text_primary"],
            height=Style.INPUT_HEIGHT
        )
        self.ent_subscale.insert(0, "Genel")
        self.ent_subscale.pack(fill="x", pady=(Style.PADDING_XS, Style.PADDING_MD))
        
        # Margin field
        ctk.CTkLabel(
            content,
            text="Kenar Payı / Taşırma (Margin px):",
            font=Style.FONTS["small_bold"],
            text_color=colors["text_secondary"]
        ).pack(anchor="w")
        
        self.ent_margin = ctk.CTkEntry(
            content,
            font=Style.FONTS["body"],
            fg_color=colors["input_bg"],
            border_color=colors["border"],
            text_color=colors["text_primary"],
            height=Style.INPUT_HEIGHT
        )
        self.ent_margin.insert(0, "4")
        self.ent_margin.pack(fill="x", pady=(Style.PADDING_XS, Style.PADDING_MD))
        
        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(Style.PADDING_MD, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="✓ Oluştur",
            command=self.on_ok,
            font=Style.FONTS["button"],
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            height=Style.BUTTON_HEIGHT,
            width=100
        ).pack(side="left", padx=(0, Style.PADDING_SM))
        
        ctk.CTkButton(
            btn_frame,
            text="İptal",
            command=self.destroy,
            font=Style.FONTS["button"],
            fg_color=colors["bg_tertiary"],
            hover_color=colors["border"],
            text_color=colors["text_primary"],
            height=Style.BUTTON_HEIGHT,
            width=100
        ).pack(side="left")
        
        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.wait_window(self)

    def on_ok(self):
        """Handle OK button click."""
        try:
            rows = int(self.ent_rows.get())
            cols = int(self.ent_cols.get())
            lbl = self.ent_label.get().strip()
            sub = self.ent_subscale.get().strip()
            
            margin_str = self.ent_margin.get().strip()
            margin = int(margin_str) if margin_str else 0
            
            if rows < 1 or cols < 1:
                raise ValueError
                
            self.result = {"rows": rows, "cols": cols, "label": lbl, "subscale": sub, "margin": margin}
            self.destroy()
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")



class AboutDialog(ctk.CTkToplevel):
    """Modern About dialog with click-to-close."""
    
    def __init__(self, parent, fonts=None):
        super().__init__(parent)
        self.title("Hakkında")
        self.fonts = fonts if fonts else {}
        
        # Frameless design
        self.overrideredirect(True)
        self.configure(fg_color="#1a1a2e")  # Dark background
        
        # Window setup
        window_width = 600
        window_height = 520
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.transient(parent)
        self.attributes('-topmost', True)
        self.update_idletasks()
        self.lift()
        self.focus_force()
        self.grab_set()
        
        # Click anywhere to close
        def close_on_click(event):
            self.destroy()
        
        self.bind("<Button-1>", close_on_click)
        self.bind("<Escape>", lambda e: self.destroy())
        
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=60, pady=60)
        container.bind("<Button-1>", close_on_click)
        
        # === Header Block ===
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(pady=(0, 20))
        header_frame.bind("<Button-1>", close_on_click)
        
        lbl_name = ctk.CTkLabel(
            header_frame,
            text="GÖRÜNGÜ",
            font=("Courier New", 36, "bold"),
            text_color="#ffffff"
        )
        lbl_name.pack()
        lbl_name.bind("<Button-1>", close_on_click)
        
        lbl_version = ctk.CTkLabel(
            header_frame,
            text="v1.0.0 (Beta)",
            font=Style.FONTS["mono"],
            text_color="#a0a0a0"
        )
        lbl_version.pack(pady=(8, 15))
        lbl_version.bind("<Button-1>", close_on_click)
        
        # Decorative line
        line = ctk.CTkFrame(header_frame, height=1, fg_color="#3d3d5c", corner_radius=0)
        line.pack(fill="x", padx=80)
        line.bind("<Button-1>", close_on_click)
        
        # === Creator Block ===
        creator_frame = ctk.CTkFrame(container, fg_color="transparent")
        creator_frame.pack(pady=(30, 0))
        creator_frame.bind("<Button-1>", close_on_click)
        
        lbl_dev_label = ctk.CTkLabel(
            creator_frame,
            text="GELİŞTİRİCİ",
            font=Style.FONTS["small_bold"],
            text_color="#c5a572"  # Antique gold
        )
        lbl_dev_label.pack()
        lbl_dev_label.bind("<Button-1>", close_on_click)
        
        lbl_dev_name = ctk.CTkLabel(
            creator_frame,
            text="Dr. Furkan BEKDEMİR",
            font=("Segoe UI", 20, "normal"),
            text_color="#ffffff"
        )
        lbl_dev_name.pack(pady=(8, 0))
        lbl_dev_name.bind("<Button-1>", close_on_click)
        
        lbl_dev_title = ctk.CTkLabel(
            creator_frame,
            text="Psikiyatri Asistanı",
            font=Style.FONTS["body"],
            text_color="#a0a0a0"
        )
        lbl_dev_title.pack(pady=(5, 0))
        lbl_dev_title.bind("<Button-1>", close_on_click)
        
        # === Philosophy Block ===
        philosophy_frame = ctk.CTkFrame(container, fg_color="transparent")
        philosophy_frame.pack(pady=(40, 0))
        philosophy_frame.bind("<Button-1>", close_on_click)
        
        lbl_quote = ctk.CTkLabel(
            philosophy_frame,
            text='"to achieve great things, two things are needed:\na plan, and not quite enough time."',
            font=("Georgia", 12, "italic"),
            text_color="#808080",
            justify="center"
        )
        lbl_quote.pack()
        lbl_quote.bind("<Button-1>", close_on_click)
        
        # === Footer Block ===
        footer_frame = ctk.CTkFrame(container, fg_color="transparent")
        footer_frame.pack(side="bottom")
        footer_frame.bind("<Button-1>", close_on_click)
        
        lbl_engine = ctk.CTkLabel(
            footer_frame,
            text="Powered by Thoth Engine",
            font=("Courier New", 9),
            text_color="#4a4a6a"
        )
        lbl_engine.pack()
        lbl_engine.bind("<Button-1>", close_on_click)
        
        # Hint text
        lbl_hint = ctk.CTkLabel(
            footer_frame,
            text="Kapatmak için herhangi bir yere tıklayın",
            font=Style.FONTS["small"],
            text_color="#3d3d5c"
        )
        lbl_hint.pack(pady=(15, 0))
        lbl_hint.bind("<Button-1>", close_on_click)
        
        self.wait_window(self)


class CornerCorrectionDialog(ctk.CTkToplevel):
    """Dialog for manual corner correction with draggable handles."""
    
    def __init__(self, parent, cv_image, initial_corners=None):
        super().__init__(parent)
        self.title("Köşe Düzeltme")
        
        colors = Style.get_theme_colors()
        
        # Window setup
        window_width = 1050
        window_height = 850
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.configure(fg_color=colors["bg_primary"])
        
        self.cv_image = cv_image.copy()
        self.result_image = None
        
        self.transient(parent)
        self.grab_set()
        
        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=colors["bg_secondary"], corner_radius=0)
        toolbar.pack(side="top", fill="x")
        
        toolbar_content = ctk.CTkFrame(toolbar, fg_color="transparent")
        toolbar_content.pack(fill="both", expand=True, padx=Style.PADDING_LG, pady=Style.PADDING_SM)
        
        ctk.CTkLabel(
            toolbar_content,
            text="📐 Köşe Düzeltme",
            font=Style.FONTS["header_md"],
            text_color=colors["text_primary"]
        ).pack(side="left")
        
        # Buttons on right
        ctk.CTkButton(
            toolbar_content,
            text="İptal",
            command=self.destroy,
            font=Style.FONTS["button"],
            fg_color=colors["bg_tertiary"],
            hover_color=colors["border"],
            text_color=colors["text_primary"],
            height=Style.BUTTON_HEIGHT,
            width=100
        ).pack(side="right", padx=(Style.PADDING_SM, 0))
        
        ctk.CTkButton(
            toolbar_content,
            text="✓ Uygula ve Kırp",
            command=self.apply_warp,
            font=Style.FONTS["button"],
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            height=Style.BUTTON_HEIGHT,
            width=140
        ).pack(side="right", padx=(Style.PADDING_SM, 0))
        
        ctk.CTkButton(
            toolbar_content,
            text="🔍 Otomatik Bul",
            command=self.run_auto_detect,
            font=Style.FONTS["button"],
            fg_color=colors["bg_tertiary"],
            hover_color=colors["border"],
            text_color=colors["text_primary"],
            height=Style.BUTTON_HEIGHT,
            width=120
        ).pack(side="right")
        
        # Canvas
        self.canvas = tk.Canvas(self, bg=colors["canvas"], bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # State
        self.corners = initial_corners if initial_corners else []
        self.current_handle = None
        self.scale = 1.0
        
        # Initial display
        self.display_image()
        if not self.corners:
            self.run_auto_detect()
        else:
            self.draw_handles()
        
        # Bindings
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        self.wait_window(self)

    def display_image(self):
        """Display the image on canvas. Logic unchanged."""
        h, w = self.cv_image.shape[:2]
        canvas_h = 750
        canvas_w = 1020
        
        scale_w = canvas_w / w
        scale_h = canvas_h / h
        self.scale = min(scale_w, scale_h, 1.0)
        
        new_w = int(w * self.scale)
        new_h = int(h * self.scale)
        
        resized = cv2.resize(self.cv_image, (new_w, new_h))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        self.tk_img = ImageTk.PhotoImage(Image.fromarray(rgb))
        
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        self.draw_handles()

    def draw_handles(self):
        """Draw corner handles. Logic unchanged."""
        self.canvas.delete("handle")
        self.canvas.delete("line")
        
        if len(self.corners) != 4:
            return
        
        # Lines
        pts = []
        for pt in self.corners:
            pts.append(pt[0] * self.scale)
            pts.append(pt[1] * self.scale)
        
        # Close loop
        pts.append(self.corners[0][0] * self.scale)
        pts.append(self.corners[0][1] * self.scale)
        
        self.canvas.create_line(pts, fill="#22c55e", width=2, tags="line")
        
        # Draw handles
        r = 10
        colors = ["#e94560", "#3b82f6", "#22c55e", "#f59e0b"]  # Different colors for each corner
        for idx, pt in enumerate(self.corners):
            x = pt[0] * self.scale
            y = pt[1] * self.scale
            self.canvas.create_oval(
                x-r, y-r, x+r, y+r, 
                fill=colors[idx], 
                outline="white", 
                width=2, 
                tags=("handle", f"h_{idx}")
            )
            self.canvas.create_text(
                x, y-18, 
                text=str(idx+1), 
                fill="white", 
                font=Style.FONTS["body_bold"], 
                tags="handle"
            )

    def run_auto_detect(self):
        """Run auto corner detection. Logic unchanged."""
        found, corners = omr_engine.detect_corners(self.cv_image)
        self.corners = corners
        self.sort_corners_ui()
        self.draw_handles()

    def sort_corners_ui(self):
        """Sort corners for proper ordering. Logic unchanged."""
        rect = omr_engine.sort_corners(self.corners)
        self.corners = rect.tolist()

    def on_mouse_down(self, event):
        """Handle mouse down. Logic unchanged."""
        x = event.x
        y = event.y
        
        # Find closest handle
        best_dist = 25  # Threshold
        best_idx = -1
        
        for idx, pt in enumerate(self.corners):
            px = pt[0] * self.scale
            py = pt[1] * self.scale
            dist = np.sqrt((x - px)**2 + (y - py)**2)
            if dist < best_dist:
                best_dist = dist
                best_idx = idx
        
        if best_idx != -1:
            self.current_handle = best_idx

    def on_mouse_drag(self, event):
        """Handle mouse drag. Logic unchanged."""
        if self.current_handle is not None:
            img_x = event.x / self.scale
            img_y = event.y / self.scale
            
            # Clamp
            h, w = self.cv_image.shape[:2]
            img_x = max(0, min(w, img_x))
            img_y = max(0, min(h, img_y))
            
            self.corners[self.current_handle] = [img_x, img_y]
            self.draw_handles()

    def on_mouse_up(self, event):
        """Handle mouse up. Logic unchanged."""
        self.current_handle = None

    def apply_warp(self):
        """Apply perspective transform. Logic unchanged."""
        self.result_image = omr_engine.get_four_point_transform(self.cv_image, self.corners)
        self.destroy()
