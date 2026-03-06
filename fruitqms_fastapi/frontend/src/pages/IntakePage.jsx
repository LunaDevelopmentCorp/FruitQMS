import { useState, useEffect } from 'react'
import api from '../api'

const STATUS_COLORS = {
  pending: 'bg-yellow-100 text-yellow-700',
  in_progress: 'bg-blue-100 text-blue-700',
  accepted: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  quarantined: 'bg-orange-100 text-orange-700',
}

export default function IntakePage() {
  const [items, setItems] = useState([])
  const [packhouses, setPackhouses] = useState([])
  const [growers, setGrowers] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({})
  const [loading, setLoading] = useState(true)

  const load = () => {
    Promise.all([
      api.get('/qms/intake').then((r) => r.ok ? r.json() : []),
      api.get('/packhouses').then((r) => r.ok ? r.json() : []),
      api.get('/growers').then((r) => r.ok ? r.json() : []),
    ]).then(([i, p, g]) => {
      setItems(Array.isArray(i) ? i : [])
      setPackhouses(Array.isArray(p) ? p : [])
      setGrowers(Array.isArray(g) ? g : [])
      setLoading(false)
    })
  }

  useEffect(() => { load() }, [])

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    const payload = {
      ...form,
      packhouse_id: parseInt(form.packhouse_id),
      grower_id: form.grower_id ? parseInt(form.grower_id) : null,
      quantity: form.quantity ? parseFloat(form.quantity) : null,
    }
    await api.post('/qms/intake', payload)
    setShowForm(false)
    setForm({})
    load()
  }

  const updateStatus = async (id, status) => {
    await api.patch(`/qms/intake/${id}`, { status })
    load()
  }

  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" /></div>

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Intake Inspections</h1>
        <button onClick={() => setShowForm(!showForm)} className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-brand-700">
          {showForm ? 'Cancel' : '+ New Inspection'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white border rounded-xl p-5 mb-6">
          <h3 className="font-semibold text-gray-800 mb-4">New Intake Inspection</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Packhouse *</label>
              <select value={form.packhouse_id || ''} onChange={set('packhouse_id')} required
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none">
                <option value="">Select...</option>
                {packhouses.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Grower</label>
              <select value={form.grower_id || ''} onChange={set('grower_id')}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none">
                <option value="">Select...</option>
                {growers.map((g) => <option key={g.id} value={g.id}>{g.grower_name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Batch Code</label>
              <input value={form.batch_code || ''} onChange={set('batch_code')}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Crop Type</label>
              <input value={form.crop_type || ''} onChange={set('crop_type')}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Variety</label>
              <input value={form.variety || ''} onChange={set('variety')}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Quantity</label>
              <input type="number" step="0.1" value={form.quantity || ''} onChange={set('quantity')}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Quantity Unit</label>
              <select value={form.quantity_unit || 'kg'} onChange={set('quantity_unit')}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none">
                <option value="kg">kg</option>
                <option value="bins">bins</option>
                <option value="pallets">pallets</option>
                <option value="boxes">boxes</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Harvest Date</label>
              <input type="date" value={form.harvest_date || ''} onChange={set('harvest_date')}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
          </div>
          <button type="submit" className="mt-4 bg-brand-600 text-white px-6 py-2 rounded-lg text-sm hover:bg-brand-700">
            Create Inspection
          </button>
        </form>
      )}

      <div className="bg-white rounded-xl border">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Batch</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Crop</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Quantity</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-500">#{item.id}</td>
                  <td className="px-4 py-3 font-medium">{item.batch_code || '—'}</td>
                  <td className="px-4 py-3">{item.crop_type || '—'}</td>
                  <td className="px-4 py-3">{item.quantity ? `${item.quantity} ${item.quantity_unit || ''}` : '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[item.status] || 'bg-gray-100'}`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{item.created_at ? new Date(item.created_at).toLocaleDateString() : ''}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {item.status === 'pending' && (
                        <>
                          <button onClick={() => updateStatus(item.id, 'accepted')} className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded hover:bg-green-200">Accept</button>
                          <button onClick={() => updateStatus(item.id, 'rejected')} className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded hover:bg-red-200">Reject</button>
                          <button onClick={() => updateStatus(item.id, 'quarantined')} className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded hover:bg-orange-200">Quarantine</button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {items.length === 0 && <p className="text-center py-8 text-gray-400 text-sm">No intake inspections yet</p>}
        </div>
      </div>
    </div>
  )
}
