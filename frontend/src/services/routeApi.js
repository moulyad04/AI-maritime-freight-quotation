const API_BASE_URL = "http://127.0.0.1:8000";

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`
  };
}

function handleAuthError(response) {
  if (response.status === 401) {
    const err = new Error("Session expired. Please log in again.");
    err.isAuthError = true;
    throw err;
  }
}

export async function getOptions() {
  const response = await fetch(`${API_BASE_URL}/api/options`, {
    headers: authHeaders()
  });

  handleAuthError(response);

  if (!response.ok) {
    throw new Error(`Failed to load form options: ${response.status}`);
  }

  return await response.json();
}

export async function getRequiredDocuments(cargoType, destination) {
  const params = new URLSearchParams({
    cargo_type: cargoType,
    destination: destination
  });

  const response = await fetch(
    `${API_BASE_URL}/api/customs/required?${params.toString()}`,
    { headers: authHeaders() }
  );

  handleAuthError(response);

  if (!response.ok) {
    throw new Error(`Failed to load required documents: ${response.status}`);
  }

  return await response.json();
}

export async function generateQuotation(quotationRequest) {
  const response = await fetch(`${API_BASE_URL}/api/quotations/generate`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(quotationRequest)
  });

  handleAuthError(response);

  if (!response.ok) {
    throw new Error(`Quotation API failed: ${response.status}`);
  }

  return await response.json();
}

export async function getMyQuotations() {
  const response = await fetch(`${API_BASE_URL}/api/quotations/mine`, {
    headers: authHeaders()
  });

  handleAuthError(response);

  if (!response.ok) {
    throw new Error(`Failed to load your quotations: ${response.status}`);
  }

  return await response.json();
}

export async function getAllQuotations(date = "") {
  const url = date
    ? `${API_BASE_URL}/api/quotations?date=${date}`
    : `${API_BASE_URL}/api/quotations`;

  const response = await fetch(url, {
    headers: authHeaders()
  });

  handleAuthError(response);

  if (!response.ok) {
    throw new Error(`Failed to load quotations: ${response.status}`);
  }

  return await response.json();
}

export async function updateQuotation(quotationId, fields) {
  const response = await fetch(`${API_BASE_URL}/api/quotations/${quotationId}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(fields)
  });

  handleAuthError(response);

  if (!response.ok) {
    throw new Error(`Failed to save changes: ${response.status}`);
  }

  return await response.json();
}

export async function decideQuotation(quotationId, status) {
  const response = await fetch(
    `${API_BASE_URL}/api/quotations/${quotationId}/decision`,
    {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ status })
    }
  );

  handleAuthError(response);

  if (!response.ok) {
    throw new Error(`Failed to update quotation: ${response.status}`);
  }

  return await response.json();
}