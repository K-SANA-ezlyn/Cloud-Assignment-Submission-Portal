// FileUploader — client-side pre-checks (UX only; the server re-validates).
import { useRef, useState } from 'react'

export default function FileUploader({ allowedExtensions, maxSizeMb, onFileSelected, disabled }) {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')

  function pick(e) {
    const chosen = e.target.files?.[0]
    setError('')
    setFile(null)
    if (!chosen) return

    const ext = chosen.name.split('.').pop().toLowerCase()
    const allowed = (allowedExtensions || []).map((x) => x.replace(/^\./, '').toLowerCase())
    if (allowed.length && !allowed.includes(ext)) {
      setError(`File type .${ext} not allowed. Allowed: ${allowed.map((x) => `.${x}`).join(', ')}`)
      return
    }
    if (maxSizeMb && chosen.size > maxSizeMb * 1024 * 1024) {
      setError(`File is too large. Limit: ${maxSizeMb} MB`)
      return
    }
    setFile(chosen)
    onFileSelected?.(chosen)
  }

  return (
    <div className="uploader">
      <input
        ref={inputRef}
        type="file"
        accept={allowedExtensions?.map((x) => `.${x.replace(/^\./, '')}`).join(',')}
        onChange={pick}
        disabled={disabled}
      />
      {file && (
        <div className="uploader-file">
          📎 {file.name} ({(file.size / 1024).toFixed(1)} KB)
        </div>
      )}
      {error && <div className="field-error">{error}</div>}
      <p className="muted">
        Accepted: {allowedExtensions?.map((x) => `.${x.replace(/^\./, '')}`).join(', ') || '—'} · Max {maxSizeMb} MB
        <br />
        <em>Server validates extension, size and file content (magic bytes) again.</em>
      </p>
    </div>
  )
}
