// assignmentService — courses + assignments endpoints.
import { apiFetch } from '../api/client.js'

export function createCourse(name) {
  return apiFetch('/api/courses', { method: 'POST', body: { name } })
}

export function listCourses() {
  return apiFetch('/api/courses')
}

export function enrollStudent(courseId, studentEmail) {
  return apiFetch(`/api/courses/${courseId}/enroll`, {
    method: 'POST',
    body: { student_email: studentEmail },
  })
}

export function listAssignments() {
  return apiFetch('/api/assignments')
}

export function getAssignment(id) {
  return apiFetch(`/api/assignments/${id}`)
}

export function createAssignment(payload) {
  return apiFetch('/api/assignments', { method: 'POST', body: payload })
}

export function updateAssignment(id, payload) {
  return apiFetch(`/api/assignments/${id}`, { method: 'PUT', body: payload })
}

export function deleteAssignment(id) {
  return apiFetch(`/api/assignments/${id}`, { method: 'DELETE' })
}
