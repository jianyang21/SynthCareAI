import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { queryRecords, createRecord } from '../../api/client'
import { Plus, X } from 'lucide-react'

const FREQ_MAP = { 1: 'Once daily', 2: 'Twice daily', 3: 'Thrice daily', 4: 'Four times daily' }
const EMPTY_ITEM = { medicine_id: '', frequency_per_day: 1, duration_days: 7, dosage: '1 tablet', instructions: 'After food' }

export default function AddPrescription() {
  const navigate = useNavigate()
  const [patients, setPatients] = useState([])
  const [doctors, setDoctors]   = useState([])
  const [medicines, setMedicines] = useState([])
  const [form, setForm] = useState({ patient_id: '', doctor_id: '' })
  const [items, setItems] = useState([{ ...EMPTY_ITEM }])
  const [saving, setSaving] = useState(false)
  const [done, setDone]   = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([queryRecords('patients'), queryRecords('doctors'), queryRecords('medicines')])
      .then(([p, d, m]) => { setPatients(p); setDoctors(d); setMedicines(m) })
  }, [])

  const setF  = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const setItem = (i, k, v) => setItems(prev => prev.map((it, idx) => idx === i ? { ...it, [k]: v } : it))
  const addItem = () => setItems(prev => [...prev, { ...EMPTY_ITEM }])
  const removeItem = (i) => setItems(prev => prev.filter((_, idx) => idx !== i))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      const rx = await createRecord('prescriptions', {
        patient_id: parseInt(form.patient_id),
        doctor_id:  parseInt(form.doctor_id),
      })
      for (const item of items) {
        await createRecord('prescription_items', {
          prescription_id:   rx.id,
          medicine_id:       parseInt(item.medicine_id),
          frequency_per_day: parseInt(item.frequency_per_day),
          frequency:         FREQ_MAP[item.frequency_per_day] ?? 'Once daily',
          duration_days:     parseInt(item.duration_days),
          duration:          `${item.duration_days} days`,
          dosage:            item.dosage,
          instructions:      item.instructions,
        })
      }
      setDone(rx)
    } catch (err) {
      setError(err?.response?.data?.detail ?? 'Failed to create prescription')
    } finally { setSaving(false) }
  }

  if (done) return (
    <div className="p-7 max-w-lg mx-auto">
      <div className="card flex flex-col items-center gap-5 py-10 text-center">
        <div className="w-16 h-16 rounded-full bg-accent2/20 flex items-center justify-center text-3xl">💊</div>
        <div>
          <h2 className="font-head text-xl font-bold mb-1">Prescription Created</h2>
          <p className="text-muted text-sm">Prescription ID: {done.id} · {items.length} medicine{items.length !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate('/admin')} className="btn btn-secondary">← Dashboard</button>
          <button onClick={() => { setForm({ patient_id:'', doctor_id:'' }); setItems([{...EMPTY_ITEM}]); setDone(null) }}
            className="btn btn-primary">Add Another</button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="p-7 max-w-2xl mx-auto flex flex-col gap-5">
      <div>
        <h1 className="font-head text-xl font-bold">Add Prescription</h1>
        <p className="text-muted text-xs mt-0.5">Create a prescription with one or more medicines</p>
      </div>

      <form onSubmit={submit} className="flex flex-col gap-4">
        {/* Header */}
        <div className="card flex flex-col gap-4">
          <p className="card-title">Prescription Header</p>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="form-label">Patient *</label>
              <select className="form-input" required value={form.patient_id} onChange={e => setF('patient_id', e.target.value)}>
                <option value="">Select patient</option>
                {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="form-label">Doctor *</label>
              <select className="form-input" required value={form.doctor_id} onChange={e => setF('doctor_id', e.target.value)}>
                <option value="">Select doctor</option>
                {doctors.map(d => <option key={d.id} value={d.id}>Dr. {d.first_name} {d.last_name} — {d.specialization}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Medicine items */}
        <div className="card flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <p className="card-title mb-0">Medicines</p>
            <button type="button" onClick={addItem} className="btn btn-secondary btn-sm"><Plus size={13} /> Add Medicine</button>
          </div>

          {items.map((item, i) => (
            <div key={i} className="p-4 bg-bg3 rounded-xl border border-white/[0.07] flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted">Medicine {i + 1}</span>
                {items.length > 1 && (
                  <button type="button" onClick={() => removeItem(i)} className="btn btn-danger btn-sm !px-1.5 !py-1">
                    <X size={12} />
                  </button>
                )}
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="form-label">Medicine *</label>
                <select className="form-input" required value={item.medicine_id}
                  onChange={e => setItem(i, 'medicine_id', e.target.value)}>
                  <option value="">Select medicine</option>
                  {medicines.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                </select>
              </div>

              <div className="grid grid-cols-4 gap-3">
                <div className="flex flex-col gap-1.5">
                  <label className="form-label">Frequency</label>
                  <select className="form-input" value={item.frequency_per_day}
                    onChange={e => setItem(i, 'frequency_per_day', parseInt(e.target.value))}>
                    {Object.entries(FREQ_MAP).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="form-label">Duration (days)</label>
                  <input type="number" min="1" className="form-input" value={item.duration_days}
                    onChange={e => setItem(i, 'duration_days', e.target.value)} />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="form-label">Dosage</label>
                  <input className="form-input" value={item.dosage}
                    onChange={e => setItem(i, 'dosage', e.target.value)} />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="form-label">Instructions</label>
                  <input className="form-input" value={item.instructions}
                    onChange={e => setItem(i, 'instructions', e.target.value)} />
                </div>
              </div>
            </div>
          ))}
        </div>

        {error && <p className="text-xs text-danger bg-danger/10 border border-danger/20 rounded-xl px-3 py-2">{error}</p>}

        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => navigate('/admin')} className="btn btn-secondary">Cancel</button>
          <button type="submit" disabled={saving} className="btn btn-primary">
            {saving ? 'Creating…' : `Create Prescription (${items.length} medicine${items.length !== 1 ? 's' : ''})`}
          </button>
        </div>
      </form>
    </div>
  )
}
