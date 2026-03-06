import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../api'

const STATUS_COLORS = {
  pending: 'bg-yellow-100 text-yellow-700',
  pass: 'bg-green-100 text-green-700',
  fail: 'bg-red-100 text-red-700',
  corrected: 'bg-blue-100 text-blue-700',
}

export default function ProcessChecksPage() {
  const [items, setItems] = useState([])
  const [packhouses, setPackhouses] = useState([])
  const [packLines, setPackLines] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({})
  const [loading, setLoading] = useState(true)
  const { t } = useTranslation()

  const load = async () => {
    const [checks, phs] = await Promise.all([
      api.get('/qms/process-checks').then((r) => r.ok ? r.json() : []),
      api.get('/packhouses').then((r) => r.ok ? r.json() : []),
    ])
    setItems(Array.isArray(checks) ? checks : [])
    setPackhouses(Array.isArray(phs) ? phs : [])
    if (phs.length > 0) {
      const lines = await api.get(`/packhouses/${phs[0].id}/pack-lines`).then((r) => r.ok ? r.json() : [])
      setPackLines(Array.isArray(lines) ? lines : [])
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    await api.post('/qms/process-checks', {
      ...form,
      pack_line_id: parseInt(form.pack_line_id),
    })
    setShowForm(false)
    setForm({})
    load()
  }

  const updateStatus = async (id, status) => {
    await api.patch(`/qms/process-checks/${id}`, { status })
    load()
  }

  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" /></div>

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">{t('processChecks.title')}</h1>
        <button onClick={() => setShowForm(!showForm)} className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-brand-700">
          {showForm ? t('fields.cancel') : t('processChecks.newCheck')}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white border rounded-xl p-5 mb-6">
          <h3 className="font-semibold text-gray-800 mb-4">{t('processChecks.formTitle')}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">{t('processChecks.packLine')} *</label>
              <select value={form.pack_line_id || ''} onChange={set('pack_line_id')} required
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none">
                <option value="">{t('fields.select')}</option>
                {packLines.map((l) => <option key={l.id} value={l.id}>{l.name} ({l.code})</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">{t('fields.batchCode')}</label>
              <input value={form.batch_code || ''} onChange={set('batch_code')}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">{t('fields.shift')}</label>
              <select value={form.shift || 'day'} onChange={set('shift')}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none">
                <option value="day">{t('processChecks.shifts.day')}</option>
                <option value="night">{t('processChecks.shifts.night')}</option>
              </select>
            </div>
          </div>
          <button type="submit" className="mt-4 bg-brand-600 text-white px-6 py-2 rounded-lg text-sm hover:bg-brand-700">
            {t('processChecks.createCheck')}
          </button>
        </form>
      )}

      <div className="bg-white rounded-xl border overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.id')}</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.batch')}</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.shift')}</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.status')}</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.issues')}</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.date')}</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-500">#{item.id}</td>
                <td className="px-4 py-3 font-medium">{item.batch_code || '—'}</td>
                <td className="px-4 py-3">{item.shift || '—'}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[item.status] || 'bg-gray-100'}`}>
                    {item.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-600">{item.issue_description || '—'}</td>
                <td className="px-4 py-3 text-gray-500">{item.created_at ? new Date(item.created_at).toLocaleDateString() : ''}</td>
                <td className="px-4 py-3">
                  {item.status === 'pending' && (
                    <div className="flex gap-1">
                      <button onClick={() => updateStatus(item.id, 'pass')} className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded hover:bg-green-200">{t('processChecks.pass')}</button>
                      <button onClick={() => updateStatus(item.id, 'fail')} className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded hover:bg-red-200">{t('processChecks.fail')}</button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <p className="text-center py-8 text-gray-400 text-sm">{t('processChecks.noChecks')}</p>}
      </div>
    </div>
  )
}
