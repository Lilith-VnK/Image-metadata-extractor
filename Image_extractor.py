import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
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

def analyze_image(exif_dict, img):
    is_modified = False
    software_used = []
    origins = []
    has_exif = False

    if exif_dict and "0th" in exif_dict:
        has_exif = True
        software = exif_dict["0th"].get(piexif.ImageIFD.Software)
        if software:
            try:
                sw_str = software.decode('utf-8', 'ignore').lower()
                software_used.append(sw_str)
                if any(x in sw_str for x in ['photoshop', 'lightroom', 'gimp', 'canva', 'snapseed', 'picsart', 'vsco']):
                    is_modified = True
                if any(x in sw_str for x in ['instagram', 'facebook', 'twitter', 'tiktok', 'whatsapp']):
                    origins.append("social_media_exif_tag")
            except:
                pass

    try:
        icc = img.info.get('icc_profile', b'').lower()
        if b'cnrgb' in icc or b'facebook' in icc:
            origins.append("meta_icc_profile")
        if b'google' in icc:
            origins.append("google_icc_profile")
    except:
        pass

    if not has_exif:
        origins.append("stripped_exif_possible_social_media")

    return {
        "is_modified": is_modified,
        "software_detected": list(set(software_used)),
        "detected_origins": list(set(origins))
    }

def process_image(filepath):
    data = {}
    try:
        with Image.open(filepath) as img:
            data["format"] = img.format
            data["mode"] = img.mode
            data["width"] = img.width
            data["height"] = img.height
            
            exif_raw = img.info.get('exif')
            if not exif_raw:
                data["analysis"] = analyze_image(None, img)
                return data
                
            exif_dict = piexif.load(exif_raw)
            data["analysis"] = analyze_image(exif_dict, img)
            
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
    
    result = process_image(filepath)
    
    try:
        os.remove(filepath)
    except:
        pass
        
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
