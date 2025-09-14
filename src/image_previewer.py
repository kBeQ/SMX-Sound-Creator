# --- Filename: src/image_previewer.py ---
import tkinter as tk
import ttkbootstrap as ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import io

class ImagePreviewer(ttk.Labelframe):
    def __init__(self, parent, controller):
        super().__init__(parent, text="3. Package Preview")
        self.controller = controller
        self.selected_bikes = []
        self.current_index = -1
        self.current_image_tk = None
        self.placeholder_image_tk = None
        self.build_ui()
        self.update_preview([])

    def on_config_update(self):
        """Standard method called by the controller to react to setting changes."""
        self.show_current_bike()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.image_label = ttk.Label(self, anchor=tk.CENTER)
        self.image_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        controls_frame = ttk.Frame(self)
        controls_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        controls_frame.grid_columnconfigure(1, weight=1)
        self.prev_button = ttk.Button(controls_frame, text="<", command=self.show_previous, bootstyle="outline")
        self.prev_button.grid(row=0, column=0, padx=(10, 5))
        self.status_label = ttk.Label(controls_frame, text="No bikes selected", anchor=tk.CENTER)
        self.status_label.grid(row=0, column=1, sticky="ew")
        self.next_button = ttk.Button(controls_frame, text=">", command=self.show_next, bootstyle="outline")
        self.next_button.grid(row=0, column=2, padx=(5, 10))

    def _get_placeholder(self, text):
        size = (128, 128)
        img = Image.new('RGB', size, color=self.winfo_toplevel().style.colors.get('dark'))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except IOError:
            font = ImageFont.load_default()
        draw.text((size[0]/2, size[1]/2), text, font=font, anchor="mm", fill=self.winfo_toplevel().style.colors.get('light'))
        self.placeholder_image_tk = ImageTk.PhotoImage(img)
        return self.placeholder_image_tk

    def update_preview(self, selected_bike_ids):
        self.selected_bikes = selected_bike_ids
        self.current_index = 0 if self.selected_bikes else -1
        self.show_current_bike()

    def show_current_bike(self):
        is_empty = not self.selected_bikes
        self.prev_button.config(state=tk.DISABLED if is_empty else tk.NORMAL)
        self.next_button.config(state=tk.DISABLED if is_empty else tk.NORMAL)

        if is_empty:
            self.image_label.config(image=self._get_placeholder("No bikes selected"))
            self.status_label.config(text="No bikes selected")
            return

        bike_id = self.selected_bikes[self.current_index]
        self.status_label.config(text=f"{bike_id} ({self.current_index + 1}/{len(self.selected_bikes)})")
        
        thumbnail_folder = self.controller.get_setting("thumbnail_folder_path", "")
        source_png_path = os.path.join(thumbnail_folder, f"{bike_id}.png")

        if not os.path.exists(source_png_path):
            self.image_label.config(image=self._get_placeholder("Image not found"))
            return

        try:
            with Image.open(source_png_path).convert("RGBA") as fg_img:
                bg_path = self.controller.get_setting("background_path", "")
                bg_img_final = None
                
                if bg_path and os.path.exists(bg_path):
                    with Image.open(bg_path).convert("RGBA") as bg_img:
                        bg_img_final = bg_img.resize((256, 256), Image.Resampling.LANCZOS)
                else:
                    bg_img_final = Image.new("RGBA", (256, 256), "WHITE")

                fg_img.thumbnail((220, 220), Image.Resampling.LANCZOS)
                
                bg_w, bg_h = bg_img_final.size
                fg_w, fg_h = fg_img.size
                offset = ((bg_w - fg_w) // 2, (bg_h - fg_h) // 2)

                bg_img_final.paste(fg_img, offset, fg_img)

                rgb_img = bg_img_final.convert('RGB')
                
                img_byte_arr = io.BytesIO()
                rgb_img.save(img_byte_arr, format='JPEG', quality=90)
                img_byte_arr.seek(0)
                
                with Image.open(img_byte_arr) as preview_img:
                    preview_img.thumbnail((128, 128), Image.Resampling.LANCZOS)
                    self.current_image_tk = ImageTk.PhotoImage(preview_img)
                    self.image_label.config(image=self.current_image_tk)
        except Exception as e:
            print(f"Error processing image for preview: {e}")
            self.image_label.config(image=self._get_placeholder("Preview Error"))

    def show_next(self):
        if not self.selected_bikes: return
        self.current_index = (self.current_index + 1) % len(self.selected_bikes)
        self.show_current_bike()

    def show_previous(self):
        if not self.selected_bikes: return
        self.current_index = (self.current_index - 1 + len(self.selected_bikes)) % len(self.selected_bikes)
        self.show_current_bike()