import { ref, computed } from 'vue'
import { login as apiLogin } from '../api/index.js'

const currentUser = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const isAdmin = computed(() => currentUser.value.role === 'admin')

export function useAuth() {
  const isAuthenticated = computed(() => {
    const token = localStorage.getItem('access_token')
    return !!token
  })

  async function login(username, password) {
    const result = await apiLogin(username, password)
    if (result && result.access_token) {
      localStorage.setItem('access_token', result.access_token)
      localStorage.setItem('user', JSON.stringify(result.user))
      currentUser.value = result.user
      return true
    }
    return false
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    currentUser.value = {}
    window.location.href = '/login.html'
  }

  function checkAuth() {
    const token = localStorage.getItem('access_token')
    if (!token) {
      window.location.href = '/login.html'
      return false
    }
    return true
  }

  return {
    currentUser,
    isAdmin,
    isAuthenticated,
    login,
    logout,
    checkAuth
  }
}
