import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, ImageStat
import piexif

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = "uploads"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def safe_div(n, d):
    return n / d if d else 0

def convert_gps(coord, ref):
    value = safe_div(coord[0][0], coord[0][1]) + \
            (safe_div(coord[1][0], coord[1][1]) / 60.0) + \
            (safe_div(coord[2][0], coord[2][1]) / 3600.0)
    if ref in [b'S', b'W', 'S', 'W']:
        value = -value
    return value

def check_letterbox(img):
    try:
        small = img.convert('L').resize((100, 100))
        w, h = small.size
        
        top = small.crop((0, 0, w, 15))
        bottom = small.crop((0, h-15, w, h))
        mid = small.crop((0, 15, w, h-15))
        
        st = ImageStat.Stat(top)
        sb = ImageStat.Stat(bottom)
        sm = ImageStat.Stat(mid)
        
        if st.stddev[0] < 8 and sb.stddev[0] < 8 and sm.stddev[0] > 15:
            return True
            
        left = small.crop((0, 0, 15, h))
        right = small.crop((w-15, 0, w, h))
        mid_v = small.crop((15, 0, w-15, h))
        
        sl = ImageStat.Stat(left)
        sr = ImageStat.Stat(right)
        sm_v = ImageStat.Stat(mid_v)
        
        if sl.stddev[0] < 8 and sr.stddev[0] < 8 and sm_v.stddev[0] > 15:
            return True
    except:
        pass
    return False

def analyze_image(exif_dict, img, original_filename, filesize):
    features = {
        "camera_photo": False,
        "camera_photo_recaptured": False,
        "screen_capture": False,
        "edited": False,
        "ai_generated": False,
        "platform_reencoded": False
    }
    software_used = []
    origins = []
    notes = []
    has_exif = False
    has_camera_model = False
    is_screenshot_heuristics = False

    screenshot_keywords = ['screenshot', 'screen_shot', 'capture', 'screencap', 'screencast', 'prtsc', 'snap', 'ss-']
    editing_software = ['photoshop', 'lightroom', 'gimp', 'canva', 'snapseed', 'picsart', 'vsco', 'remini', 'faceapp', 'meitu', 'capcut', 'b612', 'beautyplus', 'illustrator', 'coreldraw', 'polarr', 'pixlr']
    social_platforms = ['instagram', 'facebook', 'twitter', 'tiktok', 'whatsapp', 'telegram', 'discord', 'line', 'wechat', 'reddit', 'messenger']
    ai_generators = ['midjourney', 'stable diffusion', 'dall-e', 'novelai', 'firefly', 'bing image creator', 'comfyui']
    screenshot_software = ['sharex', 'snipping tool', 'mac os x', 'gnome-screenshot', 'spectacle', 'android', 'screenshot']
    social_media_dimensions = [720, 800, 1024, 1080, 1280, 1350, 1600, 2048]

    filename_lower = original_filename.lower()
    if any(x in filename_lower for x in screenshot_keywords):
        is_screenshot_heuristics = True
        origins.append("screenshot_from_filename")
    if any(x in filename_lower for x in social_platforms):
        origins.append("social_media_from_filename")

    for key, value in img.info.items():
        if isinstance(value, bytes):
            try:
                value = value.decode('utf-8', 'ignore').lower()
            except:
                value = ""
        elif isinstance(value, str):
            value = value.lower()
        else:
            value = str(value).lower()
            
        key_lower = str(key).lower()

        if any(x in value for x in screenshot_keywords):
            is_screenshot_heuristics = True
            origins.append("screenshot_from_metadata")
        if any(x in value for x in ai_generators):
            features["ai_generated"] = True
            origins.append("ai_generated_from_metadata")
        if any(x in value for x in social_platforms):
            origins.append("social_media_from_metadata")
            
        if key_lower in ['software', 'processingsoftware', 'creator', 'description']:
            software_used.append(value)
            if any(x in value for x in screenshot_software):
                is_screenshot_heuristics = True

    if exif_dict:
        if "0th" in exif_dict and exif_dict["0th"]:
            has_exif = True
            make = exif_dict["0th"].get(piexif.ImageIFD.Make)
            model = exif_dict["0th"].get(piexif.ImageIFD.Model)
            software = exif_dict["0th"].get(piexif.ImageIFD.Software)
            
            if make or model:
                has_camera_model = True

            if software:
                try:
                    sw_str = software.decode('utf-8', 'ignore').lower()
                    software_used.append(sw_str)
                    if any(x in sw_str for x in editing_software):
                        features["edited"] = True
                    if any(x in sw_str for x in social_platforms):
                        origins.append("social_media_exif_tag")
                    if any(x in sw_str for x in screenshot_software):
                        is_screenshot_heuristics = True
                        origins.append("screenshot_from_exif")
                    if any(x in sw_str for x in ai_generators):
                        features["ai_generated"] = True
                        origins.append("ai_generated_from_exif")
                except:
                    pass

        if "Exif" in exif_dict and exif_dict["Exif"]:
            has_exif = True
            user_comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment)
            if user_comment:
                try:
                    uc_str = user_comment.decode('utf-8', 'ignore').lower()
                    if 'screenshot' in uc_str:
                        is_screenshot_heuristics = True
                        origins.append("screenshot_from_exif_comment")
                except:
                    pass

    try:
        icc = img.info.get('icc_profile', b'').lower()
        if b'cnrgb' in icc or b'facebook' in icc:
            origins.append("meta_icc_profile")
        if b'google' in icc:
            origins.append("google_icc_profile")
        if b'display p3' in icc and img.format == 'PNG' and not has_camera_model:
            is_screenshot_heuristics = True
            origins.append("ios_mac_screenshot_profile")
        if b'srgb iec61966-2.1' in icc and img.format == 'PNG' and not has_camera_model:
            origins.append("generic_srgb_png_possible_screenshot")
    except:
        pass

    is_letterboxed = check_letterbox(img)
    width, height = img.size
    max_dim = max(width, height)
    bpp = (filesize * 8) / (width * height) if (width * height) > 0 else 0

    if is_screenshot_heuristics or (img.format == 'PNG' and not has_exif):
        if is_letterboxed:
            features["camera_photo_recaptured"] = True
            origins.append("screenshot_of_photo_detected")
        else:
            features["screen_capture"] = True
    elif not has_exif and img.format == 'JPEG' and is_letterboxed:
        features["camera_photo_recaptured"] = True
        origins.append("screenshot_of_photo_sent_via_social_media")

    if not has_exif and img.format in ['JPEG', 'WEBP'] and not is_screenshot_heuristics and not features["camera_photo_recaptured"] and not features["edited"] and not features["ai_generated"]:
        features["platform_reencoded"] = True
        notes.append("All camera EXIF metadata is missing completely.")
        
        if max_dim in social_media_dimensions or (width == 720 and height == 1280):
            notes.append(f"Resolution ({width}x{height}) matches common social media compression scaling.")
        else:
            notes.append("Resolution does not match typical native camera sensor outputs.")
            
        if bpp < 1.5:
            notes.append(f"Low bits-per-pixel ratio ({bpp:.2f}) strongly indicates heavy platform re-compression.")

    if has_camera_model and not is_screenshot_heuristics and not features["ai_generated"] and not is_letterboxed and not features["edited"]:
        features["camera_photo"] = True
        notes.append("Contains original camera metadata and typical sensor characteristics.")

    if features["camera_photo_recaptured"]:
        features["screen_capture"] = False
        features["camera_photo"] = False
        notes.append("Detected letterboxing/borders on a screen capture, indicating a photo of a photo/screen.")

    verdict = "unknown"
    confidence = 0.0

    if features["ai_generated"]:
        verdict = "ai_generated"
        confidence = 0.95
    elif features["camera_photo_recaptured"]:
        verdict = "camera_photo_recaptured"
        confidence = 0.88
    elif features["screen_capture"]:
        verdict = "screen_capture"
        confidence = 0.90
    elif features["edited"]:
        verdict = "edited"
        confidence = 0.85
    elif features["platform_reencoded"]:
        verdict = "platform_reencoded"
        confidence = 0.88
    elif features["camera_photo"]:
        verdict = "camera_photo"
        confidence = 0.92

    return {
        "verdict": verdict,
        "confidence": confidence,
        "notes": notes,
        "features": features,
        "software_detected": list(set([s.strip() for s in software_used if s.strip()])),
        "detected_origins": list(set(origins))
    }

