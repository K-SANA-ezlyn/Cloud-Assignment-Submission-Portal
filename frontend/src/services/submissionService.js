// submissionService — submissions, downloads, grading and dashboards.
import { apiFetch, getToken } from '../api/client.js'

const API_BASE = import.meta.env.VITE_API_URL || ''

export function mySubmissions() {
  return apiFetch('/api/submissions/me')
}

export function assignmentSubmissions(assignmentId) {
  return apiFetch(`/api/assignments/${assignmentId}/submissions`)
}

export function getSubmission(id) {
  return apiFetch(`/api/submissions/${id}`)
}

export function gradeSubmission(id, marks, feedback) {
  return apiFetch(`/api/submissions/${id}/grade`, {
    method: 'POST',
    body: { marks: Number(marks), feedback },
  })
}

export function getFeedback(id) {
  return apiFetch(`/api/submissions/${id}/feedback`)
}

// Upload with browser-native fetch so we can send multipart FormData.
export function submitAssignment(assignmentId, file) {
  const formData = new FormData()
  formData.append('file', file)
  return apiFetch(`/api/assignments/${assignmentId}/submit`, { method: 'POST', formData })
}

// Authenticated download: fetch as blob, trigger a save dialog.
// (The file is NOT publicly hosted — every byte passes authorization.)
export async function downloadSubmission(submissionId, fileName) {
  const response = await fetch(`${API_BASE}/api/submissions/${submissionId}/download`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  })
  if (!response.ok) {
    let detail = `Download failed (${response.status})`
    try {
      const data = await response.json()
      if (data?.detail) detail = data.detail
    } catch { /* not JSON */ }
    throw new Error(detail)
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName || 'submission'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export function studentDashboard() {
  return apiFetch('/api/dashboard/student')
}

export function teacherDashboard() {
  return apiFetch('/api/dashboard/teacher')
}
