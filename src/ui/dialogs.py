
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk

from src.core import omr_engine

class RegionPropertiesDialog(tk.Toplevel):
    def __init__(self, parent, default_label="", default_subscale="General", default_value=""):
        super().__init__(parent)
        self.title("Region Properties")
        window_width = 300
        window_height = 250
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.result = None
        
        # make modal
        self.transient(parent)
        self.grab_set()
        
        # layout
        pad = 10
        
        tk.Label(self, text="Etiket (Örn: S1-A):").pack(anchor=tk.W, padx=pad, pady=(pad, 0))
        self.ent_label = tk.Entry(self)
        self.ent_label.insert(0, default_label)
        self.ent_label.pack(fill=tk.X, padx=pad, pady=(0, pad))
        
        tk.Label(self, text="Değer/Puan (Örn: 1, 5, A):").pack(anchor=tk.W, padx=pad)
        self.ent_value = tk.Entry(self)
        self.ent_value.insert(0, default_value)
        self.ent_value.pack(fill=tk.X, padx=pad, pady=(0, pad))
        self.ent_value.focus_set() # focus on value since it's most common
        
        tk.Label(self, text="Alt Ölçek (Örn: Depresyon):").pack(anchor=tk.W, padx=pad)
        self.ent_subscale = tk.Entry(self)
        self.ent_subscale.insert(0, default_subscale)
        self.ent_subscale.pack(fill=tk.X, padx=pad, pady=(0, pad))
        
        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=pad, pady=pad)
        
        tk.Button(btn_frame, text="OK", command=self.on_ok, width=10, bg="#dddddd").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.destroy, width=10).pack(side=tk.LEFT, padx=5)
        
        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.wait_window(self)

    def on_ok(self):
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

class GridDialog(tk.Toplevel):
    def __init__(self, parent, default_label="Q1"):
        super().__init__(parent)
        self.title("Grid Oluştur")
        window_width = 300
        window_height = 250
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.result = None
        
        self.transient(parent)
        self.grab_set()
        
        pad = 10
        
        tk.Label(self, text="Satır Sayısı:").pack(anchor=tk.W, padx=pad, pady=(pad, 0))
        self.ent_rows = tk.Entry(self)
        self.ent_rows.insert(0, "1")
        self.ent_rows.pack(fill=tk.X, padx=pad)
        
        tk.Label(self, text="Sütun Sayısı:").pack(anchor=tk.W, padx=pad)
        self.ent_cols = tk.Entry(self)
        self.ent_cols.insert(0, "5")
        self.ent_cols.pack(fill=tk.X, padx=pad)
        
        tk.Label(self, text="Başlangıç Etiketi (Örn: S1):").pack(anchor=tk.W, padx=pad)
        self.ent_label = tk.Entry(self)
        self.ent_label.insert(0, default_label)
        self.ent_label.pack(fill=tk.X, padx=pad)
        
        tk.Label(self, text="Alt Ölçek:").pack(anchor=tk.W, padx=pad)
        self.ent_subscale = tk.Entry(self)
        self.ent_subscale.insert(0, "Genel")
        self.ent_subscale.pack(fill=tk.X, padx=pad)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=pad, pady=pad)
        
        tk.Button(btn_frame, text="Oluştur", command=self.on_ok, width=10, bg="#dddddd").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="İptal", command=self.destroy, width=10).pack(side=tk.LEFT, padx=5)
        
        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.wait_window(self)

    def on_ok(self):
        try:
            rows = int(self.ent_rows.get())
            cols = int(self.ent_cols.get())
            lbl = self.ent_label.get().strip()
            sub = self.ent_subscale.get().strip()
            
            if rows < 1 or cols < 1:
                raise ValueError
                
            self.result = {"rows": rows, "cols": cols, "label": lbl, "subscale": sub}
            self.destroy()
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")

