# --- Filename: settings_ui.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class SettingsFrame(ttk.Frame):
    name = "Settings"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

    def build_ui(self):
        # Clear any old widgets before drawing
        for widget in self.winfo_children():
            widget.destroy()

        # Use a scrolled frame for content
        scrollable_frame = ttk.ScrolledFrame(self, autohide=True, padding=20)
        scrollable_frame.pack(fill=BOTH, expand=True)

        # --- Appearance Section ---
        theme_frame = ttk.Labelframe(scrollable_frame, text="Appearance", padding=15)
        theme_frame.pack(fill='x', expand=True)
        ttk.Label(theme_frame, text="Theme:").pack(side='left', padx=(0, 10))
        theme_selector = ttk.Combobox(master=theme_frame, values=self.controller.style.theme_names())
        theme_selector.pack(side='left', fill='x', expand=True)
        theme_selector.set(self.controller.style.theme_use())

        def change_theme(e):
            self.controller.style.theme_use(theme_selector.get())
        theme_selector.bind("<<ComboboxSelected>>", change_theme)

        # --- Add new settings sections here as needed ---