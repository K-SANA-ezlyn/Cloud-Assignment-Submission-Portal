// RegisterPage — student self-registration, teacher invite-code gate.
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registerUser } from '../services/authService.js'
import { ErrorBanner } from '../components/StatusBadge.jsx'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'STUDENT', inviteCode: '' })
  const [error, setError] = useState('')
  const [ok, setOk] = useState(false)
  const [busy, setBusy] = useState(false)

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await registerUser(form)
      setOk(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (ok) {
    return (
      <main className="auth-page">
        <div className="card auth-card">
          <h1>Account created 🎉</h1>
          <p className="muted">Your {form.role.toLowerCase()} account is ready. Please log in.</p>
          <Link className="btn btn-primary" to="/login">
            Go to login
          </Link>
        </div>
      </main>
    )
  }

  return (
    <main className="auth-page">
      <form className="card auth-card" onSubmit={onSubmit}>
        <h1>Create account</h1>
        <p className="muted">Students register freely; teachers need an invite code from the admin.</p>
        <ErrorBanner message={error} />
        <label>
          Full name
          <input value={form.name} onChange={(e) => set('name', e.target.value)} required minLength={2} />
        </label>
        <label>
          Email
          <input type="email" value={form.email} onChange={(e) => set('email', e.target.value)} required />
        </label>
        <label>
          Password
          <input
            type="password"
            value={form.password}
            onChange={(e) => set('password', e.target.value)}
            required
            minLength={8}
            placeholder="min 8 characters"
          />
        </label>
        <label>
          I am a…
          <select value={form.role} onChange={(e) => set('role', e.target.value)}>
            <option value="STUDENT">Student</option>
            <option value="TEACHER">Teacher</option>
          </select>
        </label>
        {form.role === 'TEACHER' && (
          <label>
            Teacher invite code
            <input
              value={form.inviteCode}
              onChange={(e) => set('inviteCode', e.target.value)}
              placeholder="provided by your institution"
              required
            />
          </label>
        )}
        <button className="btn btn-primary" disabled={busy}>
          {busy ? 'Creating…' : 'Create account'}
        </button>
        <p className="muted">
          Already registered? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </main>
  )
}
