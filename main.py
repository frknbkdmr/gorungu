"""
GÖRÜNGÜ - Main Entry Point

Modern OMR (Optical Mark Recognition) application with splash screen.
"""

import customtkinter as ctk
import os
from PIL import Image
import time

from src.ui.app import OMRApp
from src.ui.styles import Style


def show_splash_screen(root: ctk.CTk):
    """
    Display a modern splash screen with progress indicator.
    """
    try:
        # Find splash image
        splash_img_path = "thoth.jpg"
        if not os.path.exists(splash_img_path):
            if os.path.exists(os.path.join("examples", "thoth.jpg")):
                splash_img_path = os.path.join("examples", "thoth.jpg")
            else:
                print("[SPLASH] Image not found, skipping splash")
                return

        # Load and resize image first
        pil_img = Image.open(splash_img_path)
        pil_img.thumbnail((650, 450))
        w, h = pil_img.size
        
        # Create CTkImage
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
        
        # Calculate window position
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_height = h + 100  # Extra for text and progress
        x = (screen_width - w) // 2
        y = (screen_height - window_height) // 2
        
        # Create splash window
        splash = ctk.CTkToplevel(root)
        splash.title("GÖRÜNGÜ")
        splash.geometry(f"{w}x{window_height}+{x}+{y}")
        splash.overrideredirect(True)
        splash.configure(fg_color="#0d1117")
        splash.attributes("-topmost", True)
        
        # Force splash to appear
        splash.lift()
        splash.focus_force()
        root.update_idletasks()
        splash.update()
        
        # Image label
        lbl_img = ctk.CTkLabel(splash, image=ctk_img, text="")
        lbl_img.pack(fill="both", expand=True, pady=(10, 0))
        
        # Title
        lbl_title = ctk.CTkLabel(
            splash, 
            text="GÖRÜNGÜ", 
            font=("Courier New", 24, "bold"), 
            text_color="#ffffff"
        )
        lbl_title.pack(pady=(5, 0))
        
        # Subtitle
        lbl_subtitle = ctk.CTkLabel(
            splash, 
            text="Powered by Thoth Engine", 
            font=("Courier New", 10), 
            text_color="#c5a572"
        )
        lbl_subtitle.pack(pady=(0, 5))
        
        # Progress bar
        progress = ctk.CTkProgressBar(
            splash, 
            width=280, 
            height=4,
            fg_color="#1a1a2e",
            progress_color="#e94560",
            corner_radius=2
        )
        progress.pack(pady=(0, 15))
        progress.set(0)
        
        # Force display
        splash.update()
        
        # Animate progress bar
        steps = 15
        for i in range(steps + 1):
            progress.set(i / steps)
            splash.update()
            time.sleep(0.05)
        
        # Brief pause at 100%
        time.sleep(0.2)
        
        # Destroy splash
        splash.destroy()
        root.update()
        
    except Exception as e:
        print(f"[SPLASH] Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point for the application."""
    # Configure appearance before creating window
    Style.configure_ctk_appearance()
    
    # Create root window
    root = ctk.CTk()
    root.withdraw()  # Hide during splash
    
    # Show splash screen
    show_splash_screen(root)
    
    # Initialize application
    app = OMRApp(root)
    
    # Show main window
    root.deiconify()
    root.lift()
    root.focus_force()
    
    # Start event loop
    root.mainloop()


if __name__ == "__main__":
    main()
