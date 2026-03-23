import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { getPrescriptionDetails, generateOrder } from '../../api/client'
import Modal from '../../components/Modal'
import { Zap } from 'lucide-react'

const fmt = d => new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })

export default function PatientPrescriptions() {
  const { user } = useAuth()
  const [prescriptions, setPrescriptions] = useState([])
  const [loading, setLoading]             = useState(true)
  const [selected, setSelected]           = useState(null)
  const [generating, setGenerating]       = useState(null)
  const [toast, setToast]                 = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const data = await getPrescriptionDetails({ patient_id: user.patientId })
      const grouped = {}
      data.forEach(row => {
        if (!grouped[row.prescription_id]) {
          grouped[row.prescription_id] = {
            id: row.prescription_id,
            doctor: `Dr. ${row.doctor_first_name} ${row.doctor_last_name}`,
            specialization: row.specialization,
            created_at: row.created_at,
            medicines: [],
          }
        }
        grouped[row.prescription_id].medicines.push({
          name: row.medicine_name, generic: row.generic_name,
          dosage: row.dosage, frequency: row.frequency,
          duration: row.duration, instructions: row.instructions,
        })
      })
      setPrescriptions(Object.values(grouped))
    } catch { setPrescriptions([]) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleGenerate = async (id) => {
    setGenerating(id)
    try {
      await generateOrder(id)
      showToast('✅ Order generated!')
    } catch (e) {
      showToast('⚠️ ' + (e?.response?.data?.detail ?? 'Failed to generate order'))
    } finally { setGenerating(null) }
  }

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3500) }

  if (loading) return <div className="p-7 text-muted">Loading…</div>

  return (
    <div className="p-7 flex flex-col gap-5">
      <div>
        <h1 className="font-head text-xl font-bold">My Prescriptions</h1>
        <p className="text-muted text-xs mt-0.5">{prescriptions.length} prescription{prescriptions.length !== 1 ? 's' : ''}</p>
      </div>

      {prescriptions.length === 0 ? (
        <div className="card text-center py-14 text-muted"><div className="text-4xl mb-3">💊</div>No prescriptions found</div>
      ) : (
        <div className="flex flex-col gap-4">
          {prescriptions.map(rx => (
            <div key={rx.id} className="card">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="font-head font-bold">Prescription #{rx.id}</div>
                  <div className="text-sm text-muted mt-0.5">{rx.doctor} · {rx.specialization}</div>
                  <div className="text-xs text-muted mt-0.5">{fmt(rx.created_at)}</div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setSelected(rx)} className="btn btn-secondary btn-sm">Details</button>
                  <button onClick={() => handleGenerate(rx.id)} disabled={generating === rx.id} className="btn btn-primary btn-sm">
                    <Zap size={12} />{generating === rx.id ? 'Generating…' : 'Generate Order'}
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {rx.medicines.map((m, i) => (
                  <span key={i} className="badge badge-green border border-accent2/20">💊 {m.name}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {selected && (
        <Modal title={`Prescription #${selected.id}`} onClose={() => setSelected(null)} maxWidth="max-w-2xl">
          <div className="flex flex-col gap-4">
            <div className="p-3 bg-bg3 rounded-xl border border-white/[0.07] text-sm">
              <div className="text-muted text-xs mb-1">Prescribed by</div>
              <div className="font-medium">{selected.doctor}</div>
              <div className="text-muted">{selected.specialization} · {fmt(selected.created_at)}</div>
            </div>
            <p className="form-label">Medicines</p>
            <div className="flex flex-col gap-3">
              {selected.medicines.map((m, i) => (
                <div key={i} className="p-4 bg-bg3 rounded-xl border border-white/[0.07]">
                  <div className="flex justify-between mb-2">
                    <span className="font-medium text-sm">{m.name}</span>
                    {m.generic && <span className="text-xs text-muted">{m.generic}</span>}
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs text-muted">
                    <span>Dosage: <span className="text-white">{m.dosage || '—'}</span></span>
                    <span>Frequency: <span className="text-white">{m.frequency || '—'}</span></span>
                    <span>Duration: <span className="text-white">{m.duration || '—'}</span></span>
                  </div>
                  {m.instructions && <div className="mt-2 text-xs text-accent3">📌 {m.instructions}</div>}
                </div>
              ))}
            </div>
          </div>
        </Modal>
      )}

      {toast && (
        <div className="fixed bottom-6 right-6 bg-bg2 border border-white/[0.07] rounded-xl px-5 py-3 text-sm shadow-xl z-50">
          {toast}
        </div>
      )}
    </div>
  )
}