def process_image(filepath, original_filename):
    data = {}
    try:
        filesize = os.path.getsize(filepath)
        with Image.open(filepath) as img:
            data["format"] = img.format
            data["mode"] = img.mode
            data["width"] = img.width
            data["height"] = img.height
            data["filesize_bytes"] = filesize
            
            exif_raw = img.info.get('exif')
            exif_dict = None
            
            if exif_raw:
                try:
                    exif_dict = piexif.load(exif_raw)
                except:
                    pass
                    
            data["analysis"] = analyze_image(exif_dict, img, original_filename, filesize)
            
            if exif_dict:
                for ifd in ("0th", "Exif"):
                    for tag in exif_dict.get(ifd, {}):
                        try:
                            tag_name = piexif.TAGS[ifd][tag]["name"]
                            val = exif_dict[ifd][tag]
                            if isinstance(val, bytes):
                                val = val.decode('utf-8', 'ignore')
                            elif isinstance(val, tuple):
                                val = str(val)
                            data[tag_name] = val
                        except:
                            continue
                            
                gps = exif_dict.get("GPS", {})
                if gps:
                    lat = gps.get(piexif.GPSIFD.GPSLatitude)
                    lat_ref = gps.get(piexif.GPSIFD.GPSLatitudeRef)
                    lon = gps.get(piexif.GPSIFD.GPSLongitude)
                    lon_ref = gps.get(piexif.GPSIFD.GPSLongitudeRef)
                    if all([lat, lat_ref, lon, lon_ref]):
                        data["gps"] = {
                            "latitude": convert_gps(lat, lat_ref),
                            "longitude": convert_gps(lon, lon_ref)
                        }
    except Exception as e:
        data["error"] = str(e)
    return data

@app.route("/extract", methods=["POST"])
def extract():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
        
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    
    result = process_image(filepath, file.filename)
    
    try:
        os.remove(filepath)
    except:
        pass
        
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
