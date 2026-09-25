// StudentDashboard — stats, upcoming deadlines, recent feedback.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { studentDashboard } from '../services/submissionService.js'
import { StatCard, EmptyState, ErrorBanner } from '../components/StatusBadge.jsx'
import { formatDateTime, deadlineInfo } from '../utils/formatters.js'
import { useAuth } from '../context/AuthContext.jsx'

export default function StudentDashboardPage() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    setError('')
    try {
      setData(await studentDashboard())
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
      <h1>Welcome, {user?.name} 👋</h1>
      <p className="muted">Your coursework at a glance.</p>
      <ErrorBanner message={error} onRetry={load} />
      {data && (
        <>
          <section className="stat-grid">
            <StatCard label="Total assignments" value={data.total_assignments} />
            <StatCard label="Pending" value={data.pending} tone="warn" />
            <StatCard label="Submitted" value={data.submitted} tone="ok" />
            <StatCard label="Late" value={data.late} tone="danger" />
            <StatCard label="Graded" value={data.graded} tone="info" />
          </section>

          <section className="grid-2">
            <div className="card">
              <h2>Upcoming deadlines</h2>
              {data.upcoming_deadlines.length === 0 ? (
                <EmptyState title="Nothing due 🎉" hint="All caught up." />
              ) : (
                <ul className="list">
                  {data.upcoming_deadlines.map((d) => {
                    const info = deadlineInfo(d.deadline)
                    return (
                      <li key={d.assignment_id} className="list-row">
                        <div>
                          <Link to={`/assignments/${d.assignment_id}`}>{d.title}</Link>
                          <div className="muted">{d.course}</div>
                        </div>
                        <span className={`badge tone-${info.tone}`}>{info.label}</span>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>

            <div className="card">
              <h2>Recent feedback</h2>
              {data.recent_feedback.length === 0 ? (
                <EmptyState title="No feedback yet" hint="Graded work appears here." />
              ) : (
                <ul className="list">
                  {data.recent_feedback.map((f) => (
                    <li key={f.submission_id} className="list-row">
                      <div>
                        <strong>{f.assignment_title}</strong>
                        <div className="muted">{formatDateTime(f.graded_at)}</div>
                      </div>
                      <span className="badge tone-info">{f.marks} marks</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>
        </>
      )}
    </main>
  )
}
