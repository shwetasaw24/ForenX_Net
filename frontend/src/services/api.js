
const API_BASE = "http://127.0.0.1:8000/api";

async function request(url, options = {}) {
  let response;

  try {
    response = await fetch(url, options);
  } catch {
    throw new Error(
      "Cannot connect to ForenXNet API. Check that FastAPI is running on port 8000."
    );
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : `Request failed (${response.status})`
    );
  }

  return data;
}

export function analyzeImage(file) {
  const form = new FormData();
  form.append("file", file);

  return request(`${API_BASE}/analyze`, {
    method: "POST",
    body: form,
  });
}

export function getHistory() {
  return request(`${API_BASE}/history`);
}

export function getAnalysis(id) {
  return request(`${API_BASE}/analyses/${encodeURIComponent(id)}`);
}

export async function checkHealth() {
  return request(`${API_BASE}/health`);
}
