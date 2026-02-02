import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import cv2
import numpy as np
import json
import os
from PIL import Image, ImageTk
import tkinter.ttk as ttk
import io
import csv

# try importing pymupdf for pdf support
try:
    import fitz  # pymupdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("pymupdf (fitz) not found. pdf support disabled. install with: pip install pymupdf")

class RegionPropertiesDialog(tk.Toplevel):
    def __init__(self, parent, default_label="", default_subscale="General", default_value=""):
        super().__init__(parent)
        self.title("Region Properties")
        self.geometry("300x250")
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
        self.geometry("300x250")
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
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Hakkında")
        
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
        
        # font fallbacks for compatibility
        try:
            # try preferred fonts, else system defaults
            header_font = ("Montserrat", 32, "bold")
            mono_font = ("Courier New", 9)
            label_font = ("Roboto", 10, "bold")
            name_font = ("Roboto", 18, "normal")
            title_font = ("Roboto", 12, "normal")
            quote_font = ("Georgia", 11, "italic")
            engine_font = ("Courier New", 8)
        except:
        # fallback to safe defaults
            header_font = ("Arial", 32, "bold")
            mono_font = ("Courier", 9)
            label_font = ("Arial", 10, "bold")
            name_font = ("Arial", 18, "normal")
            title_font = ("Arial", 12, "normal")
            quote_font = ("Times New Roman", 11, "italic")
            engine_font = ("Courier", 8)
        
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
        
        # wait for window to close (modal behavior)
        self.wait_window(self)

class OMRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GÖRÜNGÜ - Powered by Thoth Engine")
        self.root.geometry("1280x850")
        
        # init state variables
        self.current_mode = None
        self.pages = [] 
        self.current_page_index = 0
        self.template_pages = []
        self.input_images = []
        self.current_input_index = 0
        self.session_results = {}
        self.session_subscales = {}
        self.canvas = None
        self.rect_start_x = None
        self.rect_start_y = None
        self.current_rect = None
        self.tk_image = None 
        self.image_scale = 1.0
        self.txt_results = None 
        
        # roi selection state
        self.selected_roi_index = None
        
        # grid mode state
        self.grid_mode_var = tk.BooleanVar(value=False)
        
        # theme config
        self.themes = {
            "light": {
                "bg": "#f4f6f9",        # Light gray background
                "panel_bg": "#ffffff",  # White panels
                "accent": "#3b82f6",    # Blue accent
                "text": "#1f2937",      # Dark text
                "success": "#10b981",   # Green
                "error": "#ef4444",     # Red
                "canvas": "#e5e7eb",    # Canvas bg
                "input_bg": "#ffffff",  # Entry/Text bg
                "input_fg": "#1f2937"   # Entry/Text fg
            },
            "dark": {
                "bg": "#1f2937",        # Dark gray background
                "panel_bg": "#374151",  # Darker panel
                "accent": "#60a5fa",    # Lighter blue accent
                "text": "#f3f4f6",      # Light text
                "success": "#34d399",   # Light green
                "error": "#f87171",     # Light red
                "canvas": "#4b5563",    # Dark canvas
                "input_bg": "#111827",  # Very dark input bg
                "input_fg": "#f3f4f6"   # Light input fg
            },
            "nile_delta": {
                "bg": "#F5F7FA",        # Clinical Background (Light Gray)
                "panel_bg": "#FFFFFF",  # Clinical White (Panels)
                "accent": "#0D47A1",    # Deep Ocean Blue (Primary)
                "text": "#212121",      # Ink Black (Text)
                "success": "#C5A572",   # Antique Gold (Secondary/Success)
                "error": "#ef4444",     # Error Red
                "canvas": "#E0E0E0",    # Canvas Background
                "input_bg": "#FFFFFF",  # Input Background
                "input_fg": "#212121"   # Input Text
            }
        }
        self.current_theme_name = "nile_delta"
        self.colors = self.themes[self.current_theme_name]
        
        # style config
        self.style = ttk.Style()
        self.style.theme_use('clam') 
        self.apply_theme()
        
        # main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Hazır")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, font=("Segoe UI", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # menu
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        self.mode_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Mod", menu=self.mode_menu)
        self.mode_menu.add_command(label="Tasarımcı Modu", command=self.setup_designer_mode)
        self.mode_menu.add_command(label="Tarayıcı Modu", command=self.setup_scanner_mode)

        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Görünüm", menu=self.view_menu)
        
        # theme submenu
        self.theme_menu = tk.Menu(self.view_menu, tearoff=0)
        self.view_menu.add_cascade(label="Tema", menu=self.theme_menu)
        
        for theme_name in self.themes.keys():
            # Capitalize for display (e.g., "light" -> "Light")
            display_name = theme_name.replace("_", " ").title()
            self.theme_menu.add_command(label=display_name, command=lambda t=theme_name: self.set_theme(t))
        
        # Add separator and About option
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Hakkında", command=self.show_about)
        
        # Help Menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Yardım", menu=self.help_menu)
        self.help_menu.add_command(label="Hakkında GÖRÜNGÜ", command=self.show_about)
        
        # init edit mode state
        self.edit_mode = False
        
        # start in designer mode
        self.setup_designer_mode()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def set_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme_name = theme_name
            self.apply_theme()

    def apply_theme(self):
        self.colors = self.themes[self.current_theme_name]
        
        # root
        self.root.configure(bg=self.colors["bg"])
        
        # ttk styles
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("Panel.TFrame", background=self.colors["panel_bg"])
        self.style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"])
        self.style.configure("Panel.TLabel", background=self.colors["panel_bg"], foreground=self.colors["text"])
        self.style.configure("Header.TLabel", background=self.colors["panel_bg"], foreground=self.colors["text"])
        
        self.style.configure("TButton", background=self.colors["panel_bg"], foreground=self.colors["text"])
        self.style.map("TButton", background=[('active', self.colors["accent"])], foreground=[('active', 'white')])
        
        self.style.configure("Accent.TButton", background=self.colors["accent"], foreground="white")
        self.style.map("Accent.TButton", background=[('active', self.colors["text"])]) # Contrast for active state
        
        self.style.configure("TLabelframe", background=self.colors["panel_bg"], foreground=self.colors["text"])
        self.style.configure("TLabelframe.Label", background=self.colors["panel_bg"], foreground=self.colors["text"])
        
        # update specific widgets
        if self.canvas:
            self.canvas.configure(bg=self.colors["canvas"])
            
        if hasattr(self, 'txt_results') and self.txt_results and self.txt_results.winfo_exists():
            self.txt_results.configure(bg=self.colors["input_bg"], fg=self.colors["input_fg"])
            
        # Force refresh of main frame to apply TFrame style
        if hasattr(self, 'main_frame'):
             # force redraw
             self.main_frame.configure(style="TFrame")
    
    def show_about(self):
        """Display the About dialog"""
        print("[ABOUT] Hakkında penceresi açılıyor...")
        AboutDialog(self.root)
        print("[ABOUT] Hakkında penceresi kapatıldı")

    # ==========================================
    # shared utils
    # ==========================================
    def load_images_from_file(self, file_path):
        """Returns a list of cv2 images from a file path (Image or PDF)"""
        print(f"[LOAD] Dosya yükleniyor: {file_path}")
        images = []
        ext = os.path.splitext(file_path)[1].lower()
        print(f"[LOAD] Dosya uzantısı: {ext}")
        
        if ext == '.pdf':
            if not PDF_AVAILABLE:
                print("[ERROR] PDF desteği yok - PyMuPDF bulunamadı")
                messagebox.showerror("Error", "PDF support requires 'pymupdf'. Please run: pip install pymupdf")
                return []
            try:
                print("[LOAD] PDF açılıyor...")
                doc = fitz.open(file_path)
                print(f"[LOAD] PDF sayfa sayısı: {len(doc)}")
                for i, page in enumerate(doc):
                    print(f"[LOAD] PDF sayfa {i+1} işleniyor...")
                    pix = page.get_pixmap(dpi=150) # 150 dpi is good enough
                    img_data = pix.tobytes("png")
                    nparr = np.frombuffer(img_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    images.append(img)
                    print(f"[LOAD] Sayfa {i+1} yüklendi - Boyut: {img.shape}")
                print(f"[LOAD] PDF başarıyla yüklendi - Toplam {len(images)} sayfa")
            except Exception as e:
                print(f"[ERROR] PDF yükleme hatası: {e}")
                messagebox.showerror("Error", f"Failed to load PDF: {e}")
                return []
        else:
            print("[LOAD] Görsel dosya okunuyor...")
            img = cv2.imread(file_path)
            if img is not None:
                images.append(img)
                print(f"[LOAD] Görsel yüklendi - Boyut: {img.shape}")
            else:
                print(f"[ERROR] Görsel okunamadı: {file_path}")
        
        print(f"[LOAD] Toplam {len(images)} görsel yüklendi")
        return images

    # ==========================================
    # DESIGNER MODE
    # ==========================================
    def setup_designer_mode(self):
        self.current_mode = "DESIGNER"
        self.clear_frame()
        self.root.title("GÖRÜNGÜ - Tasarımcı Modu")
        self.status_var.set("Tasarımcı Modu: Başlamak için boş bir form yükleyin.")

        # toolbar
        toolbar = ttk.Frame(self.main_frame, style="Panel.TFrame", padding=10)
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
        
        # grid tool toggle
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


        # Canvas area
        # Main Content Area (Canvas + Side Panel)
        content_area = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        content_area.pack(fill=tk.BOTH, expand=True)
        
        # canvas frame
        self.canvas_frame = ttk.Frame(content_area, style="TFrame")
        content_area.add(self.canvas_frame, weight=3)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg=self.colors["canvas"], bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # roi editor panel
        self.roi_panel = ttk.Frame(content_area, style="Panel.TFrame", padding=5)
        content_area.add(self.roi_panel, weight=1)
        
        ttk.Label(self.roi_panel, text="Bölge Listesi", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        # treeview for rois
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
        
        # treeview bindings
        self.roi_tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.roi_tree.bind("<Double-1>", self.on_roi_list_double_click)
        
        # Zoom & Pan State
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Bindings
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Button-3>", self.undo_last_roi) # Right click to undo
        
        # keyboard bindings
        self.root.bind("<Key>", self.on_key_press)
        
        # zoom/pan bindings
        self.canvas.bind("<MouseWheel>", self.on_zoom) # Windows
        self.canvas.bind("<Button-4>", self.on_zoom)   # Linux Scroll Up
        self.canvas.bind("<Button-5>", self.on_zoom)   # Linux Scroll Down
        self.canvas.bind("<ButtonPress-2>", self.start_pan) # Middle click
        self.canvas.bind("<B2-Motion>", self.do_pan)
        
        # reset
        self.pages = []
        self.current_page_index = 0
        self.refresh_roi_list()

    def refresh_roi_list(self):
        # check if treeview exists (might be destroyed in scanner mode)
        if not hasattr(self, 'roi_tree') or not self.roi_tree.winfo_exists():
            return

        # clear existing items
        for item in self.roi_tree.get_children():
            self.roi_tree.delete(item)
            
        if not self.pages: return
        
        rois = self.pages[self.current_page_index]['rois']
        for i, roi in enumerate(rois):
            # insert into treeview
            # use index as iid to map back
            self.roi_tree.insert("", "end", iid=str(i), values=(roi['label'], roi['value'], roi.get('subscale', 'Genel')))
            
        # restore selection if valid
        if self.selected_roi_index is not None and 0 <= self.selected_roi_index < len(rois):
            self.roi_tree.selection_set(str(self.selected_roi_index))
            self.roi_tree.see(str(self.selected_roi_index))
        else:
            self.selected_roi_index = None

    def on_tree_select(self, event):
        selected_items = self.roi_tree.selection()
        if not selected_items:
            self.selected_roi_index = None
        else:
            self.selected_roi_index = int(selected_items[0])
            
        self.refresh_canvas()

    def on_roi_list_double_click(self, event):
        if self.selected_roi_index is None: return
        if not self.pages: return
        
        rois = self.pages[self.current_page_index]['rois']
        roi = rois[self.selected_roi_index]
        
        # open dialog with current values
        dialog = RegionPropertiesDialog(self.root, roi['label'], roi.get('subscale', 'Genel'), roi['value'])
        
        if dialog.result:
            # update roi
            roi['label'] = dialog.result['label']
            roi['value'] = dialog.result['value']
            roi['subscale'] = dialog.result['subscale']
            
            self.refresh_roi_list()
            self.refresh_canvas()

    def on_key_press(self, event):
        if self.current_mode != "DESIGNER": return
        
        # check if focus is on input widget or treeview
        focused_widget = self.root.focus_get()
        if isinstance(focused_widget, (tk.Entry, tk.Text, ttk.Entry)):
            return
            
        # special handling for treeview
        if isinstance(focused_widget, ttk.Treeview):
            if event.keysym == "Delete":
                # allow delete
                pass
            else:
                # ignore other shortcuts
                return
            
        if self.selected_roi_index is None: return
        if not self.pages: return
        
        rois = self.pages[self.current_page_index]['rois']
        roi = rois[self.selected_roi_index]
        
        key = event.keysym
        
        # movement step
        step = 10 if (event.state & 0x0001) else 1 # shift check (approx)
        # resize mode (alt key)
        # check for alt key state
        is_alt = (event.state & 0x20000) or (event.state & 131072)
        
        if key == "Delete":
            rois.pop(self.selected_roi_index)
            self.selected_roi_index = None
            self.refresh_roi_list()
            self.refresh_canvas()
            return
            
        if is_alt:
            # resize
            if key == "Left": roi['w'] = max(5, roi['w'] - 1)
            elif key == "Right": roi['w'] += 1
            elif key == "Up": roi['h'] = max(5, roi['h'] - 1)
            elif key == "Down": roi['h'] += 1
        else:
            # move
            if key == "Left": roi['x'] -= step
            elif key == "Right": roi['x'] += step
            elif key == "Up": roi['y'] -= step
            elif key == "Down": roi['y'] += step
            
        self.refresh_canvas()
    def to_canvas_coords(self, img_x, img_y):
        """convert image coords to canvas coords"""
        # (image coord * scale * zoom) + pan
        x = (img_x * self.image_scale * self.zoom_scale) + self.pan_x
        y = (img_y * self.image_scale * self.zoom_scale) + self.pan_y
        return x, y

    def to_image_coords(self, canvas_x, canvas_y):
        """convert canvas coords to image coords"""
        # (canvas coord - pan) / (scale * zoom)
        x = (canvas_x - self.pan_x) / (self.image_scale * self.zoom_scale)
        y = (canvas_y - self.pan_y) / (self.image_scale * self.zoom_scale)
        return int(x), int(y)

    # ==========================================
    # zoom & pan handlers
    # ==========================================
    def on_zoom(self, event):
        if not self.tk_image: return
        
        # determine zoom direction
        if event.num == 5 or event.delta < 0:
            factor = 0.9
        else:
            factor = 1.1
            
        # limit zoom
        new_zoom = self.zoom_scale * factor
        if new_zoom < 0.1 or new_zoom > 10.0:
            return
            
        # zoom centered on mouse
        # mouse pos in canvas coords
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)
        
        # mouse pos relative to image (before zoom)
        rel_x = (mouse_x - self.pan_x) / self.zoom_scale
        rel_y = (mouse_y - self.pan_y) / self.zoom_scale
        
        # update zoom
        self.zoom_scale = new_zoom
        
        # adjust pan to keep mouse point stable
        # new_mouse_x = (rel_x * new_zoom) + new_pan_x
        # we want new_mouse_x == mouse_x
        # so: mouse_x = (rel_x * new_zoom) + new_pan_x
        # new_pan_x = mouse_x - (rel_x * new_zoom)
        
        self.pan_x = mouse_x - (rel_x * self.zoom_scale)
        self.pan_y = mouse_y - (rel_y * self.zoom_scale)
        
        self.refresh_canvas()

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def do_pan(self, event):
        # calculate delta
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        
        self.pan_x += dx
        self.pan_y += dy
        
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
        self.refresh_canvas()

    def refresh_canvas(self):
        """redraw image and overlays with zoom/pan"""
        if not self.pages and not self.input_images: return
        
        if not self.pages and not self.input_images: return
        
        # determine image to show
        img = None
        rois = []
        
        if self.current_mode == "DESIGNER" and self.pages:
            page = self.pages[self.current_page_index]
            img = page['image']
            rois = page['rois']
        elif self.current_mode == "SCANNER" and self.input_images:
            # Use aligned image if available for this page, otherwise raw input
            if self.current_input_index in self.session_results:
                img = self.session_results[self.current_input_index]['aligned_image']
            else:
                img = self.input_images[self.current_input_index]
            # scanner rois drawn separately
            
        if img is None: return
        
        # resize logic handled by zoom
        # keep image_scale as base "fit to window"
        # zoom_scale is dynamic zoom
        
        # resize image for display
        # note: resizing full image on zoom can be slow
        # optimization: only resize if zoom changed significantly or use pil
        
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
        # position image at pan coords
        self.canvas.create_image(self.pan_x, self.pan_y, anchor=tk.NW, image=self.tk_image)
        
        # redraw rois
        if self.current_mode == "DESIGNER":
            self.redraw_rois(rois)
        elif self.current_mode == "SCANNER" and self.current_input_index in self.session_results:
             self.draw_scanner_rois(self.session_results[self.current_input_index]['details'])

    def update_nav_buttons(self):
        total = len(self.pages)
        if total == 0:
            self.lbl_page.config(text="Sayfa Yok")
            self.btn_prev.config(state=tk.DISABLED)
            self.btn_next.config(state=tk.DISABLED)
            return
            
        self.lbl_page.config(text=f"Sayfa {self.current_page_index + 1}/{total}")
        
        if self.current_page_index > 0:
            self.btn_prev.config(state=tk.NORMAL)
        else:
            self.btn_prev.config(state=tk.DISABLED)
            
        if self.current_page_index < total - 1:
            self.btn_next.config(state=tk.NORMAL)
        else:
            self.btn_next.config(state=tk.DISABLED)

    def prev_page(self):
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.display_current_page()

    def next_page(self):
        if self.current_page_index < len(self.pages) - 1:
            self.current_page_index += 1
            self.display_current_page()

    def load_blank_form(self):
        file_path = filedialog.askopenfilename(filetypes=[("Files", "*.jpg *.jpeg *.png *.bmp *.pdf")])
        if not file_path:
            return
        
        loaded_imgs = self.load_images_from_file(file_path)
        if not loaded_imgs:
            messagebox.showerror("Error", "Could not load images.")
            return

        # init pages
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
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
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

    def display_current_page(self):
        if not self.pages:
            self.canvas.delete("all")
            return
            
        page = self.pages[self.current_page_index]
        self.display_image(page['image'], page['rois'])
        self.update_nav_buttons()

    def display_image(self, cv_img, rois=None):
        # calculate base scale to fit window
        h, w = cv_img.shape[:2]
        canvas_h = 700
        canvas_w = 1100
        
        scale_w = canvas_w / w
        scale_h = canvas_h / h
        self.image_scale = min(scale_w, scale_h, 1.0) # don't upscale
        
        # reset zoom/pan on new image
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        self.refresh_canvas()
        self.refresh_roi_list()

    def on_mouse_down(self, event):
        self.canvas.focus_set() # grab focus
        if not self.pages: return
        
        # check for selection first
        click_x = self.canvas.canvasx(event.x)
        click_y = self.canvas.canvasy(event.y)
        
        # convert to image coords to check against rois
        img_x, img_y = self.to_image_coords(click_x, click_y)
        
        rois = self.pages[self.current_page_index]['rois']
        clicked_index = None
        
        # check in reverse order (topmost first)
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
            # deselect if visited outside
            if self.selected_roi_index is not None:
                self.selected_roi_index = None
                self.refresh_canvas()
                self.refresh_roi_list()
        
        # start drawing new roi
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
        
        # normalize coords (top-left, bottom-right)
        x1 = min(self.rect_start_x, cur_x)
        y1 = min(self.rect_start_y, cur_y)
        x2 = max(self.rect_start_x, cur_x)
        y2 = max(self.rect_start_y, cur_y)
        
        # ignore tiny accidental clicks
        if (x2 - x1) < 5 or (y2 - y1) < 5:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            return

        # check for grid mode
        if self.grid_mode_var.get():
            # grid mode
            current_rois = self.pages[self.current_page_index]['rois']
            default_label = f"Q{len(current_rois)+1}"
            
            dialog = GridDialog(self.root, default_label)
            
            if dialog.result is None:
                self.canvas.delete(self.current_rect)
                self.current_rect = None
                return
                
            rows = dialog.result['rows']
            cols = dialog.result['cols']
            base_label = dialog.result['label']
            subscale = dialog.result['subscale']
            
            # convert selection to image coords
            orig_x, orig_y = self.to_image_coords(x1, y1)
            orig_x2, orig_y2 = self.to_image_coords(x2, y2)
            
            total_w = orig_x2 - orig_x
            total_h = orig_y2 - orig_y
            
            cell_w = total_w / cols
            cell_h = total_h / rows
            
            # create rois
            count = 1
            for r in range(rows):
                for c in range(cols):
                    # Calculate cell position
                    cell_x = int(orig_x + (c * cell_w))
                    cell_y = int(orig_y + (r * cell_h))
                    cell_w_int = int(cell_w)
                    cell_h_int = int(cell_h)
                    
                    # generate label (e.g., q1-1, q1-2)
                    # using simple sequential suffix
                    lbl = f"{base_label}-{count}"
                    
                    roi_data = {
                        "x": cell_x, "y": cell_y, "w": cell_w_int, "h": cell_h_int,
                        "value": "1", # default value
                        "label": lbl,
                        "subscale": subscale
                    }
                    self.pages[self.current_page_index]['rois'].append(roi_data)
                    count += 1
            
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            self.redraw_rois(self.pages[self.current_page_index]['rois'])
            self.refresh_roi_list()
            return

        # standard single roi
        current_rois = self.pages[self.current_page_index]['rois']
        default_label = f"Madde {len(current_rois)+1}"
        last_subscale = "Genel"
        if current_rois:
            last_subscale = current_rois[-1].get('subscale', "Genel")
            
        dialog = RegionPropertiesDialog(self.root, default_label, last_subscale)
        
        if dialog.result is None: # user cancelled
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            return

        val = dialog.result['value']
        label = dialog.result['label']
        subscale = dialog.result['subscale']

        # convert canvas coords back to image coords
        orig_x, orig_y = self.to_image_coords(x1, y1)
        orig_x2, orig_y2 = self.to_image_coords(x2, y2)
        
        orig_w = orig_x2 - orig_x
        orig_h = orig_y2 - orig_y
        
        roi_data = {
            "x": orig_x, "y": orig_y, "w": orig_w, "h": orig_h,
            "value": val,
            "label": label,
            "subscale": subscale
        }
        self.pages[self.current_page_index]['rois'].append(roi_data)
        
        # make rectangle permanent (green)
        self.canvas.delete(self.current_rect)
        self.current_rect = None
        
        # redraw all
        self.redraw_rois(self.pages[self.current_page_index]['rois'])
        self.refresh_roi_list()

    def undo_last_roi(self, event):
        if self.pages and self.pages[self.current_page_index]['rois']:
            self.pages[self.current_page_index]['rois'].pop()
            self.redraw_rois(self.pages[self.current_page_index]['rois'])
            self.refresh_roi_list()

    def clear_rois(self):
        if self.pages:
            self.pages[self.current_page_index]['rois'] = []
            self.redraw_rois([])
            self.refresh_roi_list()

    def show_help(self):
        help_text = """
Kısayollar ve Kullanım:

Seçim:
- Tıklama: Bir kutucuğu seçmek için üzerine tıklayın.
- Liste: Sağdaki listeden de seçim yapabilirsiniz.

Düzenleme:
- Çift Tıklama (Liste): Değerini değiştirmek için listedeki öğeye çift tıklayın.
- Delete (Sil): Seçili kutucuğu siler.

Hareket Ettirme:
- Yön Tuşları: Seçili kutucuğu 1 piksel kaydırır.
- Shift + Yön Tuşları: Seçili kutucuğu 10 piksel kaydırır.

Boyutlandırma:
- Alt + Yön Tuşları: Seçili kutucuğun boyutunu değiştirir.

Diğer:
- Sağ Tık (Boş alan): Son eklenen kutucuğu geri alır.
- Grid Aracı: Çoklu kutucuk eklemek için kullanın.
"""
        messagebox.showinfo("Yardım / Kısayollar", help_text)

    def redraw_rois(self, rois):
        self.canvas.delete("roi")
        for i, item in enumerate(rois):
            # apply zoom/pan
            x, y = self.to_canvas_coords(item['x'], item['y'])
            w = item['w'] * self.image_scale * self.zoom_scale
            h = item['h'] * self.image_scale * self.zoom_scale
            
            # highlight selected
            color = "green"
            width = 2
            if i == self.selected_roi_index:
                color = "red" # or yellow, or cyan
                width = 3
            
            self.canvas.create_rectangle(x, y, x+w, y+h, outline=color, width=width, tags="roi")
            sub = item.get('subscale', 'Genel')
            self.canvas.create_text(x, y-5, text=f"{item['label']} ({item['value']}) [{sub}]", fill="blue", anchor=tk.SW, tags="roi")

    def save_template(self):
        print("[SAVE] Şablon kaydetme işlemi başlatıldı")
        if not self.pages:
            print("[ERROR] Kaydedilecek sayfa yok")
            messagebox.showwarning("Uyarı", "Yüklü sayfa yok!")
            return
        
        print(f"[SAVE] Toplam {len(self.pages)} sayfa kaydedilecek")
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not file_path:
            print("[SAVE] Kullanıcı iptal etti")
            return
        
        print(f"[SAVE] Kayıt yolu: {file_path}")
        base_name = os.path.splitext(file_path)[0]
        
        template_pages_data = []
        
        for idx, page in enumerate(self.pages):
            # save reference image for this page
            ref_save_path = f"{base_name}_p{idx}.jpg"
            print(f"[SAVE] Sayfa {idx+1} - ROI sayısı: {len(page['rois'])}")
            cv2.imwrite(ref_save_path, page['image'])
            print(f"[SAVE] Referans görseli kaydedildi: {ref_save_path}")
            
            template_pages_data.append({
                "page_index": idx,
                "ref_image_storage": os.path.basename(ref_save_path), # store relative path
                "rois": page['rois']
            })
            
        data = {
            "version": "2.0",
            "pages": template_pages_data
        }
        
        print(f"[SAVE] JSON dosyası yazılıyor...")
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        
        print(f"[SAVE] ✓ Şablon başarıyla kaydedildi - {len(self.pages)} sayfa, Toplam ROI: {sum(len(p['rois']) for p in self.pages)}")
        messagebox.showinfo("Başarılı", f"Şablon kaydedildi: {file_path}\n{len(self.pages)} referans görseli oluşturuldu.")

    def setup_scanner_mode(self):
        self.current_mode = "SCANNER"
        self.clear_frame()
        self.root.title("GÖRÜNGÜ - Tarayıcı Modu (Manuel)")
        self.status_var.set("Tarayıcı Modu: Başlamak için şablon ve resimleri yükleyin.")
        
        # control panel
        panel = ttk.Frame(self.main_frame, width=320, style="Panel.TFrame", padding=15)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        panel.pack_propagate(False)  # fixed width
        
        # section 1: setup
        lbl_setup = ttk.Label(panel, text="1. Kurulum", style="Header.TLabel")
        lbl_setup.pack(anchor=tk.W, pady=(0, 10))
        
        frm_setup = ttk.LabelFrame(panel, text="Veri Yükleme", padding=10)
        frm_setup.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Button(frm_setup, text="Şablon Yükle (JSON)", command=self.load_template).pack(fill=tk.X, pady=2)
        self.lbl_template = ttk.Label(frm_setup, text="Şablon yüklenmedi", foreground=self.colors["error"], font=("Segoe UI", 9))
        self.lbl_template.pack(pady=2)
        
        ttk.Separator(frm_setup, orient='horizontal').pack(fill=tk.X, pady=5)
        
        ttk.Button(frm_setup, text="Resimleri Yükle", command=self.load_filled_form).pack(fill=tk.X, pady=2)
        ttk.Button(frm_setup, text="Klasör Yükle", command=self.load_filled_folder).pack(fill=tk.X, pady=2)
        
        # section 2: navigation
        lbl_nav = ttk.Label(panel, text="2. Navigasyon", style="Header.TLabel")
        lbl_nav.pack(anchor=tk.W, pady=(0, 10))
        
        frm_nav = ttk.LabelFrame(panel, text="Girdi Resimleri", padding=10)
        frm_nav.pack(fill=tk.X, pady=(0, 20))
        
        nav_inner = ttk.Frame(frm_nav)
        nav_inner.pack(fill=tk.X)
        
        self.btn_scan_prev = ttk.Button(nav_inner, text="<", command=self.scan_prev_page, state=tk.DISABLED, width=4)
        self.btn_scan_prev.pack(side=tk.LEFT)
        
        self.lbl_scan_page = ttk.Label(nav_inner, text="0/0", anchor=tk.CENTER)
        self.lbl_scan_page.pack(side=tk.LEFT, expand=True)
        
        self.btn_scan_next = ttk.Button(nav_inner, text=">", command=self.scan_next_page, state=tk.DISABLED, width=4)
        self.btn_scan_next.pack(side=tk.LEFT)
        
        # crop/align button
        ttk.Button(frm_nav, text="Kırp/Düzelt", command=self.open_corner_correction).pack(fill=tk.X, pady=(5, 0))
        
        # section 3: scoring
        lbl_score = ttk.Label(panel, text="3. Puanlama", style="Header.TLabel")
        lbl_score.pack(anchor=tk.W, pady=(0, 10))
        
        frm_score = ttk.LabelFrame(panel, text="İşlem", padding=10)
        frm_score.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(frm_score, text="Şablon Sayfası Kullan:").pack(anchor=tk.W)
        self.cmb_template_page = ttk.Combobox(frm_score, state="readonly")
        self.cmb_template_page.pack(fill=tk.X, pady=(2, 10))
        
        # threshold control
        ttk.Label(frm_score, text="İşaretlenme Eşiği (Threshold):").pack(anchor=tk.W, pady=(5, 0))
        
        # frame for slider and label
        threshold_frame = ttk.Frame(frm_score)
        threshold_frame.pack(fill=tk.X, pady=(2, 10))
        
        # init dynamic threshold
        if not hasattr(self, 'dynamic_threshold'):
            self.dynamic_threshold = 0.12
        
        # threshold value label
        self.lbl_threshold_value = ttk.Label(threshold_frame, text=f"{self.dynamic_threshold:.3f}", width=6)
        self.lbl_threshold_value.pack(side=tk.RIGHT)
        
        # threshold slider
        self.threshold_slider = tk.Scale(
            threshold_frame,
            from_=0.01,
            to=0.50,
            resolution=0.001,
            orient=tk.HORIZONTAL,
            command=self.on_threshold_change,
            showvalue=0,  # hide value on slider
            bg=self.colors["panel_bg"],
            fg=self.colors["text"],
            highlightthickness=0,
            troughcolor=self.colors["canvas"]
        )
        self.threshold_slider.set(self.dynamic_threshold)
        self.threshold_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(frm_score, text="Bu Sayfayı Puanla", command=self.score_current_page, style="Accent.TButton").pack(fill=tk.X, pady=(0, 5))
        
        self.btn_edit_mode = ttk.Button(frm_score, text="Veri Düzenleme: Kapalı", command=self.toggle_edit_mode)
        self.btn_edit_mode.pack(fill=tk.X)
        
        # session score
        self.lbl_total_score = ttk.Label(panel, text="Toplam Oturum Puanı: 0", font=("Segoe UI", 12, "bold"), background="#e0e7ff", padding=10, anchor=tk.CENTER)
        self.lbl_total_score.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(panel, text="Raporu Görüntüle", command=self.show_session_report).pack(fill=tk.X, pady=(0, 10))
        
        # center area: canvas
        center_frame = ttk.Frame(self.main_frame, style="TFrame")
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        self.canvas = tk.Canvas(center_frame, bg=self.colors["canvas"], bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # right panel: details
        details_panel = ttk.Frame(self.main_frame, width=320, style="Panel.TFrame", padding=15)
        details_panel.pack(side=tk.RIGHT, fill=tk.Y)
        details_panel.pack_propagate(False)  # fixed width
        
        ttk.Label(details_panel, text="Detaylar", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        # results text area
        results_frame = ttk.Frame(details_panel)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.txt_results = tk.Text(
            results_frame, 
            font=("Consolas", 9), 
            relief=tk.FLAT, 
            bg=self.colors["input_bg"], 
            fg=self.colors["input_fg"],
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set
        )
        self.txt_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.txt_results.yview)
        
        # zoom & pan state
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # bindings
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Button-3>", self.undo_last_roi) # right click undo
        
        # zoom/pan bindings
        self.canvas.bind("<MouseWheel>", self.on_zoom) # windows
        self.canvas.bind("<Button-4>", self.on_zoom)   # linux scroll up
        self.canvas.bind("<Button-5>", self.on_zoom)   # linux scroll down
        self.canvas.bind("<ButtonPress-2>", self.start_pan) # middle click
        self.canvas.bind("<B2-Motion>", self.do_pan)
        
        # variables
        self.template_pages = [] 
        self.input_images = []
        self.current_input_index = 0
        self.session_results = {} 
        self.session_subscales = {}

    def open_corner_correction(self):
        print("[CORNER] Köşe düzeltme işlemi başlatıldı")
        if not self.input_images:
            print("[ERROR] Yüklenmiş görsel yok")
            messagebox.showwarning("Uyarı", "Lütfen önce resim yükleyin.")
            return
        
        print(f"[CORNER] Mevcut görsel: {self.current_input_index+1}/{len(self.input_images)}")
        current_img = self.input_images[self.current_input_index]
        print(f"[CORNER] Görsel boyutu: {current_img.shape}")
        
        # try auto-detect first
        print("[CORNER] Otomatik köşe tespiti başlatılıyor...")
        found, corners = CornerCorrectionDialog.detect_corners(current_img)
        
        if found:
            print("[CORNER] ✓ Köşeler otomatik tespit edildi")
            # auto-warp immediately
            # re-using warp logic
            
            src_pts = np.array(corners, dtype="float32")
            
            # sort corners
            # simple sort impl
            rect = np.zeros((4, 2), dtype="float32")
            s = src_pts.sum(axis=1)
            rect[0] = src_pts[np.argmin(s)] # tl
            rect[2] = src_pts[np.argmax(s)] # br
            diff = np.diff(src_pts, axis=1)
            rect[1] = src_pts[np.argmin(diff)] # tr
            rect[3] = src_pts[np.argmax(diff)] # bl
            src_pts = rect
            
            (tl, tr, br, bl) = src_pts
            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            maxWidth = max(int(widthA), int(widthB))
            
            heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            maxHeight = max(int(heightA), int(heightB))
            
            dst_pts = np.array([
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1]], dtype="float32")
            
            print("[CORNER] Perspektif dönüşümü uygulanıyor...")
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            result_image = cv2.warpPerspective(current_img, M, (maxWidth, maxHeight))
            print(f"[CORNER] ✓ Otomatik düzeltme tamamlandı - Yeni boyut: {result_image.shape}")
            
            # update state
            self.input_images[self.current_input_index] = result_image
            if self.current_input_index in self.session_results:
                del self.session_results[self.current_input_index]
                self.txt_results.delete(1.0, tk.END)
                self.update_total_score()
            self.update_scanner_ui()
            # optional: toast instead of popup
            self.status_var.set("Otomatik düzeltme uygulandı.")
            print("[CORNER] ✓ İşlem tamamlandı (otomatik)")
            return

        # if failed, open dialog
        print("[CORNER] Otomatik tespit başarısız, manuel düzenleme açılıyor...")
        dialog = CornerCorrectionDialog(self.root, current_img, initial_corners=corners)
        
        if dialog.result_image is not None:
            print("[CORNER] ✓ Manuel düzeltme tamamlandı")
            # update image
            self.input_images[self.current_input_index] = dialog.result_image
            
            # clear previous results
            if self.current_input_index in self.session_results:
                del self.session_results[self.current_input_index]
                self.txt_results.delete(1.0, tk.END)
                self.update_total_score()
                
            self.update_scanner_ui()
            print("[CORNER] ✓ İşlem tamamlandı (manuel)")
            messagebox.showinfo("Başarılı", "Resim kırpıldı ve düzeltildi.")
        else:
            print("[CORNER] Kullanıcı işlemi iptal etti")

    def load_template(self):
        print("[TEMPLATE] Şablon yükleme başlatıldı")
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file_path:
            print("[TEMPLATE] Kullanıcı iptal etti")
            return
        
        print(f"[TEMPLATE] Şablon dosyası: {file_path}")
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        print(f"[TEMPLATE] JSON verisi okundu - Versiyon: {data.get('version', 'legacy')}")
        self.template_pages = []
        base_dir = os.path.dirname(file_path)
        
        if "pages" in data:
            print(f"[TEMPLATE] Çoklu sayfa formatı tespit edildi - {len(data['pages'])} sayfa")
            for i, p_data in enumerate(data["pages"]):
                ref_name = p_data["ref_image_storage"]
                ref_path = os.path.join(base_dir, ref_name)
                print(f"[TEMPLATE] Sayfa {i+1} referans görseli: {ref_path}")
                if os.path.exists(ref_path):
                    img = cv2.imread(ref_path)
                    roi_count = len(p_data["rois"])
                    print(f"[TEMPLATE] Sayfa {i+1} yüklendi - {roi_count} ROI")
                    self.template_pages.append({
                        "image": img,
                        "rois": p_data["rois"],
                        "page_index": p_data["page_index"]
                    })
                else:
                    print(f"[ERROR] Referans görseli bulunamadı: {ref_path}")
        else:
            # legacy format
            print("[TEMPLATE] Eski format (legacy) tespit edildi")
            ref_name = data.get("ref_image_storage", "")
            ref_path = os.path.join(base_dir, ref_name)
            if not os.path.exists(ref_path):
                ref_path = data.get("ref_image_path", "")
            print(f"[TEMPLATE] Referans görsel yolu: {ref_path}")
            if os.path.exists(ref_path):
                img = cv2.imread(ref_path)
                roi_count = len(data["rois"])
                print(f"[TEMPLATE] Legacy şablon yüklendi - {roi_count} ROI")
                self.template_pages.append({
                    "image": img,
                    "rois": data["rois"],
                    "page_index": 0
                })
            else:
                print(f"[ERROR] Legacy referans görseli bulunamadı: {ref_path}")
        
        if self.template_pages:
            print(f"[TEMPLATE] ✓ Şablon başarıyla yüklendi - {len(self.template_pages)} sayfa")
            self.lbl_template.config(text=f"{os.path.basename(file_path)} ({len(self.template_pages)} sayfa)", foreground=self.colors["success"])
            # update combobox
            self.cmb_template_page['values'] = [f"Sayfa {i+1}" for i in range(len(self.template_pages))]
            if self.cmb_template_page['values']:
                self.cmb_template_page.current(0)
        else:
            print("[ERROR] Şablon yüklenemedi - Referans görselleri bulunamadı")
            messagebox.showerror("Hata", "Referans görselleri yüklenemedi.")

    def load_filled_form(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")])
        if not file_paths:
            return
        self._load_inputs(file_paths)

    def load_filled_folder(self):
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
        print(f"[INPUT] {len(file_paths)} dosya yüklenecek")
        self.input_images = []
        for i, path in enumerate(file_paths):
            print(f"[INPUT] Dosya {i+1}/{len(file_paths)}: {path}")
            imgs = self.load_images_from_file(path)
            self.input_images.extend(imgs)
            
        if self.input_images:
            print(f"[INPUT] ✓ Toplam {len(self.input_images)} görsel yüklendi")
            self.current_input_index = 0
            self.session_results = {}
            print("[INPUT] Tarayıcı UI güncelleniyor...")
            self.update_scanner_ui()
            messagebox.showinfo("Yüklendi", f"{len(self.input_images)} resim yüklendi.")
        else:
            print("[ERROR] Hiç görsel yüklenemedi")
            messagebox.showwarning("Uyarı", "Resim bulunamadı.")

    def update_scanner_ui(self):
        if not self.input_images:
            self.lbl_scan_page.config(text="0/0")
            self.btn_scan_prev.config(state=tk.DISABLED)
            self.btn_scan_next.config(state=tk.DISABLED)
            self.canvas.delete("all")
            return
            
        total = len(self.input_images)
        self.lbl_scan_page.config(text=f"{self.current_input_index + 1}/{total}")
        
        self.btn_scan_prev.config(state=tk.NORMAL if self.current_input_index > 0 else tk.DISABLED)
        self.btn_scan_next.config(state=tk.NORMAL if self.current_input_index < total - 1 else tk.DISABLED)
        
        # display current image
        self.display_image(self.input_images[self.current_input_index])
        
        # auto-select template if matching index
        if self.template_pages and self.current_input_index < len(self.template_pages):
            self.cmb_template_page.current(self.current_input_index)

    def scan_prev_page(self):
        if self.current_input_index > 0:
            self.current_input_index -= 1
            self.update_scanner_ui()
            
    def scan_next_page(self):
        if self.current_input_index < len(self.input_images) - 1:
            self.current_input_index += 1
            self.update_scanner_ui()

    def score_current_page(self):
        print("[SCORE] Sayfa değerlendirme başlatıldı")
        if not self.template_pages:
            print("[ERROR] Şablon yüklenmemiş")
            messagebox.showerror("Hata", "Şablon yüklenmedi.")
            return
        if not self.input_images:
            print("[ERROR] Girdi görseli yok")
            messagebox.showerror("Hata", "Girdi resmi yok.")
            return
            
        # get selected template
        t_idx = self.cmb_template_page.current()
        if t_idx == -1:
            print("[ERROR] Şablon sayfası seçilmemiş")
            messagebox.showerror("Hata", "Bir şablon sayfası seçin.")
            return
        
        print(f"[SCORE] Şablon sayfası: {t_idx+1}, Girdi görseli: {self.current_input_index+1}/{len(self.input_images)}")
        t_page = self.template_pages[t_idx]
        input_img = self.input_images[self.current_input_index]
        print(f"[SCORE] Girdi görseli boyutu: {input_img.shape}, Şablon ROI sayısı: {len(t_page['rois'])}")
        
        try:
            self.txt_results.delete(1.0, tk.END)
            self.txt_results.insert(tk.END, f"Şablon Sayfası {t_idx+1} ile hizalanıyor...\n")
            self.root.update()
            
            print("[ALIGN] Hizalama işlemi başlatılıyor...")
            aligned, H = self.align_images(input_img, t_page['image'])
            
            if aligned is None:
                print("[ERROR] Hizalama başarısız oldu")
                self.txt_results.insert(tk.END, "Hizalama BAŞARISIZ.\n")
                messagebox.showwarning("Hizalama Hatası", "Resim şablonla hizalanamadı. Işıklandırmayı veya açıyı kontrol edin.")
                return
            
            print("[ALIGN] ✓ Hizalama başarılı")
            
            # score
            print("[SCORE] Puanlama işlemi başlatılıyor...")
            page_score, page_subscales, page_log, page_details = self.score_page(aligned, t_page['rois'])
            print(f"[SCORE] ✓ Puanlama tamamlandı - Toplam puan: {page_score}")
            print(f"[SCORE] Alt ölçekler: {page_subscales}")
            
            # update session scores
            self.session_results[self.current_input_index] = {
                "total": page_score,
                "subscales": page_subscales,
                "details": page_details,
                "aligned_image": aligned, # store aligned image
                "rois_def": t_page['rois'] # store roi defs
            }
            print(f"[SCORE] Sonuçlar oturuma kaydedildi")
            
            self.update_results_display(page_score, page_log)
            self.update_total_score()
            
            # show visuals
            print("[SCORE] Görseller güncelleniyor...")
            self.display_image(aligned)
            self.draw_scanner_rois(page_details)
            print("[SCORE] ✓ İşlem tamamlandı")
            
        except Exception as e:
            print(f"[ERROR] Puanlama hatası: {str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Hata", f"İşlem başarısız: {str(e)}")

    def update_results_display(self, score, log):
        self.txt_results.delete(1.0, tk.END)
        self.txt_results.insert(tk.END, f"Puan: {score}\n\n")
        for line in log:
            self.txt_results.insert(tk.END, line + "\n")

    def update_total_score(self):
        total_score = sum(r['total'] for r in self.session_results.values())
        self.lbl_total_score.config(text=f"Toplam Oturum Puanı: {total_score}")

    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
            self.btn_edit_mode.config(text="Veri Düzenleme: AÇIK", style="Accent.TButton")
            self.canvas.bind("<Button-1>", self.on_scanner_roi_click)
            messagebox.showinfo("Düzenleme Modu", "Artık kutucuklara tıklayarak durumlarını (İşaretli/İşaretsiz) değiştirebilirsiniz.")
        else:
            self.btn_edit_mode.config(text="Veri Düzenleme: Kapalı", style="TButton")
            self.canvas.unbind("<Button-1>")

    def on_threshold_change(self, value):
        """threshold slider callback"""
        self.dynamic_threshold = float(value)
        # update label
        if hasattr(self, 'lbl_threshold_value'):
            self.lbl_threshold_value.config(text=f"{self.dynamic_threshold:.3f}")

    def on_scanner_roi_click(self, event):
        if not self.edit_mode: return
        
        print("[EDIT] ROI düzenleme tıklaması algılandı")
        if self.current_input_index not in self.session_results:
            print("[EDIT] Bu sayfa için sonuç yok")
            return
        
        # find clicked item
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        item = self.canvas.find_closest(x, y)
        tags = self.canvas.gettags(item)
        
        roi_idx = -1
        for tag in tags:
            if tag.startswith("roi_"):
                roi_idx = int(tag.split("_")[1])
                break
        
        if roi_idx == -1:
            print("[EDIT] Tıklanan bölgede ROI bulunamadı")
            return
        
        # toggle state
        res = self.session_results[self.current_input_index]
        details = res['details']
        
        # update threshold automatically
        # if marked manually, maybe lower threshold
        # if unmarked manually, maybe raise threshold
        current_fill = details[roi_idx]['fill_ratio']
        was_marked = details[roi_idx]['is_marked']
        
        # Toggle
        details[roi_idx]['is_marked'] = not was_marked
        print(f"[EDIT] ROI durumu değiştirildi: {was_marked} -> {details[roi_idx]['is_marked']} (fill_ratio: {current_fill:.3f})")
        
        # learn from interaction
        self.update_threshold_from_manual_input(not was_marked, current_fill)
        
        # recalc score
        print("[EDIT] Sayfa yeniden hesaplanıyor...")
        self.recalculate_page_score(self.current_input_index)
        
        # redraw
        self.draw_scanner_rois(details)
        print("[EDIT] ✓ ROI düzenleme tamamlandı")

    def update_threshold_from_manual_input(self, is_now_marked, fill_ratio):
        """
        adapt threshold based on user correction.
        """
        if not hasattr(self, 'dynamic_threshold'):
            self.dynamic_threshold = 0.12
            
        # learning rate / safety margin
        margin = 0.01
        
        threshold_changed = False
        
        if is_now_marked:
            # user says should be marked.
            # lower threshold if needed.
            if self.dynamic_threshold > fill_ratio:
                print(f"Learning: Lowering threshold from {self.dynamic_threshold:.3f} to {fill_ratio - margin:.3f}")
                self.dynamic_threshold = max(0.01, fill_ratio - margin)
                threshold_changed = True
        else:
            # user says should NOT be marked.
            # raise threshold if needed.
            if self.dynamic_threshold < fill_ratio:
                print(f"Learning: Raising threshold from {self.dynamic_threshold:.3f} to {fill_ratio + margin:.3f}")
                self.dynamic_threshold = min(0.90, fill_ratio + margin)
                threshold_changed = True
        
        # update ui if changed
        if threshold_changed:
            # update slider
            if hasattr(self, 'threshold_slider') and self.threshold_slider.winfo_exists():
                self.threshold_slider.set(self.dynamic_threshold)
            
            # update label
            if hasattr(self, 'lbl_threshold_value') and self.lbl_threshold_value.winfo_exists():
                self.lbl_threshold_value.config(text=f"{self.dynamic_threshold:.3f}")
            
            # update status
            self.status_var.set(f"Eşik değeri otomatik olarak {self.dynamic_threshold:.3f} değerine güncellendi.")

    def recalculate_page_score(self, input_idx):
        res = self.session_results[input_idx]
        details = res['details']
        
        p_score = 0
        p_subscales = {}
        p_log = []
        
        for item in details:
            roi_def = item['roi_def']
            is_marked = item['is_marked']
            val_str = roi_def['value']
            label = roi_def['label']
            subscale = roi_def.get('subscale', 'Genel')
            
            status = "[ ]"
            if is_marked:
                status = "[X]"
                try:
                    score = float(val_str)
                    p_score += score
                    p_subscales[subscale] = p_subscales.get(subscale, 0) + score
                except ValueError:
                    pass
            
            p_log.append(f"{status} {label} [{subscale}]: {val_str if is_marked else '0'} (Manuel)")
            
        # update stored results
        res['total'] = p_score
        res['subscales'] = p_subscales
        
        # update ui if current page
        if input_idx == self.current_input_index:
            self.update_results_display(p_score, p_log)
            self.update_total_score()

    def draw_scanner_rois(self, details):
        self.canvas.delete("scanner_roi")
        for idx, item in enumerate(details):
            roi = item['roi_def']
            # apply zoom/pan
            x, y = self.to_canvas_coords(roi['x'], roi['y'])
            w = roi['w'] * self.image_scale * self.zoom_scale
            h = roi['h'] * self.image_scale * self.zoom_scale
            
            color = "green" if item['is_marked'] else "red"
            # draw semi-transparent-like rect
            self.canvas.create_rectangle(x, y, x+w, y+h, outline=color, width=2, tags=("scanner_roi", f"roi_{idx}"))

    def show_session_report(self):
        if not self.session_results:
            messagebox.showinfo("Rapor", "Henüz puanlanmış sayfa yok.")
            return
            
        total_score = 0
        subscale_totals = {}
        
        for res in self.session_results.values():
            total_score += res['total']
            for sub, val in res['subscales'].items():
                subscale_totals[sub] = subscale_totals.get(sub, 0) + val
                
        report = f"=== OTURUM RAPORU ===\n\n"
        report += f"Toplam Puan: {total_score}\n"
        report += f"İşlenen Sayfa Sayısı: {len(self.session_results)}\n\n"
        report += "--- Alt Ölçekler ---\n"
        
        for sub, val in subscale_totals.items():
            report += f"{sub}: {val}\n"
            
        # custom dialog for report
        # simple toplevel
        top = tk.Toplevel(self.root)
        top.title("Sonuç Raporu")
        top.geometry("400x500")
        top.configure(bg=self.colors["bg"])
        
        txt = tk.Text(top, font=("Consolas", 11), bg=self.colors["input_bg"], fg=self.colors["input_fg"], padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert(tk.END, report)
        txt.config(state=tk.DISABLED) # read-only
        
        btn_export = ttk.Button(top, text="Excel'e Aktar (.csv)", command=self.export_report)
        btn_export.pack(fill=tk.X, padx=10, pady=10)

    def export_report(self):
        if not self.session_results:
            messagebox.showwarning("Uyarı", "Dışa aktarılacak veri yok.")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if not file_path:
            return
            
        try:
            # collect all unique subscales
            all_subscales = set()
            for res in self.session_results.values():
                all_subscales.update(res['subscales'].keys())
            sorted_subscales = sorted(list(all_subscales))
            
            header = ["Sayfa No", "Toplam Puan"] + sorted_subscales
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f: # utf-8-sig for excel
                writer = csv.writer(f, delimiter=';') # semicolon safer for excel in some regions
                writer.writerow(header)
                
                # write page rows
                for page_idx, res in self.session_results.items():
                    row = [page_idx + 1, res['total']]
                    for sub in sorted_subscales:
                        row.append(res['subscales'].get(sub, 0))
                    writer.writerow(row)
                    
                # write totals row
                writer.writerow([])
                total_row = ["GENEL TOPLAM", sum(r['total'] for r in self.session_results.values())]
                
                # calculate subscale totals
                sub_totals = {sub: 0 for sub in sorted_subscales}
                for res in self.session_results.values():
                    for sub, val in res['subscales'].items():
                        sub_totals[sub] += val
                        
                for sub in sorted_subscales:
                    total_row.append(sub_totals[sub])
                    
                writer.writerow(total_row)
                
            messagebox.showinfo("Başarılı", f"Rapor kaydedildi:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme başarısız: {e}")


    def score_page(self, aligned_img, rois):
        # ... logic extracted from old process_form ...
        print(f"[SCORE_PAGE] Sayfa puanlama başladı - {len(rois)} ROI işlenecek")
        gray_aligned = cv2.cvtColor(aligned_img, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(gray_aligned, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 15, 5)
        kernel = np.ones((2,2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        print("[SCORE_PAGE] Görsel ön işleme tamamlandı (grayscale + binary + morph)")
        
        p_score = 0
        p_subscales = {}
        p_log = []
        p_details = []
        
        # ensure dynamic threshold exists
        if not hasattr(self, 'dynamic_threshold'):
            self.dynamic_threshold = 0.12
            print(f"[SCORE_PAGE] Dinamik eşik değeri başlatıldı: {self.dynamic_threshold}")
        else:
            print(f"[SCORE_PAGE] Mevcut dinamik eşik: {self.dynamic_threshold}")
            
        for item in rois:
            x, y, w, h = item['x'], item['y'], item['w'], item['h']
            label = item['label']
            val_str = item['value']
            subscale = item.get('subscale', 'Genel')
            
            margin_x = int(w * 0.15)
            margin_y = int(h * 0.15)
            roi_x = x + margin_x
            roi_y = y + margin_y
            roi_w = w - (2 * margin_x)
            roi_h = h - (2 * margin_y)
            
            # binary fill ratio
            roi_bin = binary[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            non_zero = cv2.countNonZero(roi_bin)
            area = roi_w * roi_h
            if area == 0: area = 1
            fill_ratio = non_zero / area
            
            # grayscale mean intensity (avg internal)
            roi_gray = gray_aligned[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            mean_intensity = cv2.mean(roi_gray)[0]
            
            # decision:
            # primary: fill ratio > threshold
            # secondary: optional scribble check (disabled)
            
            is_marked = fill_ratio > self.dynamic_threshold
            
            # optional: scribble override
            # if not is_marked and mean_intensity < 180 and fill_ratio > 0.05:
            #    is_marked = True
            
            p_details.append({
                'roi_def': item,
                'is_marked': is_marked,
                'fill_ratio': fill_ratio,
                'mean_intensity': mean_intensity
            })
            
            status = "[ ]"
            if is_marked:
                status = "[X]"
                try:
                    score = float(val_str)
                    p_score += score
                    p_subscales[subscale] = p_subscales.get(subscale, 0) + score
                except ValueError:
                    pass
            
            p_log.append(f"{status} {label} [{subscale}]: {val_str if is_marked else '0'} ({fill_ratio:.2f})")
        
        print(f"[SCORE_PAGE] ✓ Puanlama tamamlandı - Toplam: {p_score}, Alt ölçek sayısı: {len(p_subscales)}")
        return p_score, p_subscales, p_log, p_details

    def align_images(self, img, ref):
        """
        align 'img' to 'ref' using sift/orb.
        tries homography, checks sanity, falls back to affine.
        """
        print("[ALIGN] Görsel hizalama başlatıldı")
        h_ref, w_ref = ref.shape[:2]
        h_img, w_img = img.shape[:2]
        print(f"[ALIGN] Girdi boyutu: {w_img}x{h_img}, Referans boyutu: {w_ref}x{h_ref}")
        
        # convert to grayscale
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_ref = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
        
        try:
            detector = cv2.SIFT_create()
            norm = cv2.NORM_L2
            print("[ALIGN] SIFT detektörü kullanılıyor")
        except AttributeError:
            detector = cv2.ORB_create(nfeatures=5000)
            norm = cv2.NORM_HAMMING
            print("[ALIGN] ORB detektörü kullanılıyor (SIFT mevcut değil)")
        
        print("[ALIGN] Özellik noktaları tespit ediliyor...")
        kp1, des1 = detector.detectAndCompute(gray_img, None)
        kp2, des2 = detector.detectAndCompute(gray_ref, None)
        print(f"[ALIGN] Girdi keypoints: {len(kp1) if kp1 else 0}, Referans keypoints: {len(kp2) if kp2 else 0}")
        
        if des1 is None or des2 is None:
            print("[ERROR] Özellik tanımlayıcıları bulunamadı")
            return None, None

        print("[ALIGN] Özellik eşleştirme yapılıyor...")
        bf = cv2.BFMatcher(norm)
        matches = bf.knnMatch(des1, des2, k=2)
        
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)
        
        print(f"[ALIGN] Toplam eşleşme: {len(matches)}, İyi eşleşme: {len(good_matches)}")
        
        if len(good_matches) > 10:
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            
            # strategy 1: try homography (perspective)
            print("[ALIGN] Homography dönüşümü deneniyor...")
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            
            is_homography_good = False
            if M is not None:
                print("[ALIGN] Homography matrisi hesaplandı")
                # sanity check: check if corners mapped reasonably
                corners = np.float32([[0, 0], [0, h_img], [w_img, h_img], [w_img, 0]]).reshape(-1, 1, 2)
                warped_corners = cv2.perspectiveTransform(corners, M)
                
                # calc warped area
                area = cv2.contourArea(warped_corners)
                ref_area = w_ref * h_ref
                
                # check for drastic change (< 50% or > 150%)
                area_ratio = area / ref_area
                print(f"[ALIGN] Homography alan oranı: {area_ratio:.2f}")
                if 0.5 < area_ratio < 1.5:
                    is_homography_good = True
                    print("[ALIGN] ✓ Homography doğrulandı")
                else:
                    print(f"[ALIGN] Homography reddedildi: Alan oranı {area_ratio:.2f}")

            if is_homography_good:
                print("[ALIGN] Homography dönüşümü uygulanıyor...")
                aligned_img = cv2.warpPerspective(img, M, (w_ref, h_ref))
                print("[ALIGN] ✓ Hizalama başarılı (Homography)")
                return aligned_img, M
            
            # strategy 2: fallback to affine (rigid + scale)
            # safer for pdfs/scans without perspective distortion
            print("[ALIGN] Affine dönüşümüne geçiliyor...")
            M_affine, inliers = cv2.estimateAffinePartial2D(src_pts, dst_pts)
            
            if M_affine is not None:
                print("[ALIGN] Affine dönüşümü uygulanıyor...")
                aligned_img = cv2.warpAffine(img, M_affine, (w_ref, h_ref))
                print("[ALIGN] ✓ Hizalama başarılı (Affine)")
                return aligned_img, M_affine
            
            print("[ERROR] Affine dönüşümü de başarısız oldu")
            return None, None
        else:
            print("[ERROR] Yetersiz iyi eşleşme (minimum 10 gerekli)")
            return None, None

class CornerCorrectionDialog(tk.Toplevel):
    def __init__(self, parent, cv_image, initial_corners=None):
        super().__init__(parent)
        self.title("Köşe Düzeltme")
        self.geometry("1000x800")
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

    @staticmethod
    def detect_corners(image):
        """returns (found_bool, corners_list)"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 75, 200)
        
        cnts, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
        
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            
            if len(approx) == 4:
                return True, [p[0].tolist() for p in approx]
                
        # fallback
        h, w = image.shape[:2]
        m = 50
        corners = [[m, m], [m, h-m], [w-m, h-m], [w-m, m]]
        return False, corners

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
        found, corners = self.detect_corners(self.cv_image)
        self.corners = corners
        self.sort_corners()
        self.draw_handles()

    def sort_corners(self):
        # sort: tl, tr, br, bl
        pts = np.array(self.corners)
        rect = np.zeros((4, 2), dtype="float32")
        
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)] # TL
        rect[2] = pts[np.argmax(s)] # BR
        
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)] # TR
        rect[3] = pts[np.argmax(diff)] # BL
        
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
        # 4 points in source
        src_pts = np.array(self.corners, dtype="float32")
        
        # 4 points in destination (a4 approx)
        # calc width/height
        (tl, tr, br, bl) = src_pts
        
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        dst_pts = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")
            
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        self.result_image = cv2.warpPerspective(self.cv_image, M, (maxWidth, maxHeight))
        
        self.destroy()

def show_splash_screen(root):
    """displays splash screen with thoth.jpg if available."""
    try:
        # check if thoth.jpg exists
        if not os.path.exists("thoth.jpg"):
            return

        splash = tk.Toplevel(root)
        splash.overrideredirect(True) # no decorations
        
        # load image
        pil_img = Image.open("thoth.jpg")
        # Resize if too big, e.g., max 600x400
        pil_img.thumbnail((600, 400))
        img = ImageTk.PhotoImage(pil_img)
        
        w, h = pil_img.size
        
        # center splash
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - w) // 2
        y = (screen_height - h) // 2
        splash.geometry(f"{w}x{h}+{x}+{y}")
        
        lbl_img = tk.Label(splash, image=img, bg="black")
        lbl_img.image = img # keep ref
        lbl_img.pack(fill=tk.BOTH, expand=True)
        
        # add text overlay
        lbl_title = tk.Label(splash, text="GÖRÜNGÜ", font=("Courier New", 24, "bold"), bg="black", fg="white")
        lbl_title.place(relx=0.5, rely=0.8, anchor=tk.CENTER)
        
        lbl_subtitle = tk.Label(splash, text="Powered by Thoth Engine", font=("Courier New", 10), bg="black", fg="#C5A572") # antique gold
        lbl_subtitle.place(relx=0.5, rely=0.9, anchor=tk.CENTER)
        
        splash.update()
        import time
        time.sleep(2) # show for 2s
        splash.destroy()
    except Exception as e:
        print(f"Splash screen error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    # hide root initially
    # normally splash is toplevel
    # withdraw root, show splash, deiconify
    root.withdraw()
    show_splash_screen(root)
    root.deiconify()
    
    app = OMRApp(root)
    root.mainloop()
