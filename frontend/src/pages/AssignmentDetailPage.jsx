// AssignmentDetail — students see brief + submit/resubmit; teachers get an overview.
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getAssignment } from '../services/assignmentService.js'
import { submitAssignment } from '../services/submissionService.js'
import { StatusBadge, ErrorBanner } from '../components/StatusBadge.jsx'
import FileUploader from '../components/FileUploader.jsx'
import { formatDateTime, deadlineInfo, formatExtensionList } from '../utils/formatters.js'
import { useAuth } from '../context/AuthContext.jsx'

export default function AssignmentDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [assignment, setAssignment] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  // student submit state
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      setAssignment(await getAssignment(id))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => {
    load()
  }, [id])

  async function handleUpload() {
    if (!file) return
    setUploading(true)
    setUploadMsg('')
    setError('')
    try {
      const result = await submitAssignment(id, file)
      setUploadMsg(`Uploaded as ${result.file_name} — status: ${result.status}`)
      setFile(null)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  if (loading) return <div className="page-loading">Loading…</div>
  if (!assignment) return <main className="page"><ErrorBanner message={error || 'Not found'} /></main>

  const info = deadlineInfo(assignment.deadline)
  const isStudent = user?.role === 'STUDENT'
  const alreadySubmitted = assignment.my_status && assignment.my_status !== 'NOT_SUBMITTED'
  const canSubmit =
    isStudent &&
    (!alreadySubmitted || (assignment.allow_resubmission && assignment.my_status !== 'GRADED'))

  return (
    <main className="page">
      <Link to="/assignments" className="muted">← All assignments</Link>
      <h1>{assignment.title}</h1>
      <div className="card meta-card">
        <div><strong>Course:</strong> {assignment.course_name}</div>
        <div><strong>Deadline:</strong> {formatDateTime(assignment.deadline)} <span className={`badge tone-${info.tone}`}>{info.label}</span></div>
        <div><strong>Max marks:</strong> {assignment.max_marks}</div>
        <div><strong>Allowed files:</strong> {formatExtensionList(assignment.allowed_extensions)} · up to {assignment.max_file_size_mb} MB</div>
        <div>
          <strong>Policies:</strong>{' '}
          {assignment.allow_resubmission ? 'Resubmission allowed until graded' : 'Single submission only'} ·{' '}
          {assignment.allow_late ? 'Late uploads accepted (marked LATE)' : 'No late uploads'}
        </div>
        {isStudent && (
          <div>
            <strong>Your status:</strong> <StatusBadge status={assignment.my_status || 'NOT_SUBMITTED'} />
            {assignment.my_marks != null && <> · <strong>Marks:</strong> {assignment.my_marks}/{assignment.max_marks}</>}
          </div>
        )}
      </div>

      <ErrorBanner message={error} onRetry={load} />

      {assignment.description && (
        <section className="card">
          <h2>Description</h2>
          <p style={{ whiteSpace: 'pre-wrap' }}>{assignment.description}</p>
        </section>
      )}

      {isStudent && (
        <section className="card">
          <h2>{alreadySubmitted ? 'Resubmit your work' : 'Submit your work'}</h2>
          {alreadySubmitted && assignment.my_status === 'GRADED' && (
            <p className="muted">This submission is graded — resubmission is closed.</p>
          )}
          {alreadySubmitted && assignment.my_status !== 'GRADED' && !assignment.allow_resubmission && (
            <p className="muted">Resubmission is not allowed for this assignment.</p>
          )}
          {canSubmit ? (
            info.past && !assignment.allow_late ? (
              <p className="muted">⌛ The deadline has passed and late uploads are disabled.</p>
            ) : (
              <>
                {info.past && assignment.allow_late && (
                  <div className="warn-banner">Deadline passed — your upload will be marked <strong>LATE</strong>.</div>
                )}
                <FileUploader
                  allowedExtensions={assignment.allowed_extensions.split(',')}
                  maxSizeMb={assignment.max_file_size_mb}
                  onFileSelected={setFile}
                  disabled={uploading}
                />
                <button className="btn btn-primary" onClick={handleUpload} disabled={!file || uploading}>
                  {uploading ? 'Uploading…' : alreadySubmitted ? 'Resubmit' : 'Upload submission'}
                </button>
                {uploadMsg && <div className="success-banner">{uploadMsg}</div>}
              </>
            )
          ) : null}
        </section>
      )}

      {user?.role === 'TEACHER' && (
        <section className="card">
          <h2>Teacher tools</h2>
          <p className="muted">{assignment.submitted_count} submission(s) received.</p>
          <Link className="btn btn-primary" to={`/assignments/${id}/review`}>
            Review &amp; grade submissions
          </Link>
        </section>
      )}
    </main>
  )
}
