// authService — every /api/auth/* call in one place.
import { apiFetch, saveSession, clearSession, getToken, getStoredUser } from '../api/client.js'

export function registerUser({ name, email, password, role, inviteCode }) {
  return apiFetch('/api/auth/register', {
    method: 'POST',
    body: { name, email, password, role, invite_code: inviteCode || null },
  })
}

export async function loginUser(email, password) {
  const data = await apiFetch('/api/auth/login', { method: 'POST', body: { email, password } })
  saveSession(data.access_token, data.user)
  return data.user
}

export function logoutUser() {
  // stateless JWT logout: server says goodbye, client discards the token
  return apiFetch('/api/auth/logout', { method: 'POST' }).finally(() => clearSession())
}

export function fetchMe() {
  return apiFetch('/api/auth/me')
}

export function currentSession() {
  return { token: getToken(), user: getStoredUser() }
}
