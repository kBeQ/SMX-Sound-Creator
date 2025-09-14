# --- Filename: smx_sound_creator.py ---
import tkinter as tk
from tkinter import filedialog, font, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame, ScrolledText
from PIL import Image, ImageTk
import os
import sys
import json

from settings_ui import SettingsFrame

APP_VERSION = "1.0.0"
CONFIG_FILE = "config.json"

def get_resource_path(filename):
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'assets', filename)

class SoundCreatorFrame(ttk.Frame):
    name = "Sound Creator"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.bold_font = font.Font(family="Helvetica", size=10, weight="bold")
        
        self.mod_name_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.engine_wav_var = tk.StringVar()
        self.idle_wav_var = tk.StringVar()
        self.low_wav_var = tk.StringVar()
        self.high_wav_var = tk.StringVar()
        self.preview_image_var = tk.StringVar()
        self.output_mode_var = tk.StringVar(value="new")
        self.bike_vars = {}
        self.bike_images = {} # To prevent garbage collection

        self.build_ui()
        
    def build_ui(self):
        # --- Main Layout: Paned Window (Top Controls, Bottom Log) ---
        main_pane = ttk.PanedWindow(self, orient=VERTICAL)
        main_pane.pack(fill=BOTH, expand=True, padx=15, pady=15)

        # --- TOP PANE: All user controls ---
        top_frame = ttk.Frame(main_pane)
        main_pane.add(top_frame, weight=4)
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_rowconfigure(2, weight=1)

        # --- LEFT COLUMN: Details, Files, Output ---
        left_col_frame = ttk.Frame(top_frame)
        left_col_frame.grid(row=0, column=0, rowspan=3, sticky='nsew', padx=(0, 15))

        details_frame = ttk.Labelframe(left_col_frame, text="1. Mod Details", padding=15)
        details_frame.pack(fill=X, pady=(0, 10))
        details_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(details_frame, text="Bike Name/Model:").grid(row=0, column=0, sticky=W, pady=2)
        ttk.Entry(details_frame, textvariable=self.mod_name_var).grid(row=0, column=1, sticky=EW, padx=5)
        ttk.Label(details_frame, text="Author:").grid(row=1, column=0, sticky=W, pady=2)
        ttk.Entry(details_frame, textvariable=self.author_var).grid(row=1, column=1, sticky=EW, padx=5)

        sounds_frame = ttk.Labelframe(left_col_frame, text="2. Sound Files (.wav)", padding=15)
        sounds_frame.pack(fill=X, pady=(0, 10))
        self.create_file_input_row(sounds_frame, "Engine:", self.engine_wav_var, 0)
        self.create_file_input_row(sounds_frame, "Idle:", self.idle_wav_var, 1)
        self.create_file_input_row(sounds_frame, "Low RPM:", self.low_wav_var, 2)
        self.create_file_input_row(sounds_frame, "High RPM:", self.high_wav_var, 3)
        
        preview_frame = ttk.Labelframe(left_col_frame, text="3. Optional Preview", padding=15)
        preview_frame.pack(fill=X, pady=(0, 10))
        self.create_file_input_row(preview_frame, "Image:", self.preview_image_var, 0, file_types=[("Image", "*.jpg *.png")])

        output_frame = ttk.Labelframe(left_col_frame, text="5. Output Location", padding=15)
        output_frame.pack(fill=X, pady=(0, 10))
        output_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(output_frame, text="Library:").grid(row=0, column=0, sticky=W, pady=(0, 5))
        self.library_selector = ttk.Combobox(output_frame, state="readonly")
        self.library_selector.grid(row=0, column=1, sticky=EW, padx=5)
        self.library_selector.bind("<<ComboboxSelected>>", self._on_library_select)
        ttk.Separator(output_frame).grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        mode_frame = ttk.Frame(output_frame)
        mode_frame.grid(row=2, column=0, columnspan=2, sticky='w')

        # --- FIX IS ON THESE TWO LINES: changed 'cmd' to 'command' ---
        ttk.Radiobutton(mode_frame, text="New Mod", var=self.output_mode_var, value="new", command=self._on_output_mode_change).pack(side=LEFT)
        ttk.Radiobutton(mode_frame, text="Existing Mod", var=self.output_mode_var, value="existing", command=self._on_output_mode_change).pack(side=LEFT, padx=10)
        
        ttk.Label(output_frame, text="Mod Name:").grid(row=3, column=0, sticky=W, pady=2)
        self.new_mod_name_entry = ttk.Entry(output_frame)
        self.new_mod_name_entry.grid(row=3, column=1, sticky=EW, padx=5)
        self.existing_mod_selector = ttk.Combobox(output_frame, state="readonly")
        self.existing_mod_selector.grid(row=3, column=1, sticky=EW, padx=5)

        self.create_button = ttk.Button(left_col_frame, text="Create Sound Mod Package", command=self.create_mod_package)
        self.create_button.pack(fill=X, pady=10, ipady=10)

        # --- RIGHT COLUMN: Bike Selection ---
        bikes_container = ttk.Labelframe(top_frame, text="4. Bikes to Include", padding=15)
        bikes_container.grid(row=0, column=1, rowspan=3, sticky='nsew')
        self.populate_bikes_frame(bikes_container)

        # --- BOTTOM PANE: Log Output ---
        log_frame = ttk.Frame(main_pane)
        main_pane.add(log_frame, weight=1)
        log_header = ttk.Frame(log_frame)
        log_header.pack(fill=X, pady=(5, 5))
        ttk.Label(log_header, text="Log Output", font=self.bold_font).pack(side=LEFT)
        self.log_output_text = ScrolledText(log_frame, wrap=tk.WORD, autohide=True, height=4)
        self.log_output_text.pack(expand=True, fill=BOTH)

    def populate_bikes_frame(self, parent):
        bikes_scrolled_frame = ScrolledFrame(parent, autohide=True)
        bikes_scrolled_frame.pack(fill=BOTH, expand=True)

        bike_list = ["Y250", "Y450", "E", "GRF250", "GRF450", "RM250", "RM450", "KW250", 
                     "KW450", "KTSX250", "KTSX450", "KTST250", "T250", "T450"]
        
        thumb_path = self.controller.get_thumbnail_path()
        cols = 4 # Number of columns for the grid

        for i, bike_name in enumerate(bike_list):
            var = tk.BooleanVar()
            self.bike_vars[bike_name] = var
            
            item_frame = ttk.Frame(bikes_scrolled_frame)
            item_frame.grid(row=i//cols, column=i%cols, padx=10, pady=5, sticky='w')
            
            # --- Thumbnail ---
            img_path = os.path.join(thumb_path, f"{bike_name}.png") if thumb_path else ""
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    img.thumbnail((48, 48), Image.Resampling.LANCZOS)
                    self.bike_images[bike_name] = ImageTk.PhotoImage(img)
                    ttk.Label(item_frame, image=self.bike_images[bike_name]).pack(side=LEFT)
                except Exception as e:
                    print(f"Error loading image {img_path}: {e}")

            cb = ttk.Checkbutton(item_frame, text=bike_name, variable=var, bootstyle="round-toggle")
            cb.pack(side=LEFT, padx=5)

    def create_file_input_row(self, parent, label_text, string_var, row_num, file_types=[("WAV", "*.wav")]):
        parent.grid_columnconfigure(1, weight=1)
        ttk.Label(parent, text=label_text).grid(row=row_num, column=0, sticky=W, pady=3)
        entry = ttk.Entry(parent, textvariable=string_var, state="readonly")
        entry.grid(row=row_num, column=1, sticky=EW, padx=5)
        button = ttk.Button(parent, text="...", bootstyle="outline", width=4, command=lambda: self.browse_for_file(string_var, file_types))
        button.grid(row=row_num, column=2)

    def browse_for_file(self, string_var, file_types):
        file_path = filedialog.askopenfilename(filetypes=file_types)
        if file_path:
            string_var.set(file_path)
            self.log(f"Selected: {os.path.basename(file_path)}")

    def update_output_options(self, mod_data):
        lib_paths = list(mod_data.keys())
        lib_display_names = [os.path.basename(p) for p in lib_paths]
        self.library_selector['values'] = lib_display_names
        
        if lib_display_names:
            self.library_selector.set(lib_display_names[0])
            self.create_button.config(state=tk.NORMAL)
            self._on_library_select()
        else:
            self.library_selector.set('')
            self.create_button.config(state=tk.DISABLED)
            self.log("Warning: No libraries in Settings. Cannot save mods.")
        self._on_output_mode_change()

    def _on_library_select(self, event=None):
        lib_name = self.library_selector.get()
        full_path = self.controller.get_full_library_path(lib_name)
        if full_path:
            mod_folders = self.controller.get_mods_for_library(full_path)
            self.existing_mod_selector['values'] = mod_folders
            if mod_folders: self.existing_mod_selector.set(mod_folders[0])
            else: self.existing_mod_selector.set('')

    def _on_output_mode_change(self):
        if self.output_mode_var.get() == "new":
            self.new_mod_name_entry.grid(row=3, column=1, sticky=EW, padx=5)
            self.existing_mod_selector.grid_forget()
        else:
            self.new_mod_name_entry.grid_forget()
            self.existing_mod_selector.grid(row=3, column=1, sticky=EW, padx=5)

    def create_mod_package(self):
        self.log("\n--- Starting Mod Creation Process ---")
        selected_bikes = [name for name, var in self.bike_vars.items() if var.get()]
        if not selected_bikes:
            self.log("ERROR: No bikes were selected!")
            return
            
        self.log(f"Bikes to include: {', '.join(selected_bikes)}")
        self.log("ERROR: Packaging logic has not been implemented yet.")

    def log(self, msg):
        self.log_output_text.text.config(state='normal')
        self.log_output_text.insert(tk.END, str(msg).strip() + "\n")
        self.log_output_text.see(tk.END)
        self.log_output_text.text.config(state='disabled')

class App(ttk.Window):
    def __init__(self, themename="superhero"):
        super().__init__(themename=themename)
        self.title(f"SMX Sound Creator v{APP_VERSION}")
        self.geometry("1400x850")

        try:
            icon_path = get_resource_path("smx_sound_creator.ico")
            if os.path.exists(icon_path): self.iconbitmap(icon_path)
        except Exception as e: print(f"Could not set icon: {e}")

        self.library_paths = []
        self.thumbnail_folder_path = ""
        self.mod_data = {}
        self.load_config()

        self.nav_frame = ttk.Frame(self)
        self.nav_frame.pack(side="top", fill="x", padx=1, pady=1)
        self.nav_buttons = {}
        self.core_frames = ["Sound Creator", "Settings"]
        for name in self.core_frames:
            btn = ttk.Button(self.nav_frame, text=name, command=lambda n=name: self.show_frame(n), bootstyle="secondary", padding=(0, 10))
            btn.pack(side="left", fill="x", expand=True, padx=(0, 1))
            self.nav_buttons[name] = btn

        self.container = ttk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_row_configure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}

        for F in (SoundCreatorFrame, SettingsFrame):
            frame = F(self.container, self)
            self.frames[F.name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.scan_all_libraries()
        self.show_frame("Sound Creator")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.library_paths = config.get("library_paths", [])
                self.thumbnail_folder_path = config.get("thumbnail_folder_path", "")
        except (FileNotFoundError, json.JSONDecodeError): pass

    def save_config(self):
        config = {
            "library_paths": self.library_paths,
            "thumbnail_folder_path": self.thumbnail_folder_path
        }
        with open(CONFIG_FILE, 'w') as f: json.dump(config, f, indent=4)

    def update_library_paths(self, new_paths):
        self.library_paths = new_paths
        self.scan_all_libraries()

    def set_thumbnail_path(self, new_path):
        self.thumbnail_folder_path = new_path
        # Re-populate the bikes frame to show new images
        self.frames["Sound Creator"].populate_bikes_frame(self.frames["Sound Creator"].winfo_children()[0].winfo_children()[0].winfo_children()[1])

    def get_library_paths(self): return self.library_paths
    def get_thumbnail_path(self): return self.thumbnail_folder_path
    def get_full_library_path(self, name): return next((p for p in self.mod_data.keys() if os.path.basename(p) == name), None)
    def get_mods_for_library(self, full_path): return sorted(list(self.mod_data.get(full_path, {}).keys()))

    def scan_all_libraries(self):
        self.mod_data.clear()
        for lib_path in self.library_paths:
            if os.path.isdir(lib_path):
                self.mod_data[lib_path] = {}
                for mod_folder in os.listdir(lib_path):
                    if os.path.isdir(os.path.join(lib_path, mod_folder)):
                        self.mod_data[lib_path][mod_folder] = []
        self.frames["Sound Creator"].update_output_options(self.mod_data)

    def show_frame(self, page_name):
        if page_name in self.frames:
            frame = self.frames[page_name]
            if page_name == "Settings": frame.build_ui()
            frame.tkraise()
            for name, btn in self.nav_buttons.items():
                btn.config(bootstyle="primary" if name == page_name else "secondary")

    def on_closing(self):
        self.save_config()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()