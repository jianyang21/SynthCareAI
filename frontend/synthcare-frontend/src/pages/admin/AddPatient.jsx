import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { createRecord, API_URL } from '../../api/client'
import { Upload, X, FileText, CheckCircle, AlertCircle, ChevronRight } from 'lucide-react'

const STEPS = ['Patient Info', 'Medical Records', 'Review']

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
const GENDERS      = ['Male', 'Female', 'Other']
const DOC_TYPES    = ['lab_report', 'blood_report', 'xray', 'mri', 'prescription_scan', 'discharge_summary', 'doctor_note', 'other']

const EMPTY = {
  first_name: '', last_name: '', gender: '', date_of_birth: '',
  email: '', phone: '', city: '', state: '', country: 'India',
  blood_group: '', address_line1: '', postal_code: '',
  emergency_contact_name: '', emergency_contact_phone: '', emergency_contact_relationship: '',
}

export default function AddPatient() {
  const navigate  = useNavigate()
  const fileRef   = useRef(null)
  const [step, setStep]       = useState(0)
  const [form, setForm]       = useState(EMPTY)
  const [files, setFiles]     = useState([])   // { file, type, name, status, error }
  const [saving, setSaving]   = useState(false)
  const [createdId, setCreatedId] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [toast, setToast]     = useState({ msg: '', type: '' })
  const [dragOver, setDragOver] = useState(false)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  // ── Step 1: create patient ─────────────────────────────────────────
  const handleCreatePatient = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const patient = await createRecord('patients', form)
      setCreatedId(patient.id)
      showToast('✅ Patient created — now upload their records', 'success')
      setStep(1)
    } catch (err) {
      showToast('❌ ' + (err?.response?.data?.detail ?? 'Failed to create patient'), 'error')
    } finally { setSaving(false) }
  }

  // ── File handling ──────────────────────────────────────────────────
  const addFiles = (incoming) => {
    const pdfs = Array.from(incoming).filter(f => f.type === 'application/pdf')
    if (pdfs.length !== incoming.length) showToast('⚠️ Only PDF files are accepted', 'error')
    setFiles(prev => [
      ...prev,
      ...pdfs.map(f => ({ file: f, type: 'lab_report', name: f.name, status: 'pending', error: null }))
    ])
  }

  const onDrop = (e) => {
    e.preventDefault(); setDragOver(false)
    addFiles(e.dataTransfer.files)
  }

  const removeFile = (i) => setFiles(prev => prev.filter((_, idx) => idx !== i))
  const setFileType = (i, type) => setFiles(prev => prev.map((f, idx) => idx === i ? { ...f, type } : f))

  // ── Step 2: upload PDFs one by one ───────────────────────────────
  const handleUploadAll = async () => {
    if (!createdId) return
    setUploading(true)

    for (let i = 0; i < files.length; i++) {
      const entry = files[i]
      if (entry.status === 'done') continue

      setFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: 'uploading' } : f))

      try {
        const fd = new FormData()
        fd.append('patient_id', createdId)
        fd.append('record_type', entry.type)
        fd.append('file', entry.file)

        const res = await fetch(`${API_URL}/records/upload`, { method: 'POST', body: fd })
        if (!res.ok) throw new Error(await res.text())

        const data = await res.json()
        setFiles(prev => prev.map((f, idx) =>
          idx === i ? { ...f, status: 'done', chunks: data.total_chunks } : f
        ))
      } catch (err) {
        setFiles(prev => prev.map((f, idx) =>
          idx === i ? { ...f, status: 'error', error: err.message } : f
        ))
      }
    }

    setUploading(false)
    const allDone = files.every(f => f.status === 'done')
    if (allDone) { showToast('✅ All records uploaded!', 'success'); setStep(2) }
    else showToast('⚠️ Some files failed — check below', 'error')
  }

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast({ msg: '', type: '' }), 4000)
  }

  const doneCount = files.filter(f => f.status === 'done').length

  // ────────────────────────────────────────────────────────────────────
  return (
    <div className="p-7 max-w-3xl mx-auto flex flex-col gap-6">

      {/* Page header */}
      <div>
        <h1 className="font-head text-xl font-bold">Add New Patient</h1>
        <p className="text-muted text-xs mt-0.5">Create patient record and upload medical PDFs to the RAG index</p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-0">
        {STEPS.map((s, i) => (
          <div key={i} className="flex items-center">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all
              ${step === i ? 'bg-accent/10 text-accent border border-accent/30'
              : step > i  ? 'text-accent2'
              : 'text-muted'}`}>
              <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold
                ${step > i ? 'bg-accent2 text-bg' : step === i ? 'bg-accent text-white' : 'bg-bg3 text-muted'}`}>
                {step > i ? '✓' : i + 1}
              </div>
              {s}
            </div>
            {i < STEPS.length - 1 && <ChevronRight size={14} className="text-muted mx-1" />}
          </div>
        ))}
      </div>

      {/* ── STEP 0: Patient Info ── */}
      {step === 0 && (
        <form onSubmit={handleCreatePatient} className="card flex flex-col gap-5">
          <p className="card-title">Patient Information</p>

          <div className="grid grid-cols-2 gap-4">
            {[['first_name','First Name',true],['last_name','Last Name',true],
              ['email','Email',true],['phone','Phone',true],
              ['city','City',false],['state','State',false],
              ['country','Country',false],['postal_code','Postal Code',false],
              ['address_line1','Address Line 1',false]].map(([k,l,req]) => (
              <div key={k} className={`flex flex-col gap-1.5 ${k === 'address_line1' ? 'col-span-2' : ''}`}>
                <label className="form-label">{l}{req && ' *'}</label>
                <input className="form-input" value={form[k] || ''} required={req}
                  onChange={e => set(k, e.target.value)} />
              </div>
            ))}

            <div className="flex flex-col gap-1.5">
              <label className="form-label">Gender *</label>
              <select className="form-input" required value={form.gender} onChange={e => set('gender', e.target.value)}>
                <option value="">Select</option>
                {GENDERS.map(g => <option key={g}>{g}</option>)}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="form-label">Blood Group</label>
              <select className="form-input" value={form.blood_group} onChange={e => set('blood_group', e.target.value)}>
                <option value="">Select</option>
                {BLOOD_GROUPS.map(b => <option key={b}>{b}</option>)}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="form-label">Date of Birth</label>
              <input type="date" className="form-input" value={form.date_of_birth}
                onChange={e => set('date_of_birth', e.target.value)} />
            </div>
          </div>

          {/* Emergency contact */}
          <div className="border-t border-white/[0.07] pt-4">
            <p className="form-label mb-3">Emergency Contact</p>
            <div className="grid grid-cols-3 gap-4">
              {[['emergency_contact_name','Name'],['emergency_contact_phone','Phone'],['emergency_contact_relationship','Relationship']].map(([k,l]) => (
                <div key={k} className="flex flex-col gap-1.5">
                  <label className="form-label">{l}</label>
                  <input className="form-input" value={form[k] || ''} onChange={e => set(k, e.target.value)} />
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => navigate('/admin/patients')} className="btn btn-secondary">Cancel</button>
            <button type="submit" disabled={saving} className="btn btn-primary">
              {saving ? 'Creating…' : 'Create Patient & Continue →'}
            </button>
          </div>
        </form>
      )}

      {/* ── STEP 1: Upload PDFs ── */}
      {step === 1 && (
        <div className="flex flex-col gap-4">
          <div className="card">
            <div className="flex items-center justify-between mb-1">
              <p className="card-title mb-0">Upload Medical Records (PDF)</p>
              <span className="badge badge-green">Patient ID: {createdId}</span>
            </div>
            <p className="text-xs text-muted mb-4">
              PDFs are chunked and indexed into the RAG vector store. The AI can then answer questions about these documents.
            </p>

            {/* Drop zone */}
            <div
              onDrop={onDrop}
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all
                ${dragOver ? 'border-accent bg-accent/5' : 'border-white/[0.07] hover:border-accent/40 hover:bg-white/[0.02]'}`}>
              <Upload size={28} className="mx-auto mb-3 text-muted" />
              <p className="text-sm font-medium text-white mb-1">Drop PDF files here or click to browse</p>
              <p className="text-xs text-muted">Only PDF files accepted · Multiple files supported</p>
              <input ref={fileRef} type="file" accept=".pdf" multiple className="hidden"
                onChange={e => addFiles(e.target.files)} />
            </div>
          </div>

          {/* File list */}
          {files.length > 0 && (
            <div className="card flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <p className="card-title mb-0">Files to Upload ({files.length})</p>
                <span className="text-xs text-muted">{doneCount}/{files.length} uploaded</span>
              </div>

              {files.map((entry, i) => (
                <div key={i} className={`flex items-center gap-3 p-3 rounded-xl border transition-all
                  ${entry.status === 'done'      ? 'border-accent2/30 bg-accent2/5'
                  : entry.status === 'error'     ? 'border-danger/30 bg-danger/5'
                  : entry.status === 'uploading' ? 'border-accent/30 bg-accent/5'
                  : 'border-white/[0.07] bg-bg3'}`}>

                  {/* Icon */}
                  <div className="flex-shrink-0">
                    {entry.status === 'done'      && <CheckCircle size={18} className="text-accent2" />}
                    {entry.status === 'error'      && <AlertCircle size={18} className="text-danger" />}
                    {entry.status === 'uploading'  && <div className="w-[18px] h-[18px] border-2 border-accent border-t-transparent rounded-full animate-spin" />}
                    {entry.status === 'pending'    && <FileText size={18} className="text-muted" />}
                  </div>

                  {/* Name */}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{entry.name}</div>
                    <div className="text-xs text-muted">
                      {entry.status === 'done'  && `✅ Indexed — ${entry.chunks} chunks in vector store`}
                      {entry.status === 'error' && <span className="text-danger">{entry.error}</span>}
                      {entry.status === 'uploading' && 'Uploading & indexing…'}
                      {entry.status === 'pending'   && `${(entry.file.size / 1024).toFixed(1)} KB`}
                    </div>
                  </div>

                  {/* Doc type selector */}
                  {entry.status !== 'done' && (
                    <select className="form-input !w-auto text-xs py-1.5 px-2"
                      value={entry.type} onChange={e => setFileType(i, e.target.value)}>
                      {DOC_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
                    </select>
                  )}
                  {entry.status === 'done' && (
                    <span className="badge badge-green text-xs">{entry.type.replace(/_/g,' ')}</span>
                  )}

                  {/* Remove */}
                  {entry.status !== 'uploading' && entry.status !== 'done' && (
                    <button onClick={() => removeFile(i)} className="btn btn-danger btn-sm !px-1.5 !py-1.5 flex-shrink-0">
                      <X size={12} />
                    </button>
                  )}
                </div>
              ))}

              <div className="flex justify-between items-center pt-2 border-t border-white/[0.07]">
                <button onClick={() => fileRef.current?.click()} className="btn btn-secondary btn-sm">
                  + Add more files
                </button>
                <div className="flex gap-3">
                  <button onClick={() => setStep(2)} className="btn btn-secondary btn-sm">
                    Skip uploads →
                  </button>
                  <button onClick={handleUploadAll} disabled={uploading || files.every(f => f.status === 'done')}
                    className="btn btn-primary disabled:opacity-40">
                    {uploading ? 'Uploading…' : `Upload ${files.filter(f => f.status !== 'done').length} files`}
                  </button>
                </div>
              </div>
            </div>
          )}

          {files.length === 0 && (
            <div className="flex justify-end gap-3">
              <button onClick={() => setStep(2)} className="btn btn-secondary">Skip — no files →</button>
            </div>
          )}
        </div>
      )}

      {/* ── STEP 2: Review / Done ── */}
      {step === 2 && (
        <div className="card flex flex-col items-center gap-5 py-10 text-center">
          <div className="w-16 h-16 rounded-full bg-accent2/20 flex items-center justify-center text-3xl">✅</div>
          <div>
            <h2 className="font-head text-xl font-bold mb-1">Patient Added Successfully</h2>
            <p className="text-muted text-sm">Patient ID: <span className="text-accent font-bold">{createdId}</span></p>
          </div>

          <div className="bg-bg3 border border-white/[0.07] rounded-xl p-4 text-sm text-left w-full max-w-sm">
            <div className="text-muted text-xs mb-2 font-semibold uppercase tracking-widest">Summary</div>
            <div className="flex justify-between py-1"><span className="text-muted">Name</span><span>{form.first_name} {form.last_name}</span></div>
            <div className="flex justify-between py-1"><span className="text-muted">Email</span><span>{form.email}</span></div>
            <div className="flex justify-between py-1"><span className="text-muted">City</span><span>{form.city || '—'}</span></div>
            <div className="flex justify-between py-1 border-t border-white/[0.07] mt-1 pt-2">
              <span className="text-muted">PDFs uploaded</span>
              <span className="text-accent2 font-semibold">{doneCount} file{doneCount !== 1 ? 's' : ''}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-muted">Vector chunks indexed</span>
              <span className="text-accent2 font-semibold">{files.filter(f=>f.status==='done').reduce((s,f)=>s+(f.chunks||0),0)}</span>
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={() => navigate('/admin/patients')} className="btn btn-secondary">← Back to Patients</button>
            <button onClick={() => { setForm(EMPTY); setFiles([]); setCreatedId(null); setStep(0) }} className="btn btn-primary">
              Add Another Patient
            </button>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast.msg && (
        <div className={`fixed bottom-6 right-6 border rounded-xl px-5 py-3 text-sm shadow-xl z-50 transition-all
          ${toast.type === 'error' ? 'bg-danger/10 border-danger/30 text-danger' : 'bg-bg2 border-white/[0.07] text-white'}`}>
          {toast.msg}
        </div>
      )}
    </div>
  )
}
