# --- Filename: src/packaging_sounds.py ---
import os
import zipfile
import io
from PIL import Image

def create_sound_mod_package(output_library_path, mod_name, selected_bikes, sound_paths, thumbnail_folder, background_path, log_callback):
    """
    Handles the logic for creating and packaging sound mods, now with correct
    image compositing to prevent transparency issues.
    """
    log_callback(f"Output library: {output_library_path}")

    mod_path = os.path.join(output_library_path, mod_name)
    try:
        os.makedirs(mod_path, exist_ok=True)
        log_callback(f"Output directory set to: {mod_path}")
    except OSError as e:
        log_callback(f"ERROR: Failed to create mod directory at '{mod_path}'. Reason: {e}")
        return False

    has_errors = False
    for bike_id in selected_bikes:
        log_callback(f"  - Packaging bike: {bike_id}")
        zip_path = os.path.join(mod_path, f"{bike_id}.zip")

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add sound files
                for _, sound_path in sound_paths.items():
                    arcname = f"{bike_id}/{os.path.basename(sound_path)}"
                    zipf.write(sound_path, arcname)
                log_callback(f"    - Added 4 sound files to {os.path.basename(zip_path)}")

                # --- CORRECTED IMAGE COMPOSITING LOGIC ---
                source_img_path = os.path.join(thumbnail_folder, f"{bike_id}.png")
                if not os.path.exists(source_img_path):
                    log_callback(f"    - WARNING: Thumbnail for {bike_id} not found. Skipping preview.jpg.")
                    continue

                try:
                    with Image.open(source_img_path).convert("RGBA") as fg_img:
                        bg_img_final = None
                        # Load custom background or create a default white one
                        if background_path and os.path.exists(background_path):
                            with Image.open(background_path).convert("RGBA") as bg_img:
                                # Resize background to match the bike image's dimensions
                                bg_img_final = bg_img.resize(fg_img.size, Image.Resampling.LANCZOS)
                        else:
                            bg_img_final = Image.new("RGBA", fg_img.size, "WHITE")

                        # Paste the bike (foreground) onto the background using its alpha mask
                        bg_img_final.paste(fg_img, (0, 0), fg_img)
                        
                        # Convert the final composite image to RGB (removes alpha)
                        rgb_img = bg_img_final.convert('RGB')
                        
                        # Save to an in-memory byte stream as a JPEG
                        img_byte_arr = io.BytesIO()
                        rgb_img.save(img_byte_arr, format='JPEG', quality=90)
                        img_byte_arr.seek(0)
                        
                        zipf.writestr(f"{bike_id}/preview.jpg", img_byte_arr.read())
                        log_callback(f"    - Added preview.jpg for {bike_id}")

                except Exception as img_e:
                    log_callback(f"    - ERROR: Failed to process image for {bike_id}. Reason: {img_e}")
                    has_errors = True
            
            log_callback(f"    - Successfully created {os.path.basename(zip_path)}")

        except Exception as e:
            log_callback(f"    - FATAL ERROR creating zip for {bike_id}: {e}")
            has_errors = True
            return False

    return not has_errors