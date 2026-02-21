from flask import Flask, render_template, request, jsonify, send_file
import os, base64, time
from io import BytesIO
from PIL import Image, ImageOps

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/photobooth')
def photobooth():
    return render_template('index.html')

def paste_rotated(canvas, img, center_x, center_y, angle, photo_w, photo_h):
    img_fit = ImageOps.fit(img, (photo_w, photo_h), centering=(0.5, 0.5))
    rotated = img_fit.rotate(-angle, expand=True, resample=Image.BICUBIC)
    paste_x = center_x - rotated.width // 2
    paste_y = center_y - rotated.height // 2
    canvas.paste(rotated, (paste_x, paste_y), rotated)

TEMPLATES = {
    "soft": {
        "file": "template_soft.png",
        "photo_w": 330, "photo_h": 250,
        "frames": [
            (464, 345, 0),
            (464, 615, 0),
            (464, 885, 0),
        ]
    },
    "dark": {
        "file": "template_dark.png",
        "photo_w": 330, "photo_h": 250,
        "frames": [
            (464, 345, 0),
            (464, 615, 0),
            (464, 885, 0),
        ]
    },
}

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    images_data = data.get('images', [])
    template_key = data.get('template', 'soft')

    config = TEMPLATES.get(template_key, TEMPLATES['soft'])
    template_path = os.path.join(basedir, "static", config['file'])
    bg = Image.open(template_path).convert("RGBA")
    canvas = bg.copy()

    photo_w = config['photo_w']
    photo_h = config['photo_h']
    frame_data = config['frames']

    for i, img_b64 in enumerate(images_data[:3]):
        try:
            img_bytes = base64.b64decode(img_b64.split(',')[1])
            img = Image.open(BytesIO(img_bytes)).convert("RGBA")
            cx, cy, angle = frame_data[i]
            paste_rotated(canvas, img, cx, cy, angle, photo_w, photo_h)
        except Exception as e:
            print(f"Gagal proses foto {i+1}: {e}")

    os.makedirs(os.path.join(basedir, "strip"), exist_ok=True)
    strip_name = f"LANY_{template_key.upper()}_{int(time.time())}.jpg"
    final_path = os.path.join(basedir, "strip", strip_name)
    canvas.convert("RGB").save(final_path, quality=95)
    return jsonify({"file": strip_name})

@app.route('/download/<f>')
def download(f):
    return send_file(os.path.join(basedir, "strip", f), as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)