import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createRecord } from '../../api/client'

const FORMS = ['Tablet','Capsule','Syrup','Injection','Cream','Drops','Inhaler','Patch','Powder']
const EMPTY = { name:'', generic_name:'', strength:'', dosage_form:'', manufacturer:'', unit_price:'', quantity:'', reorder_level:'20' }

export default function AddMedicine() {
  const navigate = useNavigate()
  const [form, setForm]   = useState(EMPTY)
  const [saving, setSaving] = useState(false)
  const [done, setDone]   = useState(null)
  const [error, setError] = useState('')
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      const { quantity, reorder_level, ...medData } = form
      medData.unit_price = parseFloat(medData.unit_price) || 0
      const med = await createRecord('medicines', medData)
      await createRecord('medicine_inventory', {
        medicine_id: med.id,
        quantity: parseInt(quantity) || 0,
        reorder_level: parseInt(reorder_level) || 20,
      })
      setDone(med)
    } catch (err) {
      setError(err?.response?.data?.detail ?? 'Failed to add medicine')
    } finally { setSaving(false) }
  }

  if (done) return (
    <div className="p-7 max-w-lg mx-auto">
      <div className="card flex flex-col items-center gap-5 py-10 text-center">
        <div className="w-16 h-16 rounded-full bg-accent2/20 flex items-center justify-center text-3xl">💊</div>
        <div>
          <h2 className="font-head text-xl font-bold mb-1">Medicine Added</h2>
          <p className="text-muted text-sm">{done.name} · ID {done.id}</p>
          <p className="text-accent2 text-sm mt-1">₹{Number(done.unit_price).toFixed(2)} per unit</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate('/admin/medicines')} className="btn btn-secondary">← Medicines</button>
          <button onClick={() => { setForm(EMPTY); setDone(null) }} className="btn btn-primary">Add Another</button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="p-7 max-w-xl mx-auto flex flex-col gap-5">
      <div>
        <h1 className="font-head text-xl font-bold">Add Medicine</h1>
        <p className="text-muted text-xs mt-0.5">Add a medicine and set initial inventory</p>
      </div>

      <form onSubmit={submit} className="card flex flex-col gap-4">
        <p className="card-title">Medicine Details</p>

        <div className="grid grid-cols-2 gap-4">
          {[['name','Medicine Name',true],['generic_name','Generic Name',false],
            ['strength','Strength (e.g. 500mg)',false],['manufacturer','Manufacturer',false]].map(([k,l,req]) => (
            <div key={k} className="flex flex-col gap-1.5">
              <label className="form-label">{l}{req && ' *'}</label>
              <input className="form-input" required={req} value={form[k]} onChange={e => set(k, e.target.value)} />
            </div>
          ))}

          <div className="flex flex-col gap-1.5">
            <label className="form-label">Dosage Form</label>
            <select className="form-input" value={form.dosage_form} onChange={e => set('dosage_form', e.target.value)}>
              <option value="">Select</option>
              {FORMS.map(f => <option key={f}>{f}</option>)}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="form-label">Unit Price (₹) *</label>
            <input type="number" step="0.01" min="0" className="form-input" required
              value={form.unit_price} onChange={e => set('unit_price', e.target.value)} />
          </div>
        </div>

        <div className="border-t border-white/[0.07] pt-4">
          <p className="form-label mb-3">Initial Inventory</p>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="form-label">Opening Stock *</label>
              <input type="number" min="0" className="form-input" required
                value={form.quantity} onChange={e => set('quantity', e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="form-label">Reorder Level</label>
              <input type="number" min="0" className="form-input"
                value={form.reorder_level} onChange={e => set('reorder_level', e.target.value)} />
              <p className="text-[11px] text-muted">Alert when stock falls below this</p>
            </div>
          </div>
        </div>

        {error && <p className="text-xs text-danger bg-danger/10 border border-danger/20 rounded-xl px-3 py-2">{error}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={() => navigate('/admin/medicines')} className="btn btn-secondary">Cancel</button>
          <button type="submit" disabled={saving} className="btn btn-primary">
            {saving ? 'Adding…' : 'Add Medicine'}
          </button>
        </div>
      </form>
    </div>
  )
}
