# --- Filename: src/settings_ui.py ---
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame

class SettingsFrame(ttk.Frame):
    name = "Settings"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

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
        for path in self.controller.get_library_paths():
            self.library_listbox.insert(tk.END, path)
        btn_frame = ttk.Frame(lib_frame)
        btn_frame.pack(fill='x', pady=(5,0))
        ttk.Button(btn_frame, text="Add Folder...", command=self.add_library_folder, bootstyle="outline").pack(side='left')
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_library_folder, bootstyle="outline-danger").pack(side='left', padx=5)

        asset_frame = ttk.Labelframe(scrollable_frame, text="Asset Configuration", padding=15)
        asset_frame.pack(fill='x', expand=True, pady=(0, 20))
        asset_frame.grid_column_configure(1, weight=1)
        
        ttk.Label(asset_frame, text="Bike Thumbnails Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.thumbnail_path_var = tk.StringVar(value=self.controller.get_setting("thumbnail_folder_path", ""))
        ttk.Entry(asset_frame, textvariable=self.thumbnail_path_var, state="readonly").grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Button(asset_frame, text="Browse...", command=self.browse_for_thumbnail_folder, bootstyle="outline").grid(row=0, column=2)

        ttk.Label(asset_frame, text="Preview Background Image:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.background_path_var = tk.StringVar(value=self.controller.get_setting("background_path", ""))
        ttk.Entry(asset_frame, textvariable=self.background_path_var, state="readonly").grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Button(asset_frame, text="Browse...", command=self.browse_for_background_image, bootstyle="outline").grid(row=1, column=2)

        theme_frame = ttk.Labelframe(scrollable_frame, text="Appearance", padding=15)
        theme_frame.pack(fill='x', expand=True)
        ttk.Label(theme_frame, text="Theme:").pack(side='left', padx=(0, 10))
        theme_selector = ttk.Combobox(master=theme_frame, values=self.controller.style.theme_names())
        theme_selector.pack(side='left', fill='x', expand=True)
        theme_selector.set(self.controller.style.theme_use())
        def change_theme(e): self.controller.style.theme_use(theme_selector.get())
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
        self.controller.update_library_paths(list(new_paths))

    def browse_for_thumbnail_folder(self):
        folder = filedialog.askdirectory(title="Select Folder Containing Bike Thumbnails")
        if folder:
            self.thumbnail_path_var.set(folder)
            self.controller.update_setting("thumbnail_folder_path", folder)

    def browse_for_background_image(self):
        filetypes = [("Image Files", "*.png *.jpg *.jpeg *.bmp")]
        path = filedialog.askopenfilename(title="Select Background Image for Preview", filetypes=filetypes)
        if path:
            self.background_path_var.set(path)
            self.controller.update_setting("background_path", path)