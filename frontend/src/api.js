const API_BASE = 'http://127.0.0.1:8000'

async function request(path, { method = 'GET', body, token } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    const message = data.detail || 'Something went wrong. Please try again.'
    throw new Error(typeof message === 'string' ? message : 'Request failed.')
  }

  return data
}

export function login(username, password) {
  return request('/api/auth/login', {
    method: 'POST',
    body: { username, password },
  })
}

export function analyzeRoute(payload, token) {
  return request('/api/routes/analyze', {
    method: 'POST',
    body: payload,
    token,
  })
}