class AboutDialog(tk.Toplevel):
    def __init__(self, parent, fonts=None):
        super().__init__(parent)
        self.title("Hakkında")
        self.fonts = fonts if fonts else {}
        
        # window config - frameless minimal design
        self.overrideredirect(True)  # remove window decorations
        self.configure(bg="#212121")  # deep charcoal grey
        
        # Fixed size
        window_width = 600
        window_height = 500
        
        # Center on screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # make modal and always on top
        self.transient(parent)
        self.attributes('-topmost', True)  # always on top
        
        # Force window to update and become visible
        self.update_idletasks()
        
        # Bring to front
        self.lift()
        self.focus_force()
        
        # Now grab focus
        self.grab_set()
        
        # track if we should close
        self.should_close = False
        
        # click anywhere to close - but not immediately
        def delayed_close(event):
            self.should_close = True
            self.destroy()
        
        self.bind("<Button-1>", delayed_close)
        
        # Main container with generous padding
        container = tk.Frame(self, bg="#212121")
        container.pack(fill=tk.BOTH, expand=True, padx=60, pady=60)
        
        # Resolve fonts
        header_font = self.fonts.get("header", ("Arial", 32, "bold"))
        mono_font = self.fonts.get("mono", ("Courier", 9))
        label_font = self.fonts.get("label", ("Arial", 10, "bold"))
        name_font = self.fonts.get("name", ("Arial", 18, "normal"))
        title_font = self.fonts.get("title", ("Arial", 12, "normal"))
        quote_font = self.fonts.get("quote", ("Times New Roman", 11, "italic"))
        engine_font = self.fonts.get("engine", ("Courier", 8))
        
        # === block a: identity (the header) ===
        header_frame = tk.Frame(container, bg="#212121")
        header_frame.pack(pady=(0, 20))
        
        # Application Name
        lbl_name = tk.Label(
            header_frame,
            text="GÖRÜNGÜ",
            font=header_font,
            bg="#212121",
            fg="#FFFFFF"
        )
        lbl_name.pack()
        lbl_name.bind("<Button-1>", delayed_close)
        
        # Version
        lbl_version = tk.Label(
            header_frame,
            text="v1.0.0 (Beta)",
            font=mono_font,
            bg="#212121",
            fg="#B0B0B0"
        )
        lbl_version.pack(pady=(5, 15))
        lbl_version.bind("<Button-1>", delayed_close)
        
        # Decorative line (60% width)
        line_frame = tk.Frame(header_frame, bg="#B0B0B0", height=1)
        line_frame.pack(fill=tk.X, padx=80)
        line_frame.bind("<Button-1>", delayed_close)
        
        # === block b: signature (the creator) ===
        creator_frame = tk.Frame(container, bg="#212121")
        creator_frame.pack(pady=(30, 0))
        
        # Label "GELİŞTİRİCİ"
        lbl_dev_label = tk.Label(
            creator_frame,
            text="GELİŞTİRİCİ",
            font=label_font,
            bg="#212121",
            fg="#C5A572"  # antique gold
        )
        lbl_dev_label.pack()
        lbl_dev_label.bind("<Button-1>", delayed_close)
        
        # Developer Name
        lbl_dev_name = tk.Label(
            creator_frame,
            text="Dr. Furkan BEKDEMİR",
            font=name_font,
            bg="#212121",
            fg="#FFFFFF"
        )
        lbl_dev_name.pack(pady=(8, 0))
        lbl_dev_name.bind("<Button-1>", delayed_close)
        
        # Title
        lbl_dev_title = tk.Label(
            creator_frame,
            text="Psikiyatri Asistanı",
            font=title_font,
            bg="#212121",
            fg="#B0B0B0"
        )
        lbl_dev_title.pack(pady=(5, 0))
        lbl_dev_title.bind("<Button-1>", delayed_close)
        
        # === block c: soul (the philosophy) ===
        philosophy_frame = tk.Frame(container, bg="#212121")
        philosophy_frame.pack(pady=(40, 0))
        
        # quote - serif font for philosophical touch
        lbl_quote = tk.Label(
            philosophy_frame,
            text='"to achieve great things, two things are needed:\na plan, and not quite enough time."',
            font=quote_font,
            bg="#212121",
            fg="#B0B0B0",
            justify=tk.CENTER,
            wraplength=400
        )
        lbl_quote.pack()
        lbl_quote.bind("<Button-1>", delayed_close)
        
        # === block d: engine (the footer) ===
        footer_frame = tk.Frame(container, bg="#212121")
        footer_frame.pack(side=tk.BOTTOM, pady=(0, 0))
        
        # powered by text - barely visible
        lbl_engine = tk.Label(
            footer_frame,
            text="Powered by Thoth Engine",
            font=engine_font,
            bg="#212121",
            fg="#4A4A4A"  # very dark grey, almost invisible
        )
        lbl_engine.pack()
        lbl_engine.bind("<Button-1>", delayed_close)
        
        # bind container click as well
        container.bind("<Button-1>", delayed_close)
        
        # subtle border to define the window edge
        self.configure(highlightbackground="#4A4A4A", highlightthickness=1)
        
        # esc key to close
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.wait_window(self)

