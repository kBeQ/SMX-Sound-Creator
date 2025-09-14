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
        
        # --- Variables to hold the paths to user-selected files ---
        self.mod_name_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.engine_wav_var = tk.StringVar()
        self.idle_wav_var = tk.StringVar()
        self.low_wav_var = tk.StringVar()
        self.high_wav_var = tk.StringVar()
        self.preview_image_var = tk.StringVar()
        
        self.build_ui()

    def build_ui(self):
        # --- THE FIX IS ON THIS LINE ---
        # Removed the invalid 'sashwidth=10' option
        main_pane = ttk.PanedWindow(self, orient=HORIZONTAL)
        main_pane.pack(fill=BOTH, expand=True, padx=15, pady=15)

        # --- LEFT PANE: Configuration ---
        left_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(left_frame, weight=1)

        # --- Project Details ---
        details_frame = ttk.Labelframe(left_frame, text="1. Mod Details", padding=15)
        details_frame.pack(fill=X, expand=True, pady=(0, 10))
        details_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(details_frame, text="Mod Name:").grid(row=0, column=0, sticky=W, pady=2)
        ttk.Entry(details_frame, textvariable=self.mod_name_var).grid(row=0, column=1, sticky=EW, padx=5)
        
        ttk.Label(details_frame, text="Author:").grid(row=1, column=0, sticky=W, pady=2)
        ttk.Entry(details_frame, textvariable=self.author_var).grid(row=1, column=1, sticky=EW, padx=5)

        # --- Required Sounds ---
        sounds_frame = ttk.Labelframe(left_frame, text="2. Required Sound Files (.wav)", padding=15)
        sounds_frame.pack(fill=X, expand=True, pady=(0, 10))
        
        self.create_file_input_row(sounds_frame, "Engine:", self.engine_wav_var, 0)
        self.create_file_input_row(sounds_frame, "Idle:", self.idle_wav_var, 1)
        self.create_file_input_row(sounds_frame, "Low RPM:", self.low_wav_var, 2)
        self.create_file_input_row(sounds_frame, "High RPM:", self.high_wav_var, 3)
        
        # --- Optional Preview Image ---
        preview_frame = ttk.Labelframe(left_frame, text="3. Optional Preview Image", padding=15)
        preview_frame.pack(fill=X, expand=True, pady=(0, 10))
        
        self.create_file_input_row(preview_frame, "Image:", self.preview_image_var, 0, file_types=[("Image Files", "*.jpg *.png")])

        # --- Create Button ---
        self.create_button = ttk.Button(
            left_frame,
            text="Create Sound Mod Package",
            bootstyle="success",
            command=self.create_mod_package # This function doesn't do anything yet
        )
        self.create_button.pack(fill=X, expand=True, pady=10, ipady=10)
        
        # --- RIGHT PANE: Log Output ---
        right_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(right_frame, weight=2)
        
        log_header_frame = ttk.Frame(right_frame)
        log_header_frame.pack(fill=X, pady=(0, 5))
        ttk.Label(log_header_frame, text="Log Output", font=self.bold_font).pack(side=LEFT)
        
        self.log_output_text = ScrolledText(right_frame, wrap=tk.WORD, autohide=True, height=6)
        self.log_output_text.pack(expand=True, fill=BOTH)
        self.log_output_text.text.config(state='disabled')
        self.log("Welcome to the SMX Sound Creator!")
        self.log("Fill in the details on the left and select your sound files to begin.")

    def create_file_input_row(self, parent, label_text, string_var, row_num, file_types=[("WAV Files", "*.wav")]):
        """Helper function to create a consistent Label-Entry-Button row."""
        parent.grid_columnconfigure(1, weight=1)
        
        ttk.Label(parent, text=label_text).grid(row=row_num, column=0, sticky=W, pady=3)
        
        entry = ttk.Entry(parent, textvariable=string_var, state="readonly")
        entry.grid(row=row_num, column=1, sticky=EW, padx=5)
        
        button = ttk.Button(
            parent,
            text="Browse...",
            bootstyle="outline",
            command=lambda: self.browse_for_file(string_var, file_types)
        )
        button.grid(row=row_num, column=2)

    def browse_for_file(self, string_var, file_types):
        """Opens a file dialog and sets the selected path to the corresponding variable."""
        file_path = filedialog.askopenfilename(title="Select File", filetypes=file_types)
        if file_path:
            string_var.set(file_path)
            self.log(f"Selected file: {file_path}")

    def create_mod_package(self):
        """Placeholder function for the packaging logic."""
        self.log("\n--- Starting Mod Creation Process ---")
        # In the future, this is where the code to validate files,
        # create a zip archive, and save it will go.
        self.log("ERROR: Packaging logic has not been implemented yet.")

    def log(self, msg):
        """Appends a message to the log output text widget."""
        self.log_output_text.text.config(state='normal')
        self.log_output_text.insert(tk.END, str(msg).strip() + "\n")
        self.log_output_text.see(tk.END)
        self.log_output_text.text.config(state='disabled')