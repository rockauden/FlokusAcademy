// Set VITE_API_URL at build time (e.g. https://api.flokusacademy.com).
// With it unset we fall back to a relative /api, which the vite dev server
// proxies to the local backend.
const API_ROOT = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')
const API_BASE = API_ROOT ? `${API_ROOT}/api` : '/api'

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('token')
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const config = {
    ...options,
    headers,
    // Required for the HttpOnly refresh cookie to travel to the API origin.
    credentials: 'include'
  }

  // A 401 from the login endpoint means "wrong PIN", not "session expired".
  // Redirecting on it would reload the page and wipe the error the login form
  // is trying to show, so let it fall through and be thrown normally.
  const isLoginRequest = endpoint.startsWith('/auth/login')

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, config)

    if (response.status === 401 && !isLoginRequest) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      return null
    }

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      // FastAPI uses `detail`; slowapi's rate-limit response uses `error`.
      throw new Error(data.detail || data.error || 'API request failed')
    }

    return data
  } catch (error) {
    console.error('API Error:', error)
    throw error
  }
}

export const api = {
  get: (path) => request(path, { method: 'GET' }),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: 'DELETE' })
}
