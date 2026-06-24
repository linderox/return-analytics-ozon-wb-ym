<template>
  <div class="flex items-center justify-center min-h-[80vh]">
    <div class="w-full max-w-md p-10 bg-white border border-[#E5E5E5] shadow-[4px_4px_0px_0px_rgba(0,0,0,0.05)]">
      <div class="mb-8 flex justify-center">
        <div class="w-12 h-12 bg-[#FBF0D3] flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-[#D97706]"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
        </div>
      </div>
      <h3 class="text-xl font-bold text-center mb-2 uppercase tracking-tight">Вход в систему</h3>
      <p class="text-[#737373] text-sm text-center mb-8 font-mono">returns-analytics-v2.0.4</p>

      <!-- Tab switcher -->
      <div class="flex border-2 border-[#1A1A1A] mb-6">
        <button
          @click="activeTab = 'email'"
          :class="activeTab === 'email' ? 'bg-[#1A1A1A] text-white' : 'bg-white text-[#1A1A1A] hover:bg-[#FBF0D3]'"
          class="flex-1 py-2 text-xs font-bold uppercase tracking-widest transition-colors"
        >Email</button>
        <button
          @click="activeTab = 'google'"
          :class="activeTab === 'google' ? 'bg-[#1A1A1A] text-white' : 'bg-white text-[#1A1A1A] hover:bg-[#FBF0D3]'"
          class="flex-1 py-2 text-xs font-bold uppercase tracking-widest transition-colors"
        >Google</button>
        <button
          @click="activeTab = 'yandex'"
          :class="activeTab === 'yandex' ? 'bg-[#1A1A1A] text-white' : 'bg-white text-[#1A1A1A] hover:bg-[#FBF0D3]'"
          class="flex-1 py-2 text-xs font-bold uppercase tracking-widest transition-colors"
        >Яндекс</button>
      </div>

      <!-- OAuth error banner (shown when redirected back with ?error=) -->
      <div v-if="oauthError" class="mb-4 text-xs text-red-600 font-mono border border-red-200 bg-red-50 px-3 py-2">
        {{ oauthErrorMessage }}
      </div>

      <!-- Email/password form -->
      <div v-if="activeTab === 'email'" class="space-y-4">
        <div v-if="!showForgot">
          <div>
            <label class="block text-xs font-bold uppercase tracking-widest mb-1 text-[#1A1A1A]">Email</label>
            <input
              v-model="email"
              type="email"
              placeholder="you@example.com"
              class="w-full border-2 border-[#1A1A1A] px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#D97706]"
            />
          </div>
          <div>
            <label class="block text-xs font-bold uppercase tracking-widest mb-1 text-[#1A1A1A]">Пароль</label>
            <input
              v-model="password"
              type="password"
              placeholder="••••••••"
              class="w-full border-2 border-[#1A1A1A] px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#D97706]"
              @keyup.enter="loginWithEmail"
            />
          </div>
          <div v-if="errorMsg" class="text-xs text-red-600 font-mono">{{ errorMsg }}</div>
          <button
            @click="loginWithEmail"
            :disabled="loading"
            class="w-full py-3 px-4 bg-[#1A1A1A] text-white flex items-center justify-center gap-2 hover:bg-[#D97706] transition-colors font-bold uppercase text-xs tracking-widest disabled:opacity-50"
          >
            <span v-if="loading">Вход...</span>
            <span v-else>Войти</span>
          </button>
          <button
            @click="showForgot = true; errorMsg = ''"
            class="w-full text-center text-xs text-[#737373] hover:text-[#D97706] transition-colors font-mono pt-1"
          >
            Забыли пароль?
          </button>
        </div>

        <!-- Forgot password form -->
        <div v-else class="space-y-4">
          <p class="text-xs text-[#737373] font-mono">Введите email — отправим ссылку для сброса пароля.</p>
          <div>
            <label class="block text-xs font-bold uppercase tracking-widest mb-1 text-[#1A1A1A]">Email</label>
            <input
              v-model="email"
              type="email"
              placeholder="you@example.com"
              class="w-full border-2 border-[#1A1A1A] px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#D97706]"
              @keyup.enter="sendReset"
            />
          </div>
          <div v-if="errorMsg" class="text-xs text-red-600 font-mono">{{ errorMsg }}</div>
          <div v-if="resetSent" class="text-xs text-green-700 font-mono border border-green-200 bg-green-50 px-3 py-2">
            Письмо отправлено — проверьте почту.
          </div>
          <button
            @click="sendReset"
            :disabled="loading || resetSent"
            class="w-full py-3 px-4 bg-[#1A1A1A] text-white flex items-center justify-center gap-2 hover:bg-[#D97706] transition-colors font-bold uppercase text-xs tracking-widest disabled:opacity-50"
          >
            <span v-if="loading">Отправка...</span>
            <span v-else>Отправить ссылку</span>
          </button>
          <button
            @click="showForgot = false; resetSent = false; errorMsg = ''"
            class="w-full text-center text-xs text-[#737373] hover:text-[#D97706] transition-colors font-mono pt-1"
          >
            ← Назад ко входу
          </button>
        </div>
      </div>

      <!-- Google OAuth -->
      <div v-if="activeTab === 'google'">
        <button
          @click="loginWithGoogle"
          class="w-full py-3 px-4 border-2 border-[#1A1A1A] flex items-center justify-center gap-3 hover:bg-[#FBF0D3] transition-colors font-bold uppercase text-xs tracking-widest"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 48 48">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            <path fill="none" d="M0 0h48v48H0z"/>
          </svg>
          Войти через Google
        </button>
      </div>

      <!-- Yandex OAuth -->
      <div v-if="activeTab === 'yandex'">
        <button
          @click="loginWithYandex"
          class="w-full py-3 px-4 border-2 border-[#FF0000] flex items-center justify-center gap-3 hover:bg-red-50 transition-colors font-bold uppercase text-xs tracking-widest text-[#FF0000]"
        >
          <!-- Yandex "Я" logo -->
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="#FF0000">
            <path d="M13.44 21V13.1H15L17.87 3H15.61L13.44 9.7H13.38L11.21 3H8.95L11.82 13.1H13.44V21H13.44ZM2.5 21H4.72V13.66H6.37C9.29 13.66 10.78 12.04 10.78 9.3C10.78 6.56 9.29 5 6.37 5H2.5V21ZM4.72 11.64V7.02H6.17C7.81 7.02 8.52 7.82 8.52 9.3C8.52 10.78 7.81 11.64 6.17 11.64H4.72Z"/>
          </svg>
          Войти через Яндекс
        </button>
        <p class="mt-4 text-[10px] text-[#A3A3A3] font-mono text-center">
          Новые пользователи будут зарегистрированы автоматически
        </p>
      </div>

      <div class="mt-8 pt-8 border-t border-[#F5F5F5] text-[10px] text-[#A3A3A3] text-center font-mono uppercase tracking-widest">
        Авторизация через Supabase OAuth
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { supabase } from '../lib/supabase'

