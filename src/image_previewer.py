# --- Filename: src/image_previewer.py ---
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import uuid
import copy

from src.element_editor_ui import ElementEditorWindow

class ImagePreviewer(ttk.Frame):
    # Define canvas and display dimensions
    PREVIEW_WIDTH = 1920
    PREVIEW_HEIGHT = 1080
    DISPLAY_WIDTH = 640 # Keep the UI display small and fast
    DISPLAY_HEIGHT = int(DISPLAY_WIDTH * (9 / 16)) # 360

    def __init__(self, parent, controller, bike_data):
        super().__init__(parent)
        self.controller = controller
        self.bike_data = bike_data
        self.selected_bikes = []
        self.current_mod_name = ""
        self.current_index = -1
        self.current_image_tk = None
        self.editor_window = None
        self.build_ui()
        self.after(100, self._set_initial_state)

    def _set_initial_state(self):
        elements = self.controller.get_setting("preview_elements", [])
        if elements: self.hierarchy_listbox.selection_set(0)

    def on_config_update(self):
        self.populate_hierarchy_list()
        self.render_preview()

    def build_ui(self):
        # The main container is now a simple frame, using pack layout
        self.pack(fill=BOTH, expand=True)

        # --- PREVIEW CANVAS (TOP) ---
        preview_container = ttk.Labelframe(self, text="3. Live Preview (16:9)", padding=10)
        preview_container.pack(side=TOP, fill=X, padx=5, pady=5)
        
        # Frame to enforce the 16:9 aspect ratio in the UI
        image_frame = ttk.Frame(preview_container, width=self.DISPLAY_WIDTH, height=self.DISPLAY_HEIGHT)
        image_frame.pack(pady=5)
        image_frame.pack_propagate(False) # Prevent the label from resizing the frame

        self.image_label = ttk.Label(image_frame, anchor=tk.CENTER)
        self.image_label.pack(fill=BOTH, expand=True)
        
        controls_frame = ttk.Frame(preview_container)
        controls_frame.pack(fill=X, expand=True)
        controls_frame.grid_columnconfigure(1, weight=1)
        self.prev_button = ttk.Button(controls_frame, text="<", command=self.show_previous, bootstyle="outline")
        self.prev_button.grid(row=0, column=0, padx=(0, 5))
        self.status_label = ttk.Label(controls_frame, text="No bikes selected", anchor=tk.CENTER)
        self.status_label.grid(row=0, column=1, sticky="ew")
        self.next_button = ttk.Button(controls_frame, text=">", command=self.show_next, bootstyle="outline")
        self.next_button.grid(row=0, column=2, padx=(5, 0))

        # --- HIERARCHY & CONTROLS (BOTTOM) ---
        hierarchy_container = ttk.Labelframe(self, text="4. Element Hierarchy", padding=10)
        hierarchy_container.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=5)
        hierarchy_container.grid_rowconfigure(0, weight=1)
        hierarchy_container.grid_columnconfigure(0, weight=1)
        
        self.hierarchy_listbox = tk.Listbox(hierarchy_container, height=6, exportselection=False)
        self.hierarchy_listbox.grid(row=0, column=0, columnspan=2, sticky="nsew")

        hierarchy_btns = ttk.Frame(hierarchy_container)
        hierarchy_btns.grid(row=1, column=0, sticky="ew", pady=(5,0))
        hierarchy_btns.grid_columnconfigure((0,1), weight=1)
        ttk.Button(hierarchy_btns, text="▲", command=self.move_element_up, bootstyle="outline").grid(row=0, column=0, sticky="ew", padx=(0,2))
        ttk.Button(hierarchy_btns, text="▼", command=self.move_element_down, bootstyle="outline").grid(row=0, column=1, sticky="ew")

        add_del_bar = ttk.Frame(hierarchy_container)
        add_del_bar.grid(row=1, column=1, sticky="ew", pady=(5,0), padx=(10,0))
        add_del_bar.grid_columnconfigure((0,1), weight=1)
        add_del_menu = ttk.Menubutton(add_del_bar, text="Add", bootstyle="outline")
        add_del_menu.grid(row=0, column=0, sticky="ew", padx=(0,2))
        menu = tk.Menu(add_del_menu, tearoff=0)
        menu.add_command(label="Text Element", command=lambda: self.add_element("text"))
        menu.add_command(label="Image Element", command=lambda: self.add_element("image"))
        add_del_menu["menu"] = menu
        ttk.Button(add_del_bar, text="Del", command=self.remove_element, bootstyle="outline-danger").grid(row=0, column=1, sticky="ew")

        edit_button = ttk.Button(hierarchy_container, text="Edit Selected Element...", command=self.open_element_editor, bootstyle="primary")
        edit_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0), ipady=5)
        
        self.populate_hierarchy_list()
        self.update_preview([])

    def render_preview(self, elements_override=None):
        if self.current_index == -1:
            self.image_label.config(image=self._get_placeholder()); return
        
        bike_id = self.selected_bikes[self.current_index]
        self.status_label.config(text=f"{bike_id} ({self.current_index + 1}/{len(self.selected_bikes)})")
        
        elements = elements_override if elements_override is not None else self.controller.get_setting("preview_elements", [])
        
        # Render on the full-size canvas in memory
        final_image = Image.new("RGBA", (self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT))

        try:
            for elem in elements:
                if not elem.get("visible", True): continue
                elem_type = elem.get("type")

                if elem_type == "background":
                    path = elem.get("path")
                    if path and os.path.exists(path):
                        with Image.open(path).convert("RGBA") as bg_img:
                            self._paste_image_element(final_image, bg_img, elem)
                    else:
                        color_img = Image.new("RGBA", final_image.size, elem.get("color", "#FFFFFF"))
                        final_image.paste(color_img, (0,0))
                
                elif elem_type in ["bike_image", "image"]:
                    thumb_folder = self.controller.get_setting("thumbnail_folder_path")
                    source_path = os.path.join(thumb_folder, f"{bike_id}.png") if elem_type == "bike_image" else elem.get("path")
                    if source_path and os.path.exists(source_path):
                        with Image.open(source_path).convert("RGBA") as fg_img:
                            self._paste_image_element(final_image, fg_img, elem)

                elif elem_type == "text":
                    text_to_draw = ""
                    source = elem.get("dataSource")
                    if source == "Bike ID": text_to_draw = bike_id
                    elif source == "Bike Name":
                        bike_name = next((name for name, b_id in self.bike_data if b_id == bike_id), bike_id)
                        text_to_draw = bike_name
                    elif source == "Mod Name": text_to_draw = self.current_mod_name
                    elif source == "Static Text": text_to_draw = elem.get("staticText", "")
                    if text_to_draw:
                        self._draw_text_element(final_image, text_to_draw, elem)

            rgb_img = final_image.convert('RGB')
            # Downscale the final render ONLY for display in the UI
            rgb_img.thumbnail((self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), Image.Resampling.LANCZOS)
            self.current_image_tk = ImageTk.PhotoImage(rgb_img)
            self.image_label.config(image=self.current_image_tk)

        except Exception as e:
            print(f"Error rendering preview: {e}")
            self.image_label.config(image=self._get_placeholder("Error"))

    def _get_placeholder(self, text="No bikes selected"):
        # Create placeholder at the display size
        size = (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)
        img = Image.new('RGB', size, color=self.winfo_toplevel().style.colors.get('dark'))
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("arial.ttf", 24)
        except IOError: font = ImageFont.load_default()
        draw.text((size[0]/2, size[1]/2), text, font=font, anchor="mm", fill=self.winfo_toplevel().style.colors.get('light'))
        self.current_image_tk = ImageTk.PhotoImage(img) # Keep reference
        return self.current_image_tk

    # --- NO CHANGES to other methods, they adapt to the new PREVIEW size automatically ---
    # (Rest of the file is identical)
    def populate_hierarchy_list(self):
        current_selection = self.hierarchy_listbox.curselection()
        self.hierarchy_listbox.delete(0, tk.END)
        elements = self.controller.get_setting("preview_elements", [])
        for element in elements:
            vis_char = "●" if element.get("visible", True) else "○"
            self.hierarchy_listbox.insert(tk.END, f' {vis_char} {element.get("name", "Untitled")}')
        
        if current_selection and current_selection[0] < self.hierarchy_listbox.size():
            self.hierarchy_listbox.selection_set(current_selection[0])
            self.hierarchy_listbox.activate(current_selection[0])

    def open_element_editor(self):
        if self.editor_window and self.editor_window.winfo_exists():
            self.editor_window.lift(); return
        selection_indices = self.hierarchy_listbox.curselection()
        if not selection_indices:
            messagebox.showinfo("No Selection", "Please select an element from the hierarchy list to edit.", parent=self); return
        index = selection_indices[0]
        elements = self.controller.get_setting("preview_elements", [])
        if index < len(elements):
            element_data = elements[index]
            self.editor_window = ElementEditorWindow(
                parent=self, controller=self.controller, element_data=element_data, element_index=index,
                live_update_callback=self._handle_live_update, close_callback=self._handle_editor_close
            )

    def _handle_live_update(self, index, temp_data):
        current_elements = self.controller.get_setting("preview_elements", [])
        temp_elements = copy.deepcopy(current_elements)
        if index < len(temp_elements):
            temp_elements[index] = temp_data
            self.render_preview(elements_override=temp_elements)

    def _handle_editor_close(self):
        self.editor_window = None
        self.on_config_update()

    def add_element(self, elem_type):
        elements = self.controller.get_setting("preview_elements", [])
        new_elem = {}
        if elem_type == "text":
            new_elem = {"id": str(uuid.uuid4()), "name": "New Text", "type": "text", "visible": True, "dataSource": "Static Text", "staticText": "Hello", "font_path": "arial.ttf", "size": 80, "color": "#FFFFFF", "align": "center", "pos_x": self.PREVIEW_WIDTH//2, "pos_y": self.PREVIEW_HEIGHT//2, "outline_size": 1, "outline_color": "#000000", "rotation": 0}
        elif elem_type == "image":
            new_elem = {"id": str(uuid.uuid4()), "name": "New Image", "type": "image", "visible": True, "path": "", "pos_x": self.PREVIEW_WIDTH//2, "pos_y": self.PREVIEW_HEIGHT//2, "scale": 0.5, "rotation": 0, "aspect_ratio": "fit"}
        else: return
        elements.append(new_elem)
        self.controller.update_setting("preview_elements", elements, broadcast=True)
        new_index = len(elements) - 1
        self.hierarchy_listbox.selection_clear(0, tk.END)
        self.hierarchy_listbox.selection_set(new_index)
        self.hierarchy_listbox.activate(new_index)

    def remove_element(self):
        selection_indices = self.hierarchy_listbox.curselection()
        if not selection_indices: return
        index = selection_indices[0]
        elements = self.controller.get_setting("preview_elements", [])
        if elements[index].get("type") in ["background", "bike_image"]:
            messagebox.showwarning("Action Denied", "The Background and Bike Image layers cannot be deleted.", parent=self); return
        del elements[index]
        self.controller.update_setting("preview_elements", elements, broadcast=True)
        new_selection_index = min(index, self.hierarchy_listbox.size() - 2)
        if new_selection_index >= 0:
            self.hierarchy_listbox.selection_set(new_selection_index)
            self.hierarchy_listbox.activate(new_selection_index)

    def move_element(self, direction):
        selection_indices = self.hierarchy_listbox.curselection()
        if not selection_indices: return
        index = selection_indices[0]
        elements = self.controller.get_setting("preview_elements", [])
        new_index = index + direction
        if 0 <= new_index < len(elements):
            elements.insert(new_index, elements.pop(index))
            self.controller.update_setting("preview_elements", elements, broadcast=True)
            self.hierarchy_listbox.selection_set(new_index)
            self.hierarchy_listbox.activate(new_index)

    def move_element_up(self): self.move_element(-1)
    def move_element_down(self): self.move_element(1)

    def update_preview(self, selected_bike_ids, mod_name=""):
        self.selected_bikes = selected_bike_ids
        self.current_mod_name = mod_name
        self.current_index = 0 if self.selected_bikes else -1
        is_empty = not self.selected_bikes
        self.prev_button.config(state=tk.DISABLED if is_empty else tk.NORMAL)
        self.next_button.config(state=tk.DISABLED if is_empty else tk.NORMAL)
        if is_empty: self.status_label.config(text="No bikes selected")
        self.render_preview()
        
    def _paste_image_element(self, final_image, source_image, settings):
        scale = float(settings.get("scale", 1.0))
        rotation = int(settings.get("rotation", 0))
        pos_x, pos_y = int(settings.get("pos_x", self.PREVIEW_WIDTH//2)), int(settings.get("pos_y", self.PREVIEW_HEIGHT//2))
        aspect_ratio = settings.get("aspect_ratio", "fit")
        if aspect_ratio == "stretch":
            img_to_paste = source_image.resize(final_image.size, Image.Resampling.LANCZOS)
        else: 
            new_size = (int(final_image.width * scale), int(final_image.height * scale))
            img_to_paste = source_image.copy()
            img_to_paste.thumbnail(new_size, Image.Resampling.LANCZOS)
        if rotation != 0:
            img_to_paste = img_to_paste.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
        offset = (pos_x - img_to_paste.width // 2, pos_y - img_to_paste.height // 2)
        final_image.paste(img_to_paste, offset, img_to_paste)

    def _draw_text_element(self, image, text, settings):
        try: font = ImageFont.truetype(settings.get("font_path"), int(settings.get("size")))
        except (IOError, ValueError, TypeError): font = ImageFont.load_default()
        rotation = int(settings.get("rotation", 0))
        outline_size = int(settings.get("outline_size", 0))
        pos_x, pos_y = int(settings.get("pos_x", self.PREVIEW_WIDTH//2)), int(settings.get("pos_y", self.PREVIEW_HEIGHT//2))
        text_bbox = font.getbbox(text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        padding = outline_size * 2
        temp_size = (text_width + padding, text_height + padding)
        txt_img = Image.new('RGBA', temp_size, (255, 255, 255, 0))
        d = ImageDraw.Draw(txt_img)
        draw_pos = (padding/2 - text_bbox[0], padding/2 - text_bbox[1])
        if outline_size > 0:
            outline_color = settings.get("outline_color", "#000000")
            for i in range(-outline_size, outline_size + 1):
                for j in range(-outline_size, outline_size + 1):
                    if i != 0 or j != 0:
                        d.text((draw_pos[0] + i, draw_pos[1] + j), text, font=font, fill=outline_color)
        d.text(draw_pos, text, font=font, fill=settings.get("color", "#FFFFFF"))
        if rotation != 0:
            txt_img = txt_img.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
        final_pos_x = pos_x - (txt_img.width / 2)
        final_pos_y = pos_y - (txt_img.height / 2)
        image.paste(txt_img, (int(final_pos_x), int(final_pos_y)), txt_img)

    def show_next(self):
        if not self.selected_bikes: return
        self.current_index = (self.current_index + 1) % len(self.selected_bikes)
        self.render_preview()
        
    def show_previous(self):
        if not self.selected_bikes: return
        self.current_index = (self.current_index - 1 + len(self.selected_bikes)) % len(self.selected_bikes)
        self.render_preview()