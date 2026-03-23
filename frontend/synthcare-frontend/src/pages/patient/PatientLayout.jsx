import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from '../../components/Sidebar'

const NAV = [
  { label: 'My Health', items: [
    { to: '/patient',               end: true, icon: '🏠', label: 'Dashboard'     },
    { to: '/patient/appointments',             icon: '📅', label: 'Appointments'  },
    { to: '/patient/prescriptions',            icon: '💊', label: 'Prescriptions' },
  ]},
  { label: 'Assistant', items: [
    { to: '/patient/chat', icon: '🤖', label: 'AI Chat' },
  ]},
]

const TITLES = {
  '/patient':               'My Dashboard',
  '/patient/appointments':  'My Appointments',
  '/patient/prescriptions': 'My Prescriptions',
  '/patient/chat':          'AI Assistant',
}

export default function PatientLayout() {
  const { pathname } = useLocation()
  return (
    <div className="flex h-screen overflow-hidden bg-bg">
      <Sidebar nav={NAV} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="h-14 border-b border-white/[0.07] flex items-center px-7 bg-bg2 flex-shrink-0">
          <span className="font-head text-[15px] font-bold">{TITLES[pathname] ?? 'Patient Portal'}</span>
        </div>
        <div className="flex-1 overflow-y-auto"><Outlet /></div>
      </div>
    </div>
  )
}
