# --- Filename: smx_sound_creator.py ---
import tkinter as tk
from tkinter import filedialog, font, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame, ScrolledText
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import sys
import json
from tkinterdnd2 import DND_FILES, TkinterDnD

from settings_ui import SettingsFrame

APP_VERSION = "1.0.0"
CONFIG_FILE = "config.json"

def get_resource_path(filename):
    if getattr(sys, "frozen", False): base_dir = sys._MEIPASS
    else: base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'assets', filename)

class SoundCreatorFrame(ttk.Frame):
    name = "Sound Creator"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.bold_font = font.Font(family="Helvetica", size=10, weight="bold")
        
        self.engine_wav_var = tk.StringVar()
        self.idle_wav_var = tk.StringVar()
        self.low_wav_var = tk.StringVar()
        self.high_wav_var = tk.StringVar()
        self.preview_image_var = tk.StringVar()
        self.output_mode_var = tk.StringVar(value="new")
        self.bike_vars = {}
        self.bike_images = {}
        self.placeholder_image = None
        self.bikes_container_frame = None

        self.engine_status_var = tk.StringVar(value="❌")
        self.idle_status_var = tk.StringVar(value="❌")
        self.low_status_var = tk.StringVar(value="❌")
        self.high_status_var = tk.StringVar(value="❌")
        
        self.log_is_visible = tk.BooleanVar(value=False)

        self.build_ui()
        
    def build_ui(self):
        main_pane = ttk.PanedWindow(self, orient=HORIZONTAL)
        main_pane.pack(fill=BOTH, expand=True, padx=15, pady=(5, 15))

        left_pane = ttk.Frame(main_pane)
        main_pane.add(left_pane, weight=1)
        left_pane.grid_rowconfigure(0, weight=1)
        left_pane.grid_columnconfigure(0, weight=1)

        left_scrolled_frame = ScrolledFrame(left_pane, autohide=True)
        left_scrolled_frame.grid(row=0, column=0, sticky='nsew')
        
        sounds_frame = ttk.Labelframe(left_scrolled_frame, text="1. Sound Files (.wav)", padding=15)
        sounds_frame.pack(fill=X, pady=(0, 10))

        # --- THE FIX IS HERE: Changed relief to "solid" and borderwidth to 1 ---
        self.drop_target = ttk.Label(
            sounds_frame, text="\nDrop engine, idle, low, and high .wav files here\n",
            bootstyle="inverse-secondary", anchor=CENTER, relief="solid", borderwidth=1
        )
        self.drop_target.pack(fill=X, pady=5)
        self.drop_target.drop_target_register(DND_FILES)
        self.drop_target.dnd_bind('<<DND_Enter>>', self._on_dnd_enter)
        self.drop_target.dnd_bind('<<DND_Leave>>', self._on_dnd_leave)
        self.drop_target.dnd_bind('<<DND_Drop>>', self._on_dnd_drop)
        
        status_frame = ttk.Frame(sounds_frame)
        status_frame.pack(fill=X, pady=(10, 5))
        self.create_status_row(status_frame, "engine.wav:", self.engine_status_var, 0)
        self.create_status_row(status_frame, "idle.wav:", self.idle_status_var, 1)
        self.create_status_row(status_frame, "low.wav:", self.low_status_var, 2)
        self.create_status_row(status_frame, "high.wav:", self.high_status_var, 3)

        preview_frame = ttk.Labelframe(left_scrolled_frame, text="2. Optional Preview", padding=15)
        preview_frame.pack(fill=X, pady=(0, 10))
        self.create_file_input_row(preview_frame, "Image:", self.preview_image_var, 0, file_types=[("Image", "*.jpg *.png")])

        output_frame = ttk.Labelframe(left_scrolled_frame, text="3. Output Location", padding=15)
        output_frame.pack(fill=X, pady=(0, 10))
        output_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(output_frame, text="Library:").grid(row=0, column=0, sticky=W, pady=(0, 5))
        self.library_selector = ttk.Combobox(output_frame, state="readonly")
        self.library_selector.grid(row=0, column=1, sticky=EW, padx=5)
        self.library_selector.bind("<<ComboboxSelected>>", self._on_library_select)
        ttk.Separator(output_frame).grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        mode_frame = ttk.Frame(output_frame)
        mode_frame.grid(row=2, column=0, columnspan=2, sticky='w')
        ttk.Radiobutton(mode_frame, text="New Mod", var=self.output_mode_var, value="new", command=self._on_output_mode_change).pack(side=LEFT)
        ttk.Radiobutton(mode_frame, text="Existing Mod", var=self.output_mode_var, value="existing", command=self._on_output_mode_change).pack(side=LEFT, padx=10)
        ttk.Label(output_frame, text="Mod Name:").grid(row=3, column=0, sticky=W, pady=2)
        self.new_mod_name_entry = ttk.Entry(output_frame)
        self.new_mod_name_entry.grid(row=3, column=1, sticky=EW, padx=5)
        self.existing_mod_selector = ttk.Combobox(output_frame, state="readonly")
        self.existing_mod_selector.grid(row=3, column=1, sticky=EW, padx=5)

        self.create_button = ttk.Button(left_scrolled_frame, text="Create Sound Mod Package", command=self.create_mod_package)
        self.create_button.pack(fill=X, pady=10, ipady=10)

        log_container = ttk.Frame(left_pane)
        log_container.grid(row=1, column=0, sticky='ew')
        self.log_is_visible = tk.BooleanVar(value=False)
        log_header = ttk.Checkbutton(log_container, text="Show Log", variable=self.log_is_visible, command=self.toggle_log, bootstyle="info-toolbutton")
        log_header.pack(fill=X)
        self.log_output_text = ScrolledText(log_container, wrap=tk.WORD, autohide=True, height=5, padding=10)
        
        self.bikes_container_frame = ttk.Labelframe(main_pane, text="4. Bikes to Include", padding=(15, 5, 15, 15))
        main_pane.add(self.bikes_container_frame, weight=2)
        self.populate_bikes_frame()

    def toggle_log(self):
        if self.log_is_visible.get(): self.log_output_text.pack(fill=BOTH, expand=True, pady=(5,0))
        else: self.log_output_text.pack_forget()

    def _on_dnd_enter(self, event):
        self.drop_target.config(bootstyle="inverse-primary", text="\nDrop Files Now\n")
    def _on_dnd_leave(self, event):
        self.drop_target.config(bootstyle="inverse-secondary", text="\nDrop engine, idle, low, and high .wav files here\n")
    def _on_dnd_drop(self, event):
        self._on_dnd_leave(event)
        filepaths = self.winfo_toplevel().tk.splitlist(event.data)
        self.log("Processing dropped files...")
        found_map = {"engine": False, "idle": False, "low": False, "high": False}
        for path in filepaths:
            filename = os.path.basename(path).lower()
            if not filename.endswith('.wav'):
                self.log(f"  - Ignoring non-wav file: {filename}"); continue
            if "engine.wav" in filename: self.engine_wav_var.set(path); found_map["engine"] = True
            elif "idle.wav" in filename: self.idle_wav_var.set(path); found_map["idle"] = True
            elif "low.wav" in filename: self.low_wav_var.set(path); found_map["low"] = True
            elif "high.wav" in filename: self.high_wav_var.set(path); found_map["high"] = True
            else: self.log(f"  - Ignoring unrecognized .wav: {filename}")
        self.engine_status_var.set("✔️" if found_map["engine"] else "❌")
        self.idle_status_var.set("✔️" if found_map["idle"] else "❌")
        self.low_status_var.set("✔️" if found_map["low"] else "❌")
        self.high_status_var.set("✔️" if found_map["high"] else "❌")
        self.log("...Done.")

    def create_status_row(self, parent, label_text, status_var, row):
        parent.grid_columnconfigure(0, weight=1)
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=W)
        ttk.Label(parent, textvariable=status_var).grid(row=row, column=1, sticky=E)

    def _get_placeholder_image(self, size, text):
        if self.placeholder_image: return self.placeholder_image
        img = Image.new('RGB', size, color=self.winfo_toplevel().style.colors.get('dark'))
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("arial.ttf", 10)
        except IOError: font = ImageFont.load_default()
        draw.text((size[0]/2, size[1]/2), text, font=font, anchor="mm", fill=self.winfo_toplevel().style.colors.get('light'))
        self.placeholder_image = ImageTk.PhotoImage(img)
        return self.placeholder_image

    def populate_bikes_frame(self):
        for widget in self.bikes_container_frame.winfo_children(): widget.destroy()
        button_bar = ttk.Frame(self.bikes_container_frame)
        button_bar.pack(fill=X, pady=(5, 10))
        ttk.Button(button_bar, text="Select All", command=self.select_all_bikes, bootstyle="outline").pack(side=LEFT, expand=True, padx=(0,5))
        ttk.Button(button_bar, text="Deselect All", command=self.deselect_all_bikes, bootstyle="outline").pack(side=LEFT, expand=True)
        bikes_scrolled_frame = ScrolledFrame(self.bikes_container_frame, autohide=True)
        bikes_scrolled_frame.pack(fill=BOTH, expand=True)
        bike_list = ["Y250", "Y450", "E", "GRF250", "GRF450", "RM250", "RM450", "KW250", "KW450", "KTSX250", "KTSX450", "KTST250", "T250", "T450"]
        thumb_path = self.controller.get_thumbnail_path()
        cols = 5
        for i, bike_name in enumerate(bike_list):
            var = tk.BooleanVar()
            self.bike_vars[bike_name] = var
            img_path = os.path.join(thumb_path, f"{bike_name}.png") if thumb_path else ""
            image_to_display = None
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    img.thumbnail((96, 96), Image.Resampling.LANCZOS)
                    self.bike_images[bike_name] = ImageTk.PhotoImage(img)
                    image_to_display = self.bike_images[bike_name]
                except Exception: image_to_display = self._get_placeholder_image((80, 50), "Error")
            else: image_to_display = self._get_placeholder_image((80, 50), "No Preview")
            cb = ttk.Checkbutton(bikes_scrolled_frame, image=image_to_display, text=bike_name, variable=var, compound=tk.TOP, bootstyle="primary-toolbutton")
            cb.grid(row=i//cols, column=i%cols, padx=5, pady=5)
            bikes_scrolled_frame.grid_columnconfigure(i%cols, weight=1)

    def select_all_bikes(self):
        for var in self.bike_vars.values(): var.set(True)

    def deselect_all_bikes(self):
        for var in self.bike_vars.values(): var.set(False)

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
        self.log_is_visible.set(True)
        self.toggle_log()
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

class App(TkinterDnD.Tk):
    def __init__(self, themename="superhero"):
        super().__init__()
        self.style = ttk.Style(theme=themename)
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
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.nav_frame = ttk.Frame(self)
        self.nav_frame.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        self.nav_frame.grid_columnconfigure((0, 1), weight=1)
        self.nav_buttons = {}
        self.core_frames = ["Sound Creator", "Settings"]
        for i, name in enumerate(self.core_frames):
            btn = ttk.Button(self.nav_frame, text=name, command=lambda n=name: self.show_frame(n), bootstyle="secondary", padding=(0, 10))
            btn.grid(row=0, column=i, sticky="ew", padx=(0, 1))
            self.nav_buttons[name] = btn
        self.container = ttk.Frame(self)
        self.container.grid(row=1, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
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
        config = {"library_paths": self.library_paths, "thumbnail_folder_path": self.thumbnail_folder_path}
        with open(CONFIG_FILE, 'w') as f: json.dump(config, f, indent=4)
    def update_library_paths(self, new_paths):
        self.library_paths = new_paths
        self.scan_all_libraries()
    def set_thumbnail_path(self, new_path):
        self.thumbnail_folder_path = new_path
        sound_creator_frame = self.frames.get("Sound Creator")
        if sound_creator_frame: sound_creator_frame.populate_bikes_frame()
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
                    if os.path.isdir(os.path.join(lib_path, mod_folder)): self.mod_data[lib_path][mod_folder] = []
        sound_creator_frame = self.frames.get("Sound Creator")
        if sound_creator_frame: sound_creator_frame.update_output_options(self.mod_data)
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