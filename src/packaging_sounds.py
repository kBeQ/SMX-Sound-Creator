# --- Filename: src/packaging_sounds.py ---
import os
import zipfile
import io
from PIL import Image, ImageDraw, ImageFont

def draw_rotated_text(image, text, settings):
    # This function is unchanged
    try:
        font_path = settings.get("font_path", "arial.ttf")
        font_size = int(settings.get("size", 20))
        font = ImageFont.truetype(font_path, font_size)
    except (IOError, ValueError, TypeError): 
        font = ImageFont.load_default()
    rotation = int(settings.get("rotation", 0))
    outline_size = int(settings.get("outline_size", 0))
    outline_color = settings.get("outline_color", "#000000")
    text_color = settings.get("color", "#FFFFFF")
    pos_x, pos_y = int(settings.get("pos_x", 128)), int(settings.get("pos_y", 128))
    text_bbox = font.getbbox(text)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    padding = outline_size * 2
    temp_size = (text_width + padding, text_height + padding)
    txt_img = Image.new('RGBA', temp_size, (255, 255, 255, 0))
    d = ImageDraw.Draw(txt_img)
    draw_pos = (padding/2 - text_bbox[0], padding/2 - text_bbox[1])
    if outline_size > 0:
        for i in range(-outline_size, outline_size + 1):
            for j in range(-outline_size, outline_size + 1):
                if i != 0 or j != 0:
                    d.text((draw_pos[0] + i, draw_pos[1] + j), text, font=font, fill=outline_color)
    d.text(draw_pos, text, font=font, fill=text_color)
    if rotation != 0:
        txt_img = txt_img.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
    final_pos_x = pos_x - (txt_img.width / 2)
    final_pos_y = pos_y - (txt_img.height / 2)
    image.paste(txt_img, (int(final_pos_x), int(final_pos_y)), txt_img)

def paste_rotated_image(final_image, source_image, settings):
    # This function is unchanged
    scale = float(settings.get("scale", 1.0))
    rotation = int(settings.get("rotation", 0))
    pos_x, pos_y = int(settings.get("pos_x", 128)), int(settings.get("pos_y", 128))
    aspect_ratio = settings.get("aspect_ratio", "fit")
    if aspect_ratio == "stretch":
        img_to_paste = source_image.resize((final_image.width, final_image.height), Image.Resampling.LANCZOS)
    else: # "fit"
        new_size = (int(final_image.width * scale), int(final_image.height * scale))
        img_to_paste = source_image.copy()
        img_to_paste.thumbnail(new_size, Image.Resampling.LANCZOS)
    if rotation != 0:
        img_to_paste = img_to_paste.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
    offset = (pos_x - img_to_paste.width // 2, pos_y - img_to_paste.height // 2)
    final_image.paste(img_to_paste, offset, img_to_paste)

def generate_preview_image(bike_id, mod_name, thumbnail_folder, preview_elements, bike_data):
    # This function is unchanged
    final_image = Image.new("RGBA", (1920, 1080))
    for elem in preview_elements:
        if not elem.get("visible", True): continue
        elem_type = elem.get("type")
        if elem_type == "background":
            path = elem.get("path")
            if path and os.path.exists(path):
                with Image.open(path).convert("RGBA") as bg_img:
                    paste_rotated_image(final_image, bg_img, elem)
            else:
                color_img = Image.new("RGBA", final_image.size, elem.get("color", "#FFFFFF"))
                final_image.paste(color_img, (0,0))
        elif elem_type in ["bike_image", "image"]:
            thumb_folder = thumbnail_folder
            source_path = os.path.join(thumb_folder, f"{bike_id}.png") if elem_type == "bike_image" else elem.get("path")
            if source_path and os.path.exists(source_path):
                with Image.open(source_path).convert("RGBA") as fg_img:
                    paste_rotated_image(final_image, fg_img, elem)
        elif elem_type == "text":
            text_to_draw = ""
            source = elem.get("dataSource")
            if source == "Bike ID": text_to_draw = bike_id
            elif source == "Bike Name":
                bike_name = next((name for name, b_id in bike_data if b_id == bike_id), bike_id)
                text_to_draw = bike_name
            elif source == "Mod Name": text_to_draw = mod_name
            elif source == "Static Text": text_to_draw = elem.get("staticText", "")
            if text_to_draw:
                draw_rotated_text(final_image, text_to_draw, elem)
    return final_image.convert('RGB')

def create_sound_mod_package(output_library_path, mod_name, selected_bikes, sound_paths, thumbnail_folder, preview_elements, bike_data, log_callback):
    mod_path = os.path.join(output_library_path, mod_name)
    try: os.makedirs(mod_path, exist_ok=True)
    except OSError as e: log_callback(f"ERROR: Failed to create mod directory at '{mod_path}'. Reason: {e}"); return False

    has_errors = False
    for bike_id in selected_bikes:
        log_callback(f"  - Packaging bike: {bike_id}")
        zip_filename = f"{bike_id} {mod_name}.zip"
        zip_path = os.path.join(mod_path, zip_filename)

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                num_sounds = len(sound_paths)
                for _, sound_path in sound_paths.items():
                    arcname = f"{bike_id}/{os.path.basename(sound_path)}"
                    zipf.write(sound_path, arcname)
                log_callback(f"    - Added {num_sounds} sound file(s) to {os.path.basename(zip_path)}")

                try:
                    # Generate the high-quality 1920x1080 image in memory
                    preview_image = generate_preview_image(bike_id, mod_name, thumbnail_folder, preview_elements, bike_data)
                    
                    # Save a copy of the preview image as a PNG file next to the zip
                    png_filename_base = os.path.splitext(zip_filename)[0]
                    png_path = os.path.join(mod_path, f"{png_filename_base}.png")
                    preview_image.save(png_path, 'PNG')
                    log_callback(f"    - Saved external preview as {os.path.basename(png_path)}")
                    
                    # Convert the final RGB image to JPEG format in memory for the zip
                    img_byte_arr = io.BytesIO()
                    preview_image.save(img_byte_arr, format='JPEG', quality=95) # High quality JPEG
                    
                    # Write the byte array to the zip file as preview.jpg
                    zipf.writestr(f"{bike_id}/preview.jpg", img_byte_arr.getvalue())
                    log_callback(f"    - Added preview.jpg for {bike_id} with custom layers.")

                except Exception as img_e:
                    log_callback(f"    - ERROR: Failed to process image for {bike_id}. Reason: {img_e}"); has_errors = True
            
            log_callback(f"    - Successfully created {os.path.basename(zip_path)}")
        except Exception as e:
            log_callback(f"    - FATAL ERROR creating zip for {bike_id}: {e}"); has_errors = True; return False
    return not has_errors