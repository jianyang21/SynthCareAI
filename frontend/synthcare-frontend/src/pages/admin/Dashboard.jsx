import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDashboard, getLowStock, getPatientAppointments, getPatientOrders, queryRecords } from '../../api/client'
import StatCard from '../../components/StatCard'
import { Plus } from 'lucide-react'

const fmt     = d => new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
const fmtTime = d => new Date(d).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [stats, setStats]   = useState(null)
  const [stock, setStock]   = useState([])
  const [appts, setAppts]   = useState([])
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getDashboard(), getLowStock(), getPatientAppointments(20), getPatientOrders(10)])
      .then(([s, st, ap, or]) => { setStats(s); setStock(st); setAppts(ap); setOrders(or) })
      .finally(() => setLoading(false))
  }, [])

  const scheduled = appts.filter(a => a.status === 'scheduled').length
  const completed  = appts.filter(a => a.status === 'completed').length

  if (loading) return <div className="p-7 text-muted">Loading…</div>

  return (
    <div className="p-7 flex flex-col gap-6">

      {/* Header + quick actions */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-head text-2xl font-extrabold">Analytics Dashboard</h1>
          <p className="text-muted text-sm mt-0.5">Live overview of all hospital operations</p>
        </div>
        <button onClick={() => navigate('/admin/add-patient')}
          className="btn btn-primary gap-2">
          <Plus size={15} /> Add Patient
        </button>
      </div>

      {/* Primary stats */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Total Patients"   value={stats?.total_patients}      color="text-accent"  icon="👥"
                  sub={`Registered in system`} />
        <StatCard label="Total Doctors"    value={stats?.total_doctors}       color="text-accent2" icon="🩺"
                  sub="Active practitioners" />
        <StatCard label="Total Revenue"
                  value={`₹${Number(stats?.total_revenue ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
                  color="text-accent2" icon="💰" sub="From fulfilled orders" />
      </div>

      {/* Secondary stats */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Appointments"     value={stats?.total_appointments}  icon="📅" />
        <StatCard label="Scheduled"        value={scheduled}  color="text-accent"  icon="🕐" />
        <StatCard label="Completed"        value={completed}  color="text-accent2" icon="✅" />
        <StatCard label="Pending Orders"   value={stats?.pending_orders} color="text-accent3" icon="📦"
                  sub="Awaiting fulfillment" />
      </div>

      <div className="grid grid-cols-3 gap-5">

        {/* Recent appointments — wider */}
        <div className="card col-span-2">
          <div className="flex items-center justify-between mb-4">
            <p className="card-title mb-0">Recent Appointments</p>
            <span className="text-xs text-muted">{appts.length} total</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full tbl">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Doctor</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {appts.slice(0, 8).map((a, i) => (
                  <tr key={i}>
                    <td className="font-medium">{a.patient_first_name} {a.patient_last_name}</td>
                    <td className="text-muted">Dr. {a.doctor_first_name} {a.doctor_last_name}</td>
                    <td className="text-muted">{fmt(a.appointment_date)}</td>
                    <td className="text-muted">{fmtTime(a.appointment_date)}</td>
                    <td>
                      <span className={`badge ${
                        a.status === 'scheduled' ? 'badge-blue'
                        : a.status === 'completed' ? 'badge-green'
                        : 'badge-red'}`}>
                        {a.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right column */}
        <div className="flex flex-col gap-4">

          {/* Low stock */}
          <div className="card flex-1">
            <p className="card-title">⚠️ Low Stock</p>
            {stock.length === 0 ? (
              <div className="text-center py-6 text-muted text-xs">All medicines stocked ✅</div>
            ) : (
              <div className="flex flex-col gap-2">
                {stock.slice(0, 5).map((m, i) => (
                  <div key={i} className="flex items-center justify-between p-2.5 bg-bg3 rounded-xl border border-white/[0.07]">
                    <div className="min-w-0 mr-2">
                      <div className="text-xs font-medium truncate">{m.name}</div>
                      <div className="text-[11px] text-muted">Reorder ≤ {m.reorder_level}</div>
                    </div>
                    <span className="badge badge-red flex-shrink-0">{m.quantity}</span>
                  </div>
                ))}
                {stock.length > 5 && (
                  <button onClick={() => navigate('/admin/medicines')}
                    className="text-xs text-accent hover:underline text-center pt-1">
                    +{stock.length - 5} more →
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Recent orders */}
          <div className="card flex-1">
            <p className="card-title">Recent Orders</p>
            {orders.length === 0 ? (
              <div className="text-center py-6 text-muted text-xs">No orders yet</div>
            ) : (
              <div className="flex flex-col gap-2">
                {orders.slice(0, 5).map((o, i) => (
                  <div key={i} className="flex items-center justify-between p-2.5 bg-bg3 rounded-xl border border-white/[0.07]">
                    <div className="min-w-0 mr-2">
                      <div className="text-xs font-medium truncate">{o.medicine_name}</div>
                      <div className="text-[11px] text-muted">Qty: {o.quantity}</div>
                    </div>
                    <span className={`badge flex-shrink-0 ${o.order_status === 'pending' ? 'badge-orange' : 'badge-green'}`}>
                      {o.order_status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
