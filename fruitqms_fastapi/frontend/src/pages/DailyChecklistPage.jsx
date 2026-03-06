import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../api'

const STATUS_COLORS = {
  submitted: 'bg-blue-100 text-blue-700',
  reviewed: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-green-100 text-green-700',
}

const TYPES = ['hygiene', 'cold_chain', 'pest_control', 'facility', 'custom']

export default function DailyChecklistPage() {
  const [items, setItems] = useState([])
  const [packhouses, setPackhouses] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ checklist_type: 'hygiene', shift: 'day' })
  const [loading, setLoading] = useState(true)
  const { t } = useTranslation()

  const load = () => {
    Promise.all([
      api.get('/qms/daily-checklists').then((r) => r.ok ? r.json() : []),
      api.get('/packhouses').then((r) => r.ok ? r.json() : []),
    ]).then(([c, p]) => {
      setItems(Array.isArray(c) ? c : [])
      setPackhouses(Array.isArray(p) ? p : [])
      setLoading(false)
    })
  }

  useEffect(() => { load() }, [])

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    await api.post('/qms/daily-checklists', {
      ...form,
      packhouse_id: parseInt(form.packhouse_id),
      checklist_date: form.checklist_date || new Date().toISOString().split('T')[0],
    })
    setShowForm(false)
    setForm({ checklist_type: 'hygiene', shift: 'day' })
    load()
  }

  const updateStatus = async (id, status) => {
    await api.patch(`/qms/daily-checklists/${id}`, { status })
    load()
  }

  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" /></div>

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">{t('dailyChecklists.title')}</h1>
        <button onClick={() => setShowForm(!showForm)} className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-brand-700">
          {showForm ? t('fields.cancel') : t('dailyChecklists.newChecklist')}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white border rounded-xl p-5 mb-6">
          <h3 className="font-semibold text-gray-800 mb-4">{t('dailyChecklists.formTitle')}</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">{t('intake.packhouse')} *</label>
              <select value={form.packhouse_id || ''} onChange={set('packhouse_id')} required
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none">
                <option value="">{t('fields.select')}</option>
                {packhouses.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">{t('dailyChecklists.checklistType')} *</label>
              <select value={form.checklist_type} onChange={set('checklist_type')} required
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none">
                {TYPES.map((tp) => <option key={tp} value={tp}>{t(`dailyChecklists.types.${tp}`)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">{t('fields.date')}</label>
              <input type="date" value={form.checklist_date || ''} onChange={set('checklist_date')}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">{t('fields.shift')}</label>
              <select value={form.shift} onChange={set('shift')}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none">
                <option value="day">{t('processChecks.shifts.day')}</option>
                <option value="night">{t('processChecks.shifts.night')}</option>
              </select>
            </div>
          </div>
          <button type="submit" className="mt-4 bg-brand-600 text-white px-6 py-2 rounded-lg text-sm hover:bg-brand-700">
            {t('dailyChecklists.createChecklist')}
          </button>
        </form>
      )}

      <div className="bg-white rounded-xl border overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.id')}</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.type')}</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.date')}</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.shift')}</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.status')}</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.passed')}</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">{t('fields.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-500">#{item.id}</td>
                <td className="px-4 py-3 font-medium capitalize">{t(`dailyChecklists.types.${item.checklist_type}`, { defaultValue: (item.checklist_type || '').replace('_', ' ') })}</td>
                <td className="px-4 py-3">{item.checklist_date || '—'}</td>
                <td className="px-4 py-3">{item.shift || '—'}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[item.status] || 'bg-gray-100'}`}>
                    {item.status}
                  </span>
                </td>
                <td className="px-4 py-3">{item.all_passed === true ? '✓' : item.all_passed === false ? '✗' : '—'}</td>
                <td className="px-4 py-3">
                  {item.status === 'submitted' && (
                    <div className="flex gap-1">
                      <button onClick={() => updateStatus(item.id, 'reviewed')} className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded hover:bg-yellow-200">{t('dailyChecklists.review')}</button>
                      <button onClick={() => updateStatus(item.id, 'approved')} className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded hover:bg-green-200">{t('dailyChecklists.approve')}</button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <p className="text-center py-8 text-gray-400 text-sm">{t('dailyChecklists.noChecklists')}</p>}
      </div>
    </div>
  )
}
