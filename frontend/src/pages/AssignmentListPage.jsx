// AssignmentList — teachers manage, students browse and submit.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listAssignments, deleteAssignment } from '../services/assignmentService.js'
import { StatusBadge, EmptyState, ErrorBanner } from '../components/StatusBadge.jsx'
import { formatDateTime, deadlineInfo, formatExtensionList } from '../utils/formatters.js'
import { useAuth } from '../context/AuthContext.jsx'

export default function AssignmentListPage() {
  const { isTeacher } = useAuth()
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    setError('')
    try {
      setItems(await listAssignments())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => {
    load()
  }, [])

  async function handleDelete(id) {
    if (!window.confirm('Delete this assignment and all its submission records?')) return
    try {
      await deleteAssignment(id)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main className="page">
      <div className="page-head">
        <div>
          <h1>Assignments</h1>
          <p className="muted">{isTeacher ? 'Manage coursework across your courses.' : 'Coursework assigned to you.'}</p>
        </div>
        {isTeacher && (
          <Link className="btn btn-primary" to="/assignments/new">
            + New assignment
          </Link>
        )}
      </div>

      <ErrorBanner message={error} onRetry={load} />
      {loading ? (
        <div className="page-loading">Loading…</div>
      ) : items.length === 0 ? (
        <EmptyState title="No assignments yet" hint={isTeacher ? 'Create your first assignment.' : 'Your teacher has not published coursework yet.'} />
      ) : (
        <div className="table-wrap card">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Course</th>
                <th>Deadline</th>
                <th>Marks</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((a) => {
                const info = deadlineInfo(a.deadline)
                return (
                  <tr key={a.id}>
                    <td>
                      <Link to={`/assignments/${a.id}`}>{a.title}</Link>
                      <div className="muted small">{formatExtensionList(a.allowed_extensions)} · {a.max_file_size_mb} MB max</div>
                    </td>
                    <td>{a.course_name}</td>
                    <td>
                      {formatDateTime(a.deadline)}
                      <div>
                        <span className={`badge tone-${info.tone}`}>{info.label}</span>
                      </div>
                    </td>
                    <td>{a.max_marks}</td>
                    <td>
                      {isTeacher ? (
                        <span className="badge tone-info">{a.submitted_count} submitted</span>
                      ) : (
                        <StatusBadge status={a.my_status || 'NOT_SUBMITTED'} />
                      )}
                    </td>
                    <td className="row-actions">
                      {isTeacher ? (
                        <>
                          <Link className="btn btn-ghost" to={`/assignments/${a.id}/review`}>
                            Review
                          </Link>
                          <Link className="btn btn-ghost" to={`/assignments/${a.id}/edit`}>
                            Edit
                          </Link>
                          <button className="btn btn-danger" onClick={() => handleDelete(a.id)}>
                            Delete
                          </button>
                        </>
                      ) : (
                        <Link className="btn btn-primary" to={`/assignments/${a.id}`}>
                          Open
                        </Link>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}
