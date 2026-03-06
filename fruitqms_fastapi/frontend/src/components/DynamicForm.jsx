import { useState } from 'react'

/**
 * Renders a form dynamically from a JSON schema (FormTemplate.schema).
 *
 * Schema shape:
 * { sections: [{ id, title, fields: [{ id, label, type, validation, options, ... }] }] }
 */

function FieldRenderer({ field, value, onChange }) {
  const base = 'w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none'

  switch (field.type) {
    case 'text':
    case 'photo':
    case 'signature':
      return <input type="text" value={value || ''} onChange={(e) => onChange(e.target.value)}
        required={field.validation?.required} className={base}
        placeholder={field.placeholder || ''} />

    case 'textarea':
      return <textarea value={value || ''} onChange={(e) => onChange(e.target.value)}
        required={field.validation?.required} rows={3} className={base}
        placeholder={field.placeholder || ''} />

    case 'number':
      return (
        <div className="flex items-center gap-2">
          <input type="number" step="any" value={value ?? ''} onChange={(e) => onChange(e.target.value ? parseFloat(e.target.value) : null)}
            required={field.validation?.required}
            min={field.validation?.min} max={field.validation?.max}
            className={base} />
          {field.unit && <span className="text-xs text-gray-500 whitespace-nowrap">{field.unit}</span>}
        </div>
      )

    case 'boolean':
      return (
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={!!value} onChange={(e) => onChange(e.target.checked)}
            className="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
          <span className="text-sm text-gray-700">{field.label}</span>
        </label>
      )

    case 'select':
      return (
        <select value={value || ''} onChange={(e) => onChange(e.target.value)}
          required={field.validation?.required} className={base}>
          <option value="">Select...</option>
          {(field.options || []).map((opt) => (
            <option key={opt.value || opt} value={opt.value || opt}>
              {opt.label || opt}
            </option>
          ))}
        </select>
      )

    case 'multi_select':
      return (
        <div className="space-y-1">
          {(field.options || []).map((opt) => {
            const val = opt.value || opt
            const checked = Array.isArray(value) && value.includes(val)
            return (
              <label key={val} className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={checked}
                  onChange={(e) => {
                    const arr = Array.isArray(value) ? [...value] : []
                    if (e.target.checked) arr.push(val)
                    else arr.splice(arr.indexOf(val), 1)
                    onChange(arr)
                  }}
                  className="w-4 h-4 rounded border-gray-300 text-brand-600" />
                <span className="text-sm">{opt.label || opt}</span>
              </label>
            )
          })}
        </div>
      )

    case 'date':
      return <input type="date" value={value || ''} onChange={(e) => onChange(e.target.value)}
        required={field.validation?.required} className={base} />

    case 'time':
      return <input type="time" value={value || ''} onChange={(e) => onChange(e.target.value)}
        required={field.validation?.required} className={base} />

    default:
      return <input type="text" value={value || ''} onChange={(e) => onChange(e.target.value)} className={base} />
  }
}

export default function DynamicForm({ schema, onSubmit, submitting }) {
  const [responses, setResponses] = useState({})

  if (!schema || !schema.sections) {
    return <p className="text-gray-500">No form schema available</p>
  }

  const setValue = (fieldId, value) => {
    setResponses((prev) => ({
      ...prev,
      [fieldId]: { value, timestamp: new Date().toISOString() },
    }))
  }

  // Check conditional visibility
  const isVisible = (field) => {
    if (!field.conditional) return true
    const depValue = responses[field.conditional.depends_on]?.value
    if (field.conditional.show_when !== undefined) {
      return depValue === field.conditional.show_when
    }
    return true
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(responses)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {schema.sections.map((section) => (
        <div key={section.id} className="bg-white border rounded-xl p-5">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            {section.title}
          </h3>
          <div className="space-y-4">
            {(section.fields || []).filter(isVisible).map((field) => (
              <div key={field.id}>
                {field.type !== 'boolean' && (
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {field.label}
                    {field.validation?.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                )}
                <FieldRenderer
                  field={field}
                  value={responses[field.id]?.value}
                  onChange={(v) => setValue(field.id, v)}
                />
                {field.help && <p className="text-xs text-gray-400 mt-1">{field.help}</p>}
              </div>
            ))}
          </div>
        </div>
      ))}

      <button
        type="submit"
        disabled={submitting}
        className="bg-brand-600 text-white px-8 py-2.5 rounded-lg font-medium hover:bg-brand-700 disabled:opacity-50 transition-colors"
      >
        {submitting ? 'Submitting...' : 'Submit Form'}
      </button>
    </form>
  )
}
