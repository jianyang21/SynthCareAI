import { useEffect, useState } from 'react'
import { queryRecords, createRecord, updateRecord, deleteRecord } from '../../api/client'
import Modal from '../../components/Modal'
import { Plus, Pencil, Trash2, Search } from 'lucide-react'

const EMPTY = { first_name:'', last_name:'', gender:'', date_of_birth:'', email:'', phone:'', city:'', blood_group:'' }

export default function AdminPatients() {
  const [patients, setPatients] = useState([])
  const [search, setSearch]     = useState('')
  const [loading, setLoading]   = useState(true)
  const [modal, setModal]       = useState(null)
  const [form, setForm]         = useState(EMPTY)
  const [editId, setEditId]     = useState(null)
  const [saving, setSaving]     = useState(false)
  const [toast, setToast]       = useState('')

  const load = async () => { setLoading(true); setPatients(await queryRecords('patients')); setLoading(false) }
  useEffect(() => { load() }, [])

  const filtered = patients.filter(p =>
    `${p.first_name} ${p.last_name} ${p.email} ${p.city}`.toLowerCase().includes(search.toLowerCase())
  )

  const openAdd  = () => { setForm(EMPTY); setModal('add') }
  const openEdit = (p) => { setForm({ ...p }); setEditId(p.id); setModal('edit') }

  const save = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      modal === 'add' ? await createRecord('patients', form) : await updateRecord('patients', { id: editId }, form)
      setModal(null); showToast(modal === 'add' ? '✅ Patient added' : '✅ Updated'); await load()
    } finally { setSaving(false) }
  }

  const del = async (p) => {
    if (!confirm(`Delete ${p.first_name} ${p.last_name}?`)) return
    await deleteRecord('patients', { id: p.id }); showToast('🗑️ Deleted'); await load()
  }

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div className="p-7 flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-head text-xl font-bold">Patients</h1>
          <p className="text-muted text-xs mt-0.5">{patients.length} registered</p>
        </div>
        <button onClick={openAdd} className="btn btn-primary"><Plus size={14} /> Add Patient</button>
      </div>

      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
        <input className="form-input pl-9" placeholder="Search by name, email, city…" value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      <div className="card p-0 overflow-hidden">
        {loading ? <div className="p-8 text-center text-muted">Loading…</div> : (
          <div className="overflow-x-auto">
            <table className="w-full tbl">
              <thead><tr><th>Name</th><th>Gender</th><th>Blood Group</th><th>City</th><th>Phone</th><th>Email</th><th></th></tr></thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr><td colSpan={7} className="text-center text-muted py-10">No patients found</td></tr>
                ) : filtered.map(p => (
                  <tr key={p.id}>
                    <td className="font-medium">{p.first_name} {p.last_name}</td>
                    <td className="text-muted">{p.gender}</td>
                    <td><span className="badge badge-blue">{p.blood_group}</span></td>
                    <td className="text-muted">{p.city}</td>
                    <td className="text-muted">{p.phone}</td>
                    <td className="text-muted">{p.email}</td>
                    <td>
                      <div className="flex gap-1.5 justify-end">
                        <button onClick={() => openEdit(p)} className="btn btn-secondary btn-sm !px-2"><Pencil size={12} /></button>
                        <button onClick={() => del(p)} className="btn btn-danger btn-sm !px-2"><Trash2 size={12} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {modal && (
        <Modal title={modal === 'add' ? 'Add Patient' : 'Edit Patient'} onClose={() => setModal(null)}>
          <form onSubmit={save} className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-3">
              {[['first_name','First Name'],['last_name','Last Name'],['email','Email'],['phone','Phone'],['city','City'],['blood_group','Blood Group']].map(([k,l]) => (
                <div key={k} className="flex flex-col gap-1.5">
                  <label className="form-label">{l}</label>
                  <input className="form-input" value={form[k]||''} onChange={e => set(k, e.target.value)} />
                </div>
              ))}
              <div className="flex flex-col gap-1.5">
                <label className="form-label">Gender</label>
                <select className="form-input" value={form.gender||''} onChange={e => set('gender', e.target.value)}>
                  <option value="">Select</option>
                  <option>Male</option><option>Female</option><option>Other</option>
                </select>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="form-label">Date of Birth</label>
                <input type="date" className="form-input" value={form.date_of_birth?.split('T')[0]||''} onChange={e => set('date_of_birth', e.target.value)} />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-2">
              <button type="button" onClick={() => setModal(null)} className="btn btn-secondary">Cancel</button>
              <button type="submit" disabled={saving} className="btn btn-primary">{saving ? 'Saving…' : modal === 'add' ? 'Add Patient' : 'Save'}</button>
            </div>
          </form>
        </Modal>
      )}

      {toast && <div className="fixed bottom-6 right-6 bg-bg2 border border-white/[0.07] rounded-xl px-5 py-3 text-sm shadow-xl z-50">{toast}</div>}
    </div>
  )
}
