// LoginPage — JWT login for both roles.
import { useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { ErrorBanner } from '../components/StatusBadge.jsx'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [params] = useSearchParams()
  const expired = params.get('expired')

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const user = await login(email, password)
      navigate(location.state?.from?.pathname || (user.role === 'TEACHER' ? '/teacher' : '/student'))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-page">
      <form className="card auth-card" onSubmit={onSubmit}>
        <h1>Welcome back</h1>
        <p className="muted">Cloud-Based Student Assignment Submission &amp; Feedback Portal</p>
        {expired && <div className="warn-banner">Session expired — please log in again.</div>}
        <ErrorBanner message={error} />
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@university.edu"
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
        </label>
        <button className="btn btn-primary" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
        <p className="muted">
          New student? <Link to="/register">Create an account</Link>
        </p>
      </form>
    </main>
  )
}
