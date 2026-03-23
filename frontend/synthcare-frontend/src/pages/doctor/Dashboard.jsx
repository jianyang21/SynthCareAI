import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { getPatientAppointments, queryRecords, getPrescriptionDetails, searchMedicalRecords } from '../../api/client'
import Modal from '../../components/Modal'
import StatCard from '../../components/StatCard'

const STATUS = { scheduled: 'badge badge-blue', completed: 'badge badge-green', cancelled: 'badge badge-red' }
const TABS   = ['All', 'Scheduled', 'Completed', 'Cancelled']
const fmt     = d => new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
const fmtTime = d => new Date(d).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })

export default function DoctorDashboard() {
  const { user } = useAuth()
  const [appointments, setAppointments] = useState([])
  const [tab, setTab]                   = useState('Scheduled')
  const [loading, setLoading]           = useState(true)
  const [selected, setSelected]         = useState(null)
  const [patientInfo, setPatientInfo]   = useState(null)
  const [prescriptions, setPrescriptions] = useState([])
  const [medNotes, setMedNotes]           = useState([])
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    getPatientAppointments()
      .then(data => setAppointments(data.filter(a => a.doctor_id === user.doctorId)))
      .finally(() => setLoading(false))
  }, [])

  const openPatient = async (appt) => {
    setSelected(appt)
    setDetailLoading(true)
    try {
      const [patients, rxData, notes] = await Promise.all([
        queryRecords('patients', { first_name: appt.patient_first_name }),
        getPrescriptionDetails({ patient_id: appt.patient_id }),
        searchMedicalRecords(appt.patient_id, 'diagnosis symptoms history').catch(() => []),
      ])
      setPatientInfo(patients[0] ?? null)
      const grouped = {}
      rxData.forEach(r => {
        if (!grouped[r.prescription_id]) grouped[r.prescription_id] = { id: r.prescription_id, created_at: r.created_at, medicines: [] }
        grouped[r.prescription_id].medicines.push(r.medicine_name)
      })
      setPrescriptions(Object.values(grouped))
      setMedNotes(notes)
    } finally { setDetailLoading(false) }
  }

  const close = () => { setSelected(null); setPatientInfo(null); setPrescriptions([]); setMedNotes([]) }

  const filtered = tab === 'All' ? appointments : appointments.filter(a => a.status === tab.toLowerCase())

  const todayCount = appointments.filter(a => {
    const d = new Date(a.appointment_date)
    const n = new Date()
    return d.toDateString() === n.toDateString()
  }).length

  return (
    <div className="p-7 flex flex-col gap-6">
      <div>
        <h1 className="font-head text-2xl font-extrabold">Welcome, {user.name} 👨‍⚕️</h1>
        <p className="text-muted text-sm mt-1">{user.specialization}</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Today's Appointments" value={todayCount}          color="text-accent"  icon="📅" />
        <StatCard label="Unique Patients"       value={new Set(appointments.map(a => a.patient_id)).size} color="text-accent2" icon="👥" />
        <StatCard label="Total Appointments"    value={appointments.length} icon="📋" />
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <p className="card-title mb-0">Patient Appointments</p>
          <div className="flex gap-2">
            {TABS.map(t => <button key={t} onClick={() => setTab(t)} className={`tab ${tab === t ? 'active' : ''}`}>{t}</button>)}
          </div>
        </div>

        {loading ? (
          <div className="text-center py-10 text-muted">Loading…</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-10 text-muted"><div className="text-3xl mb-2">📅</div>No appointments</div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {filtered.map((a, i) => (
              <div key={i} onClick={() => openPatient(a)}
                className="p-4 bg-bg3 rounded-xl border border-white/[0.07] cursor-pointer hover:border-accent/50 transition-all hover:-translate-y-0.5">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center text-accent font-bold text-sm flex-shrink-0">
                    {a.patient_first_name?.[0]}{a.patient_last_name?.[0]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{a.patient_first_name} {a.patient_last_name}</div>
                    <div className="text-xs text-muted">Patient #{a.patient_id}</div>
                  </div>
                  <span className={STATUS[a.status] ?? 'badge badge-grey'}>{a.status}</span>
                </div>
                <div className="text-xs text-muted border-t border-white/[0.07] pt-2">
                  📅 {fmt(a.appointment_date)} at {fmtTime(a.appointment_date)}
                </div>
                {a.notes && <div className="text-xs text-muted mt-1 truncate">📝 {a.notes}</div>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Patient detail modal */}
      {selected && (
        <Modal title={`${selected.patient_first_name} ${selected.patient_last_name}`} onClose={close} maxWidth="max-w-2xl">
          {detailLoading ? (
            <div className="text-center py-10 text-muted">Loading patient data…</div>
          ) : (
            <div className="flex flex-col gap-5">
              {/* Basic info */}
              {patientInfo && (
                <div className="grid grid-cols-2 gap-2">
                  {[['Gender', patientInfo.gender], ['Blood Group', patientInfo.blood_group],
                    ['Date of Birth', patientInfo.date_of_birth], ['Phone', patientInfo.phone],
                    ['Email', patientInfo.email], ['City', patientInfo.city]
                  ].filter(([, v]) => v).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-sm p-2.5 bg-bg3 rounded-xl">
                      <span className="text-muted">{k}</span>
                      <span className="font-medium">{v}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* This appointment */}
              <div className="p-3 bg-accent/5 border border-accent/20 rounded-xl text-sm">
                <div className="text-xs text-muted mb-1">This appointment</div>
                <div className="flex items-center gap-3">
                  <span>{new Date(selected.appointment_date).toLocaleString('en-IN')}</span>
                  <span className={STATUS[selected.status] ?? 'badge badge-grey'}>{selected.status}</span>
                </div>
                {selected.notes && <div className="text-muted text-xs mt-1">{selected.notes}</div>}
              </div>

              {/* Prescriptions */}
              {prescriptions.length > 0 && (
                <div>
                  <p className="form-label mb-3">Prescriptions ({prescriptions.length})</p>
                  <div className="flex flex-col gap-2">
                    {prescriptions.map((rx, i) => (
                      <div key={i} className="p-3 bg-bg3 rounded-xl border border-white/[0.07]">
                        <div className="text-xs text-muted mb-2">Prescription #{rx.id} · {fmt(rx.created_at)}</div>
                        <div className="flex flex-wrap gap-1.5">
                          {rx.medicines.map((m, j) => (
                            <span key={j} className="badge badge-green border border-accent2/20">💊 {m}</span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Medical notes */}
              {medNotes.length > 0 && (
                <div>
                  <p className="form-label mb-3">Medical Records</p>
                  <div className="flex flex-col gap-2 max-h-48 overflow-y-auto">
                    {medNotes.map((n, i) => (
                      <div key={i} className="p-3 bg-bg3 rounded-xl border border-white/[0.07] text-xs text-muted">
                        <span className="badge badge-orange border border-accent3/20 mr-2 mb-1">{n.record_type}</span>
                        {n.answer_chunk}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {prescriptions.length === 0 && medNotes.length === 0 && (
                <div className="text-center py-6 text-muted text-sm">No prescriptions or medical records found</div>
              )}
            </div>
          )}
        </Modal>
      )}
    </div>
  )
}
