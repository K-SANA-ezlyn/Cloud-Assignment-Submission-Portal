// AssignmentForm — teacher creates or edits an assignment.
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { createAssignment, getAssignment, listCourses, updateAssignment } from '../services/assignmentService.js'
import { ErrorBanner } from '../components/StatusBadge.jsx'

// datetime-local value -> ISO with timezone (server stores UTC)
function localToIso(value) {
  if (!value) return ''
  const d = new Date(value)
  return d.toISOString()
}

// ISO -> datetime-local input value (browser-local time)
function isoToLocal(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export default function AssignmentFormPage() {
  const { id } = useParams()
  const editing = Boolean(id)
  const navigate = useNavigate()

  const [courses, setCourses] = useState([])
  const [form, setForm] = useState({
    course_id: '',
    title: '',
    description: '',
    deadlineLocal: '',
    max_marks: 100,
    allowed_extensions: 'pdf',
    max_file_size_mb: 10,
    allow_resubmission: false,
    allow_late: true,
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    listCourses()
      .then((cs) => {
        setCourses(cs)
        if (!editing && cs.length > 0) {
          setForm((f) => (f.course_id ? f : { ...f, course_id: cs[0].id }))
        }
      })
      .catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!editing) return
    getAssignment(id)
      .then((a) =>
        setForm({
          course_id: a.course_id,
          title: a.title,
          description: a.description || '',
          deadlineLocal: isoToLocal(a.deadline),
          max_marks: a.max_marks,
          allowed_extensions: a.allowed_extensions,
          max_file_size_mb: a.max_file_size_mb,
          allow_resubmission: a.allow_resubmission,
          allow_late: a.allow_late,
        }),
      )
      .catch((err) => setError(err.message))
  }, [id, editing])

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!form.course_id) {
      setError('Create a course first (Courses page), then create the assignment.')
      return
    }
    const payload = {
      course_id: form.course_id,
      title: form.title,
      description: form.description,
      deadline: localToIso(form.deadlineLocal),
      max_marks: Number(form.max_marks),
      allowed_extensions: form.allowed_extensions,
      max_file_size_mb: Number(form.max_file_size_mb),
      allow_resubmission: form.allow_resubmission,
      allow_late: form.allow_late,
    }
    setBusy(true)
    try {
      const saved = editing ? await updateAssignment(id, payload) : await createAssignment(payload)
      navigate(`/assignments/${saved.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="page">
      <h1>{editing ? 'Edit assignment' : 'New assignment'}</h1>
      <form className="card form-card" onSubmit={onSubmit}>
        <ErrorBanner message={error} />

        <label>
          Course
          <select value={form.course_id} onChange={(e) => set('course_id', e.target.value)} required>
            {courses.length === 0 && <option value="">— create a course first —</option>}
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Title
          <input value={form.title} onChange={(e) => set('title', e.target.value)} required minLength={3} maxLength={200} />
        </label>

        <label>
          Description
          <textarea
            value={form.description}
            onChange={(e) => set('description', e.target.value)}
            rows={5}
            maxLength={5000}
            placeholder="What should students do? Any resources? Grading rubric?"
          />
        </label>

        <div className="form-row">
          <label>
            Deadline (your local time)
            <input
              type="datetime-local"
              value={form.deadlineLocal}
              onChange={(e) => set('deadlineLocal', e.target.value)}
              required
            />
          </label>
          <label>
            Max marks
            <input type="number" min={1} max={1000} value={form.max_marks} onChange={(e) => set('max_marks', e.target.value)} required />
          </label>
        </div>

        <div className="form-row">
          <label>
            Allowed file types (comma separated)
            <input value={form.allowed_extensions} onChange={(e) => set('allowed_extensions', e.target.value)} placeholder="pdf,docx,zip" />
          </label>
          <label>
            Max file size (MB)
            <input type="number" min={1} max={100} value={form.max_file_size_mb} onChange={(e) => set('max_file_size_mb', e.target.value)} required />
          </label>
        </div>

        <div className="form-row checkboxes">
          <label className="check">
            <input type="checkbox" checked={form.allow_resubmission} onChange={(e) => set('allow_resubmission', e.target.checked)} />
            Allow resubmission (until graded)
          </label>
          <label className="check">
            <input type="checkbox" checked={form.allow_late} onChange={(e) => set('allow_late', e.target.checked)} />
            Accept late uploads (marked LATE)
          </label>
        </div>

        <button className="btn btn-primary" disabled={busy}>
          {busy ? 'Saving…' : editing ? 'Save changes' : 'Create assignment'}
        </button>
      </form>
    </main>
  )
}
