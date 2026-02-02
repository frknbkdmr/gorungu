
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

from src import config
from src.ui import designer, scanner, dialogs

class OMRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GÖRÜNGÜ - Powered by Thoth Engine")
        self.root.geometry("1280x850")
        
        print("[APP] GÖRÜNGÜ başlatılıyor...")
        
        # State
        self.current_mode = None # "DESIGNER" or "SCANNER"
        self.mode_instance = None # Instance of DesignerMode or ScannerMode
        
        # Theme
        self.colors = config.THEMES[config.DEFAULT_THEME]
        self.style = ttk.Style()
        self.style.theme_use('clam')
        # UI Structure
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.apply_theme()
        
        self.status_var = tk.StringVar(value="Hazır")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, font=config.FONTS["preferred"]["status"])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.setup_menu()
        
        # Start in Designer Mode
        self.switch_to_designer()

    def setup_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Mode Menu
        self.mode_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Mod", menu=self.mode_menu)
        self.mode_menu.add_command(label="Tasarımcı Modu", command=self.switch_to_designer)
        self.mode_menu.add_command(label="Tarayıcı Modu", command=self.switch_to_scanner)
        
        # View Menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Görünüm", menu=self.view_menu)
        
        # Theme Submenu
        self.theme_menu = tk.Menu(self.view_menu, tearoff=0)
        self.view_menu.add_cascade(label="Tema", menu=self.theme_menu)
        
        for theme_name in config.THEMES.keys():
            display_name = theme_name.replace("_", " ").title()
            self.theme_menu.add_command(label=display_name, command=lambda t=theme_name: self.set_theme(t))
            
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Hakkında", command=self.show_about)
        
        # Help Menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Yardım", menu=self.help_menu)
        self.help_menu.add_command(label="Hakkında GÖRÜNGÜ", command=self.show_about)

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def set_theme(self, theme_name):
        if theme_name in config.THEMES:
            print(f"[APP] Tema değişti: {theme_name}")
            self.colors = config.THEMES[theme_name]
            self.apply_theme()
            # Re-initialize current mode to apply theme colors completely if needed
            # For now, just simplistic re-render might be needed 
            # or we rely on mode using self.app.colors on redraw
            if self.mode_instance:
                 # Ideally modes should have a 'on_theme_change' or we rebuild UI
                 self.mode_instance.setup_ui(self.main_frame) 

    def apply_theme(self):
        # Apply to root
        self.root.configure(bg=self.colors["bg"])
        
        # Configure ttk styles
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("Panel.TFrame", background=self.colors["panel_bg"])
        self.style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"])
        self.style.configure("Panel.TLabel", background=self.colors["panel_bg"], foreground=self.colors["text"])
        self.style.configure("Header.TLabel", background=self.colors["panel_bg"], foreground=self.colors["text"])
        
        self.style.configure("TButton", background=self.colors["panel_bg"], foreground=self.colors["text"])
        self.style.map("TButton", background=[('active', self.colors["accent"])], foreground=[('active', 'white')])
        
        self.style.configure("Accent.TButton", background=self.colors["accent"], foreground="white")
        self.style.map("Accent.TButton", background=[('active', self.colors["text"])])
        
        self.style.configure("TLabelframe", background=self.colors["panel_bg"], foreground=self.colors["text"])
        self.style.configure("TLabelframe.Label", background=self.colors["panel_bg"], foreground=self.colors["text"])
        
        # Refresh main frame background
        self.main_frame.configure(style="TFrame")

    def switch_to_designer(self):
        self.current_mode = "DESIGNER"
        self.clear_frame()
        self.root.title("GÖRÜNGÜ - Tasarımcı Modu")
        print("[APP] Mod değişti: TASARIMCI")
        self.status_var.set("Tasarımcı Modu: Başlamak için boş bir form yükleyin.")
        
        self.mode_instance = designer.DesignerMode(self)
        self.mode_instance.setup_ui(self.main_frame)
        
        # Bind keys
        self.root.bind("<Key>", self.on_key_press)

    def switch_to_scanner(self):
        self.current_mode = "SCANNER"
        self.clear_frame()
        self.root.title("GÖRÜNGÜ - Tarayıcı Modu (Manuel)")
        print("[APP] Mod değişti: TARAYICI")
        self.status_var.set("Tarayıcı Modu: Başlamak için şablon ve resimleri yükleyin.")
        
        self.mode_instance = scanner.ScannerMode(self)
        self.mode_instance.setup_ui(self.main_frame)
        
        # Unbind keys or rebind if scanner needs them
        self.root.unbind("<Key>") # Scanner doesn't use arrow keys for ROI moving

    def on_key_press(self, event):
        # Route key press to active mode if it handles it
        if self.current_mode == "DESIGNER" and hasattr(self.mode_instance, 'on_key_press'):
            # Check if focus is on an entry widget to avoid conflict
            focused = self.root.focus_get()
            if isinstance(focused, (tk.Entry, tk.Text, ttk.Entry)):
                return
            self.mode_instance.on_key_press(event)

    def show_about(self):
        dialogs.AboutDialog(self.root, config.FONTS["preferred"])
