# --- Filename: smx_sound_creator.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import sys
import json

from sound_creator_ui import SoundCreatorFrame
from settings_ui import SettingsFrame

APP_VERSION = "1.0.0"
CONFIG_FILE = "config.json"

def get_resource_path(filename):
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'assets', filename)

class App(ttk.Window):
    def __init__(self, themename="superhero"):
        super().__init__(themename=themename)
        self.title(f"SMX Sound Creator v{APP_VERSION}")
        self.geometry("1200x750")

        try:
            icon_path = get_resource_path("smx_sound_creator.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not set application icon: {e}")

        # --- Data Management ---
        self.library_paths = []
        self.mod_data = {} # Will store {'category': ['mod1.zip', 'mod2.zip']}
        self.load_config()

        # --- UI Initialization ---
        self.nav_frame = ttk.Frame(self)
        self.nav_frame.pack(side="top", fill="x", padx=1, pady=1)
        self.nav_buttons = {}

        self.core_frames = ["Sound Creator", "Settings"]
        for name in self.core_frames:
            button = ttk.Button(
                self.nav_frame, text=name, command=lambda n=name: self.show_frame(n),
                bootstyle="secondary", padding=(0, 10)
            )
            button.pack(side="left", fill="x", expand=True, padx=(0, 1))
            self.nav_buttons[name] = button

        self.container = ttk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}

        for F in (SoundCreatorFrame, SettingsFrame):
            frame = F(self.container, self)
            self.frames[F.name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.scan_all_libraries() # Perform initial scan on startup
        self.show_frame("Sound Creator")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                self.library_paths = config_data.get("library_paths", [])
        except (FileNotFoundError, json.JSONDecodeError):
            self.library_paths = []

    def save_config(self):
        config_data = {"library_paths": self.library_paths}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)

    def update_library_paths(self, new_paths):
        self.library_paths = new_paths
        self.save_config()
        self.scan_all_libraries() # Re-scan whenever paths change

    def scan_all_libraries(self):
        self.mod_data.clear()
        sound_creator_frame = self.frames.get("Sound Creator")
        
        for lib_path in self.library_paths:
            if not os.path.isdir(lib_path):
                continue
            
            for item_name in os.listdir(lib_path):
                item_path = os.path.join(lib_path, item_name)
                if os.path.isdir(item_path): # This is a category folder
                    category_name = item_name
                    if category_name not in self.mod_data:
                        self.mod_data[category_name] = []
                    
                    # Look for mod .zip files inside the category folder
                    for mod_file in os.listdir(item_path):
                        if mod_file.lower().endswith('.zip'):
                            self.mod_data[category_name].append(mod_file)
        
        # After scanning, update the UI
        if sound_creator_frame:
            all_categories = sorted(list(self.mod_data.keys()))
            sound_creator_frame.update_categories(all_categories)
            sound_creator_frame.log(f"Scan complete. Found {len(all_categories)} categories.")

    def show_frame(self, page_name):
        if page_name in self.frames:
            frame = self.frames[page_name]
            if page_name == "Settings":
                frame.build_ui()
            frame.tkraise()
            for name, btn in self.nav_buttons.items():
                btn.config(bootstyle="primary" if name == page_name else "secondary")

    def on_closing(self):
        self.save_config()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()