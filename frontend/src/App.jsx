// App — routing table with client-side RBAC.
import { Navigate, Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import { ProtectedRoute, RoleRoute } from './components/ProtectedRoute.jsx'
import { useAuth } from './context/AuthContext.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import StudentDashboardPage from './pages/StudentDashboardPage.jsx'
import TeacherDashboardPage from './pages/TeacherDashboardPage.jsx'
import AssignmentListPage from './pages/AssignmentListPage.jsx'
import AssignmentDetailPage from './pages/AssignmentDetailPage.jsx'
import AssignmentFormPage from './pages/AssignmentFormPage.jsx'
import MySubmissionsPage from './pages/MySubmissionsPage.jsx'
import ReviewSubmissionsPage from './pages/ReviewSubmissionsPage.jsx'
import CoursesPage from './pages/CoursesPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'

export default function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route element={<ProtectedRoute />}>
          {/* shared */}
          <Route path="/assignments" element={<AssignmentListPage />} />
          <Route path="/assignments/:id" element={<AssignmentDetailPage />} />

          {/* student-only */}
          <Route element={<RoleRoute role="STUDENT" />}>
            <Route path="/student" element={<StudentDashboardPage />} />
            <Route path="/my-submissions" element={<MySubmissionsPage />} />
          </Route>

          {/* teacher-only */}
          <Route element={<RoleRoute role="TEACHER" />}>
            <Route path="/teacher" element={<TeacherDashboardPage />} />
            <Route path="/assignments/new" element={<AssignmentFormPage />} />
            <Route path="/assignments/:id/edit" element={<AssignmentFormPage />} />
            <Route path="/assignments/:id/review" element={<ReviewSubmissionsPage />} />
            <Route path="/courses" element={<CoursesPage />} />
          </Route>
        </Route>

        <Route path="/" element={<RootRedirect />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  )
}

function RootRedirect() {
  const { user, loading } = useAuth()
  if (loading) return <div className="page-loading">Loading…</div>
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={user.role === 'TEACHER' ? '/teacher' : '/student'} replace />
}
