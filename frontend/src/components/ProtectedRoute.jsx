// ProtectedRoute + RoleRoute — client-side authorization gates.
// (The server re-checks everything; these guards just shape the UX.)
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <div className="page-loading">Loading…</div>
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />
  return <Outlet />
}

export function RoleRoute({ role }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="page-loading">Loading…</div>
  // A student typing /teacher in the URL is bounced to their own dashboard.
  if (!user || user.role !== role) {
    const home = user?.role === 'TEACHER' ? '/teacher' : '/student'
    return <Navigate to={home} replace />
  }
  return <Outlet />
}
