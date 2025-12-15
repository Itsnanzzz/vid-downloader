import os
import random
import string
import time
import threading
import uuid
from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
# CORS: allow frontend dev server & custom headers
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-API-Key"],
            "expose_headers": ["Content-Disposition"]
        }
    },
    supports_credentials=False
)

# ------------------------------
# CONFIG
# ------------------------------
UPLOAD_FOLDER = "temp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "ico"}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB
DELETE_AFTER_SECONDS = 60     # hapus file otomatis setelah 1 menit
API_KEY = os.environ.get("API_KEY")  # ambil dari environment


# ------------------------------
# API KEY CHECK
# ------------------------------
def require_api_key():
    client_key = request.headers.get("x-api-key") or request.args.get("key")
    if API_KEY:  # jika API key diset, wajib cocok
        if client_key != API_KEY:
            return False
    return True


# ------------------------------
# Generate nama file custom (lebih aman)
# ------------------------------
def random_name(base):
    unique_id = str(uuid.uuid4())[:8]  # lebih unique dari random 6 digit
    timestamp = str(int(time.time()))[-6:]
    return f"{base}-{timestamp}-{unique_id}"


# ------------------------------
# Auto-delete worker
# ------------------------------
def auto_delete_worker():
    while True:
        try:
            now = time.time()

            for filename in os.listdir(UPLOAD_FOLDER):
                path = os.path.join(UPLOAD_FOLDER, filename)

                if os.path.isfile(path):
                    age = now - os.path.getmtime(path)

                    if age > DELETE_AFTER_SECONDS:
                        try:
                            os.remove(path)
                            print(f"[AUTO-DELETE] {filename}")
                        except Exception as e:
                            print(f"[ERROR] Failed to delete {filename}: {e}")

            time.sleep(30)  # cek setiap 30 detik
        except Exception as e:
            print(f"[ERROR] Auto-delete worker: {e}")
            time.sleep(30)


thread = threading.Thread(target=auto_delete_worker, daemon=True)
thread.start()


# ------------------------------
# Helper: Clean up file safely
# ------------------------------
def safe_remove(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"[ERROR] Failed to remove {filepath}: {e}")


# ------------------------------
# API: Convert Image
# ------------------------------
@app.route("/api/convert", methods=["POST"])
def convert_image():
    orig_path = None
    output_path = None

    try:
        # API Key
        if not require_api_key():
            return jsonify({"error": "unauthorized"}), 401

        if "file" not in request.files:
            return jsonify({"error": "no file uploaded"}), 400

        file = request.files["file"]
        target_format = (request.form.get("format") or "").lower()

        if not file or file.filename == "":
            return jsonify({"error": "invalid file"}), 400

        # Validasi format
        if target_format not in ALLOWED_EXT:
            return jsonify({"error": "invalid format"}), 400

        # Normalize format for Pillow
        pillow_format = target_format
        if target_format == "jpg":
            pillow_format = "jpeg"

        # Size limiter
        file.seek(0, os.SEEK_END)
        size = file.tell()
        if size > MAX_SIZE:
            return jsonify({"error": "file too large (max 10MB)"}), 413
        file.seek(0)

        # Simpan file original sementara
        orig_name = secure_filename(file.filename)
        orig_path = os.path.join(UPLOAD_FOLDER, f"orig-{uuid.uuid4()}-{orig_name}")
        file.save(orig_path)

        # Load gambar dengan error handling
        try:
            img = Image.open(orig_path)
            img.load()  # force load untuk detect corrupt file
        except Exception as e:
            safe_remove(orig_path)
            return jsonify({"error": f"invalid image file: {str(e)}"}), 400

        # Generate nama output
        new_name = random_name("imgconvert") + "." + target_format
        output_path = os.path.join(UPLOAD_FOLDER, new_name)

        # Convert + compress dengan handling per format
        save_kwargs = {"optimize": True}

        if pillow_format in ["jpeg"]:
            # JPEG tidak support transparency
            if img.mode in ["RGBA", "LA", "P"]:
                # Convert dengan background putih
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")
            save_kwargs["quality"] = 85

        elif pillow_format == "webp":
            # WebP support transparency
            if img.mode == "P":
                img = img.convert("RGBA")
            save_kwargs["quality"] = 85

        elif pillow_format == "png":
            # PNG support transparency
            if img.mode == "P":
                img = img.convert("RGBA")

        elif pillow_format == "ico":
            # ICO format special handling
            if img.mode == "P":
                img = img.convert("RGBA")
            # ICO biasanya untuk icon kecil
            sizes = [(16, 16), (32, 32), (48, 48)]
            img.save(output_path, format="ICO", sizes=sizes)
            safe_remove(orig_path)
            return jsonify({
                "download_url": f"/api/download/{new_name}",
                "filename": new_name
            })

        # Save dengan format yang sudah dinormalisasi
        img.save(output_path, format=pillow_format.upper(), **save_kwargs)

        # Hapus file original setelah sukses convert
        safe_remove(orig_path)

        return jsonify({
            "download_url": f"/api/download/{new_name}",
            "filename": new_name
        })

    except Exception as e:
        # Cleanup jika ada error
        safe_remove(orig_path)
        safe_remove(output_path)
        print(f"[ERROR] Conversion failed: {e}")
        return jsonify({"error": f"conversion failed: {str(e)}"}), 500


# ------------------------------
# API: Download File
# ------------------------------
@app.route("/api/download/<filename>")
def download_file(filename):
    try:
        # API Key (opsional untuk download)
        if not require_api_key():
            return jsonify({"error": "unauthorized"}), 401

        # Security check: prevent path traversal
        filename = secure_filename(filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        if not os.path.exists(filepath):
            return jsonify({"error": "file not found"}), 404

        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return jsonify({"error": "download failed"}), 500


# ------------------------------
# Health check
# ------------------------------
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "timestamp": time.time()})


# ------------------------------
# Handle OPTIONS for CORS preflight
# ------------------------------
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-API-Key')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response


# ------------------------------
# Vercel handler
# ------------------------------
def handler(request):
    return app(request)


# ------------------------------
# local run
# ------------------------------
if __name__ == "__main__":
    print(f"[INFO] Upload folder: {UPLOAD_FOLDER}")
    print(f"[INFO] Auto-delete after: {DELETE_AFTER_SECONDS}s")
    print(f"[INFO] API Key required: {bool(API_KEY)}")
    app.run(port=5000, debug=True)