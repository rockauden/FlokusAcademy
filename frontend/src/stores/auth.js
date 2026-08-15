import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, setSessionHandlers } from '../api/client'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(null)
  const role = ref(null)
  const displayName = ref('')
  const username = ref('')

  const isAuthenticated = computed(() => !!token.value)
  const isTeacher = computed(() => role.value === 'teacher')
  const isStudent = computed(() => role.value === 'student')

  function loadFromStorage() {
    token.value = localStorage.getItem('token')
    role.value = localStorage.getItem('role')
    displayName.value = localStorage.getItem('displayName')
    username.value = localStorage.getItem('username')
  }

  function clearSession() {
    token.value = null
    role.value = null
    displayName.value = ''
    username.value = ''
    localStorage.clear()
  }

  // The API client owns the 401-and-refresh flow, but it cannot import this
  // store (this store imports it), so it calls back in here instead.
  setSessionHandlers({
    // A silent refresh succeeded. The client has already written the new token
    // to localStorage; this only mirrors it into reactive state so anything
    // bound to the store stays consistent.
    onRefreshed: (data) => {
      token.value = data.access_token
      if (data.role) {
        role.value = data.role
        localStorage.setItem('role', data.role)
      }
      if (data.display_name) {
        displayName.value = data.display_name
        localStorage.setItem('displayName', data.display_name)
      }
    },
    // Refresh failed or the replay was refused — the session is genuinely over.
    // router.push rather than window.location.href: a hard navigation reloads
    // the whole SPA, which is slow on a tablet and throws away any error the
    // current view was showing.
    onExpired: () => {
      clearSession()
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
  })

  /**
   * Sign in. Throws on failure so the caller can show the real reason —
   * "Incorrect username or PIN" (401) or "Rate limit exceeded" (429) — rather
   * than a generic message. Callers must handle the rejection.
   */
  async function login(user, pin) {
    const data = await api.post('/auth/login', { username: user, pin })
    if (!data || !data.access_token) {
      throw new Error('Login failed. Please try again.')
    }

    token.value = data.access_token
    role.value = data.role
    displayName.value = data.display_name
    username.value = user

    localStorage.setItem('token', data.access_token)
    localStorage.setItem('role', data.role)
    localStorage.setItem('displayName', data.display_name)
    localStorage.setItem('username', user)
    return true
  }

  /**
   * Sign out. Calls the API first so the server clears refresh_token_id and
   * expires the cookie. Without that the refresh cookie stays valid for its
   * full 7 days, and once silent refresh exists it can be spent for new
   * sessions long after the user believes they logged out.
   *
   * Local state is cleared even if the call fails, so a network error cannot
   * strand someone in a logged-in UI they cannot leave.
   */
  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Logout request failed; clearing local session anyway', error)
    }
    clearSession()
    router.push('/login')
  }

  return { token, role, displayName, username, isAuthenticated, isTeacher, isStudent, loadFromStorage, login, logout }
})
