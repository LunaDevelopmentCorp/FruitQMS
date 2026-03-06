import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import OrganizationPage from './pages/OrganizationPage'
import IntakePage from './pages/IntakePage'
import ProcessChecksPage from './pages/ProcessChecksPage'
import FinalInspectionPage from './pages/FinalInspectionPage'
import DailyChecklistPage from './pages/DailyChecklistPage'
import FormTemplatesPage from './pages/FormTemplatesPage'
import FormSubmitPage from './pages/FormSubmitPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/organization" element={<OrganizationPage />} />
                <Route path="/intake" element={<IntakePage />} />
                <Route path="/process-checks" element={<ProcessChecksPage />} />
                <Route path="/final-inspections" element={<FinalInspectionPage />} />
                <Route path="/daily-checklists" element={<DailyChecklistPage />} />
                <Route path="/forms" element={<FormTemplatesPage />} />
                <Route path="/forms/:templateId/submit" element={<FormSubmitPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
