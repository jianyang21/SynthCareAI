import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import clsx from 'clsx'
import { LogOut } from 'lucide-react'

const AVATAR_CLS = {
  patient: 'bg-accent/20 text-accent',
  doctor:  'bg-accent2/20 text-accent2',
  admin:   'bg-accent3/20 text-accent3',
}

export default function Sidebar({ nav }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const initials = user?.name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()

  return (
    <aside className="w-[220px] min-w-[220px] bg-bg2 border-r border-white/[0.07] flex flex-col py-5 gap-0.5 overflow-y-auto">
      {/* Logo */}
      <div className="font-head text-[17px] font-extrabold px-5 pb-5 mb-1 border-b border-white/[0.07]">
        Synth<span className="text-accent">Care</span>
        <span className="ml-2 text-[10px] font-normal text-muted uppercase tracking-widest align-middle">AI</span>
      </div>

      {/* Nav sections */}
      {nav.map((section, si) => (
        <div key={si} className="mt-1">
          {section.label && (
            <p className="text-[10px] font-semibold text-muted uppercase tracking-[1.5px] px-5 py-2">
              {section.label}
            </p>
          )}
          {section.items.map(item => (
            <NavLink key={item.to} to={item.to} end={item.end}
              className={({ isActive }) => clsx('nav-item', isActive && 'active')}>
              <span className="text-[15px] w-5 text-center">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>
      ))}

      {/* User chip */}
      <div className="mt-auto mx-3 pt-4 border-t border-white/[0.07]">
        <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-bg3 border border-white/[0.07]">
          <div className={clsx('w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0', AVATAR_CLS[user?.role])}>
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[12.5px] font-medium text-white truncate">{user?.name}</div>
            <div className="text-[11px] text-muted capitalize">{user?.role}</div>
          </div>
          <button onClick={() => { logout(); navigate('/login') }}
            className="p-1.5 rounded-lg hover:bg-white/10 text-muted hover:text-white transition-colors">
            <LogOut size={13} />
          </button>
        </div>
      </div>
    </aside>
  )
}
