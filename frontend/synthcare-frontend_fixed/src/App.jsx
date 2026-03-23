import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'

import Login                from './pages/Login'
import PatientLayout        from './pages/patient/PatientLayout'
import PatientDashboard     from './pages/patient/Dashboard'
import PatientAppointments  from './pages/patient/Appointments'
import PatientPrescriptions from './pages/patient/Prescriptions'
import PatientChat          from './pages/patient/Chat'
import DoctorLayout         from './pages/doctor/DoctorLayout'
import DoctorDashboard      from './pages/doctor/Dashboard'
import DoctorChat           from './pages/doctor/Chat'
import AdminLayout          from './pages/admin/AdminLayout'
import AdminDashboard       from './pages/admin/Dashboard'
import AdminPatients        from './pages/admin/Patients'
import AdminDoctors         from './pages/admin/Doctors'
import AdminMedicines       from './pages/admin/Medicines'
import AdminChat            from './pages/admin/Chat'
import AddPatient           from './pages/shared/AddPatient'

function Guard({ role, children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen bg-bg flex items-center justify-center text-muted text-sm">Loading…</div>
  if (!user) return <Navigate to="/login" replace />
  if (role && user.role !== role) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  const { user, loading } = useAuth()

  if (loading) return (
    <div className="min-h-screen bg-bg flex items-center justify-center">
      <div className="text-muted text-sm">Loading…</div>
    </div>
  )

  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      {/* Patient */}
      <Route path="/patient" element={<Guard role="patient"><PatientLayout /></Guard>}>
        <Route index               element={<PatientDashboard />} />
        <Route path="appointments"  element={<PatientAppointments />} />
        <Route path="prescriptions" element={<PatientPrescriptions />} />
        <Route path="chat"          element={<PatientChat />} />
      </Route>

      {/* Doctor */}
      <Route path="/doctor" element={<Guard role="doctor"><DoctorLayout /></Guard>}>
        <Route index              element={<DoctorDashboard />} />
        <Route path="add-patient"  element={<AddPatient />} />
        <Route path="chat"         element={<DoctorChat />} />
      </Route>

      {/* Admin */}
      <Route path="/admin" element={<Guard role="admin"><AdminLayout /></Guard>}>
        <Route index              element={<AdminDashboard />} />
        <Route path="patients"    element={<AdminPatients />} />
        <Route path="doctors"     element={<AdminDoctors />} />
        <Route path="medicines"   element={<AdminMedicines />} />
        <Route path="add-patient" element={<AddPatient />} />
        <Route path="chat"        element={<AdminChat />} />
      </Route>

      <Route path="/" element={
        user ? <Navigate to={`/${user.role}`} replace /> : <Navigate to="/login" replace />
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
