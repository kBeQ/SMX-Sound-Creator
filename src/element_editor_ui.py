# --- Filename: src/element_editor_ui.py ---
import tkinter as tk
from tkinter import filedialog, colorchooser
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame

class ElementEditorWindow(ttk.Toplevel):
    def __init__(self, parent, controller, element_data, element_index, live_update_callback, close_callback):
        super().__init__(parent)
        self.controller = controller
        self.element_data = element_data.copy()
        self.original_element_data = element_data.copy()
        self.element_index = element_index
        self.live_update_callback = live_update_callback
        self.close_callback = close_callback
        self.inspector_vars = {}
        self._is_populating = True

        self.title(f"Edit: {self.element_data.get('name', 'Element')}")
        self.geometry("450x650")
        self.transient(parent)
        self.grab_set()

        self.build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.after(100, lambda: setattr(self, '_is_populating', False))

    def build_ui(self):
        # ... (no changes to this method) ...
        for widget in self.winfo_children(): widget.destroy()
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=True)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        scroll_frame = ScrolledFrame(main_frame, autohide=True)
        scroll_frame.grid(row=0, column=0, sticky="nsew")
        scroll_frame.grid_columnconfigure(1, weight=1)
        elem_type = self.element_data.get("type")
        self.create_widget(scroll_frame, "Element Name:", 0, "name", "entry")
        self.create_widget(scroll_frame, "Visible:", 1, "visible", "checkbutton")
        ttk.Separator(scroll_frame).grid(row=2, column=0, columnspan=3, sticky='ew', pady=10)
        row_offset = 3
        if elem_type == "background": self.populate_background_widgets(scroll_frame, row_offset)
        elif elem_type == "bike_image": self.populate_bike_image_widgets(scroll_frame, row_offset)
        elif elem_type == "image": self.populate_image_widgets(scroll_frame, row_offset)
        elif elem_type == "text": self.populate_text_widgets(scroll_frame, row_offset)
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, sticky="sew", pady=(15, 0))
        btn_frame.grid_columnconfigure((0, 1), weight=1)
        ttk.Button(btn_frame, text="Save & Close", command=self.on_save, bootstyle="success").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel, bootstyle="secondary").grid(row=0, column=1, sticky="ew")

    def populate_background_widgets(self, parent, start_row):
        r = start_row
        if self.element_data.get("path"):
            self.create_widget(parent, "Image Path:", r, "path", "image_path_clearable"); r+=1
            self.create_widget(parent, "Aspect Ratio:", r, "aspect_ratio", "aspect_ratio"); r+=1
            self.create_widget(parent, "Position (X):", r, "pos_x", "spinbox", {"from_": -2048, "to": 2048}); r+=1
            self.create_widget(parent, "Position (Y):", r, "pos_y", "spinbox", {"from_": -2048, "to": 2048}); r+=1
            self.create_widget(parent, "Scale:", r, "scale", "spinbox", {"from_": 0.1, "to": 5.0, "increment": 0.05}); r+=1
            self.create_widget(parent, "Rotation:", r, "rotation", "spinbox", {"from_": -360, "to": 360}); r+=1
        else:
            self.create_widget(parent, "Image Path:", r, "path", "image_path_clearable"); r+=1
            self.create_widget(parent, "Solid Color:", r, "color", "color"); r+=1

    def populate_bike_image_widgets(self, parent, start_row):
        r = start_row
        self.create_widget(parent, "Aspect Ratio:", r, "aspect_ratio", "aspect_ratio"); r+=1
        self.create_widget(parent, "Position (X):", r, "pos_x", "spinbox", {"from_": -2048, "to": 2048}); r+=1
        self.create_widget(parent, "Position (Y):", r, "pos_y", "spinbox", {"from_": -2048, "to": 2048}); r+=1
        self.create_widget(parent, "Scale:", r, "scale", "spinbox", {"from_": 0.1, "to": 3.0, "increment": 0.05}); r+=1
        self.create_widget(parent, "Rotation:", r, "rotation", "spinbox", {"from_": -360, "to": 360}); r+=1
    
    def populate_image_widgets(self, parent, start_row):
        r = start_row
        self.create_widget(parent, "Image Path:", r, "path", "image_path_clearable"); r+=1
        self.create_widget(parent, "Aspect Ratio:", r, "aspect_ratio", "aspect_ratio"); r+=1
        self.create_widget(parent, "Position (X):", r, "pos_x", "spinbox", {"from_": -2048, "to": 2048}); r+=1
        self.create_widget(parent, "Position (Y):", r, "pos_y", "spinbox", {"from_": -2048, "to": 2048}); r+=1
        self.create_widget(parent, "Scale:", r, "scale", "spinbox", {"from_": 0.1, "to": 5.0, "increment": 0.05}); r+=1
        self.create_widget(parent, "Rotation:", r, "rotation", "spinbox", {"from_": -360, "to": 360}); r+=1

    def populate_text_widgets(self, parent, start_row):
        r = start_row
        self.create_widget(parent, "Data Source:", r, "dataSource", "combobox", {"values": ["Bike ID", "Bike Name", "Mod Name", "Static Text"]}); r+=1
        if self.element_data.get("dataSource") == "Static Text":
            self.create_widget(parent, "Static Text:", r, "staticText", "entry"); r+=1
        font_names = self.controller.get_font_names()
        self.create_widget(parent, "Font:", r, "font_path", "combobox", {"values": font_names, "rebuild_ui_on_select": False}); r+=1
        self.create_widget(parent, "Size:", r, "size", "spinbox", {"from_": 8, "to": 500}); r+=1
        self.create_widget(parent, "Rotation:", r, "rotation", "spinbox", {"from_": -360, "to": 360}); r+=1
        self.create_widget(parent, "Color:", r, "color", "color"); r+=1
        self.create_widget(parent, "Alignment:", r, "align", "combobox", {"values": ["left", "center", "right"], "rebuild_ui_on_select": False}); r+=1
        self.create_widget(parent, "Position (X):", r, "pos_x", "spinbox", {"from_": -2048, "to": 2048}); r+=1
        self.create_widget(parent, "Position (Y):", r, "pos_y", "spinbox", {"from_": -2048, "to": 2048}); r+=1
        ttk.Separator(parent).grid(row=r, column=0, columnspan=3, sticky='ew', pady=10); r+=1
        self.create_widget(parent, "Outline Size:", r, "outline_size", "spinbox", {"from_": 0, "to": 20}); r+=1
        self.create_widget(parent, "Outline Color:", r, "outline_color", "color"); r+=1

    # --- NO CHANGES to other methods ---
    # (Rest of the file is identical)
    def create_widget(self, parent, label, row, key, widget_type, options=None):
        options = options or {}
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=4, padx=5)
        var = self.create_var(key, self.element_data.get(key))
        widget_frame = ttk.Frame(parent)
        widget_frame.grid(row=row, column=1, sticky=tk.EW, padx=5)
        widget = None
        if widget_type == "entry":
            widget_frame.columnconfigure(0, weight=1)
            widget = ttk.Entry(widget_frame, textvariable=var)
        elif widget_type == "checkbutton":
            widget = ttk.Checkbutton(parent, variable=var, bootstyle="round-toggle")
            widget.grid(row=row, column=1, sticky=tk.W, padx=5)
            return
        elif widget_type in ["font", "image_path_clearable"]:
            widget_frame.columnconfigure(0, weight=1)
            ft = [("Font Files", "*.ttf *.otf")] if widget_type == "font" else [("Image Files", "*.png *.jpg *.jpeg *.bmp")]
            entry = ttk.Entry(widget_frame, textvariable=var, state="readonly")
            entry.grid(row=0, column=0, sticky=tk.EW)
            browse_btn = ttk.Button(widget_frame, text="...", command=lambda v=var: self.browse_for_path(v, ft), bootstyle="outline", width=4)
            browse_btn.grid(row=0, column=1, padx=(5,2))
            if widget_type == "image_path_clearable":
                clear_btn = ttk.Button(widget_frame, text="X", command=lambda v=var: (v.set(""), self.build_ui()), bootstyle="danger-outline", width=3)
                clear_btn.grid(row=0, column=2)
            return
        elif widget_type == "spinbox":
            widget_frame.columnconfigure(0, weight=1)
            widget = ttk.Spinbox(widget_frame, from_=options.get("from_", 0), to=options.get("to", 100), increment=options.get("increment", 1), textvariable=var, command=lambda: self.update_data(key, var.get()))
        elif widget_type == "color":
            widget_frame.columnconfigure(0, weight=1)
            widget = ttk.Button(widget_frame, textvariable=var, command=lambda v=var: self.choose_color(v), bootstyle="light")
        elif widget_type == "combobox":
            widget_frame.columnconfigure(0, weight=1)
            widget = ttk.Combobox(widget_frame, textvariable=var, values=options.get("values", []), state="readonly")
            if options.get("rebuild_ui_on_select", True):
                widget.bind("<<ComboboxSelected>>", lambda e: self.build_ui())
        elif widget_type == "aspect_ratio":
            widget_frame.columnconfigure(0, weight=1)
            widget = ttk.Combobox(widget_frame, textvariable=var, values=["Fit (Keep Ratio)", "Stretch to Fill"], state="readonly")
        if widget:
            widget.grid(row=0, column=0, sticky=tk.EW)

    def create_var(self, key, value):
        if key == 'font_path':
            display_name = self.controller.get_font_name_from_path(value)
            var = tk.StringVar(value=display_name)
        elif key == 'aspect_ratio':
            display_value = "Stretch to Fill" if value == "stretch" else "Fit (Keep Ratio)"
            var = tk.StringVar(value=display_value)
        elif isinstance(value, bool): var = tk.BooleanVar(value=value)
        elif isinstance(value, (int, float)): var = tk.DoubleVar(value=value)
        else: var = tk.StringVar(value=str(value) if value is not None else "")
        var.trace_add("write", lambda *a, k=key, v=var: self.update_data(k, v.get()))
        self.inspector_vars[key] = var
        return var

    def update_data(self, key, value):
        if self._is_populating: return
        value_to_store = None
        if key == 'font_path':
            value_to_store = self.controller.get_font_path(value)
        elif key == 'aspect_ratio':
            value_to_store = "stretch" if value == "Stretch to Fill" else "fit"
        else:
            original_value = self.element_data.get(key)
            try:
                if isinstance(original_value, bool): value_to_store = bool(value)
                elif isinstance(original_value, int): value_to_store = int(float(value))
                elif isinstance(original_value, float): value_to_store = float(value)
                else: value_to_store = value
            except (ValueError, TypeError): return

        self.element_data[key] = value_to_store
        if self.live_update_callback:
            self.live_update_callback(self.element_index, self.element_data)

    def choose_color(self, var):
        initial_color = var.get() if var.get() else "#FFFFFF"
        color = colorchooser.askcolor(title="Choose color", initialcolor=initial_color)
        if color and color[1]: var.set(color[1])

    def browse_for_path(self, var, filetypes):
        path = filedialog.askopenfilename(title="Select File", filetypes=filetypes)
        if path:
            var.set(path)
            if self.element_data.get('type') == 'background':
                self.build_ui()

    def on_save(self):
        elements = self.controller.get_setting("preview_elements", [])
        if self.element_index < len(elements):
            elements[self.element_index] = self.element_data
            self.controller.update_setting("preview_elements", elements, broadcast=True)
        self.destroy()

    def on_cancel(self):
        if self.live_update_callback:
             self.live_update_callback(self.element_index, self.original_element_data)
        self.destroy()
    
    def destroy(self):
        if self.close_callback:
            self.close_callback()
        super().destroy()