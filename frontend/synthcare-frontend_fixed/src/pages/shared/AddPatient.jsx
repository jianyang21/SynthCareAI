import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { createRecord, API_URL } from '../../api/client'
import { Upload, X, FileText, CheckCircle, AlertCircle, ChevronRight } from 'lucide-react'

const STEPS      = ['Patient Info', 'Upload PDFs', 'Done']
const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
const GENDERS      = ['Male', 'Female', 'Other']
const DOC_TYPES    = [
  'lab_report', 'blood_report', 'xray', 'mri',
  'prescription_scan', 'discharge_summary', 'doctor_note', 'other',
]

const EMPTY = {
  first_name: '', last_name: '', gender: '',
  date_of_birth: '', email: '', phone: '',
  city: '', blood_group: '',
}

export default function AddPatient() {
  const { user }  = useAuth()
  const navigate  = useNavigate()
  const fileRef   = useRef(null)

  const [step, setStep]           = useState(0)
  const [form, setForm]           = useState(EMPTY)
  const [files, setFiles]         = useState([])      // { file, type, status, chunks, error }
  const [createdId, setCreatedId] = useState(null)
  const [saving, setSaving]       = useState(false)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver]   = useState(false)
  const [toast, setToast]         = useState({ msg: '', ok: true })

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const backPath = user?.role === 'doctor' ? '/doctor' : '/admin/patients'

  // ── Step 0: create the patient record ────────────────────────────
  const handleCreate = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const patient = await createRecord('patients', form)
      setCreatedId(patient.id)
      showToast('Patient created — now upload any PDF records', true)
      setStep(1)
    } catch (err) {
      showToast(err?.response?.data?.detail ?? 'Failed to create patient', false)
    } finally { setSaving(false) }
  }

  // ── File handling ─────────────────────────────────────────────────
  const addFiles = (incoming) => {
    const pdfs = Array.from(incoming).filter(f => f.type === 'application/pdf')
    if (pdfs.length < incoming.length) showToast('Only PDF files are accepted', false)
    setFiles(prev => [
      ...prev,
      ...pdfs.map(f => ({ file: f, type: 'lab_report', status: 'pending', chunks: 0, error: null })),
    ])
  }

  const onDrop = (e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files) }
  const removeFile  = (i) => setFiles(prev => prev.filter((_, idx) => idx !== i))
  const setFileType = (i, t) => setFiles(prev => prev.map((f, idx) => idx === i ? { ...f, type: t } : f))

  // ── Step 1: upload PDFs to /records/upload ───────────────────────
  const handleUploadAll = async () => {
    setUploading(true)
    for (let i = 0; i < files.length; i++) {
      if (files[i].status === 'done') continue
      setFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: 'uploading' } : f))
      try {
        const fd = new FormData()
        fd.append('patient_id', createdId)
        fd.append('record_type', files[i].type)
        fd.append('file', files[i].file)
        const res = await fetch(`${API_URL}/records/upload`, { method: 'POST', body: fd })
        if (!res.ok) throw new Error(await res.text())
        const data = await res.json()
        setFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: 'done', chunks: data.total_chunks } : f))
      } catch (err) {
        setFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: 'error', error: err.message } : f))
      }
    }
    setUploading(false)
  }

  const allDone     = files.length > 0 && files.every(f => f.status === 'done')
  const doneCount   = files.filter(f => f.status === 'done').length
  const totalChunks = files.filter(f => f.status === 'done').reduce((s, f) => s + (f.chunks || 0), 0)
  const showToast   = (msg, ok = true) => { setToast({ msg, ok }); setTimeout(() => setToast({ msg: '', ok: true }), 4000) }

  // ─────────────────────────────────────────────────────────────────
  return (
    <div className="p-7 max-w-2xl mx-auto flex flex-col gap-6">

      {/* Header */}
      <div>
        <h1 className="font-head text-xl font-bold">Add New Patient</h1>
        <p className="text-muted text-xs mt-0.5">
          Create a patient record and optionally upload medical PDFs — they'll be indexed for AI search
        </p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-1">
        {STEPS.map((s, i) => (
          <div key={i} className="flex items-center gap-1">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium transition-all
              ${step === i  ? 'bg-accent/10 text-accent border border-accent/30'
              : step > i    ? 'text-accent2'
              : 'text-muted'}`}>
              <div className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0
                ${step > i ? 'bg-accent2 text-bg' : step === i ? 'bg-accent text-white' : 'bg-bg3 text-muted'}`}>
                {step > i ? '✓' : i + 1}
              </div>
              {s}
            </div>
            {i < STEPS.length - 1 && <ChevronRight size={12} className="text-muted" />}
          </div>
        ))}
      </div>

      {/* ── STEP 0: Patient Info ────────────────────────────────── */}
      {step === 0 && (
        <form onSubmit={handleCreate} className="card flex flex-col gap-5">
          <p className="card-title">Patient Details</p>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="form-label">First Name *</label>
              <input className="form-input" required value={form.first_name}
                onChange={e => set('first_name', e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="form-label">Last Name *</label>
              <input className="form-input" required value={form.last_name}
                onChange={e => set('last_name', e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="form-label">Email *</label>
              <input className="form-input" type="email" required value={form.email}
                onChange={e => set('email', e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="form-label">Phone *</label>
              <input className="form-input" required value={form.phone}
                onChange={e => set('phone', e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="form-label">Gender *</label>
              <select className="form-input" required value={form.gender}
                onChange={e => set('gender', e.target.value)}>
                <option value="">Select</option>
                {GENDERS.map(g => <option key={g}>{g}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="form-label">Blood Group</label>
              <select className="form-input" value={form.blood_group}
                onChange={e => set('blood_group', e.target.value)}>
                <option value="">Select</option>
                {BLOOD_GROUPS.map(b => <option key={b}>{b}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="form-label">Date of Birth</label>
              <input type="date" className="form-input" value={form.date_of_birth}
                onChange={e => set('date_of_birth', e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="form-label">City</label>
              <input className="form-input" value={form.city}
                onChange={e => set('city', e.target.value)} />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2 border-t border-white/[0.07]">
            <button type="button" onClick={() => navigate(backPath)} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="btn btn-primary">
              {saving ? 'Creating…' : 'Create Patient →'}
            </button>
          </div>
        </form>
      )}

      {/* ── STEP 1: Upload PDFs ─────────────────────────────────── */}
      {step === 1 && (
        <div className="flex flex-col gap-4">

          {/* Info strip */}
          <div className="flex items-center justify-between p-3 bg-accent2/5 border border-accent2/20 rounded-xl text-sm">
            <span className="text-accent2 font-medium">
              ✅ Patient created — ID <strong>{createdId}</strong>
            </span>
            <button onClick={() => setStep(2)} className="text-xs text-muted hover:text-white transition-colors">
              Skip & finish →
            </button>
          </div>

          {/* Drop zone */}
          <div className="card">
            <p className="card-title">Upload Medical PDFs</p>
            <p className="text-xs text-muted mb-4">
              PDFs are chunked and stored in the vector database. The AI assistant can then answer questions about them.
            </p>

            <div
              onDrop={onDrop}
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all
                ${dragOver
                  ? 'border-accent bg-accent/5'
                  : 'border-white/[0.07] hover:border-accent/40 hover:bg-white/[0.015]'}`}>
              <Upload size={26} className="mx-auto mb-3 text-muted" />
              <p className="text-sm font-medium text-white mb-1">Drop PDFs here or click to browse</p>
              <p className="text-xs text-muted">Only PDF files · Multiple files supported</p>
              <input ref={fileRef} type="file" accept=".pdf" multiple className="hidden"
                onChange={e => addFiles(e.target.files)} />
            </div>
          </div>

          {/* File list */}
          {files.length > 0 && (
            <div className="card flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <p className="card-title mb-0">Files ({files.length})</p>
                <span className="text-xs text-muted">{doneCount} / {files.length} indexed</span>
              </div>

              {files.map((entry, i) => (
                <div key={i} className={`flex items-center gap-3 p-3 rounded-xl border transition-all
                  ${entry.status === 'done'      ? 'border-accent2/30 bg-accent2/5'
                  : entry.status === 'error'     ? 'border-danger/30 bg-danger/5'
                  : entry.status === 'uploading' ? 'border-accent/30 bg-accent/5'
                  : 'border-white/[0.07] bg-bg3'}`}>

                  {/* Status icon */}
                  <div className="flex-shrink-0 w-5 flex items-center justify-center">
                    {entry.status === 'done'      && <CheckCircle size={16} className="text-accent2" />}
                    {entry.status === 'error'     && <AlertCircle size={16} className="text-danger" />}
                    {entry.status === 'uploading' && <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />}
                    {entry.status === 'pending'   && <FileText size={16} className="text-muted" />}
                  </div>

                  {/* File info */}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{entry.file.name}</div>
                    <div className="text-xs text-muted">
                      {entry.status === 'done'      && `✅ ${entry.chunks} chunks indexed in vector store`}
                      {entry.status === 'error'     && <span className="text-danger">{entry.error}</span>}
                      {entry.status === 'uploading' && 'Uploading & indexing…'}
                      {entry.status === 'pending'   && `${(entry.file.size / 1024).toFixed(1)} KB`}
                    </div>
                  </div>

                  {/* Doc type */}
                  {entry.status !== 'done' ? (
                    <select value={entry.type} onChange={e => setFileType(i, e.target.value)}
                      className="form-input !w-auto text-xs py-1 px-2 flex-shrink-0">
                      {DOC_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
                    </select>
                  ) : (
                    <span className="badge badge-green text-[11px] flex-shrink-0">
                      {entry.type.replace(/_/g, ' ')}
                    </span>
                  )}

                  {/* Remove */}
                  {(entry.status === 'pending' || entry.status === 'error') && (
                    <button onClick={() => removeFile(i)}
                      className="btn btn-danger btn-sm !px-1.5 !py-1.5 flex-shrink-0">
                      <X size={11} />
                    </button>
                  )}
                </div>
              ))}

              <div className="flex justify-between items-center pt-2 border-t border-white/[0.07]">
                <button onClick={() => fileRef.current?.click()} className="btn btn-secondary btn-sm">
                  + Add more
                </button>
                <div className="flex gap-2">
                  {allDone && (
                    <button onClick={() => setStep(2)} className="btn btn-success btn-sm">
                      Finish →
                    </button>
                  )}
                  {!allDone && (
                    <button onClick={handleUploadAll}
                      disabled={uploading || files.every(f => f.status === 'done')}
                      className="btn btn-primary btn-sm disabled:opacity-40">
                      {uploading
                        ? 'Uploading…'
                        : `Upload ${files.filter(f => f.status === 'pending').length} file(s)`}
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── STEP 2: Done ────────────────────────────────────────── */}
      {step === 2 && (
        <div className="card flex flex-col items-center gap-5 py-12 text-center">
          <div className="w-16 h-16 rounded-full bg-accent2/20 flex items-center justify-center text-3xl">✅</div>
          <div>
            <h2 className="font-head text-xl font-bold mb-1">Patient Added Successfully</h2>
            <p className="text-muted text-sm">
              {form.first_name} {form.last_name} · Patient ID <span className="text-accent font-bold">#{createdId}</span>
            </p>
          </div>

          {/* Summary */}
          <div className="w-full max-w-xs bg-bg3 border border-white/[0.07] rounded-xl p-4 text-sm text-left">
            <p className="form-label mb-3">Summary</p>
            {[
              ['Name',           `${form.first_name} ${form.last_name}`],
              ['Email',          form.email],
              ['Blood Group',    form.blood_group || '—'],
              ['City',           form.city || '—'],
              ['PDFs uploaded',  `${doneCount} file${doneCount !== 1 ? 's' : ''}`],
              ['Chunks indexed', totalChunks],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between py-1.5 border-b border-white/[0.05] last:border-0">
                <span className="text-muted">{k}</span>
                <span className="font-medium">{v}</span>
              </div>
            ))}
          </div>

          <div className="flex gap-3">
            <button onClick={() => navigate(backPath)} className="btn btn-secondary">
              ← Back
            </button>
            <button onClick={() => {
              setForm(EMPTY); setFiles([]); setCreatedId(null); setStep(0)
            }} className="btn btn-primary">
              Add Another Patient
            </button>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast.msg && (
        <div className={`fixed bottom-6 right-6 border rounded-xl px-5 py-3 text-sm shadow-xl z-50 transition-all
          ${toast.ok
            ? 'bg-bg2 border-white/[0.07] text-white'
            : 'bg-danger/10 border-danger/30 text-danger'}`}>
          {toast.msg}
        </div>
      )}
    </div>
  )
}
