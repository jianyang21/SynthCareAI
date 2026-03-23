import { createContext, useContext, useState, useEffect } from 'react'
import { queryRecords } from '../api/client'

const AuthContext = createContext(null)
const COOKIE_KEY  = 'synthcare_user'
const ADMIN_EMAIL = import.meta.env.VITE_ADMIN_EMAIL || 'admin@synthcare.com'

// ── cookie helpers ────────────────────────────────────────────────────
function saveCookie(user) {
  const val     = encodeURIComponent(JSON.stringify(user))
  const expires = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toUTCString()
  document.cookie = `${COOKIE_KEY}=${val}; expires=${expires}; path=/; SameSite=Lax`
}

function loadCookie() {
  const match = document.cookie.split('; ').find(r => r.startsWith(`${COOKIE_KEY}=`))
  if (!match) return null
  try { return JSON.parse(decodeURIComponent(match.split('=').slice(1).join('='))) }
  catch { return null }
}

function clearCookie() {
  document.cookie = `${COOKIE_KEY}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`
}

// ── provider ──────────────────────────────────────────────────────────
export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // Restore session from cookie on mount
  useEffect(() => {
    const saved = loadCookie()
    if (saved) setUser(saved)
    setLoading(false)
  }, [])

  const login = async (role, email) => {
    try {
      if (role === 'patient') {
        const rows = await queryRecords('patients', { email })
        if (!rows.length) return { ok: false, error: 'No patient account found with that email.' }
        const p = rows[0]
        const u = {
          id:        p.id,
          patientId: p.id,
          name:      `${p.first_name} ${p.last_name}`,
          email:     p.email,
          city:      p.city,
          phone:     p.phone,
          blood_group: p.blood_group,
          role:      'patient',
        }
        setUser(u); saveCookie(u)
        return { ok: true }
      }

      if (role === 'doctor') {
        const rows = await queryRecords('doctors', { email })
        if (!rows.length) return { ok: false, error: 'No doctor account found with that email.' }
        const d = rows[0]
        const u = {
          id:             d.id,
          doctorId:       d.id,
          name:           `Dr. ${d.first_name} ${d.last_name}`,
          email:          d.email,
          role:           'doctor',
          specialization: d.specialization,
          phone:          d.phone,
        }
        setUser(u); saveCookie(u)
        return { ok: true }
      }

      if (role === 'admin') {
        // Admin credentials come from env — no DB table needed
        if (email.toLowerCase() !== ADMIN_EMAIL.toLowerCase()) {
          return { ok: false, error: `Admin email not recognised. Use ${ADMIN_EMAIL}` }
        }
        const u = { id: 0, name: 'Admin', email, role: 'admin' }
        setUser(u); saveCookie(u)
        return { ok: true }
      }

      return { ok: false, error: 'Unknown role.' }
    } catch {
      return { ok: false, error: 'Cannot reach backend. Is the server running?' }
    }
  }

  const logout = () => { setUser(null); clearCookie() }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
