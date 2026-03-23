import { X } from 'lucide-react'

export default function Modal({ title, onClose, children, maxWidth = 'max-w-lg' }) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-5"
         onClick={e => e.target === e.currentTarget && onClose()}>
      <div className={`bg-bg2 border border-white/[0.07] rounded-2xl p-7 w-full ${maxWidth} max-h-[90vh] overflow-y-auto shadow-[0_24px_80px_rgba(0,0,0,0.6)]`}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-head text-lg font-bold">{title}</h2>
          <button onClick={onClose} className="btn btn-secondary btn-sm !px-2 !py-2"><X size={14} /></button>
        </div>
        {children}
      </div>
    </div>
  )
}
