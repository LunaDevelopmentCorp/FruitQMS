import { NavLink } from 'react-router-dom'
import { useAuth } from '../AuthContext'

const links = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/organization', label: 'Organization', icon: '🏢' },
  { to: '/intake', label: 'Intake Inspections', icon: '📦' },
  { to: '/process-checks', label: 'Process Checks', icon: '⚙️' },
  { to: '/final-inspections', label: 'Final Inspections', icon: '✅' },
  { to: '/daily-checklists', label: 'Daily Checklists', icon: '📋' },
  { to: '/forms', label: 'Form Templates', icon: '📝' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()

  return (
    <aside className="w-64 bg-brand-800 text-white min-h-screen flex flex-col">
      <div className="p-4 border-b border-brand-700">
        <h1 className="text-xl font-bold flex items-center gap-2">
          🍊 FruitQMS
        </h1>
        <p className="text-brand-300 text-xs mt-1">Quality Management System</p>
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
          Sign Out
        </button>
      </div>
    </aside>
  )
}
