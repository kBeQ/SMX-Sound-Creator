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
import platform
import uuid

if platform.system() == "Windows":
    import winsound

from src.settings_ui import SettingsFrame
from src.image_previewer import ImagePreviewer
from src.packaging_sounds import create_sound_mod_package

APP_VERSION = "1.4.0"
CONFIG_FILE = "config.json"

BIKE_DATA = [
    ("YAMAHA YZ250F", "Y250"), ("YAMAHA YZ450F", "Y450"),
    ("ALTA REDSHIFT MX", "E"), ("HONDA CR250R", "GRF250"),
    ("HONDA CR450R", "GRF450"), ("SUZUKI RM-Z 250", "RM250"),
    ("SUZUKI RM-Z 450", "RM450"), ("KAWASAKI KX250", "KW250"),
    ("KAWASAKI KX450", "KW450"), ("KTM 250 SX-F", "KTSX250"),
    ("KTM 450 SX-F", "KTSX450"), ("KTM 250 SX", "KTST250"),
    ("TM 250Fi", "T250"), ("TM 450Fi", "T450")
]

def get_resource_path(filename):
    if getattr(sys, "frozen", False): base_dir = sys._MEIPASS
    else: base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'assets', filename)

class SoundCreatorFrame(ttk.Frame):
    name = "Sound Creator"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.engine_wav_var = tk.StringVar()
        self.idle_wav_var = tk.StringVar()
        self.low_wav_var = tk.StringVar()
        self.high_wav_var = tk.StringVar()
        self.output_mode_var = tk.StringVar(value="new")
        self.new_mod_name_var = tk.StringVar(value="CustomName")
        self.bike_vars = {}
        self.bike_images = {}
        self.placeholder_image = None
        self.previewer = None
        self.engine_status_var = tk.StringVar(value="❌")
        self.idle_status_var = tk.StringVar(value="❌")
        self.low_status_var = tk.StringVar(value="❌")
        self.high_status_var = tk.StringVar(value="❌")
        self.log_is_visible = tk.BooleanVar(value=False)
        self.include_engine_var = tk.BooleanVar(value=True)
        self.include_idle_var = tk.BooleanVar(value=True)
        self.include_low_var = tk.BooleanVar(value=True)
        self.include_high_var = tk.BooleanVar(value=True)
        self.build_ui()

    def on_config_update(self):
        self.populate_bikes_frame()
        if self.previewer: self.previewer.on_config_update()

    def build_ui(self):
        # Outer PanedWindow for Left vs (Center + Right)
        main_pane = ttk.PanedWindow(self, orient=HORIZONTAL)
        main_pane.pack(fill=BOTH, expand=True, padx=15, pady=(5, 15))

        # --- LEFT PANE ---
        left_pane_container = ttk.Frame(main_pane)
        main_pane.add(left_pane_container, weight=1) # Proportional weight
        left_pane = ScrolledFrame(left_pane_container, autohide=True, padding=10)
        left_pane.pack(fill=BOTH, expand=True)
        sounds_frame = ttk.Labelframe(left_pane, text="1. Sound Files (.wav)", padding=15)
        sounds_frame.pack(fill=X, expand=True, pady=(0, 10))
        self.setup_sound_widgets(sounds_frame)
        output_frame = ttk.Labelframe(left_pane, text="2. Output Location", padding=15)
        output_frame.pack(fill=X, expand=True, pady=(0, 10))
        self.setup_output_widgets(output_frame)
        self.create_button = ttk.Button(left_pane, text="Create Sound Mod Package", command=self.create_mod_package)
        self.create_button.pack(fill=X, pady=10, ipady=10)
        log_container = ttk.Frame(left_pane)
        log_container.pack(fill=X, expand=True)
        self.log_is_visible = tk.BooleanVar(value=False)
        log_header = ttk.Checkbutton(log_container, text="Show Log", variable=self.log_is_visible, command=self.toggle_log, bootstyle="info-toolbutton")
        log_header.pack(fill=X)
        self.log_output_text = ScrolledText(log_container, wrap=tk.WORD, autohide=True, height=5, padding=10)

        # --- NESTED PANE for Center vs Right ---
        center_right_pane = ttk.PanedWindow(main_pane, orient=HORIZONTAL)
        main_pane.add(center_right_pane, weight=3) # Takes more space

        # --- CENTER PANE (Previewer) ---
        self.previewer = ImagePreviewer(center_right_pane, self.controller, BIKE_DATA)
        center_right_pane.add(self.previewer, weight=1) # This pane WILL expand

        # --- RIGHT PANE (Bikes) ---
        right_pane = ttk.Labelframe(center_right_pane, text="5. Bikes to Include", padding=(15, 5, 15, 15))
        center_right_pane.add(right_pane, weight=0) # This pane WILL NOT expand
        self.bikes_container_frame = right_pane

        self.populate_bikes_frame()

    def setup_sound_widgets(self, parent):
        top_button_frame = ttk.Frame(parent)
        top_button_frame.pack(fill=X, pady=(0, 10))
        top_button_frame.grid_columnconfigure(0, weight=1)
        ttk.Button(top_button_frame, text="Select Folder with Sounds...", command=self.browse_for_sound_folder, bootstyle="primary").grid(row=0, column=0, sticky='ew', ipady=5, pady=(0, 10))
        stop_button = ttk.Button(top_button_frame, text="Stop Sound", command=self._stop_all_sounds, bootstyle="danger-outline")
        stop_button.grid(row=0, column=1, sticky='nsew', ipady=5, padx=(10, 0), pady=(0, 10))
        if platform.system() != "Windows": stop_button.config(state=tk.DISABLED)
        ttk.Separator(parent).pack(fill=X, pady=5)
        self.create_sound_input_row(parent, "Engine:", self.engine_wav_var, self.engine_status_var, self.include_engine_var)
        self.create_sound_input_row(parent, "Idle:", self.idle_wav_var, self.idle_status_var, self.include_idle_var)
        self.create_sound_input_row(parent, "Low:", self.low_wav_var, self.low_status_var, self.include_low_var)
        self.create_sound_input_row(parent, "High:", self.high_wav_var, self.high_status_var, self.include_high_var)

    def setup_output_widgets(self, parent):
        parent.grid_columnconfigure(1, weight=1)
        ttk.Label(parent, text="Library:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.library_selector = ttk.Combobox(parent, state="readonly")
        self.library_selector.grid(row=0, column=1, sticky='ew', padx=5)
        self.library_selector.bind("<<ComboboxSelected>>", self._on_library_select)
        ttk.Separator(parent).grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        mode_frame = ttk.Frame(parent)
        mode_frame.grid(row=2, column=0, columnspan=2, sticky='w')
        ttk.Radiobutton(mode_frame, text="New Mod", var=self.output_mode_var, value="new", command=self._on_output_mode_change).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Existing Mod", var=self.output_mode_var, value="existing", command=self._on_output_mode_change).pack(side=tk.LEFT, padx=10)
        ttk.Label(parent, text="Mod Name:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.new_mod_name_entry = ttk.Entry(parent, textvariable=self.new_mod_name_var)
        self.new_mod_name_entry.grid(row=3, column=1, sticky='ew', padx=5)
        self.existing_mod_selector = ttk.Combobox(parent, state="readonly")
        self.existing_mod_selector.grid(row=3, column=1, sticky='ew', padx=5)
        self.new_mod_name_var.trace_add("write", self._update_previewer)
        self.existing_mod_selector.bind("<<ComboboxSelected>>", self._update_previewer)

    def _get_current_mod_name(self):
        if self.output_mode_var.get() == "new": return self.new_mod_name_var.get().strip()
        else: return self.existing_mod_selector.get()

    def _update_previewer(self, *args):
        selected_ids = [bike_id for bike_id, var in self.bike_vars.items() if var.get()]
        mod_name = self._get_current_mod_name()
        if self.previewer: self.previewer.update_preview(selected_ids, mod_name)

    def populate_bikes_frame(self):
        for widget in self.bikes_container_frame.winfo_children(): widget.destroy()
        button_bar = ttk.Frame(self.bikes_container_frame)
        button_bar.pack(fill=X, pady=(5, 10))
        ttk.Button(button_bar, text="Select All", command=self.select_all_bikes, bootstyle="outline").pack(side=tk.LEFT, expand=True, padx=(0,5))
        ttk.Button(button_bar, text="Deselect All", command=self.deselect_all_bikes, bootstyle="outline").pack(side=tk.LEFT, expand=True)
        bikes_scrolled_frame = ScrolledFrame(self.bikes_container_frame, autohide=True)
        bikes_scrolled_frame.pack(fill=BOTH, expand=True)
        thumb_path = self.controller.get_setting("thumbnail_folder_path")
        cols = 2 # Adjusted for a narrower, vertical-friendly layout
        for i, (bike_name, bike_id) in enumerate(BIKE_DATA):
            var = tk.BooleanVar(value=(i == 0)); self.bike_vars[bike_id] = var
            img_path = os.path.join(thumb_path, f"{bike_id}.png") if thumb_path else ""
            image_to_display = self._get_bike_thumbnail(img_path, bike_id)
            button_text = f"{bike_name}\n{bike_id}"
            cb = ttk.Checkbutton(
                bikes_scrolled_frame, image=image_to_display, text=button_text, variable=var,
                compound=tk.TOP, bootstyle="primary-toolbutton",
                command=lambda bike_id=bike_id: self._on_bike_selection_change(bike_id)
            )
            cb.grid(row=i//cols, column=i%cols, padx=5, pady=5)
        self._update_previewer()

    def _on_bike_selection_change(self, changed_bike_id):
        var = self.bike_vars[changed_bike_id]
        if not var.get():
            selected_count = sum(v.get() for v in self.bike_vars.values())
            if selected_count == 0:
                var.set(True)
                messagebox.showinfo("Selection Required", "At least one bike must be selected at all times.", parent=self)
        self._update_previewer()

    def _get_bike_thumbnail(self, img_path, bike_id):
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path); img.thumbnail((96, 96), Image.Resampling.LANCZOS)
                self.bike_images[bike_id] = ImageTk.PhotoImage(img)
                return self.bike_images[bike_id]
            except Exception: return self._get_placeholder_image((80, 50), "Error")
        else: return self._get_placeholder_image((80, 50), "No Preview")

    def _get_placeholder_image(self, size, text):
        img = Image.new('RGB', size, color=self.winfo_toplevel().style.colors.get('dark'))
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("arial.ttf", 10)
        except IOError: font = ImageFont.load_default()
        draw.text((size[0]/2, size[1]/2), text, font=font, anchor="mm", fill=self.winfo_toplevel().style.colors.get('light'))
        return ImageTk.PhotoImage(img)

    def select_all_bikes(self):
        for var in self.bike_vars.values(): var.set(True)
        self._update_previewer()

    def deselect_all_bikes(self):
        first_bike_id = BIKE_DATA[0][1]
        for bike_id, var in self.bike_vars.items():
            var.set(bike_id == first_bike_id)
        self._update_previewer()

    def toggle_log(self):
        if self.log_is_visible.get(): self.log_output_text.pack(fill=BOTH, expand=True, pady=(5,0))
        else: self.log_output_text.pack_forget()

    def _play_sound(self, sound_var):
        if platform.system() != "Windows": return
        sound_path = sound_var.get()
        if not sound_path or not os.path.exists(sound_path): return
        try: winsound.PlaySound(sound_path, winsound.SND_ASYNC | winsound.SND_PURGE)
        except Exception as e: messagebox.showerror("Playback Error", f"Could not play the sound file.\n\nError: {e}")

    def _stop_all_sounds(self):
        if platform.system() == "Windows": winsound.PlaySound(None, winsound.SND_PURGE)

    def browse_for_sound_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder Containing Sound Files")
        if not folder_path: return
        self.log_is_visible.set(True); self.toggle_log()
        self.log(f"Scanning folder: {folder_path}")
        sound_files = {"engine.wav": self.engine_wav_var, "idle.wav": self.idle_wav_var, "low.wav": self.low_wav_var, "high.wav": self.high_wav_var}
        found_any = False
        for filename, var in sound_files.items():
            full_path = os.path.join(folder_path, filename)
            if os.path.exists(full_path): var.set(full_path); self.log(f"  - Found: {filename}"); found_any = True
        if not found_any: self.log("Warning: No required .wav files found.")
        self.update_all_statuses()

    def update_all_statuses(self):
        self.engine_status_var.set("✔️" if self.engine_wav_var.get() else "❌"); self.idle_status_var.set("✔️" if self.idle_wav_var.get() else "❌")
        self.low_status_var.set("✔️" if self.low_wav_var.get() else "❌"); self.high_status_var.set("✔️" if self.high_wav_var.get() else "❌")

    def create_sound_input_row(self, parent, label_text, string_var, status_var, include_var):
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=X, pady=2)
        row_frame.grid_columnconfigure(1, weight=1)
        
        entry = ttk.Entry(row_frame, textvariable=string_var, state="readonly")
        entry.grid(row=0, column=1, sticky='ew', padx=5)
        
        status_label = ttk.Label(row_frame, textvariable=status_var, width=2)
        status_label.grid(row=0, column=2, padx=5)
        
        browse_button = ttk.Button(row_frame, text="...", bootstyle="outline", width=4, command=lambda: self.browse_for_file(string_var, [("WAV", "*.wav")]))
        browse_button.grid(row=0, column=3)
        
        play_button = ttk.Button(row_frame, text="▶", bootstyle="success-outline", width=4, command=lambda: self._play_sound(string_var))
        play_button.grid(row=0, column=4, padx=(5, 0))
        if platform.system() != "Windows":
            play_button.config(state=tk.DISABLED)

        def toggle_row_state(*args):
            is_enabled = include_var.get()
            new_state = tk.NORMAL if is_enabled else tk.DISABLED
            entry.config(state="readonly" if is_enabled else tk.DISABLED)
            browse_button.config(state=new_state)
            status_label.config(state=new_state)
            if platform.system() == "Windows":
                play_button.config(state=new_state)

        checkbutton = ttk.Checkbutton(row_frame, text=label_text, variable=include_var, width=7, command=toggle_row_state)
        checkbutton.grid(row=0, column=0, sticky=tk.W)
        
        toggle_row_state()

    def browse_for_file(self, string_var, file_types):
        file_path = filedialog.askopenfilename(filetypes=file_types)
        if file_path: string_var.set(file_path); self.update_all_statuses()

    def update_output_options(self, mod_data):
        lib_paths = list(mod_data.keys()); lib_display_names = [os.path.basename(p) for p in lib_paths]
        self.library_selector['values'] = lib_display_names
        if lib_display_names: self.library_selector.set(lib_display_names[0]); self.create_button.config(state=tk.NORMAL); self._on_library_select()
        else: self.library_selector.set(''); self.create_button.config(state=tk.DISABLED)
        self._on_output_mode_change()

    def _on_library_select(self, event=None):
        lib_name = self.library_selector.get(); full_path = self.controller.get_full_library_path(lib_name)
        if full_path:
            mod_folders = self.controller.get_mods_for_library(full_path)
            self.existing_mod_selector['values'] = mod_folders
            if mod_folders: self.existing_mod_selector.set(mod_folders[0])
            else: self.existing_mod_selector.set('')
        self._update_previewer()

    def _on_output_mode_change(self):
        is_new = self.output_mode_var.get() == "new"
        self.new_mod_name_entry.grid(row=3, column=1, sticky='ew', padx=5) if is_new else self.new_mod_name_entry.grid_forget()
        self.existing_mod_selector.grid_forget() if is_new else self.existing_mod_selector.grid(row=3, column=1, sticky='ew', padx=5)
        self._update_previewer()

    def create_mod_package(self):
        self.log_is_visible.set(True); self.toggle_log()
        self.log("\n--- Starting Mod Creation Process ---")
        lib_name = self.library_selector.get()
        if not lib_name: messagebox.showerror("Validation Error", "Please select an output library."); return
        full_lib_path = self.controller.get_full_library_path(lib_name)
        mod_name = self._get_current_mod_name()
        if not mod_name: messagebox.showerror("Validation Error", "Mod Name cannot be empty."); return
        
        sound_paths = {}
        sound_map = {
            "engine": (self.include_engine_var, self.engine_wav_var),
            "idle": (self.include_idle_var, self.idle_wav_var),
            "low": (self.include_low_var, self.low_wav_var),
            "high": (self.include_high_var, self.high_wav_var),
        }

        for name, (include_var, path_var) in sound_map.items():
            if include_var.get():
                path = path_var.get()
                if not path or not os.path.exists(path):
                    messagebox.showerror("Validation Error", f"'{name.capitalize()}' sound is enabled, but the file is not selected or does not exist.", parent=self)
                    return
                sound_paths[name] = path

        if not sound_paths:
            messagebox.showerror("Validation Error", "At least one sound file must be enabled and selected to create a package.", parent=self)
            return

        selected_bikes = [bike_id for bike_id, var in self.bike_vars.items() if var.get()]
        if not selected_bikes: messagebox.showerror("Validation Error", "Please select at least one bike."); return
        preview_elements = self.controller.get_setting("preview_elements", [])
        success = create_sound_mod_package(
            output_library_path=full_lib_path, mod_name=mod_name, selected_bikes=selected_bikes,
            sound_paths=sound_paths, thumbnail_folder=self.controller.get_setting("thumbnail_folder_path"),
            preview_elements=preview_elements, bike_data=BIKE_DATA, log_callback=self.log
        )
        if success:
            self.log("\n--- Mod Creation Complete! ---")
            messagebox.showinfo("Success", f"Mod '{mod_name}' created successfully in library '{lib_name}'.")
        else:
            self.log("\n--- Mod Creation Finished with Errors ---")
            messagebox.showwarning("Process Finished", "Mod creation failed. Please check the log for details.")
        self.controller.scan_all_libraries()

    def log(self, msg):
        self.log_output_text.text.config(state='normal')
        self.log_output_text.insert(tk.END, str(msg).strip() + "\n")
        self.log_output_text.see(tk.END)
        self.log_output_text.text.config(state='disabled')


class App(tk.Tk):
    def __init__(self, themename="superhero"):
        super().__init__()
        self.style = ttk.Style(theme=themename)
        self.title(f"SMX Sound Creator v{APP_VERSION}")
        self.geometry("1600x900")
        try:
            icon_path = get_resource_path("smx_sound_creator.ico")
            if os.path.exists(icon_path): self.iconbitmap(icon_path)
        except Exception: pass
        self.config = {}
        self.mod_data = {}
        self.fonts = {}
        self.font_path_to_name = {}
        self.load_config()
        self.scan_and_build_font_list()
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.nav_frame = ttk.Frame(self)
        self.nav_frame.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        self.nav_frame.grid_columnconfigure((0, 1), weight=1)
        self.nav_buttons = {}
        for i, name in enumerate(["Sound Creator", "Settings"]):
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
            with open(CONFIG_FILE, 'r') as f: self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): self.config = {}
        self.config.setdefault("library_paths", [])
        self.config.setdefault("thumbnail_folder_path", "")
        self.config.setdefault("font_folder_paths", [])

        if "preview_elements" not in self.config:
            self.config["preview_elements"] = [
                {"id": str(uuid.uuid4()), "name": "Background", "type": "background", "visible": True, "path": "", "color": "#FFFFFF", "pos_x": 960, "pos_y": 540, "scale": 1.0, "rotation": 0, "aspect_ratio": "fit"},
                {"id": str(uuid.uuid4()), "name": "Bike Image", "type": "bike_image", "visible": True, "pos_x": 960, "pos_y": 540, "scale": 0.85, "rotation": 0, "aspect_ratio": "fit"},
                {"id": str(uuid.uuid4()), "name": "Bike ID", "type": "text", "visible": True, "dataSource": "Bike ID", "staticText": "", "font_path": "arial.ttf", "size": 80, "color": "#FFFFFF", "align": "center", "pos_x": 960, "pos_y": 80, "outline_size": 2, "outline_color": "#000000", "rotation": 0},
                {"id": str(uuid.uuid4()), "name": "Mod Name", "type": "text", "visible": True, "dataSource": "Mod Name", "staticText": "", "font_path": "arial.ttf", "size": 70, "color": "#FFFFFF", "align": "center", "pos_x": 960, "pos_y": 1000, "outline_size": 2, "outline_color": "#000000", "rotation": 0}
            ]
        else: # Config Upgrader
            for elem in self.config["preview_elements"]:
                if elem.get("type") in ["background", "bike_image", "image"]:
                    elem.setdefault("rotation", 0)
                    elem.setdefault("aspect_ratio", "fit")
                    elem.setdefault("pos_x", 128)
                    elem.setdefault("pos_y", 128)
                    elem.setdefault("scale", 1.0)
                if elem.get("type") == "text":
                    elem.setdefault("rotation", 0)

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=4)
    def get_setting(self, key, default=None): return self.config.get(key, default)
    def update_setting(self, key, value, broadcast=True):
        self.config[key] = value
        self.save_config()
        if broadcast: self.broadcast_config_update()

    def broadcast_config_update(self):
        for frame in self.frames.values():
            if hasattr(frame, 'on_config_update'): frame.on_config_update()
            
    def update_library_paths(self, new_paths):
        self.config["library_paths"] = new_paths; self.save_config(); self.scan_all_libraries()
    def get_library_paths(self): return self.get_setting("library_paths", [])
    def get_full_library_path(self, name): return next((p for p in self.mod_data.keys() if os.path.basename(p) == name), None)
    def get_mods_for_library(self, full_path): return sorted(list(self.mod_data.get(full_path, {}).keys()))
    
    def scan_and_build_font_list(self):
        self.fonts.clear()
        self.font_path_to_name.clear()
        self.fonts["Default (Arial)"] = "arial.ttf"
        self.font_path_to_name["arial.ttf"] = "Default (Arial)"
        font_paths = self.get_setting("font_folder_paths", [])
        for folder in font_paths:
            if not os.path.isdir(folder): continue
            for root, _, files in os.walk(folder):
                for filename in files:
                    if filename.lower().endswith(('.ttf', '.otf')):
                        full_path = os.path.join(root, filename)
                        display_name = os.path.splitext(filename)[0].replace('-', ' ').replace('_', ' ')
                        if display_name in self.fonts:
                            parent_folder = os.path.basename(os.path.dirname(full_path))
                            display_name = f"{display_name} ({parent_folder})"
                        self.fonts[display_name] = full_path
                        self.font_path_to_name[full_path] = display_name

    def get_font_names(self):
        return sorted(list(self.fonts.keys()))

    def get_font_path(self, font_name):
        return self.fonts.get(font_name, "arial.ttf")

    def get_font_name_from_path(self, font_path):
        return self.font_path_to_name.get(font_path, "Default (Arial)")

    def update_font_folder_paths(self, new_paths):
        self.config["font_folder_paths"] = new_paths
        self.save_config()
        self.scan_and_build_font_list()
        self.broadcast_config_update()
        
    def scan_all_libraries(self):
        self.mod_data.clear()
        for lib_path in self.get_library_paths():
            if os.path.isdir(lib_path):
                self.mod_data[lib_path] = {}
                for mod_folder in os.listdir(lib_path):
                    if os.path.isdir(os.path.join(lib_path, mod_folder)): self.mod_data[lib_path][mod_folder] = []
        sound_creator_frame = self.frames.get("Sound Creator")
        if sound_creator_frame: sound_creator_frame.update_output_options(self.mod_data)
        
    def show_frame(self, page_name):
        if page_name in self.frames:
            frame = self.frames[page_name]; frame.tkraise()
            for name, btn in self.nav_buttons.items():
                btn.config(bootstyle="primary" if name == page_name else "secondary")
                
    def on_closing(self):
        if platform.system() == "Windows": winsound.PlaySound(None, winsound.SND_PURGE)
        self.save_config()
        self.destroy()

if __name__ == "__main__":
    if not os.path.exists("src"): os.makedirs("src")
    app = App()
    app.mainloop()
