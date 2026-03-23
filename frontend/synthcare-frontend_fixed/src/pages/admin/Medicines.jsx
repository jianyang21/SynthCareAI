import { useEffect, useState } from 'react'
import { queryRecords, createRecord, updateRecord, deleteRecord, getLowStock } from '../../api/client'
import Modal from '../../components/Modal'
import { Plus, Pencil, Trash2, Search, AlertTriangle } from 'lucide-react'

const FORMS = ['Tablet','Capsule','Syrup','Injection','Cream','Drops','Inhaler']
const EMPTY = { name:'', generic_name:'', strength:'', dosage_form:'', manufacturer:'', unit_price:'', quantity:'', reorder_level:'' }

export default function AdminMedicines() {
  const [medicines, setMedicines] = useState([])
  const [inventory, setInventory] = useState([])
  const [lowStock, setLowStock]   = useState([])
  const [search, setSearch]       = useState('')
  const [tab, setTab]             = useState('all')
  const [loading, setLoading]     = useState(true)
  const [modal, setModal]         = useState(null)
  const [form, setForm]           = useState(EMPTY)
  const [editId, setEditId]       = useState(null)
  const [saving, setSaving]       = useState(false)
  const [toast, setToast]         = useState('')

  const load = async () => {
    setLoading(true)
    const [meds, inv, low] = await Promise.all([queryRecords('medicines'), queryRecords('medicine_inventory'), getLowStock()])
    setMedicines(meds); setInventory(inv); setLowStock(low)
    setLoading(false)
  }
  useEffect(() => { load() }, [])

  const getInv = (id) => inventory.find(i => i.medicine_id === id)

  const display = tab === 'low'
    ? medicines.filter(m => lowStock.find(l => l.medicine_id === m.id))
    : medicines

  const filtered = display.filter(m =>
    `${m.name} ${m.generic_name} ${m.manufacturer}`.toLowerCase().includes(search.toLowerCase())
  )

  const openAdd  = () => { setForm(EMPTY); setModal('add') }
  const openEdit = (m) => {
    const inv = getInv(m.id)
    setForm({ ...m, quantity: inv?.quantity??'', reorder_level: inv?.reorder_level??'' })
    setEditId(m.id); setModal('edit')
  }

  const save = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      const { quantity, reorder_level, ...medData } = form
      medData.unit_price = parseFloat(medData.unit_price) || 0
      if (modal === 'add') {
        const med = await createRecord('medicines', medData)
        await createRecord('medicine_inventory', { medicine_id: med.id, quantity: parseInt(quantity)||0, reorder_level: parseInt(reorder_level)||20 })
      } else {
        await updateRecord('medicines', { id: editId }, medData)
        const inv = getInv(editId)
        if (inv) await updateRecord('medicine_inventory', { id: inv.id }, { quantity: parseInt(quantity)||0, reorder_level: parseInt(reorder_level)||20 })
      }
      setModal(null); showToast(modal === 'add' ? '✅ Medicine added' : '✅ Updated'); await load()
    } finally { setSaving(false) }
  }

  const del = async (m) => {
    if (!confirm(`Delete ${m.name}?`)) return
    const inv = getInv(m.id)
    if (inv) await deleteRecord('medicine_inventory', { id: inv.id })
    await deleteRecord('medicines', { id: m.id })
    showToast('🗑️ Deleted'); await load()
  }

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div className="p-7 flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-head text-xl font-bold">Medicines & Inventory</h1>
          <p className="text-muted text-xs mt-0.5">{medicines.length} medicines · <span className="text-danger">{lowStock.length} low stock</span></p>
        </div>
        <button onClick={openAdd} className="btn btn-primary"><Plus size={14} /> Add Medicine</button>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input className="form-input pl-9" placeholder="Search medicines…" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <button onClick={() => setTab('all')} className={`tab ${tab==='all'?'active':''}`}>All</button>
        <button onClick={() => setTab('low')} className={`tab ${tab==='low'?'active':''} flex items-center gap-1.5`}>
          <AlertTriangle size={12} />Low Stock ({lowStock.length})
        </button>
      </div>

      <div className="card p-0 overflow-hidden">
        {loading ? <div className="p-8 text-center text-muted">Loading…</div> : (
          <div className="overflow-x-auto">
            <table className="w-full tbl">
              <thead><tr><th>Medicine</th><th>Generic</th><th>Form</th><th>Strength</th><th>Price</th><th>Stock</th><th>Reorder</th><th></th></tr></thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr><td colSpan={8} className="text-center text-muted py-10">No medicines found</td></tr>
                ) : filtered.map(m => {
                  const inv = getInv(m.id)
                  const isLow = inv && inv.quantity <= inv.reorder_level
                  return (
                    <tr key={m.id}>
                      <td className="font-medium">{m.name}</td>
                      <td className="text-muted">{m.generic_name}</td>
                      <td><span className="badge badge-grey">{m.dosage_form}</span></td>
                      <td className="text-muted">{m.strength}</td>
                      <td>₹{Number(m.unit_price||0).toFixed(2)}</td>
                      <td><span className={`badge ${isLow?'badge-red':'badge-green'}`}>{inv?.quantity??'—'}</span></td>
                      <td className="text-muted">{inv?.reorder_level??'—'}</td>
                      <td>
                        <div className="flex gap-1.5 justify-end">
                          <button onClick={() => openEdit(m)} className="btn btn-secondary btn-sm !px-2"><Pencil size={12} /></button>
                          <button onClick={() => del(m)} className="btn btn-danger btn-sm !px-2"><Trash2 size={12} /></button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {modal && (
        <Modal title={modal==='add'?'Add Medicine':'Edit Medicine'} onClose={() => setModal(null)} maxWidth="max-w-2xl">
          <form onSubmit={save} className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-3">
              {[['name','Medicine Name'],['generic_name','Generic Name'],['manufacturer','Manufacturer'],['strength','Strength']].map(([k,l]) => (
                <div key={k} className="flex flex-col gap-1.5">
                  <label className="form-label">{l}</label>
                  <input className="form-input" value={form[k]||''} onChange={e => set(k, e.target.value)} />
                </div>
              ))}
              <div className="flex flex-col gap-1.5">
                <label className="form-label">Dosage Form</label>
                <select className="form-input" value={form.dosage_form||''} onChange={e => set('dosage_form', e.target.value)}>
                  <option value="">Select</option>
                  {FORMS.map(f => <option key={f}>{f}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="form-label">Unit Price (₹)</label>
                <input type="number" step="0.01" className="form-input" value={form.unit_price||''} onChange={e => set('unit_price', e.target.value)} />
              </div>
            </div>
            <div className="border-t border-white/[0.07] pt-4">
              <p className="form-label mb-3">Inventory</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <label className="form-label">Current Stock</label>
                  <input type="number" className="form-input" value={form.quantity||''} onChange={e => set('quantity', e.target.value)} />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="form-label">Reorder Level</label>
                  <input type="number" className="form-input" value={form.reorder_level||''} onChange={e => set('reorder_level', e.target.value)} />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-2">
              <button type="button" onClick={() => setModal(null)} className="btn btn-secondary">Cancel</button>
              <button type="submit" disabled={saving} className="btn btn-primary">{saving?'Saving…':modal==='add'?'Add Medicine':'Save'}</button>
            </div>
          </form>
        </Modal>
      )}

      {toast && <div className="fixed bottom-6 right-6 bg-bg2 border border-white/[0.07] rounded-xl px-5 py-3 text-sm shadow-xl z-50">{toast}</div>}
    </div>
  )
}
