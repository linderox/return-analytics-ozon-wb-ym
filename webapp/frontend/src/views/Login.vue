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

      <button
        @click="loginWithGoogle"
        class="w-full py-3 px-4 border-2 border-[#1A1A1A] flex items-center justify-center gap-3 hover:bg-[#FBF0D3] transition-colors font-bold uppercase text-xs tracking-widest"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v8"/><path d="M8 12h8"/></svg>
        Войти через Google
      </button>

      <div class="mt-8 pt-8 border-t border-[#F5F5F5] text-[10px] text-[#A3A3A3] text-center font-mono uppercase tracking-widest">
        Авторизация через Supabase OAuth
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { supabase } from '../lib/supabase'

const loginWithGoogle = async () => {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.origin
    }
  })
  if (error) console.error('Error logging in:', error.message)
}
</script>
