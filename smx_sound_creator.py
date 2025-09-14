# --- Filename: smx_sound_creator.py ---
import tkinter as tk
from tkinter import filedialog, font, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
import os
import sys
import json

# We still import SettingsFrame from its own file, which is good practice.
from settings_ui import SettingsFrame

APP_VERSION = "1.0.0"
CONFIG_FILE = "config.json"

def get_resource_path(filename):
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'assets', filename)

# ===================================================================
# --- MERGED CLASS: The entire UI for the main tab is now here. ---
# ===================================================================
class SoundCreatorFrame(ttk.Frame):
    name = "Sound Creator"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller # Still need this to access the main window
        self.bold_font = font.Font(family="Helvetica", size=10, weight="bold")
        
        self.mod_name_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.engine_wav_var = tk.StringVar()
        self.idle_wav_var = tk.StringVar()
        self.low_wav_var = tk.StringVar()
        self.high_wav_var = tk.StringVar()
        self.preview_image_var = tk.StringVar()
        self.output_mode_var = tk.StringVar(value="new")
        
        # --- Data now lives directly in the frame that uses it ---
        self.library_paths = []
        self.mod_data = {}
        
        self.build_ui()
        self.load_config() # Load config and run the first scan
        
    def build_ui(self):
        main_pane = ttk.PanedWindow(self, orient=HORIZONTAL)
        main_pane.pack(fill=BOTH, expand=True, padx=15, pady=15)

        left_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(left_frame, weight=1)

        details_frame = ttk.Labelframe(left_frame, text="1. Mod Details", padding=15)
        details_frame.pack(fill=X, expand=True, pady=(0, 10))
        details_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(details_frame, text="Mod Name/Bike:").grid(row=0, column=0, sticky=W, pady=2)
        ttk.Entry(details_frame, textvariable=self.mod_name_var).grid(row=0, column=1, sticky=EW, padx=5)
        ttk.Label(details_frame, text="Author:").grid(row=1, column=0, sticky=W, pady=2)
        ttk.Entry(details_frame, textvariable=self.author_var).grid(row=1, column=1, sticky=EW, padx=5)

        sounds_frame = ttk.Labelframe(left_frame, text="2. Required Sound Files (.wav)", padding=15)
        sounds_frame.pack(fill=X, expand=True, pady=(0, 10))
        
        self.create_file_input_row(sounds_frame, "Engine:", self.engine_wav_var, 0)
        self.create_file_input_row(sounds_frame, "Idle:", self.idle_wav_var, 1)
        self.create_file_input_row(sounds_frame, "Low RPM:", self.low_wav_var, 2)
        self.create_file_input_row(sounds_frame, "High RPM:", self.high_wav_var, 3)
        
        preview_frame = ttk.Labelframe(left_frame, text="3. Optional Preview Image", padding=15)
        preview_frame.pack(fill=X, expand=True, pady=(0, 10))
        self.create_file_input_row(preview_frame, "Image:", self.preview_image_var, 0, file_types=[("Image Files", "*.jpg *.png")])

        output_frame = ttk.Labelframe(left_frame, text="4. Output Location", padding=15)
        output_frame.pack(fill=X, expand=True, pady=(0, 10))
        output_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(output_frame, text="Destination Library:").grid(row=0, column=0, sticky=W, pady=(0, 5))
        self.library_selector = ttk.Combobox(output_frame, state="readonly")
        self.library_selector.grid(row=0, column=1, columnspan=2, sticky=EW, padx=5)
        self.library_selector.bind("<<ComboboxSelected>>", self._on_library_select)
        
        ttk.Separator(output_frame, orient=HORIZONTAL).grid(row=1, column=0, columnspan=3, sticky='ew', pady=10)
        
        mode_frame = ttk.Frame(output_frame)
        mode_frame.grid(row=2, column=0, columnspan=3, sticky='w')
        ttk.Radiobutton(mode_frame, text="Create New Mod", variable=self.output_mode_var, value="new", command=self._on_output_mode_change).pack(side=LEFT, padx=(0, 10))
        ttk.Radiobutton(mode_frame, text="Add to Existing Mod", variable=self.output_mode_var, value="existing", command=self._on_output_mode_change).pack(side=LEFT)

        ttk.Label(output_frame, text="New Mod Name:").grid(row=3, column=0, sticky=W, pady=2)
        self.new_mod_name_entry = ttk.Entry(output_frame)
        self.new_mod_name_entry.grid(row=3, column=1, columnspan=2, sticky=EW, padx=5)

        ttk.Label(output_frame, text="Existing Mod:").grid(row=4, column=0, sticky=W, pady=2)
        self.existing_mod_selector = ttk.Combobox(output_frame, state="readonly")
        self.existing_mod_selector.grid(row=4, column=1, columnspan=2, sticky=EW, padx=5)

        self.create_button = ttk.Button(left_frame, text="Create Sound Mod Package", command=self.create_mod_package)
        self.create_button.pack(fill=X, expand=True, pady=10, ipady=10)
        
        right_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(right_frame, weight=2)
        
        log_header_frame = ttk.Frame(right_frame)
        log_header_frame.pack(fill=X, pady=(0, 5))
        ttk.Label(log_header_frame, text="Log Output", font=self.bold_font).pack(side=LEFT)
        
        self.log_output_text = ScrolledText(right_frame, wrap=tk.WORD, autohide=True)
        self.log_output_text.pack(expand=True, fill=BOTH)
        self.log_output_text.text.config(state='disabled')
    
    # --- All data logic is now inside the frame that uses it ---
    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                self.library_paths = config_data.get("library_paths", [])
        except (FileNotFoundError, json.JSONDecodeError):
            self.library_paths = []
        self.scan_all_libraries()

    def save_config(self):
        config_data = {"library_paths": self.library_paths}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)

    def update_library_paths(self, new_paths):
        self.library_paths = new_paths
        self.save_config()
        self.scan_all_libraries()

    def scan_all_libraries(self):
        self.mod_data.clear()
        for lib_path in self.library_paths:
            if os.path.isdir(lib_path):
                self.mod_data[lib_path] = {}
                for mod_folder_name in os.listdir(lib_path):
                    mod_folder_path = os.path.join(lib_path, mod_folder_name)
                    if os.path.isdir(mod_folder_path):
                        self.mod_data[lib_path][mod_folder_name] = []
                        for zip_file_name in os.listdir(mod_folder_path):
                            if zip_file_name.lower().endswith('.zip'):
                                self.mod_data[lib_path][mod_folder_name].append(zip_file_name)
        self.update_output_options(self.mod_data)
        self.log("Scan complete. Library data has been updated.")

    # --- All UI logic remains here ---
    def create_file_input_row(self, parent, label_text, string_var, row_num, file_types=[("WAV Files", "*.wav")]):
        parent.grid_columnconfigure(1, weight=1)
        ttk.Label(parent, text=label_text).grid(row=row_num, column=0, sticky=W, pady=3)
        entry = ttk.Entry(parent, textvariable=string_var, state="readonly")
        entry.grid(row=row_num, column=1, sticky=EW, padx=5)
        button = ttk.Button(parent, text="Browse...", bootstyle="outline", command=lambda: self.browse_for_file(string_var, file_types))
        button.grid(row=row_num, column=2)

    def browse_for_file(self, string_var, file_types):
        file_path = filedialog.askopenfilename(title="Select File", filetypes=file_types)
        if file_path:
            string_var.set(file_path)
            self.log(f"Selected file: {os.path.basename(file_path)}")

    def update_output_options(self, mod_data):
        self.mod_data = mod_data
        lib_paths = list(self.mod_data.keys())
        lib_display_names = [os.path.basename(p) for p in lib_paths]
        self.library_selector['values'] = lib_display_names
        
        if lib_display_names:
            self.library_selector.set(lib_display_names[0])
            self.create_button.config(state=tk.NORMAL)
            self.log("Ready. Select an output location and create your mod.")
            self._on_library_select()
        else:
            self.library_selector.set('')
            self.create_button.config(state=tk.DISABLED)
            self.log("Warning: No libraries found. Please add one in Settings.")
        self._on_output_mode_change()

    def _on_library_select(self, event=None):
        selected_lib_name = self.library_selector.get()
        full_path = next((p for p in self.mod_data.keys() if os.path.basename(p) == selected_lib_name), None)
        if full_path:
            mod_folders = sorted(list(self.mod_data[full_path].keys()))
            self.existing_mod_selector['values'] = mod_folders
            if mod_folders:
                self.existing_mod_selector.set(mod_folders[0])
            else:
                self.existing_mod_selector.set('')

    def _on_output_mode_change(self):
        if self.output_mode_var.get() == "new":
            self.new_mod_name_entry.config(state=tk.NORMAL)
            self.existing_mod_selector.config(state=tk.DISABLED)
        else:
            self.new_mod_name_entry.config(state=tk.DISABLED)
            self.existing_mod_selector.config(state=tk.NORMAL)

    def create_mod_package(self):
        self.log("\n--- Starting Mod Creation Process ---")
        dest_lib_name = self.library_selector.get()
        output_mode = self.output_mode_var.get()
        if not dest_lib_name:
            self.log("ERROR: No destination library selected.")
            return
        if output_mode == 'new':
            mod_folder_name = self.new_mod_name_entry.get().strip()
            if not mod_folder_name:
                self.log("ERROR: 'New Mod Name' cannot be empty.")
                return
        else:
            mod_folder_name = self.existing_mod_selector.get()
            if not mod_folder_name:
                self.log("ERROR: No existing mod selected to add to.")
                return
        self.log(f"Destination Library: {dest_lib_name}")
        self.log(f"Output Mod Folder: {mod_folder_name}")
        self.log("ERROR: Packaging logic has not been implemented yet.")

    def log(self, msg):
        self.log_output_text.text.config(state='normal')
        self.log_output_text.insert(tk.END, str(msg).strip() + "\n")
        self.log_output_text.see(tk.END)
        self.log_output_text.text.config(state='disabled')

# ==========================================================
# --- The Main App Class is now much simpler. ---
# ==========================================================
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

        # The loop still works the same way
        for F in (SoundCreatorFrame, SettingsFrame):
            frame = F(self.container, self)
            self.frames[F.name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("Sound Creator")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_frame(self, page_name):
        if page_name in self.frames:
            frame = self.frames[page_name]
            if page_name == "Settings":
                frame.build_ui()
            frame.tkraise()
            for name, btn in self.nav_buttons.items():
                btn.config(bootstyle="primary" if name == page_name else "secondary")

    def on_closing(self):
        # Tell the main frame to save its config before closing
        sound_creator_frame = self.frames.get("Sound Creator")
        if sound_creator_frame:
            sound_creator_frame.save_config()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()