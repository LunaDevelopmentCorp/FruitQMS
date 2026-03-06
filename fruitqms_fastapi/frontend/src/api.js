const BASE = '/api/v1'

function getToken() {
  return localStorage.getItem('access_token')
}

function setTokens(access, refresh) {
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}

function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const lang = localStorage.getItem('language')
  if (lang) headers['X-Language'] = lang

  const res = await fetch(`${BASE}${path}`, { ...options, headers })

  // If 401 and we have a refresh token, try refreshing
  if (res.status === 401 && localStorage.getItem('refresh_token')) {
    const refreshRes = await fetch(`${BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: localStorage.getItem('refresh_token') }),
    })
    if (refreshRes.ok) {
      const data = await refreshRes.json()
      setTokens(data.access_token, data.refresh_token)
      headers['Authorization'] = `Bearer ${data.access_token}`
      return fetch(`${BASE}${path}`, { ...options, headers })
    } else {
      clearTokens()
      window.location.href = '/login'
    }
  }

  return res
}

const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: 'DELETE' }),

  // Auth helpers
  login: async (email, password) => {
    const res = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) throw new Error('Login failed')
    const data = await res.json()
    setTokens(data.access_token, data.refresh_token)
    return data
  },

  register: async (payload) => {
    const res = await request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Registration failed')
    }
    return res.json()
  },

  logout: () => {
    clearTokens()
    window.location.href = '/login'
  },

  getMe: () => request('/auth/me').then((r) => (r.ok ? r.json() : null)),

  isAuthenticated: () => !!getToken(),
  setTokens,
  clearTokens,
}

export default api
