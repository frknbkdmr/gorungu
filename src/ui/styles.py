"""
UI Styles Module - Centralized styling constants for GÖRÜNGÜ

This module contains all UI-related constants (colors, fonts, dimensions)
separated from functional logic to enable easy theming and consistency.
"""

import customtkinter as ctk


class Style:
    """
    Central style configuration class.
    All UI widgets should reference these constants for consistent styling.
    """
    
    # ==========================================================================
    # COLOR PALETTES
    # ==========================================================================
    
    THEMES = {
        "dark": {
            "bg_primary": "#1a1a2e",       # Main background
            "bg_secondary": "#16213e",     # Panel backgrounds
            "bg_tertiary": "#0f3460",      # Card backgrounds
            "accent": "#e94560",           # Primary accent (buttons, highlights)
            "accent_hover": "#ff6b6b",     # Accent on hover
            "text_primary": "#eaeaea",     # Main text
            "text_secondary": "#a0a0a0",   # Muted text
            "text_muted": "#6c757d",       # Very subtle text
            "success": "#00d25b",          # Success states
            "warning": "#ffab00",          # Warning states
            "error": "#fc424a",            # Error states
            "canvas": "#0d1b2a",           # Canvas background
            "border": "#2d3748",           # Border color
            "input_bg": "#1e293b",         # Input field backgrounds
        },
        "light": {
            "bg_primary": "#f8fafc",       # Main background
            "bg_secondary": "#ffffff",     # Panel backgrounds
            "bg_tertiary": "#f1f5f9",      # Card backgrounds
            "accent": "#3b82f6",           # Primary accent
            "accent_hover": "#2563eb",     # Accent on hover
            "text_primary": "#1e293b",     # Main text
            "text_secondary": "#64748b",   # Muted text
            "text_muted": "#94a3b8",       # Very subtle text
            "success": "#22c55e",          # Success states
            "warning": "#f59e0b",          # Warning states
            "error": "#ef4444",            # Error states
            "canvas": "#e2e8f0",           # Canvas background
            "border": "#e2e8f0",           # Border color
            "input_bg": "#ffffff",         # Input field backgrounds
        },
        "nile_delta": {
            "bg_primary": "#f5f7fa",       # Clinical background
            "bg_secondary": "#ffffff",     # Panel backgrounds
            "bg_tertiary": "#eef2f6",      # Card backgrounds
            "accent": "#0d47a1",           # Deep ocean blue
            "accent_hover": "#1565c0",     # Lighter blue on hover
            "text_primary": "#212121",     # Ink black
            "text_secondary": "#546e7a",   # Muted text
            "text_muted": "#90a4ae",       # Very subtle text
            "success": "#c5a572",          # Antique gold
            "warning": "#ff8f00",          # Warning
            "error": "#d32f2f",            # Error red
            "canvas": "#e0e0e0",           # Canvas background
            "border": "#cfd8dc",           # Border color
            "input_bg": "#ffffff",         # Input backgrounds
        }
    }
    
    # Current theme (can be changed at runtime)
    current_theme = "dark"
    
    # ==========================================================================
    # FONTS
    # ==========================================================================
    
    # Font families with fallbacks
    FONT_FAMILY_PRIMARY = "Segoe UI"
    FONT_FAMILY_MONO = "Consolas"
    FONT_FAMILY_HEADER = "Segoe UI"
    
    # Font configurations (family, size, weight)
    FONTS = {
        "header_xl": (FONT_FAMILY_HEADER, 26, "bold"),
        "header_lg": (FONT_FAMILY_HEADER, 20, "bold"),
        "header_md": (FONT_FAMILY_HEADER, 16, "bold"),
        "body": (FONT_FAMILY_PRIMARY, 12, "normal"),
        "body_bold": (FONT_FAMILY_PRIMARY, 12, "bold"),
        "small": (FONT_FAMILY_PRIMARY, 11, "normal"),
        "small_bold": (FONT_FAMILY_PRIMARY, 11, "bold"),
        "mono": (FONT_FAMILY_MONO, 12, "normal"),
        "mono_small": (FONT_FAMILY_MONO, 11, "normal"),
        "button": (FONT_FAMILY_PRIMARY, 12, "normal"),
        "score_display": (FONT_FAMILY_PRIMARY, 32, "bold"),
    }
    
    # ==========================================================================
    # DIMENSIONS
    # ==========================================================================
    
    # Panel widths
    PANEL_WIDTH_SM = 280
    PANEL_WIDTH_MD = 320
    PANEL_WIDTH_LG = 400
    
    # Padding and margins
    PADDING_XS = 5
    PADDING_SM = 10
    PADDING_MD = 15
    PADDING_LG = 20
    PADDING_XL = 30
    
    # Border radius
    CORNER_RADIUS_SM = 6
    CORNER_RADIUS_MD = 10
    CORNER_RADIUS_LG = 15
    
    # Button dimensions
    BUTTON_HEIGHT = 40      # Increased for safety
    BUTTON_HEIGHT_SM = 32   # Increased size
    
    # Input dimensions
    INPUT_HEIGHT = 34
    
    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================
    
    @classmethod
    def get_color(cls, color_name: str) -> str:
        """Get a color from the current theme."""
        return cls.THEMES[cls.current_theme].get(color_name, "#ffffff")
    
    @classmethod
    def get_theme_colors(cls) -> dict:
        """Get all colors for the current theme."""
        return cls.THEMES[cls.current_theme]
    
    @classmethod
    def set_theme(cls, theme_name: str):
        """Change the current theme."""
        if theme_name in cls.THEMES:
            cls.current_theme = theme_name
    
    @classmethod
    def configure_ctk_appearance(cls):
        """Configure customtkinter appearance based on current theme."""
        if cls.current_theme == "dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
        
        # Set default color theme
        ctk.set_default_color_theme("blue")
        
        # Set default scaling for better visibility
        # 1.1 is a safe slight boost without breaking layouts
        ctk.set_widget_scaling(1.1)
        ctk.set_window_scaling(1.1)


