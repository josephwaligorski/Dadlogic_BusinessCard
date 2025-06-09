from flask import Flask, jsonify
import requests

SERVICES = [
    {"name": "gateway", "url": "http://gateway:8080/health"},
    {"name": "documentconverter", "url": "http://documentconverter:5002/health"},
    {"name": "urlheaderapp", "url": "http://urlheaderapp:5001/health"},
    {"name": "base64decoder", "url": "http://base64decoder:5003/health"},
    #{"name": "healthaggregator", "url": "http://healthaggregator:5004/health"}, - self-referential, not needed
]

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    results = {}
    for svc in SERVICES:
        try:
            resp = requests.get(svc["url"], timeout=2)
            results[svc["name"]] = resp.json() if resp.status_code == 200 else {"status": "fail"}
        except Exception as e:
            results[svc["name"]] = {"status": "fail", "error": str(e)}
    return jsonify(results), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)
