import { STATUS_LABELS, STATUS_TONES } from '../utils/constants.js'

export function StatusBadge({ status }) {
  return <span className={`badge tone-${STATUS_TONES[status] || 'muted'}`}>{STATUS_LABELS[status] || status}</span>
}

export function StatCard({ label, value, tone = 'info' }) {
  return (
    <div className={`stat-card tone-border-${tone}`}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

export function EmptyState({ title, hint }) {
  return (
    <div className="empty-state">
      <div className="empty-title">{title}</div>
      {hint && <div className="empty-hint">{hint}</div>}
    </div>
  )
}

export function ErrorBanner({ message, onRetry }) {
  if (!message) return null
  return (
    <div className="error-banner" role="alert">
      <span>⚠️ {message}</span>
      {onRetry && (
        <button className="btn btn-ghost" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}
