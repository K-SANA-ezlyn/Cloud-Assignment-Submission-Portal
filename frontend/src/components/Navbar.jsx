// Navbar — role-aware navigation + logout.
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <header className="navbar">
      <Link to={user ? (user.role === 'TEACHER' ? '/teacher' : '/student') : '/login'} className="brand">
        ☁️ Assignment Portal
      </Link>
      {user && (
        <>
          <nav className="nav-links">
            <NavLink to={user.role === 'TEACHER' ? '/teacher' : '/student'}>Dashboard</NavLink>
            <NavLink to="/assignments">Assignments</NavLink>
            {user.role === 'STUDENT' && <NavLink to="/my-submissions">My Submissions</NavLink>}
            {user.role === 'TEACHER' && <NavLink to="/courses">Courses</NavLink>}
          </nav>
          <div className="nav-user">
            <span className="role-chip">{user.role}</span>
            <span className="user-name">{user.name}</span>
            <button className="btn btn-ghost" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </>
      )}
    </header>
  )
}
