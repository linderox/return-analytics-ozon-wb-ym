import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { supabase } from '../lib/supabase'

const ADMIN_CACHE_KEY = 'mp_is_admin'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<any>(null)
  const isAdmin = ref(localStorage.getItem(ADMIN_CACHE_KEY) === 'true')
  const isLoaded = ref(false)

  let _initPromise: Promise<void> | null = null

  async function fetchProfile(accessToken: string) {
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/profile`, {
        headers: { Authorization: `Bearer ${accessToken}` }
      })
      isAdmin.value = res.data.is_admin === true
      localStorage.setItem(ADMIN_CACHE_KEY, String(isAdmin.value))
    } catch (e: any) {
      const status = e?.response?.status
      // Only clear admin status on auth errors — not server/network errors
      if (status === 401 || status === 403) {
        isAdmin.value = false
        localStorage.removeItem(ADMIN_CACHE_KEY)
      }
      // On 5xx or network failure, keep the cached value so routing still works
    }
  }

  async function _doInitialize() {
    const { data: { session } } = await supabase.auth.getSession()
    user.value = session?.user || null

    if (session) {
      await fetchProfile(session.access_token)
    }

    isLoaded.value = true

    supabase.auth.onAuthStateChange(async (_event, session) => {
      user.value = session?.user || null
      if (session) {
        await fetchProfile(session.access_token)
      } else {
        isAdmin.value = false
      }
    })
  }

  function initialize(): Promise<void> {
    if (!_initPromise) {
      _initPromise = _doInitialize()
    }
    return _initPromise
  }

  async function logout() {
    await supabase.auth.signOut()
    user.value = null
    isAdmin.value = false
    isLoaded.value = false
    _initPromise = null
    window.location.href = '/login'
  }

  return { user, isAdmin, isLoaded, initialize, logout }
})
