// AuthContext — global authentication state for the SPA.
import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { currentSession, fetchMe, loginUser, logoutUser } from '../services/authService.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // On boot: trust localStorage for an instant paint, then re-validate
  // the token against /api/auth/me (handles expiry + role changes).
  useEffect(() => {
    const { token } = currentSession()
    if (!token) {
      setLoading(false)
      return
    }
    fetchMe()
      .then(setUser)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      isStudent: user?.role === 'STUDENT',
      isTeacher: user?.role === 'TEACHER',
      async login(email, password) {
        const u = await loginUser(email, password)
        setUser(u)
        return u
      },
      async logout() {
        try {
          await logoutUser()
        } finally {
          setUser(null)
        }
      },
    }),
    [user, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
