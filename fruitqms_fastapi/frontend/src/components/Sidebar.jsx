import { NavLink } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { useTranslation } from 'react-i18next'

export default function Sidebar() {
  const { user, logout } = useAuth()
  const { t } = useTranslation()

  const links = [
    { to: '/', label: t('nav.dashboard'), icon: '📊' },
    { to: '/organization', label: t('nav.organization'), icon: '🏢' },
    { to: '/intake', label: t('nav.intake'), icon: '📦' },
    { to: '/process-checks', label: t('nav.processChecks'), icon: '⚙️' },
    { to: '/final-inspections', label: t('nav.finalInspections'), icon: '✅' },
    { to: '/daily-checklists', label: t('nav.dailyChecklists'), icon: '📋' },
    { to: '/forms', label: t('nav.formTemplates'), icon: '📝' },
    { to: '/settings', label: t('nav.settings'), icon: '⚙️' },
  ]

  return (
    <aside className="w-64 bg-brand-800 text-white min-h-screen flex flex-col">
      <div className="p-4 border-b border-brand-700">
        <h1 className="text-xl font-bold flex items-center gap-2">
          🍊 {t('app.name')}
        </h1>
        <p className="text-brand-300 text-xs mt-1">{t('app.subtitle')}</p>
      </div>

      <nav className="flex-1 py-4">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                isActive
                  ? 'bg-brand-700 text-white font-medium'
                  : 'text-brand-200 hover:bg-brand-700/50 hover:text-white'
              }`
            }
          >
            <span>{link.icon}</span>
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-brand-700">
        <div className="text-sm text-brand-200 mb-2">
          {user?.name} <span className="text-brand-400">({user?.role})</span>
        </div>
        <button
          onClick={logout}
          className="text-xs text-brand-300 hover:text-white transition-colors"
        >
          {t('nav.signOut')}
        </button>
      </div>
    </aside>
  )
}