class CornerCorrectionDialog(tk.Toplevel):
    def __init__(self, parent, cv_image, initial_corners=None):
        super().__init__(parent)
        self.title("Köşe Düzeltme")
        window_width = 1000
        window_height = 800
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.cv_image = cv_image.copy()
        self.result_image = None
        
        self.transient(parent)
        self.grab_set()
        
        # ui layout
        btn_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        tk.Button(btn_frame, text="Otomatik Bul", command=self.run_auto_detect, width=15).pack(side=tk.LEFT, padx=20)
        tk.Button(btn_frame, text="Uygula ve Kırp", command=self.apply_warp, width=15, bg="#4caf50", fg="white").pack(side=tk.RIGHT, padx=20)
        tk.Button(btn_frame, text="İptal", command=self.destroy, width=15).pack(side=tk.RIGHT, padx=20)
        
        self.canvas = tk.Canvas(self, bg="#333333")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # state
        self.corners = initial_corners if initial_corners else [] 
        self.current_handle = None
        self.scale = 1.0
        
        # initial display
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
        h, w = self.cv_image.shape[:2]
        canvas_h = 700
        canvas_w = 980
        
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
        self.canvas.delete("handle")
        self.canvas.delete("line")
        
        if len(self.corners) != 4: return
        
        # lines
        pts = []
        for pt in self.corners:
            pts.append(pt[0] * self.scale)
            pts.append(pt[1] * self.scale)
        
        # close loop
        pts.append(self.corners[0][0] * self.scale)
        pts.append(self.corners[0][1] * self.scale)
        
        self.canvas.create_line(pts, fill="#00ff00", width=2, tags="line")
        
        # draw handles
        r = 8
        for idx, pt in enumerate(self.corners):
            x = pt[0] * self.scale
            y = pt[1] * self.scale
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="red", outline="white", width=2, tags=("handle", f"h_{idx}"))
            self.canvas.create_text(x, y-20, text=str(idx+1), fill="yellow", font=("Arial", 12, "bold"), tags="handle")

    def run_auto_detect(self):
        found, corners = omr_engine.detect_corners(self.cv_image)
        self.corners = corners
        self.sort_corners_ui()
        self.draw_handles()

    def sort_corners_ui(self):
         # use engine's sort but we need it in list format for UI state
        rect = omr_engine.sort_corners(self.corners)
        self.corners = rect.tolist()

    def on_mouse_down(self, event):
        x = event.x
        y = event.y
        
        # find closest handle
        best_dist = 20 # Threshold
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
        if self.current_handle is not None:
            # update corner position
            # canvas to image
            img_x = event.x / self.scale
            img_y = event.y / self.scale
            
            # clamp
            h, w = self.cv_image.shape[:2]
            img_x = max(0, min(w, img_x))
            img_y = max(0, min(h, img_y))
            
            self.corners[self.current_handle] = [img_x, img_y]
            self.draw_handles()

    def on_mouse_up(self, event):
        self.current_handle = None

    def apply_warp(self):
        # use engine warp
        self.result_image = omr_engine.get_four_point_transform(self.cv_image, self.corners)
        self.destroy()