# ==========================================================================
# WIDGET FACTORY FUNCTIONS
# ==========================================================================

def create_section_header(parent, text: str) -> ctk.CTkFrame:
    """
    Create a styled section header with separator line.
    Returns the frame containing the header.
    """
    colors = Style.get_theme_colors()
    
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    
    label = ctk.CTkLabel(
        frame, 
        text=text,
        font=Style.FONTS["small_bold"],
        text_color=colors["text_muted"]
    )
    label.pack(side="left", padx=(0, Style.PADDING_SM))
    
    separator = ctk.CTkFrame(
        frame, 
        height=1, 
        fg_color=colors["border"]
    )
    separator.pack(side="left", fill="x", expand=True, pady=Style.PADDING_SM)
    
    return frame


def create_accent_button(parent, text: str, command=None, **kwargs) -> ctk.CTkButton:
    """Create a styled accent (primary) button."""
    colors = Style.get_theme_colors()
    
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        font=Style.FONTS["button"],
        fg_color=colors["accent"],
        hover_color=colors["accent_hover"],
        height=Style.BUTTON_HEIGHT,
        corner_radius=Style.CORNER_RADIUS_MD,
        **kwargs
    )


def create_secondary_button(parent, text: str, command=None, **kwargs) -> ctk.CTkButton:
    """Create a styled secondary button."""
    colors = Style.get_theme_colors()
    
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        font=Style.FONTS["button"],
        fg_color=colors["bg_tertiary"],
        hover_color=colors["border"],
        text_color=colors["text_primary"],
        height=Style.BUTTON_HEIGHT,
        corner_radius=Style.CORNER_RADIUS_MD,
        **kwargs
    )


def create_status_label(parent, text: str = "", status: str = "normal") -> ctk.CTkLabel:
    """
    Create a status label with color based on status type.
    status: "normal", "success", "warning", "error"
    """
    colors = Style.get_theme_colors()
    
    color_map = {
        "normal": colors["text_secondary"],
        "success": colors["success"],
        "warning": colors["warning"],
        "error": colors["error"],
    }
    
    return ctk.CTkLabel(
        parent,
        text=text,
        font=Style.FONTS["small"],
        text_color=color_map.get(status, colors["text_secondary"])
    )
