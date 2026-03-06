import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../api'

function Tab({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
        active ? 'border-brand-600 text-brand-700' : 'border-transparent text-gray-500 hover:text-gray-700'
      }`}
    >
      {children}
    </button>
  )
}

function DataTable({ columns, data, onRowClick }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-gray-50">
            {columns.map((c) => (
              <th key={c.key} className="text-left px-4 py-3 font-medium text-gray-600">{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y">
          {data.map((row, i) => (
            <tr key={row.id || i} className="hover:bg-gray-50 cursor-pointer" onClick={() => onRowClick?.(row)}>
              {columns.map((c) => (
                <td key={c.key} className="px-4 py-3 text-gray-700">{c.render ? c.render(row) : row[c.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length === 0 && <p className="text-center py-8 text-gray-400 text-sm">No records found</p>}
    </div>
  )
}

function CreateForm({ fields, onSubmit, title }) {
  const [form, setForm] = useState({})
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const { t } = useTranslation()

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    await onSubmit(form)
    setForm({})
    setOpen(false)
    setSaving(false)
  }

  if (!open) return (
    <button onClick={() => setOpen(true)} className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-brand-700 transition-colors">
      + {title}
    </button>
  )

  return (
    <form onSubmit={handleSubmit} className="bg-white border rounded-lg p-4 mb-4">
      <h3 className="font-medium text-gray-800 mb-3">{title}</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {fields.map((f) => (
          <div key={f.key}>
            <label className="block text-xs text-gray-600 mb-1">{f.label}</label>
            <input
              value={form[f.key] || ''}
              onChange={set(f.key)}
              required={f.required}
              type={f.type || 'text'}
              className="w-full px-3 py-1.5 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            />
          </div>
        ))}
      </div>
      <div className="flex gap-2 mt-3">
        <button type="submit" disabled={saving} className="bg-brand-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-brand-700 disabled:opacity-50">
          {saving ? t('fields.saving') : t('fields.save')}
        </button>
        <button type="button" onClick={() => setOpen(false)} className="px-4 py-1.5 rounded-lg text-sm border hover:bg-gray-50">{t('fields.cancel')}</button>
      </div>
    </form>
  )
}

export default function OrganizationPage() {
  const [tab, setTab] = useState('org')
  const [orgs, setOrgs] = useState([])
  const [packhouses, setPackhouses] = useState([])
  const [growers, setGrowers] = useState([])
  const [loading, setLoading] = useState(true)
  const { t } = useTranslation()

  const load = () => {
    Promise.all([
      api.get('/organizations').then((r) => r.ok ? r.json() : []),
      api.get('/packhouses').then((r) => r.ok ? r.json() : []),
      api.get('/growers').then((r) => r.ok ? r.json() : []),
    ]).then(([o, p, g]) => {
      setOrgs(Array.isArray(o) ? o : [])
      setPackhouses(Array.isArray(p) ? p : [])
      setGrowers(Array.isArray(g) ? g : [])
      setLoading(false)
    })
  }

  useEffect(() => { load() }, [])

  const createOrg = async (data) => {
    await api.post('/organizations', { ...data, org_type: data.org_type || 'packhouse' })
    load()
  }

  const createPackhouse = async (data) => {
    const orgId = orgs[0]?.id
    if (!orgId) return alert(t('organization.createOrgFirst'))
    await api.post('/packhouses', { ...data, organization_id: orgId })
    load()
  }

  const createGrower = async (data) => {
    const orgId = orgs[0]?.id
    if (!orgId) return alert(t('organization.createOrgFirst'))
    await api.post('/growers', { ...data, organization_id: orgId })
    load()
  }

  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" /></div>

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-4">{t('organization.title')}</h1>

      <div className="flex gap-1 border-b mb-4">
        <Tab active={tab === 'org'} onClick={() => setTab('org')}>{t('organization.organizations')}</Tab>
        <Tab active={tab === 'ph'} onClick={() => setTab('ph')}>{t('organization.packhouses')}</Tab>
        <Tab active={tab === 'growers'} onClick={() => setTab('growers')}>{t('organization.growers')}</Tab>
      </div>

      {tab === 'org' && (
        <div className="bg-white rounded-xl border">
          <div className="p-4 border-b flex justify-between items-center">
            <h2 className="font-semibold text-gray-800">{t('organization.organizations')}</h2>
            <CreateForm title={t('organization.newOrganization')} onSubmit={createOrg} fields={[
              { key: 'name', label: t('fields.name'), required: true },
              { key: 'org_type', label: t('fields.type'), required: true },
              { key: 'ggn_number', label: t('fields.ggnNumber') },
              { key: 'country', label: t('fields.country') },
              { key: 'address', label: t('fields.address') },
            ]} />
          </div>
          <DataTable
            columns={[
              { key: 'name', label: t('fields.name') },
              { key: 'org_type', label: t('fields.type') },
              { key: 'ggn_number', label: t('fields.ggn') },
              { key: 'country', label: t('fields.country') },
              { key: 'is_active', label: t('fields.active'), render: (r) => r.is_active ? '✓' : '✗' },
            ]}
            data={orgs}
          />
        </div>
      )}

      {tab === 'ph' && (
        <div className="bg-white rounded-xl border">
          <div className="p-4 border-b flex justify-between items-center">
            <h2 className="font-semibold text-gray-800">{t('organization.packhouses')}</h2>
            <CreateForm title={t('organization.newPackhouse')} onSubmit={createPackhouse} fields={[
              { key: 'code', label: t('fields.code'), required: true },
              { key: 'name', label: t('fields.name'), required: true },
              { key: 'address', label: t('fields.address') },
              { key: 'country', label: t('fields.country') },
              { key: 'staff_count', label: t('fields.staffCount'), type: 'number' },
            ]} />
          </div>
          <DataTable
            columns={[
              { key: 'code', label: t('fields.code') },
              { key: 'name', label: t('fields.name') },
              { key: 'address', label: t('fields.address') },
              { key: 'staff_count', label: t('fields.staff') },
              { key: 'is_active', label: t('fields.active'), render: (r) => r.is_active ? '✓' : '✗' },
            ]}
            data={packhouses}
          />
        </div>
      )}

      {tab === 'growers' && (
        <div className="bg-white rounded-xl border">
          <div className="p-4 border-b flex justify-between items-center">
            <h2 className="font-semibold text-gray-800">{t('organization.growers')}</h2>
            <CreateForm title={t('organization.newGrower')} onSubmit={createGrower} fields={[
              { key: 'grower_code', label: t('fields.code'), required: true },
              { key: 'grower_name', label: t('fields.name'), required: true },
              { key: 'field_name', label: t('fields.fieldName') },
              { key: 'crop_type', label: t('fields.cropType') },
              { key: 'size_hectares', label: t('fields.sizeHa'), type: 'number' },
            ]} />
          </div>
          <DataTable
            columns={[
              { key: 'grower_code', label: t('fields.code') },
              { key: 'grower_name', label: t('fields.name') },
              { key: 'field_name', label: t('fields.field') },
              { key: 'crop_type', label: t('fields.crop') },
              { key: 'size_hectares', label: t('fields.hectares') },
            ]}
            data={growers}
          />
        </div>
      )}
    </div>
  )
}
