// MySubmissions — student's history with download + feedback access.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { mySubmissions, downloadSubmission } from '../services/submissionService.js'
import { StatusBadge, EmptyState, ErrorBanner } from '../components/StatusBadge.jsx'
import { formatDateTime, formatBytes } from '../utils/formatters.js'

export default function MySubmissionsPage() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [dlError, setDlError] = useState('')

  useEffect(() => {
    mySubmissions()
      .then(setRows)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  async function handleDownload(sub) {
    setDlError('')
    try {
      await downloadSubmission(sub.id, sub.file_name)
    } catch (err) {
      setDlError(err.message)
    }
  }

  return (
    <main className="page">
      <h1>My submissions</h1>
      <p className="muted">Every upload, its status, marks and teacher feedback.</p>
      <ErrorBanner message={error || dlError} />

      {loading ? (
        <div className="page-loading">Loading…</div>
      ) : rows.length === 0 ? (
        <EmptyState title="Nothing submitted yet" hint="Open an assignment to upload your first file." />
      ) : (
        <div className="table-wrap card">
          <table>
            <thead>
              <tr>
                <th>Assignment</th>
                <th>File</th>
                <th>Attempt</th>
                <th>Submitted</th>
                <th>Status</th>
                <th>Marks</th>
                <th>Feedback</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.id}>
                  <td><Link to={`/assignments/${s.assignment_id}`}>Assignment</Link></td>
                  <td>{s.file_name}<div className="muted small">{formatBytes(s.file_size)}</div></td>
                  <td>#{s.attempt_no}</td>
                  <td>{formatDateTime(s.submitted_at)}</td>
                  <td><StatusBadge status={s.status} /></td>
                  <td>{s.marks ?? '—'}</td>
                  <td className="feedback-cell">{s.feedback || '—'}</td>
                  <td>
                    <button className="btn btn-ghost" onClick={() => handleDownload(s)}>
                      ⬇ Download
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}
