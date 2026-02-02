"""
Configuration and constants for the OMR Application.
"""

THEMES = {
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

DEFAULT_THEME = "nile_delta"

# Font configurations fallback logic should be handled i UI or here
# For now, let's keep it simple
FONTS = {
    "preferred": {
        "header": ("Montserrat", 32, "bold"),
        "mono": ("Courier New", 9),
        "label": ("Roboto", 10, "bold"),
        "name": ("Roboto", 18, "normal"),
        "title": ("Roboto", 12, "normal"),
        "quote": ("Georgia", 11, "italic"),
        "engine": ("Courier New", 8),
        "status": ("Segoe UI", 9),
        "total_score": ("Segoe UI", 12, "bold"),
        "results": ("Consolas", 9)
    },
    "fallback": {
        "header": ("Arial", 32, "bold"),
        "mono": ("Courier", 9),
        "label": ("Arial", 10, "bold"),
        "name": ("Arial", 18, "normal"),
        "title": ("Arial", 12, "normal"),
        "quote": ("Times New Roman", 11, "italic"),
        "engine": ("Courier", 8),
        "status": ("Arial", 9),
        "total_score": ("Arial", 12, "bold"),
        "results": ("Courier", 9)
    }
}
