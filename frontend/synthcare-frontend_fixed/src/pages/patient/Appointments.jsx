import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { getPatientAppointments, queryRecords, createRecord } from '../../api/client'
import Modal from '../../components/Modal'
import { Plus } from 'lucide-react'

const STATUS_CLS = { scheduled: 'badge-blue', completed: 'badge-green', cancelled: 'badge-red' }
const TABS = ['All', 'Scheduled', 'Completed', 'Cancelled']
const fmt     = d => new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
const fmtTime = d => new Date(d).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })

export default function PatientAppointments() {
  const { user } = useAuth()
  const [appointments, setAppointments] = useState([])
  const [doctors, setDoctors]           = useState([])
  const [tab, setTab]                   = useState('All')
  const [showModal, setShowModal]       = useState(false)
  const [loading, setLoading]           = useState(true)
  const [saving, setSaving]             = useState(false)
  const [form, setForm] = useState({ doctor_id: '', appointment_date: '', notes: '' })

  const load = async () => {
    setLoading(true)
    const [appts, docs] = await Promise.all([getPatientAppointments(), queryRecords('doctors')])
    setAppointments(appts.filter(a => a.patient_id === user.patientId))
    setDoctors(docs)
    setLoading(false)
  }
  useEffect(() => { load() }, [])

  const filtered = tab === 'All' ? appointments : appointments.filter(a => a.status === tab.toLowerCase())

  const handleBook = async e => {
    e.preventDefault(); setSaving(true)
    try {
      await createRecord('appointments', {
        patient_id: user.patientId,
        doctor_id: parseInt(form.doctor_id),
        appointment_date: form.appointment_date,
        status: 'scheduled',
        notes: form.notes,
      })
      setShowModal(false)
      setForm({ doctor_id: '', appointment_date: '', notes: '' })
      await load()
    } finally { setSaving(false) }
  }

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div className="p-7 flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-head text-xl font-bold">My Appointments</h1>
          <p className="text-muted text-xs mt-0.5">{appointments.length} total</p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn btn-primary gap-2">
          <Plus size={15} /> Book Appointment
        </button>
      </div>

      <div className="flex gap-2">
        {TABS.map(t => <button key={t} onClick={() => setTab(t)} className={"tab " + (tab === t ? 'active' : '')}>{t}</button>)}
      </div>

      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-muted text-sm">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-muted text-sm"><div className="text-3xl mb-2">📅</div>No appointments found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full tbl">
              <thead><tr><th>Doctor</th><th>Specialization</th><th>Date</th><th>Time</th><th>Notes</th><th>Status</th></tr></thead>
              <tbody>
                {filtered.map((a, i) => (
                  <tr key={i}>
                    <td className="font-medium">Dr. {a.doctor_first_name} {a.doctor_last_name}</td>
                    <td className="text-muted">{a.specialization}</td>
                    <td>{fmt(a.appointment_date)}</td>
                    <td className="text-muted">{fmtTime(a.appointment_date)}</td>
                    <td className="text-muted max-w-[200px] truncate">{a.notes || '—'}</td>
                    <td><span className={"badge " + (STATUS_CLS[a.status] ?? 'badge-grey')}>{a.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <Modal title="Book Appointment" onClose={() => setShowModal(false)}>
          <form onSubmit={handleBook} className="flex flex-col gap-4">
            <div>
              <label className="form-label">Doctor</label>
              <select className="form-input" required value={form.doctor_id} onChange={e => set('doctor_id', e.target.value)}>
                <option value="">Select a doctor</option>
                {doctors.map(d => <option key={d.id} value={d.id}>Dr. {d.first_name} {d.last_name} — {d.specialization}</option>)}
              </select>
            </div>
            <div>
              <label className="form-label">Date & Time</label>
              <input type="datetime-local" className="form-input" required value={form.appointment_date}
                onChange={e => set('appointment_date', e.target.value)} />
            </div>
            <div>
              <label className="form-label">Notes (optional)</label>
              <textarea className="form-input" rows={3} placeholder="Describe your symptoms..."
                value={form.notes} onChange={e => set('notes', e.target.value)} />
            </div>
            <div className="flex justify-end gap-3 mt-1">
              <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary">Cancel</button>
              <button type="submit" disabled={saving} className="btn btn-primary">
                {saving ? 'Booking...' : 'Book Appointment'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
