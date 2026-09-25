// TeacherDashboard — workload overview across the teacher's courses.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { teacherDashboard } from '../services/submissionService.js'
import { StatCard, EmptyState, ErrorBanner } from '../components/StatusBadge.jsx'
import { formatDateTime, deadlineInfo } from '../utils/formatters.js'
import { useAuth } from '../context/AuthContext.jsx'

export default function TeacherDashboardPage() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    setError('')
    try {
      setData(await teacherDashboard())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => {
    load()
  }, [])

  if (loading) return <div className="page-loading">Loading dashboard…</div>

  return (
    <main className="page">
      <div className="page-head">
        <div>
          <h1>Welcome, {user?.name} 👋</h1>
          <p className="muted">Your teaching workload at a glance.</p>
        </div>
        <Link className="btn btn-primary" to="/assignments/new">
          + New assignment
        </Link>
        </div>

      <ErrorBanner message={error} onRetry={load} />
      {data && (
        <>
          <section className="stat-grid">
            <StatCard label="Assignments" value={data.total_assignments} />
            <StatCard label="Students" value={data.total_students} />
            <StatCard label="Submissions" value={data.total_submissions} />
            <StatCard label="Pending reviews" value={data.pending_reviews} tone="warn" />
            <StatCard label="Late" value={data.late_submissions} tone="danger" />
            <StatCard label="Graded" value={data.graded_submissions} tone="info" />
          </section>

          <section className="grid-2">
            <div className="card">
              <h2>Recent uploads</h2>
              {data.recent_uploads.length === 0 ? (
                <EmptyState title="No submissions yet" hint="They will appear here as students upload." />
              ) : (
                <ul className="list">
                  {data.recent_uploads.map((u) => (
                    <li key={u.submission_id} className="list-row">
                      <div>
                        <strong>{u.assignment_title}</strong> — {u.student_name}
                        <div className="muted">
                          {u.file_name} · {formatDateTime(u.submitted_at)}
                        </div>
                      </div>
                      <span className="badge tone-warn">{u.status}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="card">
              <h2>Upcoming deadlines</h2>
              {data.upcoming_deadlines.length === 0 ? (
                <EmptyState title="No upcoming deadlines" hint="Create an assignment to get started." />
              ) : (
                <ul className="list">
                  {data.upcoming_deadlines.map((d) => {
                    const info = deadlineInfo(d.deadline)
                    return (
                      <li key={d.assignment_id} className="list-row">
                        <div>
                          <Link to={`/assignments/${d.assignment_id}/review`}>{d.title}</Link>
                          <div className="muted">
                            {d.course} · {d.submitted_count} submitted
                          </div>
                        </div>
                        <span className={`badge tone-${info.tone}`}>{info.label}</span>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>
          </section>
        </>
      )}
    </main>
  )
}
