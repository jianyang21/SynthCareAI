import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from '../../components/Sidebar'

const NAV = [
  { label: 'Practice', items: [
    { to: '/doctor',             end: true, icon: '🏠', label: 'Dashboard'   },
    { to: '/doctor/add-patient',            icon: '➕', label: 'Add Patient' },
  ]},
  { label: 'Assistant', items: [
    { to: '/doctor/chat', icon: '🤖', label: 'AI Chat' },
  ]},
]

const TITLES = {
  '/doctor':              "Doctor's Dashboard",
  '/doctor/add-patient':  'Add New Patient',
  '/doctor/chat':         'AI Assistant',
}

export default function DoctorLayout() {
  const { pathname } = useLocation()
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar nav={NAV} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="h-14 border-b border-white/[0.07] flex items-center px-7 bg-bg2 flex-shrink-0">
          <span className="font-head text-base font-bold">{TITLES[pathname] ?? 'Doctor Portal'}</span>
        </div>
        <div className="flex-1 overflow-y-auto bg-bg"><Outlet /></div>
      </div>
    </div>
  )
}
