import { useEffect, useState } from 'react'
import { queryRecords, createRecord, updateRecord, deleteRecord } from '../../api/client'
import Modal from '../../components/Modal'
import { Plus, Pencil, Trash2, Search } from 'lucide-react'

const SPECS = ['Cardiology','Neurology','Oncology','Orthopedics','Pediatrics','Dermatology','Radiology','Psychiatry','General Medicine','ENT']
const EMPTY = { first_name:'', last_name:'', specialization:'', email:'', phone:'' }
const COLORS = ['text-accent','text-accent2','text-accent3']

export default function AdminDoctors() {
  const [doctors, setDoctors] = useState([])
  const [search, setSearch]   = useState('')
  const [loading, setLoading] = useState(true)
  const [modal, setModal]     = useState(null)
  const [form, setForm]       = useState(EMPTY)
  const [editId, setEditId]   = useState(null)
  const [saving, setSaving]   = useState(false)
  const [toast, setToast]     = useState('')

  const load = async () => { setLoading(true); setDoctors(await queryRecords('doctors')); setLoading(false) }
  useEffect(() => { load() }, [])

  const filtered = doctors.filter(d =>
    `${d.first_name} ${d.last_name} ${d.specialization} ${d.email}`.toLowerCase().includes(search.toLowerCase())
  )

  const openAdd  = () => { setForm(EMPTY); setModal('add') }
  const openEdit = (d) => { setForm({ ...d }); setEditId(d.id); setModal('edit') }

  const save = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      modal === 'add' ? await createRecord('doctors', form) : await updateRecord('doctors', { id: editId }, form)
      setModal(null); showToast(modal === 'add' ? '✅ Doctor added' : '✅ Updated'); await load()
    } finally { setSaving(false) }
  }

  const del = async (d) => {
    if (!confirm(`Delete Dr. ${d.first_name} ${d.last_name}?`)) return
    await deleteRecord('doctors', { id: d.id }); showToast('🗑️ Deleted'); await load()
  }

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div className="p-7 flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-head text-xl font-bold">Doctors</h1>
          <p className="text-muted text-xs mt-0.5">{doctors.length} on staff</p>
        </div>
        <button onClick={openAdd} className="btn btn-primary"><Plus size={14} /> Add Doctor</button>
      </div>

      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
        <input className="form-input pl-9" placeholder="Search by name or specialization…" value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      {loading ? <div className="text-center py-10 text-muted">Loading…</div> : (
        <div className="grid grid-cols-2 gap-4">
          {filtered.map((d, i) => (
            <div key={d.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 rounded-full bg-accent2/20 flex items-center justify-center text-accent2 font-bold flex-shrink-0">
                    {d.first_name?.[0]}{d.last_name?.[0]}
                  </div>
                  <div>
                    <div className="font-head font-bold text-sm">Dr. {d.first_name} {d.last_name}</div>
                    <div className={`text-xs font-medium ${COLORS[i % 3]}`}>{d.specialization}</div>
                  </div>
                </div>
                <div className="flex gap-1.5">
                  <button onClick={() => openEdit(d)} className="btn btn-secondary btn-sm !px-2"><Pencil size={12} /></button>
                  <button onClick={() => del(d)} className="btn btn-danger btn-sm !px-2"><Trash2 size={12} /></button>
                </div>
              </div>
              <div className="flex flex-col gap-1 text-xs text-muted border-t border-white/[0.07] pt-3">
                {d.email && <span>✉️ {d.email}</span>}
                {d.phone && <span>📞 {d.phone}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {modal && (
        <Modal title={modal === 'add' ? 'Add Doctor' : 'Edit Doctor'} onClose={() => setModal(null)}>
          <form onSubmit={save} className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-3">
              {[['first_name','First Name'],['last_name','Last Name'],['email','Email'],['phone','Phone']].map(([k,l]) => (
                <div key={k} className="flex flex-col gap-1.5">
                  <label className="form-label">{l}</label>
                  <input className="form-input" value={form[k]||''} onChange={e => set(k, e.target.value)} />
                </div>
              ))}
              <div className="col-span-2 flex flex-col gap-1.5">
                <label className="form-label">Specialization</label>
                <select className="form-input" value={form.specialization||''} onChange={e => set('specialization', e.target.value)}>
                  <option value="">Select</option>
                  {SPECS.map(s => <option key={s}>{s}</option>)}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-2">
              <button type="button" onClick={() => setModal(null)} className="btn btn-secondary">Cancel</button>
              <button type="submit" disabled={saving} className="btn btn-primary">{saving ? 'Saving…' : modal === 'add' ? 'Add Doctor' : 'Save'}</button>
            </div>
          </form>
        </Modal>
      )}

      {toast && <div className="fixed bottom-6 right-6 bg-bg2 border border-white/[0.07] rounded-xl px-5 py-3 text-sm shadow-xl z-50">{toast}</div>}
    </div>
  )
}
