<template>
  <div class="flex items-center justify-center min-h-[80vh]">
    <div class="w-full max-w-md p-10 bg-white border border-[#E5E5E5] shadow-[4px_4px_0px_0px_rgba(0,0,0,0.05)]">
      <div class="mb-8 flex justify-center">
        <div class="w-12 h-12 bg-[#FBF0D3] flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-[#D97706]"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        </div>
      </div>
      <h3 class="text-xl font-bold text-center mb-2 uppercase tracking-tight">Новый пароль</h3>
      <p class="text-[#737373] text-sm text-center mb-8 font-mono">returns-analytics-v2.0.4</p>

      <!-- Waiting for recovery session -->
      <div v-if="!ready" class="text-center text-sm text-[#737373] font-mono py-4">
        Проверка ссылки...
      </div>

      <!-- Invalid link -->
      <div v-else-if="invalidLink" class="space-y-4">
        <div class="text-xs text-red-600 font-mono border border-red-200 bg-red-50 px-3 py-2">
          Ссылка недействительна или истекла. Запросите новую.
        </div>
        <RouterLink
          to="/login"
          class="block w-full py-3 px-4 border-2 border-[#1A1A1A] text-center font-bold uppercase text-xs tracking-widest hover:bg-[#FBF0D3] transition-colors"
        >
          Вернуться ко входу
        </RouterLink>
      </div>

      <!-- Set new password form -->
      <div v-else-if="!done" class="space-y-4">
        <div>
          <label class="block text-xs font-bold uppercase tracking-widest mb-1 text-[#1A1A1A]">Новый пароль</label>
          <input
            v-model="password"
            type="password"
            placeholder="••••••••"
            class="w-full border-2 border-[#1A1A1A] px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#D97706]"
          />
        </div>
        <div>
          <label class="block text-xs font-bold uppercase tracking-widest mb-1 text-[#1A1A1A]">Подтвердите пароль</label>
          <input
            v-model="passwordConfirm"
            type="password"
            placeholder="••••••••"
            class="w-full border-2 border-[#1A1A1A] px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#D97706]"
            @keyup.enter="updatePassword"
          />
        </div>
        <div v-if="errorMsg" class="text-xs text-red-600 font-mono">{{ errorMsg }}</div>
        <button
          @click="updatePassword"
          :disabled="loading"
          class="w-full py-3 px-4 bg-[#1A1A1A] text-white flex items-center justify-center gap-2 hover:bg-[#D97706] transition-colors font-bold uppercase text-xs tracking-widest disabled:opacity-50"
        >
          <span v-if="loading">Сохранение...</span>
          <span v-else>Сохранить пароль</span>
        </button>
      </div>

      <!-- Success -->
      <div v-else class="space-y-4">
        <div class="text-xs text-green-700 font-mono border border-green-200 bg-green-50 px-3 py-2">
          Пароль успешно изменён.
        </div>
        <RouterLink
          to="/"
          class="block w-full py-3 px-4 bg-[#1A1A1A] text-white text-center font-bold uppercase text-xs tracking-widest hover:bg-[#D97706] transition-colors"
        >
          На главную
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { supabase } from '../lib/supabase'

const ready = ref(false)
const invalidLink = ref(false)
const done = ref(false)
const password = ref('')
const passwordConfirm = ref('')
const errorMsg = ref('')
const loading = ref(false)

onMounted(() => {
  // Supabase fires PASSWORD_RECOVERY when it detects the recovery token in the URL hash
  supabase.auth.onAuthStateChange((event) => {
    if (event === 'PASSWORD_RECOVERY') {
      ready.value = true
    }
  })

  // Detect error in hash (e.g. expired link sent to wrong URL)
  const hash = window.location.hash
  if (hash.includes('error=')) {
    ready.value = true
    invalidLink.value = true
    return
  }

  // If there's a valid session already (recovery token was auto-consumed), allow immediately
  supabase.auth.getSession().then(({ data: { session } }) => {
    if (session) ready.value = true
  })

  // Fallback: if no event fires after 3s, assume link is bad
  setTimeout(() => {
    if (!ready.value) {
      ready.value = true
      invalidLink.value = true
    }
  }, 3000)
})

const updatePassword = async () => {
  errorMsg.value = ''
  if (!password.value) {
    errorMsg.value = 'Введите новый пароль'
    return
  }
  if (password.value !== passwordConfirm.value) {
    errorMsg.value = 'Пароли не совпадают'
    return
  }
  if (password.value.length < 6) {
    errorMsg.value = 'Пароль должен быть не менее 6 символов'
    return
  }
  loading.value = true
  const { error } = await supabase.auth.updateUser({ password: password.value })
  loading.value = false
  if (error) {
    errorMsg.value = error.message
  } else {
    done.value = true
  }
}
</script>
