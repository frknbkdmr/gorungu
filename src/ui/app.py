"""
Main Application Module - GÖRÜNGÜ OMR Application

Modernized with customtkinter for a professional, themed UI experience.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

from src import config
from src.ui import designer, scanner, dialogs
from src.ui.styles import Style


class OMRApp:
    """
    Main application class that manages the UI modes and theme.
    """
    
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("GÖRÜNGÜ - Powered by Thoth Engine")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Try to increase menu font size (platform dependent)
        self.root.option_add("*Menu.font", "SegoeUI 12")
        
        print("[APP] GÖRÜNGÜ başlatılıyor...")
        
        # Initialize style system
        Style.configure_ctk_appearance()
        self.colors = Style.get_theme_colors()
        
        # State
        self.current_mode = None  # "DESIGNER" or "SCANNER"
        self.mode_instance = None  # Instance of DesignerMode or ScannerMode
        
        # Configure root window appearance
        self.root.configure(fg_color=self.colors["bg_primary"])
        
        # Main content frame
        self.main_frame = ctk.CTkFrame(
            self.root, 
            fg_color=self.colors["bg_primary"],
            corner_radius=0
        )
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Status bar at bottom
        self.status_frame = ctk.CTkFrame(
            self.root, 
            height=32, 
            fg_color=self.colors["bg_secondary"],
            corner_radius=0
        )
        self.status_frame.pack(side="bottom", fill="x")
        self.status_frame.pack_propagate(False)
        
        self.status_var = tk.StringVar(value="Hazır")
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            textvariable=self.status_var,
            font=Style.FONTS["small"],
            text_color=self.colors["text_secondary"],
            anchor="w"
        )
        self.status_label.pack(side="left", padx=Style.PADDING_MD, pady=Style.PADDING_XS)
        
        # Theme indicator in status bar
        self.theme_indicator = ctk.CTkLabel(
            self.status_frame,
            text=f"Tema: {Style.current_theme.replace('_', ' ').title()}",
            font=Style.FONTS["small"],
            text_color=self.colors["text_muted"]
        )
        self.theme_indicator.pack(side="right", padx=Style.PADDING_MD, pady=Style.PADDING_XS)
        
        # Setup menu
        self.setup_menu()
        
        # Start in Designer Mode
        self.switch_to_designer()

    def setup_menu(self):
        """Setup the application menu bar."""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Mode Menu
        self.mode_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Mod", menu=self.mode_menu)
        self.mode_menu.add_command(label="🎨 Tasarımcı Modu", command=self.switch_to_designer)
        self.mode_menu.add_command(label="📷 Tarayıcı Modu", command=self.switch_to_scanner)
        
        # View Menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Görünüm", menu=self.view_menu)
        
        # Theme Submenu
        self.theme_menu = tk.Menu(self.view_menu, tearoff=0)
        self.view_menu.add_cascade(label="Tema", menu=self.theme_menu)
        
        theme_icons = {"dark": "🌙", "light": "☀️", "nile_delta": "🏛️"}
        for theme_name in Style.THEMES.keys():
            icon = theme_icons.get(theme_name, "")
            display_name = f"{icon} {theme_name.replace('_', ' ').title()}"
            self.theme_menu.add_command(
                label=display_name, 
                command=lambda t=theme_name: self.set_theme(t)
            )
            
        self.view_menu.add_separator()
        self.view_menu.add_command(label="ℹ️ Hakkında", command=self.show_about)
        
        # Help Menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Yardım", menu=self.help_menu)
        self.help_menu.add_command(label="📖 Hakkında GÖRÜNGÜ", command=self.show_about)

    def clear_frame(self):
        """Clear all widgets from the main frame."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def set_theme(self, theme_name: str):
        """Change the application theme."""
        if theme_name in Style.THEMES:
            print(f"[APP] Tema değişti: {theme_name}")
            Style.set_theme(theme_name)
            Style.configure_ctk_appearance()
            self.colors = Style.get_theme_colors()
            self.apply_theme()
            
            # Rebuild current mode UI
            if self.mode_instance:
                self.clear_frame()
                self.mode_instance.colors = self.colors
                self.mode_instance.setup_ui(self.main_frame)

    def apply_theme(self):
        """Apply current theme colors to the application."""
        self.root.configure(fg_color=self.colors["bg_primary"])
        self.main_frame.configure(fg_color=self.colors["bg_primary"])
        self.status_frame.configure(fg_color=self.colors["bg_secondary"])
        self.status_label.configure(text_color=self.colors["text_secondary"])
        self.theme_indicator.configure(
            text=f"Tema: {Style.current_theme.replace('_', ' ').title()}",
            text_color=self.colors["text_muted"]
        )

    def switch_to_designer(self):
        """Switch to Designer Mode."""
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
        """Switch to Scanner Mode."""
        self.current_mode = "SCANNER"
        self.clear_frame()
        self.root.title("GÖRÜNGÜ - Tarayıcı Modu (Manuel)")
        print("[APP] Mod değişti: TARAYICI")
        self.status_var.set("Tarayıcı Modu: Başlamak için şablon ve resimleri yükleyin.")
        
        self.mode_instance = scanner.ScannerMode(self)
        self.mode_instance.setup_ui(self.main_frame)
        
        # Key events are inherently routed to the active mode safely.

    def on_key_press(self, event):
        """Route key press to active mode if it handles it."""
        if self.current_mode == "DESIGNER" and hasattr(self.mode_instance, 'on_key_press'):
            # Check if focus is on an entry widget to avoid conflict
            focused = self.root.focus_get()
            if isinstance(focused, (tk.Entry, tk.Text, ctk.CTkEntry, ctk.CTkTextbox)):
                return
            self.mode_instance.on_key_press(event)

    def show_about(self):
        """Show the About dialog."""
        dialogs.AboutDialog(self.root, config.FONTS["preferred"])
