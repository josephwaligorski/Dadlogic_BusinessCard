from flask import Flask, send_from_directory
import requests
import os

app = Flask(__name__)

DOCUMENT_CONVERTER_URL = os.getenv("DOCUMENT_CONVERTER_URL", "http://documentconverter:5002")
VISION_API_URL = os.getenv("VISION_API_URL", "https://api.openai.com/v1/vision/extract")  # Replace with actual
GHL_API_URL = os.getenv("GHL_API_URL", "https://rest.gohighlevel.com/v1")
GHL_AGENCY_TOKEN = os.getenv("GHL_AGENCY_TOKEN")  # Securely set in env
# Session/subaccount ID should come from user/session context, possibly from GHL SSO/JWT

# Serve React static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
    if path != "" and os.path.exists(os.path.join(build_dir, path)):
        return send_from_directory(build_dir, path)
    else:
        return send_from_directory(build_dir, 'index.html')


@app.route("/api/import-business-card", methods=["POST"])
def import_card():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    # In production: securely infer subaccount/location ID from session, or pass as a hidden field if necessary
    subaccount_id = request.headers.get("X-Subaccount-ID", "HARDCODE_FOR_DEV")  # Replace with real context in prod

    results = []
    for f in files:
        # 1. Convert file to images (one per page/side)
        conv_resp = requests.post(
            f"{DOCUMENT_CONVERTER_URL}/convert", files={"file": (f.filename, f.stream, f.content_type)}
        )
        if conv_resp.status_code != 200:
            results.append({"status": "error", "detail": "File conversion failed", "name": f.filename})
            continue
        images = conv_resp.json().get("images", [])
        # 2. Extract contact data from each image (one page/side per image)
        for img_b64 in images:
            vision_resp = requests.post(
                VISION_API_URL,
                headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
                json={"image_base64": img_b64, "prompt": "Extract all visible business card fields as JSON."}
            )
            if vision_resp.status_code != 200:
                results.append({"status": "error", "detail": "Vision extraction failed"})
                continue
            data = vision_resp.json()
            # Map fields
            name = data.get("name")
            email = data.get("email")
            phone = data.get("phone")
            company = data.get("company")
            # 3. Check/create/update contact in GHL
            status, detail = upsert_contact_in_ghl(subaccount_id, name, email, phone, company, data)
            results.append({
                "status": status,
                "name": name,
                "email": email,
                "phone": phone,
                "company": company,
                "detail": detail
            })
    return jsonify({"results": results})


def upsert_contact_in_ghl(subaccount_id, name, email, phone, company, all_fields):
    # 1. Search for contact by email
    search = requests.get(
        f"{GHL_API_URL}/contacts/",
        headers={"Authorization": f"Bearer {GHL_AGENCY_TOKEN}", "Content-Type": "application/json"},
        params={"locationId": subaccount_id, "query": email or phone}
    )
    found = None
    if search.status_code == 200:
        contacts = search.json().get("contacts", [])
        for c in contacts:
            if c.get("email") == email or (phone and c.get("phone") == phone):
                found = c
                break
    if found:
        # Update contact
        update = requests.put(
            f"{GHL_API_URL}/contacts/{found['id']}",
            headers={"Authorization": f"Bearer {GHL_AGENCY_TOKEN}", "Content-Type": "application/json"},
            json={**all_fields, "locationId": subaccount_id}
        )
        if update.status_code == 200:
            return "updated", "Contact updated"
        else:
            return "error", f"GHL update failed: {update.text}"
    else:
        # Create contact
        create = requests.post(
            f"{GHL_API_URL}/contacts/",
            headers={"Authorization": f"Bearer {GHL_AGENCY_TOKEN}", "Content-Type": "application/json"},
            json={**all_fields, "locationId": subaccount_id}
        )
        if create.status_code == 200:
            return "created", "Contact created"
        else:
            return "error", f"GHL create failed: {create.text}"
        

@app.route("/api/health-summary", methods=["GET"])
def health_summary():
    resp = requests.get("http://healthaggregator:5004/health", timeout=3)
    return (resp.content, resp.status_code, resp.headers.items())

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
