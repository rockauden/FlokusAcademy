import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api/client'
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

  async function login(user, pin) {
    try {
      const data = await api.post('/auth/login', { username: user, pin })
      if (data && data.access_token) {
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
      return false
    } catch (e) {
      console.error(e)
      return false
    }
  }

  function logout() {
    token.value = null
    role.value = null
    displayName.value = ''
    username.value = ''
    localStorage.clear()
    router.push('/login')
  }

  return { token, role, displayName, username, isAuthenticated, isTeacher, isStudent, loadFromStorage, login, logout }
})
