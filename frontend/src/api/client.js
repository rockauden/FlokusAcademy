// Set VITE_API_URL at build time (e.g. https://api.flokusacademy.com).
// With it unset we fall back to a relative /api, which the vite dev server
// proxies to the local backend.
const API_ROOT = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')
const API_BASE = API_ROOT ? `${API_ROOT}/api` : '/api'

// The auth store registers these at init. This module deliberately does not
// import the store: the store imports this module, so importing it back would
// be a cycle. Defaults are no-ops so a request made before registration still
// behaves sanely.
let handlers = {
  onRefreshed: () => {},
  onExpired: () => {}
}

export function setSessionHandlers(next) {
  handlers = { ...handlers, ...next }
}

// Single-flight. The server rotates the refresh token on every use and treats a
// replayed one as a compromised session — it clears refresh_token_id outright,
// killing the session rather than just refusing the request. So if a view fires
// several requests, they all 401 together, and each refreshed independently,
// the first would succeed and the rest would arrive with a spent token and log
// the user out. Concurrent callers must therefore share one refresh, not race.
let refreshPromise = null

function refreshSession() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // The HttpOnly cookie is the entire credential here — no bearer token,
        // and page JavaScript can neither read nor forge it.
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Session expired')
      }

      const data = await response.json().catch(() => ({}))
      if (!data.access_token) {
        throw new Error('Session expired')
      }

      // localStorage is what the Authorization header is built from, so it has
      // to be updated here; the store's reactive copy is synced via the handler.
      localStorage.setItem('token', data.access_token)
      handlers.onRefreshed(data)
      return data.access_token
    })().finally(() => {
      refreshPromise = null
    })
  }

  return refreshPromise
}

function endSession() {
  localStorage.removeItem('token')
  handlers.onExpired()
}

async function performRequest(endpoint, options, isRetry) {
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

  // A 401 from login means "wrong PIN", not "session expired" — refreshing or
  // redirecting on it would wipe the error the login form is trying to show.
  // /auth/refresh and /auth/logout are excluded for a different reason: trying
  // to refresh in response to their own 401 would recurse.
  const isSessionEndpoint =
    endpoint.startsWith('/auth/login') ||
    endpoint.startsWith('/auth/refresh') ||
    endpoint.startsWith('/auth/logout')

  const response = await fetch(`${API_BASE}${endpoint}`, config)

  if (response.status === 401 && !isSessionEndpoint) {
    if (isRetry) {
      // Already replayed once with a freshly minted token and still refused.
      // The session is genuinely gone — stop rather than loop.
      endSession()
      throw new Error('Your session has expired. Please log in again.')
    }

    try {
      await refreshSession()
    } catch {
      endSession()
      throw new Error('Your session has expired. Please log in again.')
    }

    // Replay once. options.body is already a JSON string, so it is safe to
    // reuse; re-entering here (rather than reusing `config`) is what picks up
    // the new token, since it is read from localStorage at the top.
    return performRequest(endpoint, options, true)
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    // FastAPI uses `detail`; slowapi's rate-limit response uses `error`.
    throw new Error(data.detail || data.error || 'API request failed')
  }

  return data
}

// Thin wrapper so a retried request is logged once, not once per attempt.
async function request(endpoint, options = {}) {
  try {
    return await performRequest(endpoint, options, false)
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
