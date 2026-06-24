<template>
  <div class="min-h-screen flex bg-[#FDFCFB] selection:bg-[#FDE68A]">
    <!-- Sidebar -->
    <aside class="w-56 bg-[#1A1A1A] flex flex-col flex-shrink-0 sticky top-0 h-screen overflow-y-auto">
      <!-- Wordmark -->
      <div class="px-6 pt-8 pb-6 border-b border-[#2A2A2A]">
        <span class="text-[#D97706] font-mono text-xs uppercase tracking-widest font-bold">Admin Panel</span>
        <div class="w-2 h-2 bg-[#D97706] rounded-full mt-2"></div>
      </div>

      <!-- Nav -->
      <nav class="flex-1 px-3 py-4 space-y-0.5">
        <RouterLink
          to="/admin"
          :class="navClass"
          active-class="!bg-[#D97706] !text-white"
          exact-active-class="!bg-[#D97706] !text-white"
        >
          <span class="font-mono text-[11px] uppercase tracking-widest">Обзор</span>
        </RouterLink>
        <RouterLink
          to="/admin/users"
          :class="navClass"
          active-class="!bg-[#D97706] !text-white"
        >
          <span class="font-mono text-[11px] uppercase tracking-widest">Пользователи</span>
        </RouterLink>
        <RouterLink
          to="/admin/shops"
          :class="navClass"
          active-class="!bg-[#D97706] !text-white"
        >
          <span class="font-mono text-[11px] uppercase tracking-widest">Магазины</span>
        </RouterLink>
        <RouterLink
          to="/admin/tokens"
          :class="navClass"
          active-class="!bg-[#D97706] !text-white"
        >
          <span class="font-mono text-[11px] uppercase tracking-widest">Токены</span>
        </RouterLink>
      </nav>

      <!-- Bottom: user info + logout -->
      <div class="px-4 py-5 border-t border-[#2A2A2A] space-y-3">
        <p class="font-mono text-[10px] text-[#737373] lowercase truncate">{{ authStore.user?.email }}</p>
        <button @click="authStore.logout()" class="font-mono text-[10px] uppercase tracking-wider text-[#737373] hover:text-red-400 transition-colors">
          Выйти
        </button>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Admin top bar -->
      <div class="border-b border-[#E5E5E5] bg-white px-8 py-3 flex items-center justify-between sticky top-0 z-40">
        <div class="font-mono text-[10px] text-[#A3A3A3] uppercase tracking-tighter">
          admin / {{ $route.name?.toString().replace('admin-', '') }} / 2026-v1.0.4
        </div>
        <div class="font-mono text-[10px] text-[#D97706] uppercase tracking-widest font-bold">
          ● Admin Mode
        </div>
      </div>

      <!-- Page content -->
      <main class="flex-1 px-8 py-8">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()

const navClass = 'flex items-center px-3 py-2.5 rounded text-[#A3A3A3] hover:bg-[#2A2A2A] hover:text-[#FDFCFB] transition-all'
</script>
