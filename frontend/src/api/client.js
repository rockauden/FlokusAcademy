const API_BASE = (import.meta.env.VITE_API_URL || '') + '/api'

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
    headers
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, config)
    
    if (response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      return null
    }

    const data = await response.json().catch(() => ({}))
    
    if (!response.ok) {
      throw new Error(data.detail || 'API request failed')
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
