// formatters — date/deadline/size presentation helpers.

export function formatDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

// Deadline badge data: compares against the BROWSER clock only for display.
// All enforcement decisions happen on the server.
export function deadlineInfo(iso) {
  if (!iso) return { label: 'No deadline', tone: 'muted', past: false }
  const deadline = new Date(iso)
  const now = new Date()
  const diffMs = deadline - now
  const past = diffMs <= 0
  const days = Math.floor(Math.abs(diffMs) / 86400000)
  const hours = Math.floor((Math.abs(diffMs) % 86400000) / 3600000)
  let label
  if (past) {
    label = days > 0 ? `Closed ${days}d ago` : `Closed ${hours}h ago`
  } else if (days >= 1) {
    label = `${days}d ${hours}h left`
  } else {
    label = `${hours}h left`
  }
  const tone = past ? 'danger' : days < 2 ? 'warn' : 'ok'
  return { label, tone, past }
}

export function formatBytes(bytes) {
  if (bytes === 0 || bytes == null) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return `${(bytes / 1024 ** i).toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

export function formatExtensionList(extString) {
  return (extString || '')
    .split(',')
    .map((e) => `.${e.trim().replace(/^\./, '')}`)
    .filter((e) => e !== '.')
    .join(', ')
}
