import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const ROLES = [
  { id: 'patient', label: 'Patient', icon: '🧑‍⚕️', placeholder: 'patient@example.com' },
  { id: 'doctor',  label: 'Doctor',  icon: '👨‍⚕️', placeholder: 'doctor@hospital.com'  },
  { id: 'admin',   label: 'Admin',   icon: '🔧',   placeholder: import.meta.env.VITE_ADMIN_EMAIL || 'admin@synthcare.com' },
]

export default function Login() {
  const [role, setRole]       = useState('patient')
  const [email, setEmail]     = useState('')
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate  = useNavigate()

  const pickRole = (r) => { setRole(r); setEmail(''); setError('') }

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true); setError('')
    const result = await login(role, email.trim())
    setLoading(false)
    if (result.ok) navigate(`/${role}`)
    else setError(result.error)
  }

  const current = ROLES.find(r => r.id === role)

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-5"
         style={{ backgroundImage: 'radial-gradient(ellipse at 20% 50%,rgba(79,142,247,.08) 0%,transparent 60%),radial-gradient(ellipse at 80% 20%,rgba(56,217,169,.06) 0%,transparent 50%)' }}>
      <div className="bg-bg2 border border-white/[0.07] rounded-2xl p-10 w-full max-w-sm shadow-[0_32px_80px_rgba(0,0,0,.5)]">

        <div className="font-head text-2xl font-extrabold mb-1">
          Synth<span className="text-accent">Care</span>
        </div>
        <p className="text-muted text-sm mb-8">Healthcare management platform</p>

        {/* Role picker */}
        <div className="grid grid-cols-3 gap-2 mb-6">
          {ROLES.map(r => (
            <button key={r.id} onClick={() => pickRole(r.id)}
              className={`py-3 px-2 rounded-xl border text-xs font-medium text-center transition-all
                ${role === r.id
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-white/[0.07] bg-bg3 text-muted hover:border-accent/40 hover:text-white'}`}>
              <div className="text-xl mb-1">{r.icon}</div>
              {r.label}
            </button>
          ))}
        </div>

        <form onSubmit={submit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="form-label">Email</label>
            <input
              className="form-input"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder={current?.placeholder}
              required
              autoComplete="email"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              placeholder="••••••••"
              autoComplete="current-password"
            />
            <p className="text-[11px] text-muted">Demo mode — any password works</p>
          </div>

          {error && (
            <p className="text-xs text-danger bg-danger/10 border border-danger/20 rounded-xl px-3 py-2">
              {error}
            </p>
          )}

          <button type="submit" disabled={loading || !email.trim()}
            className="btn btn-primary w-full justify-center mt-1 disabled:opacity-50">
            {loading
              ? <span className="flex items-center gap-2"><span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"/>Signing in…</span>
              : `Sign in as ${current?.label}`}
          </button>
        </form>

        {/* Dynamic hint — shows which role is selected */}
        <div className="mt-5 p-3 bg-bg3 border border-white/[0.07] rounded-xl">
          <p className="text-[11px] text-muted mb-1 font-semibold uppercase tracking-widest">
            {current?.label} login
          </p>
          <p className="text-xs text-muted">
            {role === 'patient' && 'Enter the email address registered for your patient account.'}
            {role === 'doctor'  && 'Enter your doctor account email registered in the system.'}
            {role === 'admin'   && `Use the admin email configured in your environment (VITE_ADMIN_EMAIL).`}
          </p>
        </div>
      </div>
    </div>
  )
}
