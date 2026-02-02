
import tkinter as tk
import os
from PIL import Image, ImageTk
import time

from src.ui.app import OMRApp

def show_splash_screen(root):
    """
    Displays splash screen with thoth.jpg if available.
    """
    try:
        # Check if thoth.jpg exists in current dir or assets
        splash_img_path = "thoth.jpg"
        if not os.path.exists(splash_img_path):
             # Try to find it in examples if not in root
            if os.path.exists(os.path.join("examples", "thoth.jpg")):
                splash_img_path = os.path.join("examples", "thoth.jpg")
            else:
                return

        splash = tk.Toplevel(root)
        splash.overrideredirect(True) # No decorations
        
        pil_img = Image.open(splash_img_path)
        pil_img.thumbnail((600, 400))
        img = ImageTk.PhotoImage(pil_img)
        
        w, h = pil_img.size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - w) // 2
        y = (screen_height - h) // 2
        splash.geometry(f"{w}x{h}+{x}+{y}")
        
        lbl_img = tk.Label(splash, image=img, bg="black")
        lbl_img.image = img # Keep reference
        lbl_img.pack(fill=tk.BOTH, expand=True)
        
        # Overlay text
        lbl_title = tk.Label(splash, text="GÖRÜNGÜ", font=("Courier New", 24, "bold"), bg="black", fg="white")
        lbl_title.place(relx=0.5, rely=0.8, anchor=tk.CENTER)
        
        lbl_subtitle = tk.Label(splash, text="Powered by Thoth Engine", font=("Courier New", 10), bg="black", fg="#C5A572")
        lbl_subtitle.place(relx=0.5, rely=0.9, anchor=tk.CENTER)
        
        splash.update()
        time.sleep(2) # Show for 2 seconds
        splash.destroy()
        
    except Exception as e:
        print(f"Splash error: {e}")

def main():
    root = tk.Tk()
    root.withdraw() # Hide root during splash
    
    show_splash_screen(root)
    
    root.deiconify() # Show root
    app = OMRApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
