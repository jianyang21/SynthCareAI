import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { getPatientAppointments } from '../../api/client'
import StatCard from '../../components/StatCard'

const STATUS_CLS = { scheduled: 'badge-blue', completed: 'badge-green', cancelled: 'badge-red' }

const fmt     = d => new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
const fmtTime = d => new Date(d).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })

export default function PatientDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading]           = useState(true)

  useEffect(() => {
    getPatientAppointments()
      .then(data => setAppointments(data.filter(a => a.patient_id === user.patientId)))
      .finally(() => setLoading(false))
  }, [])

  const upcoming = appointments
    .filter(a => a.status === 'scheduled')
    .sort((a, b) => new Date(a.appointment_date) - new Date(b.appointment_date))

  const doctors = Object.values(
    appointments.reduce((acc, a) => {
      const key = `${a.doctor_first_name}${a.doctor_last_name}`
      if (a.doctor_first_name && !acc[key]) acc[key] = a
      return acc
    }, {})
  )

  if (loading) return <div className="p-7 text-muted text-sm">Loading…</div>

  return (
    <div className="p-7 flex flex-col gap-6">
      <div>
        <h1 className="font-head text-2xl font-extrabold">Good morning, {user.name.split(' ')[0]} 👋</h1>
        <p className="text-muted text-sm mt-1">Here's your health overview</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Upcoming"        value={upcoming.length}     color="text-accent"  icon="📅" />
        <StatCard label="Your Doctors"    value={doctors.length}      color="text-accent2" icon="🩺" />
        <StatCard label="All Appointments" value={appointments.length} icon="📋" />
      </div>

      {doctors.length > 0 && (
        <div className="card">
          <p className="card-title">Your Assigned Doctors</p>
          <div className="grid grid-cols-2 gap-3">
            {doctors.map((d, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-bg3 rounded-xl border border-white/[0.07]">
                <div className="w-10 h-10 rounded-full bg-accent2/20 text-accent2 font-bold text-sm flex items-center justify-center flex-shrink-0">
                  {d.doctor_first_name?.[0]}{d.doctor_last_name?.[0]}
                </div>
                <div>
                  <div className="text-sm font-medium">Dr. {d.doctor_first_name} {d.doctor_last_name}</div>
                  <div className="text-xs text-muted">{d.specialization}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <p className="card-title mb-0">Upcoming Appointments</p>
          <button onClick={() => navigate('/patient/appointments')} className="btn btn-secondary btn-sm">View all</button>
        </div>
        {upcoming.length === 0 ? (
          <div className="text-center py-10 text-muted text-sm">
            <div className="text-3xl mb-2">📅</div>No upcoming appointments
          </div>
        ) : (
          <div className="flex flex-col gap-2.5">
            {upcoming.slice(0, 5).map((a, i) => (
              <div key={i} className="flex items-center justify-between p-3.5 bg-bg3 rounded-xl border border-white/[0.07]">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-accent/10 text-accent text-xs font-bold flex items-center justify-center flex-shrink-0">
                    {new Date(a.appointment_date).getDate()}
                  </div>
                  <div>
                    <div className="text-sm font-medium">Dr. {a.doctor_first_name} {a.doctor_last_name}</div>
                    <div className="text-xs text-muted">{a.specialization} · {fmt(a.appointment_date)} at {fmtTime(a.appointment_date)}</div>
                  </div>
                </div>
                <span className={`badge ${STATUS_CLS[a.status] ?? 'badge-grey'}`}>{a.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
