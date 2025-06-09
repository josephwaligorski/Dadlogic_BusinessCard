import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/get-headers", methods=["POST"])
def get_headers():
    # Try query string first
    url = request.args.get("url")
    # Then form field
    if not url:
        url = request.form.get("url")
    # Then JSON
    if not url and request.is_json:
        url = request.get_json().get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    try:
        resp = requests.head(url, allow_redirects=True)
        headers = dict(resp.headers)
        return jsonify({"headers": headers, "final_url": resp.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
