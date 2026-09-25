// CoursesPage — teachers create courses and enroll students by email.
import { useEffect, useState } from 'react'
import { createCourse, enrollStudent, listCourses } from '../services/assignmentService.js'
import { EmptyState, ErrorBanner } from '../components/StatusBadge.jsx'

export default function CoursesPage() {
  const [courses, setCourses] = useState([])
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)
  const [enrollEmails, setEnrollEmails] = useState({})

  async function load() {
    setLoading(true)
    try {
      setCourses(await listCourses())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => {
    load()
  }, [])

  async function handleCreate(e) {
    e.preventDefault()
    setError('')
    setNotice('')
    try {
      await createCourse(name)
      setName('')
      setNotice('Course created.')
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleEnroll(courseId) {
    setError('')
    setNotice('')
    try {
      const email = enrollEmails[courseId] || ''
      await enrollStudent(courseId, email)
      setNotice(`Enrolled ${email}.`)
      setEnrollEmails((m) => ({ ...m, [courseId]: '' }))
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main className="page">
      <h1>Courses</h1>
      <p className="muted">Your courses. Students must be enrolled to see (and submit to) assignments.</p>
      <ErrorBanner message={error} onRetry={load} />
      {notice && <div className="success-banner">{notice}</div>}

      <form className="card inline-form" onSubmit={handleCreate}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New course name, e.g. Cloud Computing (CS-402)"
          required
          minLength={2}
        />
        <button className="btn btn-primary">Create course</button>
      </form>

      {loading ? (
        <div className="page-loading">Loading…</div>
      ) : courses.length === 0 ? (
        <EmptyState title="No courses yet" hint="Create your first course above." />
      ) : (
        <div className="stack">
          {courses.map((c) => (
            <div key={c.id} className="card course-card">
              <div>
                <strong>{c.name}</strong>
                <div className="muted small">
                  {c.student_count} student(s) · {c.assignment_count} assignment(s)
                </div>
              </div>
              <form
                className="inline-form"
                onSubmit={(e) => {
                  e.preventDefault()
                  handleEnroll(c.id)
                }}
              >
                <input
                  type="email"
                  value={enrollEmails[c.id] || ''}
                  onChange={(e) => setEnrollEmails((m) => ({ ...m, [c.id]: e.target.value }))}
                  placeholder="student email to enroll"
                  required
                />
                <button className="btn btn-ghost">Enroll</button>
              </form>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
