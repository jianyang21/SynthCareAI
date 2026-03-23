export default function StatCard({ label, value, sub, color = 'text-white', icon }) {
  return (
    <div className="card flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="card-title mb-0">{label}</span>
        {icon && <span className="text-xl">{icon}</span>}
      </div>
      <div className={`font-head text-[32px] font-extrabold leading-none ${color}`}>{value ?? '—'}</div>
      {sub && <div className="text-xs text-muted">{sub}</div>}
    </div>
  )
}
