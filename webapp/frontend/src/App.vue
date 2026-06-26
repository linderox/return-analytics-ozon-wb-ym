<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const route = useRoute()

onMounted(() => {
  authStore.initialize()
})
</script>

<template>
  <div class="min-h-screen bg-[#FDFCFB] text-[#1A1A1A] font-sans selection:bg-[#FDE68A]">
    <header v-if="authStore.user && !route.path.startsWith('/admin')" class="border-b border-[#E5E5E5] bg-white sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 h-14 flex justify-between items-center font-mono text-sm uppercase tracking-wider">
        <nav class="flex space-x-8">
          <RouterLink to="/" class="hover:text-[#D97706] transition-colors flex items-center gap-2">
            <span class="w-2 h-2 bg-[#D97706] rounded-full"></span>
            Профиль
          </RouterLink>
          <RouterLink to="/dashboard" class="hover:text-[#D97706] transition-colors flex items-center gap-2">
            Дашборд
          </RouterLink>
          <RouterLink to="/billing" class="hover:text-[#D97706] transition-colors flex items-center gap-2">
            Тарифы
          </RouterLink>
        </nav>
        <div class="flex items-center space-x-6">
          <span class="text-[#737373] lowercase">{{ authStore.user?.email }}</span>
          <button @click="authStore.logout()" class="border border-[#E5E5E5] px-3 py-1 hover:bg-[#1A1A1A] hover:text-white transition-all active:scale-95">
            Выйти
          </button>
        </div>
      </div>
    </header>

    <div v-if="authStore.user && !route.path.startsWith('/admin')" class="max-w-7xl mx-auto px-4 py-2 border-b border-[#E5E5E5] bg-[#FBF0D3]/30 font-mono text-[10px] text-[#737373] uppercase tracking-tighter">
      root / {{ route.name }} / 2026-v1.0.4
    </div>

    <main :class="route.path.startsWith('/admin') ? '' : 'max-w-7xl mx-auto px-4 py-8'">
      <RouterView />
    </main>

    <footer v-if="!route.path.startsWith('/admin')" class="max-w-7xl mx-auto px-4 py-12 border-t border-[#E5E5E5] mt-20 opacity-30 font-mono text-[10px] uppercase tracking-widest text-center">
      © 2026 Anton Mislawsky — marketplace returns infrastructure
    </footer>
  </div>
</template>

<style>
@import 'tailwindcss/base';
@import 'tailwindcss/components';
@import 'tailwindcss/utilities';

:root {
  --claude-yellow: #FBF0D3;
  --claude-accent: #D97706;
}

body {
  margin: 0;
  -webkit-font-smoothing: antialiased;
}

.router-link-active {
  color: var(--claude-accent);
  font-weight: 600;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: #FDFCFB;
}
::-webkit-scrollbar-thumb {
  background: #E5E5E5;
}
::-webkit-scrollbar-thumb:hover {
  background: #D4D4D4;
}
</style>
