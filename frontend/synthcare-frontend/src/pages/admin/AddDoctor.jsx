import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createRecord } from '../../api/client'

const SPECS = ['Cardiology','Neurology','Oncology','Orthopedics','Pediatrics',
               'Dermatology','Radiology','Psychiatry','General Medicine','ENT',
               'Gastroenterology','Nephrology','Urology','Endocrinology','Pulmonology']

const EMPTY = { first_name:'', last_name:'', specialization:'', email:'', phone:'' }

export default function AddDoctor() {
  const navigate  = useNavigate()
  const [form, setForm]   = useState(EMPTY)
  const [saving, setSaving] = useState(false)
  const [done, setDone]   = useState(null)
  const [error, setError] = useState('')
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      const doc = await createRecord('doctors', form)
      setDone(doc)
    } catch (err) {
      setError(err?.response?.data?.detail ?? 'Failed to create doctor')
    } finally { setSaving(false) }
  }

  if (done) return (
    <div className="p-7 max-w-lg mx-auto">
      <div className="card flex flex-col items-center gap-5 py-10 text-center">
        <div className="w-16 h-16 rounded-full bg-accent2/20 flex items-center justify-center text-3xl">✅</div>
        <div>
          <h2 className="font-head text-xl font-bold mb-1">Doctor Added</h2>
          <p className="text-muted text-sm">Dr. {done.first_name} {done.last_name} · ID {done.id}</p>
          <p className="text-accent2 text-sm mt-1">{done.specialization}</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate('/admin/doctors')} className="btn btn-secondary">← Back to Doctors</button>
          <button onClick={() => { setForm(EMPTY); setDone(null) }} className="btn btn-primary">Add Another</button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="p-7 max-w-xl mx-auto flex flex-col gap-5">
      <div>
        <h1 className="font-head text-xl font-bold">Add New Doctor</h1>
        <p className="text-muted text-xs mt-0.5">Add a doctor to the system</p>
      </div>

      <form onSubmit={submit} className="card flex flex-col gap-4">
        <p className="card-title">Doctor Details</p>

        <div className="grid grid-cols-2 gap-4">
          {[['first_name','First Name',true],['last_name','Last Name',true],
            ['email','Email',true],['phone','Phone',false]].map(([k,l,req]) => (
            <div key={k} className="flex flex-col gap-1.5">
              <label className="form-label">{l}{req && ' *'}</label>
              <input className="form-input" required={req} value={form[k]}
                onChange={e => set(k, e.target.value)} />
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="form-label">Specialization *</label>
          <select className="form-input" required value={form.specialization}
            onChange={e => set('specialization', e.target.value)}>
            <option value="">Select specialization</option>
            {SPECS.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>

        {error && <p className="text-xs text-danger bg-danger/10 border border-danger/20 rounded-xl px-3 py-2">{error}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={() => navigate('/admin/doctors')} className="btn btn-secondary">Cancel</button>
          <button type="submit" disabled={saving} className="btn btn-primary">
            {saving ? 'Adding…' : 'Add Doctor'}
          </button>
        </div>
      </form>
    </div>
  )
}
