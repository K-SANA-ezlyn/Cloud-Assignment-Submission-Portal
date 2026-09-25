// API base URL.
//  * development: '' -> same-origin, Vite proxies /api to FastAPI
//  * production:  set VITE_API_URL (e.g. https://your-api.onrender.com)
const API_BASE = import.meta.env.VITE_API_URL || ''

// ---------------------------------------------------------------------------
// Token storage — the "session" of this SPA.
// ---------------------------------------------------------------------------
const TOKEN_KEY = 'portal_token'
const USER_KEY = 'portal_user'

export function saveSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY))
  } catch {
    return null
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

// ---------------------------------------------------------------------------
// Low-level request helper: attaches the JWT and normalizes API errors.
// ---------------------------------------------------------------------------
export async function apiFetch(path, { method = 'GET', body, formData, headers = {} } = {}) {
  const finalHeaders = { ...headers }
  const token = getToken()
  if (token) finalHeaders['Authorization'] = `Bearer ${token}`
  if (body !== undefined) finalHeaders['Content-Type'] = 'application/json'

  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: finalHeaders,
      body: formData ? formData : body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    // Network failure — backend unreachable / internet down
    throw new Error('Cannot reach the server. Check your connection and try again.')
  }

  if (response.status === 401) {
    clearSession()
    // redirect to login unless we are already there
    if (!window.location.pathname.startsWith('/login')) {
      window.location.href = '/login?expired=1'
    }
    throw new Error('Session expired — please log in again.')
  }

  let data = null
  const text = await response.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!response.ok) {
    const detail = data?.detail || data?.message || `Request failed (${response.status})`
    const err = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
    err.status = response.status
    throw err
  }
  return data
}
