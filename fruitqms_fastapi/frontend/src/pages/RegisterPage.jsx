import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../api'

export default function RegisterPage() {
  const [form, setForm] = useState({
    name: '', username: '', email: '', password: '', role: 'viewer', language: 'en',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { t } = useTranslation()

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.register(form)
      navigate('/login')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-brand-100">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-brand-800">🍊 {t('auth.register')}</h1>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded-lg mb-4 text-sm">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('auth.fullName')}</label>
            <input value={form.name} onChange={set('name')} required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('auth.username')}</label>
            <input value={form.username} onChange={set('username')} required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('auth.email')}</label>
            <input type="email" value={form.email} onChange={set('email')} required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('auth.password')}</label>
            <input type="password" value={form.password} onChange={set('password')} required minLength={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('auth.role')}</label>
              <select value={form.role} onChange={set('role')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none">
                <option value="viewer">{t('roles.viewer')}</option>
                <option value="inspector">{t('roles.inspector')}</option>
                <option value="qa_manager">{t('roles.qa_manager')}</option>
                <option value="auditor">{t('roles.auditor')}</option>
                <option value="admin">{t('roles.admin')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('auth.language')}</label>
              <select value={form.language} onChange={set('language')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none">
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="pt">Português</option>
                <option value="de">Deutsch</option>
              </select>
            </div>
          </div>

          <button type="submit" disabled={loading}
            className="w-full bg-brand-600 text-white py-2.5 rounded-lg font-medium hover:bg-brand-700 transition-colors disabled:opacity-50">
            {loading ? t('auth.registering') : t('auth.createAccount')}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-4">
          {t('auth.alreadyRegistered')} <Link to="/login" className="text-brand-600 hover:underline font-medium">{t('auth.signIn')}</Link>
        </p>
      </div>
    </div>
  )
}
