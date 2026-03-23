import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from '../../components/Sidebar'

const NAV = [
  { label: 'Overview', items: [
    { to: '/admin', end: true, icon: '📊', label: 'Analytics' },
  ]},
  { label: 'Manage', items: [
    { to: '/admin/patients',    icon: '👥', label: 'Patients'    },
    { to: '/admin/doctors',     icon: '🩺', label: 'Doctors'     },
    { to: '/admin/medicines',   icon: '💊', label: 'Medicines'   },
    { to: '/admin/add-patient', icon: '➕', label: 'Add Patient' },
  ]},
  { label: 'Assistant', items: [
    { to: '/admin/chat', icon: '🤖', label: 'AI Chat' },
  ]},
]

const TITLES = {
  '/admin':               'Analytics Dashboard',
  '/admin/patients':      'Manage Patients',
  '/admin/doctors':       'Manage Doctors',
  '/admin/medicines':     'Medicines & Inventory',
  '/admin/add-patient':   'Add New Patient',
  '/admin/chat':          'AI Assistant',
}

export default function AdminLayout() {
  const { pathname } = useLocation()
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar nav={NAV} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="h-14 border-b border-white/[0.07] flex items-center px-7 bg-bg2 flex-shrink-0">
          <span className="font-head text-base font-bold">{TITLES[pathname] ?? 'Admin Portal'}</span>
        </div>
        <div className="flex-1 overflow-y-auto bg-bg"><Outlet /></div>
      </div>
    </div>
  )
}
