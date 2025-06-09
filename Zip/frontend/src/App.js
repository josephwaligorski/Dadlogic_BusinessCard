import React, { useState } from "react";
import axios from "axios";

function App() {
  const [files, setFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);

  // Mobile: trigger camera
  const openCamera = () => {
    document.getElementById("fileInput").click();
  };

  // File selection/capture
  const handleFileChange = (e) => {
    setFiles([...e.target.files]);
    setResults([]);
    setError(null);
  };

  // Submit/upload files
  const handleSubmit = async () => {
    setProcessing(true);
    setResults([]);
    setError(null);

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
      // In GHL context, these could be set by session/cookies
      // If needed, pass subaccount/agency token here as hidden input or fetched from session
      const resp = await axios.post("/api/import-business-card", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        // withCredentials: true, // if GHL sets cookies for session
      });
      setResults(resp.data.results || []);
    } catch (e) {
      setError(e.response?.data?.error || e.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: 480, margin: "auto", padding: 16 }}>
      <h2>Business Card Importer</h2>
      <p>Upload or capture business card(s) to create/update contacts in GoHighLevel.</p>
      <input
        id="fileInput"
        type="file"
        accept="image/*,application/pdf"
        multiple
        capture="environment"
        style={{ display: "none" }}
        onChange={handleFileChange}
      />
      <button onClick={openCamera} disabled={processing} style={{ width: "100%", marginBottom: 8 }}>
        {files.length === 0 ? "Take Photo / Upload" : "Change Photo(s)/File(s)"}
      </button>
      {files.length > 0 && (
        <ul>
          {Array.from(files).map((file, i) => (
            <li key={i}>{file.name}</li>
          ))}
        </ul>
      )}
      <button
        onClick={handleSubmit}
        disabled={processing || files.length === 0}
        style={{ width: "100%", marginBottom: 8 }}
      >
        {processing ? "Processing..." : "Submit"}
      </button>
      {error && <div style={{ color: "red" }}>Error: {error}</div>}
      {results.length > 0 && (
        <div>
          <h4>Results</h4>
          <ul>
            {results.map((res, i) => (
              <li key={i}>
                {res.status}: {res.name || res.email || "Unknown"} ({res.detail || ""})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
