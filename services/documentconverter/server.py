from flask import Flask, request, jsonify
import tempfile
import os
from pdf2image import convert_from_bytes
from PIL import Image
import base64

app = Flask(__name__)

def encode_img(img):
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as out:
        img.save(out.name)
        with open(out.name, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        os.unlink(out.name)
    return b64

@app.route("/convert", methods=["POST"])
def convert():
    f = request.files["file"]
    if f.filename.lower().endswith(".pdf"):
        pages = convert_from_bytes(f.read())
        b64s = [encode_img(p) for p in pages]
    else:
        img = Image.open(f.stream)
        b64s = [encode_img(img)]
    return jsonify({"images": b64s})

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
