import { useState, useEffect } from 'react'
import api from '../api'

function StatCard({ label, value, sub, color = 'brand' }) {
  const colors = {
    brand: 'bg-brand-50 border-brand-200 text-brand-700',
    red: 'bg-red-50 border-red-200 text-red-700',
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    amber: 'bg-amber-50 border-amber-200 text-amber-700',
  }
  return (
    <div className={`rounded-xl border p-5 ${colors[color]}`}>
      <p className="text-sm font-medium opacity-80">{label}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
      {sub && <p className="text-xs mt-1 opacity-70">{sub}</p>}
    </div>
  )
}

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [ncs, setNcs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/qms/reports/dashboard').then((r) => r.ok ? r.json() : null),
      api.get('/qms/reports/non-conformances').then((r) => r.ok ? r.json() : { items: [] }),
    ]).then(([s, n]) => {
      setStats(s)
      setNcs(n.items || n.non_conformances || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" /></div>

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h1>

      {stats ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard label="Intake Inspections" value={stats.intake_count ?? 0} sub={`${stats.intake_pass_rate ?? 0}% pass rate`} />
            <StatCard label="Process Checks" value={stats.process_check_count ?? 0} sub={`${stats.process_check_pass_rate ?? 0}% pass rate`} color="blue" />
            <StatCard label="Final Inspections" value={stats.final_inspection_count ?? 0} sub={`${stats.final_inspection_pass_rate ?? 0}% pass rate`} color="amber" />
            <StatCard label="Daily Checklists" value={stats.daily_checklist_count ?? 0} sub={`${stats.daily_checklist_pass_rate ?? 0}% pass rate`} color="brand" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
            <StatCard label="Form Submissions" value={stats.form_submission_count ?? 0} color="blue" />
            <StatCard label="Non-Conformances" value={stats.non_conformance_count ?? 0} color="red" sub="Last 7 days" />
          </div>
        </>
      ) : (
        <div className="bg-white rounded-xl border p-8 text-center text-gray-500 mb-8">
          <p className="text-lg">No data yet</p>
          <p className="text-sm mt-1">Run the seed script or start creating inspections to see stats here.</p>
        </div>
      )}

      <div className="bg-white rounded-xl border">
        <div className="px-5 py-4 border-b">
          <h2 className="font-semibold text-gray-800">Recent Non-Conformances</h2>
        </div>
        {ncs.length === 0 ? (
          <p className="p-5 text-gray-500 text-sm">No non-conformances found.</p>
        ) : (
          <div className="divide-y">
            {ncs.map((nc, i) => (
              <div key={i} className="px-5 py-3 flex items-center justify-between text-sm">
                <div>
                  <span className="font-medium text-gray-800">{nc.type || nc.operation_type}</span>
                  <span className="text-gray-400 mx-2">·</span>
                  <span className="text-gray-600">{nc.notes || nc.description || 'No details'}</span>
                </div>
                <span className="text-xs text-gray-400">{nc.created_at ? new Date(nc.created_at).toLocaleDateString() : ''}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
