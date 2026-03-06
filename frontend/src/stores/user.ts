import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

interface User {
  id: number
  username: string
  roles: string[]
  is_active: boolean
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const user = ref<User | null>(null)
  const router = useRouter()

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.roles.includes('admin') || false)

  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('access_token', newToken)
  }

  function setUser(newUser: User) {
    user.value = newUser
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    // Router push will be handled by the component calling logout or router guard
  }

  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    setToken,
    setUser,
    logout
  }
})