const router = useRouter()
const route = useRoute()
const activeTab = ref<'email' | 'google' | 'yandex'>('email')
const email = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)
const showForgot = ref(false)
const resetSent = ref(false)
const oauthError = ref('')

const oauthErrorMessages: Record<string, string> = {
  yandex_denied: 'Вы отменили вход через Яндекс',
  yandex_token: 'Ошибка получения токена Яндекс',
  no_email: 'Яндекс не предоставил email адрес',
  create_user: 'Ошибка создания пользователя',
  session: 'Ошибка создания сессии',
  oauth_error: 'Ошибка OAuth авторизации',
}

const oauthErrorMessage = ref('')

onMounted(() => {
  const errorCode = route.query.error as string
  if (errorCode) {
    oauthError.value = errorCode
    oauthErrorMessage.value = oauthErrorMessages[errorCode] || 'Ошибка авторизации'
    activeTab.value = 'yandex'
    // Clean up URL
    router.replace({ query: {} })
  }
})

const loginWithEmail = async () => {
  errorMsg.value = ''
  loading.value = true
  const { error } = await supabase.auth.signInWithPassword({
    email: email.value,
    password: password.value,
  })
  loading.value = false
  if (error) {
    errorMsg.value = error.message
  } else {
    router.push('/')
  }
}

const sendReset = async () => {
  if (!email.value) {
    errorMsg.value = 'Введите email'
    return
  }
  errorMsg.value = ''
  loading.value = true
  const { error } = await supabase.auth.resetPasswordForEmail(email.value, {
    redirectTo: `${window.location.origin}/reset-password`,
  })
  loading.value = false
  if (error) {
    errorMsg.value = error.message
  } else {
    resetSent.value = true
  }
}

const loginWithGoogle = async () => {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: window.location.origin }
  })
  if (error) console.error('Error logging in:', error.message)
}

const loginWithYandex = () => {
  // Redirect to backend which handles the full Yandex OAuth flow
  window.location.href = `${import.meta.env.VITE_API_URL}/api/auth/yandex`
}
</script>
