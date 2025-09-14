# --- Filename: settings_ui.py ---
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame

class SettingsFrame(ttk.Frame):
    name = "Settings"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller # The controller is the main App instance

    def build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        scrollable_frame = ScrolledFrame(self, autohide=True, padding=20)
        scrollable_frame.pack(fill=BOTH, expand=True)

        lib_frame = ttk.Labelframe(scrollable_frame, text="Local Mod Libraries (Categories)", padding=15)
        lib_frame.pack(fill='x', expand=True, pady=(0, 20))
        ttk.Label(lib_frame, text="Add folders that represent your top-level categories (e.g., '4-Strokes').").pack(anchor='w')
        
        list_frame = ttk.Frame(lib_frame)
        list_frame.pack(fill='x', expand=True, pady=10)

        self.library_listbox = tk.Listbox(list_frame, height=5)
        self.library_listbox.pack(side='left', fill='x', expand=True)

        # --- UPDATED: Get paths from the SoundCreatorFrame ---
        sound_creator_frame = self.controller.frames.get("Sound Creator")
        if sound_creator_frame:
            for path in sound_creator_frame.library_paths:
                self.library_listbox.insert(tk.END, path)
            
        btn_frame = ttk.Frame(lib_frame)
        btn_frame.pack(fill='x', pady=(5,0))
        ttk.Button(btn_frame, text="Add Folder...", command=self.add_library_folder, bootstyle="outline").pack(side='left')
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_library_folder, bootstyle="outline-danger").pack(side='left', padx=5)

        theme_frame = ttk.Labelframe(scrollable_frame, text="Appearance", padding=15)
        theme_frame.pack(fill='x', expand=True)
        ttk.Label(theme_frame, text="Theme:").pack(side='left', padx=(0, 10))
        
        theme_selector = ttk.Combobox(master=theme_frame, values=self.controller.style.theme_names())
        theme_selector.pack(side='left', fill='x', expand=True)
        theme_selector.set(self.controller.style.theme_use())

        def change_theme(e):
            self.controller.style.theme_use(theme_selector.get())
        theme_selector.bind("<<ComboboxSelected>>", change_theme)

    def add_library_folder(self):
        folder = filedialog.askdirectory(title="Select a Library Folder")
        if not folder: return
        current_libs = self.library_listbox.get(0, tk.END)
        if folder in current_libs:
            messagebox.showinfo("Duplicate", "That folder is already in the library.")
            return
        self.library_listbox.insert(tk.END, folder)
        self.save_library_changes()

    def remove_library_folder(self):
        selections = self.library_listbox.curselection()
        if not selections:
            messagebox.showwarning("No Selection", "Please select a folder to remove.")
            return
        for index in reversed(selections):
            self.library_listbox.delete(index)
        self.save_library_changes()

    def save_library_changes(self):
        new_paths = self.library_listbox.get(0, tk.END)
        # --- UPDATED: Call the function on the SoundCreatorFrame instance ---
        sound_creator_frame = self.controller.frames.get("Sound Creator")
        if sound_creator_frame:
            sound_creator_frame.update_library_paths(list(new_paths))