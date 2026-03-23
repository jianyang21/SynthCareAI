import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { queryRecords, createRecord } from '../../api/client'

export default function AddAppointment() {
  const navigate  = useNavigate()
  const [patients, setPatients] = useState([])
  const [doctors, setDoctors]   = useState([])
  const [form, setForm] = useState({ patient_id:'', doctor_id:'', appointment_date:'', status:'scheduled', notes:'' })
  const [saving, setSaving] = useState(false)
  const [done, setDone]   = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([queryRecords('patients'), queryRecords('doctors')])
      .then(([p, d]) => { setPatients(p); setDoctors(d) })
  }, [])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      const appt = await createRecord('appointments', {
        patient_id: parseInt(form.patient_id),
        doctor_id:  parseInt(form.doctor_id),
        appointment_date: form.appointment_date,
        status: form.status,
        notes: form.notes,
      })
      setDone(appt)
    } catch (err) {
      setError(err?.response?.data?.detail ?? 'Failed to create appointment')
    } finally { setSaving(false) }
  }

  const STATUS_OPTIONS = ['scheduled', 'completed', 'cancelled']

  if (done) return (
    <div className="p-7 max-w-lg mx-auto">
      <div className="card flex flex-col items-center gap-5 py-10 text-center">
        <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center text-3xl">📅</div>
        <div>
          <h2 className="font-head text-xl font-bold mb-1">Appointment Scheduled</h2>
          <p className="text-muted text-sm">Appointment ID: {done.id}</p>
          <p className="text-accent text-sm mt-1">{new Date(done.appointment_date).toLocaleString('en-IN')}</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate('/admin')} className="btn btn-secondary">← Dashboard</button>
          <button onClick={() => { setForm({ patient_id:'', doctor_id:'', appointment_date:'', status:'scheduled', notes:'' }); setDone(null) }}
            className="btn btn-primary">Add Another</button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="p-7 max-w-xl mx-auto flex flex-col gap-5">
      <div>
        <h1 className="font-head text-xl font-bold">Add Appointment</h1>
        <p className="text-muted text-xs mt-0.5">Schedule an appointment between a patient and doctor</p>
      </div>

      <form onSubmit={submit} className="card flex flex-col gap-4">
        <p className="card-title">Appointment Details</p>

        <div className="flex flex-col gap-1.5">
          <label className="form-label">Patient *</label>
          <select className="form-input" required value={form.patient_id} onChange={e => set('patient_id', e.target.value)}>
            <option value="">Select patient</option>
            {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name} (ID: {p.id})</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="form-label">Doctor *</label>
          <select className="form-input" required value={form.doctor_id} onChange={e => set('doctor_id', e.target.value)}>
            <option value="">Select doctor</option>
            {doctors.map(d => <option key={d.id} value={d.id}>Dr. {d.first_name} {d.last_name} — {d.specialization}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="form-label">Date & Time *</label>
            <input type="datetime-local" className="form-input" required
              value={form.appointment_date} onChange={e => set('appointment_date', e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="form-label">Status</label>
            <select className="form-input" value={form.status} onChange={e => set('status', e.target.value)}>
              {STATUS_OPTIONS.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="form-label">Notes</label>
          <textarea className="form-input" rows={3} placeholder="Reason for visit, symptoms…"
            value={form.notes} onChange={e => set('notes', e.target.value)} />
        </div>

        {error && <p className="text-xs text-danger bg-danger/10 border border-danger/20 rounded-xl px-3 py-2">{error}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={() => navigate('/admin')} className="btn btn-secondary">Cancel</button>
          <button type="submit" disabled={saving} className="btn btn-primary">
            {saving ? 'Scheduling…' : 'Schedule Appointment'}
          </button>
        </div>
      </form>
    </div>
  )
}
