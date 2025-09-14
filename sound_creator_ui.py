import tkinter as tk
from tkinter import filedialog, font
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText

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
        
        self.build_ui()

    def build_ui(self):
        main_pane = ttk.PanedWindow(self, orient=HORIZONTAL)
        main_pane.pack(fill=BOTH, expand=True, padx=15, pady=15)

        left_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(left_frame, weight=1)

        details_frame = ttk.Labelframe(left_frame, text="1. Mod Details", padding=15)
        details_frame.pack(fill=X, expand=True, pady=(0, 10))
        details_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(details_frame, text="Mod Name:").grid(row=0, column=0, sticky=W, pady=2)
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

        # --- NEW: Output Location Section ---
        output_frame = ttk.Labelframe(left_frame, text="4. Output Location", padding=15)
        output_frame.pack(fill=X, expand=True, pady=(0, 10))
        output_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(output_frame, text="Category:").grid(row=0, column=0, sticky=W)
        self.category_selector = ttk.Combobox(output_frame, state="readonly")
        self.category_selector.grid(row=0, column=1, sticky=EW, padx=5)
        
        self.create_button = ttk.Button(
            left_frame, text="Create Sound Mod Package", bootstyle="success",
            command=self.create_mod_package
        )
        self.create_button.pack(fill=X, expand=True, pady=10, ipady=10)
        
        right_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(right_frame, weight=2)
        
        log_header_frame = ttk.Frame(right_frame)
        log_header_frame.pack(fill=X, pady=(0, 5))
        ttk.Label(log_header_frame, text="Log Output", font=self.bold_font).pack(side=LEFT)
        
        self.log_output_text = ScrolledText(right_frame, wrap=tk.WORD, autohide=True, height=6)
        self.log_output_text.pack(expand=True, fill=BOTH)
        self.log_output_text.text.config(state='disabled')
        self.log("Welcome to the SMX Sound Creator!")
        self.log("Go to Settings to add a Mod Library folder to begin.")

    def create_file_input_row(self, parent, label_text, string_var, row_num, file_types=[("WAV Files", "*.wav")]):
        parent.grid_columnconfigure(1, weight=1)
        ttk.Label(parent, text=label_text).grid(row=row_num, column=0, sticky=W, pady=3)
        entry = ttk.Entry(parent, textvariable=string_var, state="readonly")
        entry.grid(row=row_num, column=1, sticky=EW, padx=5)
        button = ttk.Button(
            parent, text="Browse...", bootstyle="outline",
            command=lambda: self.browse_for_file(string_var, file_types)
        )
        button.grid(row=row_num, column=2)

    def browse_for_file(self, string_var, file_types):
        file_path = filedialog.askopenfilename(title="Select File", filetypes=file_types)
        if file_path:
            string_var.set(file_path)
            self.log(f"Selected file: {os.path.basename(file_path)}")

    def update_categories(self, categories):
        """Called by the main app to populate the category dropdown."""
        self.category_selector['values'] = categories
        if categories:
            self.category_selector.set(categories[0])
            self.create_button.config(state=tk.NORMAL)
            self.log("Ready. Select a category and create your mod.")
        else:
            self.category_selector.set('')
            self.create_button.config(state=tk.DISABLED)
            self.log("Warning: No categories found. Please add a library in Settings and ensure it has subfolders.")

    def create_mod_package(self):
        self.log("\n--- Starting Mod Creation Process ---")
        self.log("ERROR: Packaging logic has not been implemented yet.")

    def log(self, msg):
        self.log_output_text.text.config(state='normal')
        self.log_output_text.insert(tk.END, str(msg).strip() + "\n")
        self.log_output_text.see(tk.END)
        self.log_output_text.text.config(state='disabled')