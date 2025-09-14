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
import zipfile
import io

# Import winsound for audio playback on Windows
if platform.system() == "Windows":
    import winsound

from settings_ui import SettingsFrame

APP_VERSION = "1.0.0"
CONFIG_FILE = "config.json"

BIKE_DATA = [
    ("YAMI YZ-F 250", "Y250"),
    ("YAMI YZ-F 450", "Y450"),
    ("YAMI Electric", "E"),
    ("HINDA CR250", "GRF250"),
    ("HINDA CR450", "GRF450"),
    ("SUCAKI RM 250", "RM250"),
    ("SUCAKI RM 450", "RM450"),
    ("Kawazavi KX 250", "KW250"),
    ("Kawazavi KX 450", "KW450"),
    ("KMA KTSX 250", "KTSX250"),
    ("KMA KTSX 450", "KTSX450"),
    ("KMA KTST 250", "KTST250"),
    ("TF MF 250", "T250"),
    ("TF MF 450", "T450")
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
        self.bold_font = font.Font(family="Helvetica", size=10, weight="bold")
        
        self.engine_wav_var = tk.StringVar()
        self.idle_wav_var = tk.StringVar()
        self.low_wav_var = tk.StringVar()
        self.high_wav_var = tk.StringVar()
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

        top_button_frame = ttk.Frame(sounds_frame)
        top_button_frame.pack(fill=X, pady=(0, 10))
        top_button_frame.grid_columnconfigure(0, weight=1)

        ttk.Button(
            top_button_frame, 
            text="Select Folder with Sounds...", 
            command=self.browse_for_sound_folder, 
            bootstyle="primary"
        ).grid(row=0, column=0, sticky='ew', ipady=5, pady=(0, 10))

        stop_button = ttk.Button(
            top_button_frame,
            text="Stop Sound",
            command=self._stop_all_sounds,
            bootstyle="danger-outline"
        )
        stop_button.grid(row=0, column=1, sticky='nsew', ipady=5, padx=(10, 0), pady=(0, 10))
        
        if platform.system() != "Windows":
            stop_button.config(state=tk.DISABLED)

        ttk.Separator(sounds_frame).pack(fill=X, pady=5)

        self.create_sound_input_row(sounds_frame, "Engine:", self.engine_wav_var, self.engine_status_var)
        self.create_sound_input_row(sounds_frame, "Idle:", self.idle_wav_var, self.idle_status_var)
        self.create_sound_input_row(sounds_frame, "Low:", self.low_wav_var, self.low_status_var)
        self.create_sound_input_row(sounds_frame, "High:", self.high_wav_var, self.high_status_var)

        output_frame = ttk.Labelframe(left_scrolled_frame, text="2. Output Location", padding=15)
        output_frame.pack(fill=X, pady=(0, 10))
        output_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(output_frame, text="Library:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.library_selector = ttk.Combobox(output_frame, state="readonly")
        self.library_selector.grid(row=0, column=1, sticky='ew', padx=5)
        self.library_selector.bind("<<ComboboxSelected>>", self._on_library_select)
        ttk.Separator(output_frame).grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        mode_frame = ttk.Frame(output_frame)
        mode_frame.grid(row=2, column=0, columnspan=2, sticky='w')
        ttk.Radiobutton(mode_frame, text="New Mod", var=self.output_mode_var, value="new", command=self._on_output_mode_change).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Existing Mod", var=self.output_mode_var, value="existing", command=self._on_output_mode_change).pack(side=tk.LEFT, padx=10)
        ttk.Label(output_frame, text="Mod Name:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.new_mod_name_entry = ttk.Entry(output_frame)
        self.new_mod_name_entry.grid(row=3, column=1, sticky='ew', padx=5)
        self.existing_mod_selector = ttk.Combobox(output_frame, state="readonly")
        self.existing_mod_selector.grid(row=3, column=1, sticky='ew', padx=5)

        self.create_button = ttk.Button(left_scrolled_frame, text="Create Sound Mod Package", command=self.create_mod_package)
        self.create_button.pack(fill=X, pady=10, ipady=10)

        log_container = ttk.Frame(left_pane)
        log_container.grid(row=1, column=0, sticky='ew')
        self.log_is_visible = tk.BooleanVar(value=False)
        log_header = ttk.Checkbutton(log_container, text="Show Log", variable=self.log_is_visible, command=self.toggle_log, bootstyle="info-toolbutton")
        log_header.pack(fill=X)
        self.log_output_text = ScrolledText(log_container, wrap=tk.WORD, autohide=True, height=5, padding=10)
        
        self.bikes_container_frame = ttk.Labelframe(main_pane, text="3. Bikes to Include", padding=(15, 5, 15, 15))
        main_pane.add(self.bikes_container_frame, weight=2)
        self.populate_bikes_frame()

    def toggle_log(self):
        if self.log_is_visible.get(): self.log_output_text.pack(fill=BOTH, expand=True, pady=(5,0))
        else: self.log_output_text.pack_forget()

    def _play_sound(self, sound_var):
        if platform.system() != "Windows":
            self.log("ERROR: Sound playback is only supported on Windows.")
            messagebox.showerror("Unsupported OS", "Sound playback is currently only available on Windows.")
            return

        sound_path = sound_var.get()
        if not sound_path:
            self.log("Playback failed: No sound file selected for this slot.")
            return
        if not os.path.exists(sound_path):
            self.log(f"Playback failed: File not found at '{sound_path}'")
            return

        try:
            self.log(f"Playing: {os.path.basename(sound_path)}")
            winsound.PlaySound(sound_path, winsound.SND_ASYNC | winsound.SND_PURGE)
        except Exception as e:
            self.log(f"ERROR: Could not play sound. {e}")
            messagebox.showerror("Playback Error", f"Could not play the sound file.\n\nError: {e}")

    def _stop_all_sounds(self):
        if platform.system() != "Windows":
            return
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
            self.log("Sound playback stopped.")
        except Exception as e:
            self.log(f"ERROR: Could not stop sound. {e}")

    def browse_for_sound_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder Containing Sound Files")
        if not folder_path: return

        self.log_is_visible.set(True)
        self.toggle_log()
        self.log(f"Scanning folder: {folder_path}")

        sound_files = ["engine.wav", "idle.wav", "low.wav", "high.wav"]
        vars_map = {
            "engine.wav": self.engine_wav_var, "idle.wav": self.idle_wav_var,
            "low.wav": self.low_wav_var, "high.wav": self.high_wav_var
        }

        found_any = False
        for filename in sound_files:
            full_path = os.path.join(folder_path, filename)
            if os.path.exists(full_path):
                vars_map[filename].set(full_path)
                self.log(f"  - Found: {filename}")
                found_any = True
        
        if not found_any:
            self.log("Warning: No required .wav files found in the selected folder.")
        
        self.update_all_statuses()
        self.log("...Scan complete.")

    def update_all_statuses(self):
        self.engine_status_var.set("✔️" if self.engine_wav_var.get() else "❌")
        self.idle_status_var.set("✔️" if self.idle_wav_var.get() else "❌")
        self.low_status_var.set("✔️" if self.low_wav_var.get() else "❌")
        self.high_status_var.set("✔️" if self.high_wav_var.get() else "❌")

    def create_sound_input_row(self, parent, label_text, string_var, status_var):
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=X, pady=2)
        row_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(row_frame, text=label_text, width=7).grid(row=0, column=0, sticky=tk.W)
        
        entry = ttk.Entry(row_frame, textvariable=string_var, state="readonly")
        entry.grid(row=0, column=1, sticky='ew', padx=5)

        ttk.Label(row_frame, textvariable=status_var, width=2).grid(row=0, column=2, padx=5)
        
        button = ttk.Button(row_frame, text="...", bootstyle="outline", width=4, 
                            command=lambda: self.browse_for_file(string_var, [("WAV", "*.wav")]))
        button.grid(row=0, column=3)

        play_button = ttk.Button(row_frame, text="▶", bootstyle="success-outline", width=4,
                                 command=lambda: self._play_sound(string_var))
        play_button.grid(row=0, column=4, padx=(5, 0))

        if platform.system() != "Windows":
            play_button.config(state=tk.DISABLED)

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
        ttk.Button(button_bar, text="Select All", command=self.select_all_bikes, bootstyle="outline").pack(side=tk.LEFT, expand=True, padx=(0,5))
        ttk.Button(button_bar, text="Deselect All", command=self.deselect_all_bikes, bootstyle="outline").pack(side=tk.LEFT, expand=True)
        bikes_scrolled_frame = ScrolledFrame(self.bikes_container_frame, autohide=True)
        bikes_scrolled_frame.pack(fill=BOTH, expand=True)
        
        thumb_path = self.controller.get_thumbnail_path()
        cols = 5
        
        style = ttk.Style()
        style.configure("Toolbutton", justify=tk.CENTER)

        for i, (bike_name, bike_id) in enumerate(BIKE_DATA):
            var = tk.BooleanVar()
            self.bike_vars[bike_id] = var 
            img_path = os.path.join(thumb_path, f"{bike_id}.png") if thumb_path else ""
            image_to_display = None
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    img.thumbnail((96, 96), Image.Resampling.LANCZOS)
                    self.bike_images[bike_id] = ImageTk.PhotoImage(img)
                    image_to_display = self.bike_images[bike_id]
                except Exception: image_to_display = self._get_placeholder_image((80, 50), "Error")
            else: image_to_display = self._get_placeholder_image((80, 50), "No Preview")
            
            button_text = f"{bike_name}\n{bike_id}"
            
            cb = ttk.Checkbutton(bikes_scrolled_frame, image=image_to_display, text=button_text, variable=var, compound=tk.TOP, bootstyle="primary-toolbutton")
            cb.grid(row=i//cols, column=i%cols, padx=5, pady=5)
            bikes_scrolled_frame.grid_columnconfigure(i%cols, weight=1)

    def select_all_bikes(self):
        for var in self.bike_vars.values(): var.set(True)

    def deselect_all_bikes(self):
        for var in self.bike_vars.values(): var.set(False)

    def create_file_input_row(self, parent, label_text, string_var, row_num, file_types=[("WAV", "*.wav")]):
        parent.grid_columnconfigure(1, weight=1)
        ttk.Label(parent, text=label_text).grid(row=row_num, column=0, sticky=tk.W, pady=3)
        entry = ttk.Entry(parent, textvariable=string_var, state="readonly")
        entry.grid(row=row_num, column=1, sticky='ew', padx=5)
        button = ttk.Button(parent, text="...", bootstyle="outline", width=4, command=lambda: self.browse_for_file(string_var, file_types))
        button.grid(row=row_num, column=2)

    def browse_for_file(self, string_var, file_types):
        file_path = filedialog.askopenfilename(filetypes=file_types)
        if file_path:
            string_var.set(file_path)
            self.log(f"Selected: {os.path.basename(file_path)}")
            self.update_all_statuses()

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
            self.new_mod_name_entry.grid(row=3, column=1, sticky='ew', padx=5)
            self.existing_mod_selector.grid_forget()
        else:
            self.new_mod_name_entry.grid_forget()
            self.existing_mod_selector.grid(row=3, column=1, sticky='ew', padx=5)

    def create_mod_package(self):
        self.log_is_visible.set(True)
        self.toggle_log()
        self.log("\n--- Starting Mod Creation Process ---")

        # 1. Validation and Data Gathering
        lib_name = self.library_selector.get()
        if not lib_name:
            self.log("ERROR: No output library selected.")
            messagebox.showerror("Validation Error", "Please select an output library from the dropdown.")
            return

        full_lib_path = self.controller.get_full_library_path(lib_name)
        if not full_lib_path:
            self.log(f"ERROR: Could not resolve full path for library '{lib_name}'.")
            messagebox.showerror("Error", f"Could not find the folder for library '{lib_name}'.")
            return

        mod_name = ""
        if self.output_mode_var.get() == "new":
            mod_name = self.new_mod_name_entry.get().strip()
        else:
            mod_name = self.existing_mod_selector.get()
        
        if not mod_name:
            self.log("ERROR: Mod Name is empty.")
            messagebox.showerror("Validation Error", "Mod Name cannot be empty.")
            return

        sound_paths = {
            "engine": self.engine_wav_var.get(),
            "idle": self.idle_wav_var.get(),
            "low": self.low_wav_var.get(),
            "high": self.high_wav_var.get()
        }

        if not all(sound_paths.values()):
            self.log("ERROR: One or more .wav files are missing.")
            messagebox.showerror("Validation Error", "Please select all four required sound files (Engine, Idle, Low, High).")
            return

        selected_bikes = [bike_id for bike_id, var in self.bike_vars.items() if var.get()]
        if not selected_bikes:
            self.log("ERROR: No bikes were selected!")
            messagebox.showerror("Validation Error", "Please select at least one bike to include in the mod package.")
            return

        self.log(f"Bikes to include: {', '.join(selected_bikes)}")

        # 2. Create the main mod directory
        mod_path = os.path.join(full_lib_path, mod_name)
        try:
            os.makedirs(mod_path, exist_ok=True)
            self.log(f"Output directory: {mod_path}")
        except OSError as e:
            self.log(f"ERROR: Failed to create mod directory at '{mod_path}'. Reason: {e}")
            messagebox.showerror("File System Error", f"Could not create the mod directory.\n\nError: {e}")
            return

        # 3. Iterate through each selected bike and create zip files
        thumb_path_base = self.controller.get_thumbnail_path()
        has_errors = False
        for bike_id in selected_bikes:
            self.log(f"  - Packaging bike: {bike_id}")
            zip_path = os.path.join(mod_path, f"{bike_id}.zip")

            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Add sound files
                    for sound_name, sound_path in sound_paths.items():
                        arcname = f"{bike_id}/{os.path.basename(sound_path)}"
                        zipf.write(sound_path, arcname)
                    
                    self.log(f"    - Added 4 sound files to {os.path.basename(zip_path)}")

                    # Handle and add the preview image
                    if not thumb_path_base:
                        self.log(f"    - WARNING: Thumbnail folder not set in Settings. Skipping preview.jpg.")
                        continue

                    source_img_path = os.path.join(thumb_path_base, f"{bike_id}.png")
                    if os.path.exists(source_img_path):
                        try:
                            with Image.open(source_img_path) as img:
                                # Convert to RGB, as JPEG doesn't support RGBA (with transparency)
                                rgb_img = img.convert('RGB')
                                
                                # Save to an in-memory byte stream
                                img_byte_arr = io.BytesIO()
                                rgb_img.save(img_byte_arr, format='JPEG', quality=90)
                                img_byte_arr.seek(0) # Rewind the stream to the beginning
                                
                                # Write the byte stream to the zip file
                                zipf.writestr(f"{bike_id}/preview.jpg", img_byte_arr.read())
                                self.log(f"    - Added preview.jpg for {bike_id}")
                        except Exception as img_e:
                            self.log(f"    - ERROR: Failed to process image for {bike_id}. Reason: {img_e}")
                            has_errors = True
                    else:
                        self.log(f"    - WARNING: Thumbnail for {bike_id} not found at {source_img_path}. Skipping preview.jpg.")
                
                self.log(f"    - Successfully created {os.path.basename(zip_path)}")

            except Exception as e:
                self.log(f"    - FATAL ERROR creating zip for {bike_id}: {e}")
                messagebox.showerror("Packaging Error", f"Failed to create package for {bike_id}.\n\nError: {e}")
                has_errors = True
                break # Stop the process if a fatal zip error occurs

        # 4. Final summary
        if has_errors:
            self.log("\n--- Mod Creation Finished with Errors ---")
            messagebox.showwarning("Process Finished", f"Mod '{mod_name}' was processed, but some errors occurred. Please check the log for details.")
        else:
            self.log("\n--- Mod Creation Complete! ---")
            messagebox.showinfo("Success", f"Mod '{mod_name}' created successfully in library '{lib_name}'.")

        # 5. Refresh the mod list in the UI
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
        self._stop_all_sounds()
        self.save_config()
        self.destroy()

    def _stop_all_sounds(self):
        if platform.system() == "Windows":
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass # Fail silently on exit

if __name__ == "__main__":
    app = App()
    app.mainloop()