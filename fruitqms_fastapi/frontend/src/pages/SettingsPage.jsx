import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../api'
import { useAuth } from '../AuthContext'

const LANGUAGES = {
  en: 'English',
  es: 'Español',
  fr: 'Français',
  pt: 'Português',
  de: 'Deutsch',
}

export default function SettingsPage() {
  const { user, setUser } = useAuth()
  const [language, setLanguage] = useState(user?.language || 'en')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const { t, i18n } = useTranslation()

  const handleLanguageChange = async (lang) => {
    setLanguage(lang)
    setSaving(true)
    setSaved(false)
    try {
      const res = await api.patch('/i18n/me/language', { language: lang })
      if (res.ok) {
        localStorage.setItem('language', lang)
        localStorage.setItem('i18nextLng', lang)
        i18n.changeLanguage(lang)
        setUser({ ...user, language: lang })
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
      }
    } catch {
      setLanguage(user?.language || 'en')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">{t('settings.title')}</h1>

      {/* Profile */}
      <div className="bg-white border rounded-xl p-5 mb-6">
        <h2 className="font-semibold text-gray-800 mb-4">{t('settings.profile')}</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <label className="text-gray-500 text-xs">{t('fields.name')}</label>
            <p className="font-medium">{user?.name}</p>
          </div>
          <div>
            <label className="text-gray-500 text-xs">{t('auth.username')}</label>
            <p className="font-medium">{user?.username}</p>
          </div>
          <div>
            <label className="text-gray-500 text-xs">{t('auth.email')}</label>
            <p className="font-medium">{user?.email}</p>
          </div>
          <div>
            <label className="text-gray-500 text-xs">{t('auth.role')}</label>
            <p className="font-medium capitalize">{user?.role?.replace('_', ' ')}</p>
          </div>
        </div>
      </div>

      {/* Language */}
      <div className="bg-white border rounded-xl p-5 mb-6">
        <h2 className="font-semibold text-gray-800 mb-4">{t('settings.languagePreference')}</h2>
        <p className="text-sm text-gray-500 mb-4">
          {t('settings.languageHelp')}
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {Object.entries(LANGUAGES).map(([code, name]) => (
            <button
              key={code}
              onClick={() => handleLanguageChange(code)}
              disabled={saving}
              className={`px-4 py-3 rounded-lg text-sm font-medium border transition-all ${
                language === code
                  ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
                  : 'bg-white text-gray-700 border-gray-200 hover:border-brand-300 hover:bg-brand-50'
              } disabled:opacity-50`}
            >
              {name}
            </button>
          ))}
        </div>
        {saved && (
          <p className="text-green-600 text-sm mt-3">{t('settings.languageSaved')}</p>
        )}
      </div>

      {/* API Info */}
      <div className="bg-white border rounded-xl p-5">
        <h2 className="font-semibold text-gray-800 mb-4">{t('settings.systemInfo')}</h2>
        <div className="text-sm text-gray-600 space-y-1">
          <p>{t('settings.api')}: <span className="font-mono text-gray-800">/api/v1</span></p>
          <p>{t('settings.swagger')}: <a href="/docs" target="_blank" className="text-brand-600 hover:underline">/docs</a></p>
          <p>{t('settings.organizationId')}: <span className="font-mono">{user?.organization_id || t('settings.none')}</span></p>
        </div>
      </div>
    </div>
  )
}
