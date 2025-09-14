# --- Filename: smx_sound_creator.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import sys
import json

# Import the UI frames for the tabs
from sound_creator_ui import SoundCreatorFrame
from settings_ui import SettingsFrame

APP_VERSION = "1.0.0"

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

        # --- Simplified Navigation ---
        self.nav_frame = ttk.Frame(self)
        self.nav_frame.pack(side="top", fill="x", padx=1, pady=1)
        self.nav_buttons = {}

        # Define the core tabs for the application
        self.core_frames = ["Sound Creator", "Settings"]
        for name in self.core_frames:
            button = ttk.Button(
                self.nav_frame,
                text=name,
                command=lambda n=name: self.show_frame(n),
                bootstyle="secondary",
                padding=(0, 10)
            )
            button.pack(side="left", fill="x", expand=True, padx=(0, 1))
            self.nav_buttons[name] = button

        # --- Frame Container ---
        self.container = ttk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}

        # Create and store the frame instances for each tab
        for F in (SoundCreatorFrame, SettingsFrame):
            frame = F(self.container, self)
            self.frames[F.name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("Sound Creator") # Show the main tool tab by default
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def show_frame(self, page_name):
        if page_name in self.frames:
            frame = self.frames[page_name]
            # Rebuild settings UI each time it's viewed
            if page_name == "Settings":
                frame.build_ui()
            frame.tkraise()
            # Update button styles to show the active tab
            for name, btn in self.nav_buttons.items():
                btn.config(bootstyle="primary" if name == page_name else "secondary")

if __name__ == "__main__":
    app = App()
    app.mainloop()