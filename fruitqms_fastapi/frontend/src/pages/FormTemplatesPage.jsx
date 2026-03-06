import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../api'

const TYPE_COLORS = {
  intake: 'bg-blue-100 text-blue-700',
  process_check: 'bg-purple-100 text-purple-700',
  final_inspection: 'bg-green-100 text-green-700',
  daily_checklist: 'bg-amber-100 text-amber-700',
  custom: 'bg-gray-100 text-gray-700',
}

export default function FormTemplatesPage() {
  const [templates, setTemplates] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const { t } = useTranslation()

  useEffect(() => {
    api.get('/forms/templates').then((r) => r.ok ? r.json() : []).then((data) => {
      setTemplates(Array.isArray(data) ? data : [])
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" /></div>

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">{t('forms.title')}</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-3">
          {templates.length === 0 ? (
            <div className="bg-white border rounded-xl p-6 text-center text-gray-500">
              <p>{t('forms.noTemplates')}</p>
              <p className="text-sm mt-1">{t('forms.noTemplatesHelp')}</p>
            </div>
          ) : (
            templates.map((tmpl) => (
              <div
                key={tmpl.id}
                onClick={() => setSelected(tmpl)}
                className={`bg-white border rounded-xl p-4 cursor-pointer transition-all hover:shadow-md ${
                  selected?.id === tmpl.id ? 'ring-2 ring-brand-500 border-brand-300' : ''
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-gray-800">{tmpl.name}</h3>
                    <p className="text-xs text-gray-500 mt-0.5">{tmpl.code}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${TYPE_COLORS[tmpl.form_type] || 'bg-gray-100'}`}>
                    {(tmpl.form_type || '').replace('_', ' ')}
                  </span>
                </div>
                {tmpl.description && (
                  <p className="text-sm text-gray-600 mt-2 line-clamp-2">{tmpl.description}</p>
                )}
                <div className="mt-3">
                  <button
                    onClick={(e) => { e.stopPropagation(); navigate(`/forms/${tmpl.id}/submit`) }}
                    className="text-xs bg-brand-100 text-brand-700 px-3 py-1 rounded-lg hover:bg-brand-200 transition-colors"
                  >
                    {t('forms.fillForm')}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="lg:col-span-2">
          {selected ? (
            <div className="bg-white border rounded-xl p-5">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-lg font-semibold text-gray-800">{selected.name}</h2>
                  <p className="text-sm text-gray-500">{selected.description}</p>
                </div>
                <button
                  onClick={() => navigate(`/forms/${selected.id}/submit`)}
                  className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-brand-700"
                >
                  {t('forms.fillForm')}
                </button>
              </div>

              <div className="border-t pt-4">
                <h3 className="text-sm font-medium text-gray-600 mb-2">{t('forms.schemaPreview')}</h3>
                {selected.schema?.sections?.map((section) => (
                  <div key={section.id} className="mb-4">
                    <h4 className="text-sm font-semibold text-gray-700 mb-1">{section.title}</h4>
                    <div className="space-y-1 ml-4">
                      {section.fields?.map((field) => (
                        <div key={field.id} className="flex items-center gap-2 text-xs">
                          <span className="bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono">{field.type}</span>
                          <span className="text-gray-700">{field.label}</span>
                          {field.validation?.required && <span className="text-red-500">*</span>}
                          {field.unit && <span className="text-gray-400">({field.unit})</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <details className="mt-4">
                <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">{t('forms.rawJsonSchema')}</summary>
                <pre className="mt-2 bg-gray-50 p-3 rounded-lg text-xs overflow-x-auto max-h-96">
                  {JSON.stringify(selected.schema, null, 2)}
                </pre>
              </details>
            </div>
          ) : (
            <div className="bg-white border rounded-xl p-12 text-center text-gray-400">
              <p className="text-lg">{t('forms.selectTemplate')}</p>
              <p className="text-sm mt-1">{t('forms.selectTemplateHelp')}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
