// ReviewSubmissions — teacher grades each submission (marks + feedback).
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { assignmentSubmissions, downloadSubmission, gradeSubmission } from '../services/submissionService.js'
import { StatusBadge, EmptyState, ErrorBanner } from '../components/StatusBadge.jsx'
import { formatDateTime, formatBytes } from '../utils/formatters.js'

export default function ReviewSubmissionsPage() {
  const { id } = useParams()
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      setRows(await assignmentSubmissions(id))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => {
    load()
  }, [id])

  async function handleDownload(sub) {
    setNotice('')
    try {
      await downloadSubmission(sub.id, sub.file_name)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main className="page">
      <Link to="/assignments" className="muted">← All assignments</Link>
      <h1>Review submissions</h1>
      <p className="muted">Download each file, award marks and leave written feedback.</p>
      <ErrorBanner message={error} onRetry={load} />
      {notice && <div className="success-banner">{notice}</div>}

      {loading ? (
        <div className="page-loading">Loading…</div>
      ) : rows.length === 0 ? (
        <EmptyState title="No submissions yet" hint="Students have not uploaded work for this assignment." />
      ) : (
        <div className="stack">
          {rows.map((sub) => (
            <GradeCard key={sub.id} sub={sub} onSaved={load} onDownload={handleDownload} />
          ))}
        </div>
      )}
    </main>
  )
}

function GradeCard({ sub, onSaved, onDownload }) {
  const [marks, setMarks] = useState(sub.marks ?? '')
  const [feedback, setFeedback] = useState(sub.feedback ?? '')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function save(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await gradeSubmission(sub.id, marks, feedback)
      onSaved?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card grade-card" onSubmit={save}>
      <div className="grade-head">
        <div>
          <strong>{sub.student_name}</strong>
          <div className="muted small">
            {sub.file_name} · {formatBytes(sub.file_size)} · attempt #{sub.attempt_no} ·{' '}
            {formatDateTime(sub.submitted_at)}
          </div>
        </div>
        <div className="grade-actions">
          <StatusBadge status={sub.status} />
          <button type="button" className="btn btn-ghost" onClick={() => onDownload(sub)}>
            ⬇ Download file
          </button>
        </div>
      </div>

      <div className="form-row">
        <label>
          Marks
          <input
            type="number"
            min={0}
            value={marks}
            onChange={(e) => setMarks(e.target.value)}
            required
          />
        </label>
        <label className="grow">
          Feedback
          <input
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            minLength={3}
            maxLength={5000}
            placeholder="What was good? What should improve?"
            required
          />
        </label>
      </div>

      {error && <div className="field-error">{error}</div>}
      <button className="btn btn-primary" disabled={busy}>
        {busy ? 'Saving…' : sub.status === 'GRADED' ? 'Update grade' : 'Submit grade'}
      </button>
    </form>
  )
}
