import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../AuthContext'
import DynamicForm from '../components/DynamicForm'

export default function FormSubmitPage() {
  const { templateId } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [template, setTemplate] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    api.get(`/forms/templates/${templateId}`)
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        setTemplate(data)
        setLoading(false)
      })
  }, [templateId])

  const handleSubmit = async (responses) => {
    setSubmitting(true)
    try {
      const res = await api.post('/forms/submissions', {
        template_id: parseInt(templateId),
        organization_id: user?.organization_id || 1,
        responses,
        status: 'submitted',
      })
      if (res.ok) {
        const data = await res.json()
        setResult(data)
      } else {
        const err = await res.json()
        alert(err.detail || 'Submission failed')
      }
    } catch (e) {
      alert('Error submitting form')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" /></div>

  if (!template) return (
    <div className="text-center py-20">
      <p className="text-gray-500">Template not found</p>
      <button onClick={() => navigate('/forms')} className="text-brand-600 hover:underline mt-2 text-sm">Back to templates</button>
    </div>
  )

  if (result) return (
    <div className="max-w-lg mx-auto text-center py-12">
      <div className="bg-green-50 border border-green-200 rounded-xl p-8">
        <div className="text-4xl mb-4">✓</div>
        <h2 className="text-xl font-bold text-green-800 mb-2">Form Submitted</h2>
        <p className="text-green-700 text-sm mb-1">Submission #{result.id}</p>
        {result.score !== null && result.score !== undefined && (
          <p className="text-lg font-semibold text-green-800 mt-2">Score: {result.score}%</p>
        )}
        <p className="text-green-600 text-sm mt-2">Status: {result.status}</p>
        <div className="mt-6 flex gap-3 justify-center">
          <button onClick={() => { setResult(null); }} className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-brand-700">
            Submit Another
          </button>
          <button onClick={() => navigate('/forms')} className="border px-4 py-2 rounded-lg text-sm hover:bg-gray-50">
            Back to Templates
          </button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <button onClick={() => navigate('/forms')} className="text-sm text-gray-500 hover:text-gray-700 mb-1">
            ← Back to Templates
          </button>
          <h1 className="text-2xl font-bold text-gray-800">{template.name}</h1>
          {template.description && <p className="text-gray-500 text-sm mt-1">{template.description}</p>}
        </div>
        <span className="bg-brand-100 text-brand-700 px-3 py-1 rounded-full text-xs font-medium">
          {(template.form_type || '').replace('_', ' ')}
        </span>
      </div>

      <DynamicForm
        schema={template.schema}
        onSubmit={handleSubmit}
        submitting={submitting}
      />
    </div>
  )
}
