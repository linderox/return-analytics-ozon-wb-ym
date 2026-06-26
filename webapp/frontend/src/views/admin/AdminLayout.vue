<template>
  <div class="min-h-screen flex bg-[#FDFCFB] selection:bg-[#FDE68A]">

    <!-- Sidebar placeholder – always reserves 72 px in the flex layout -->
    <div class="w-[72px] flex-shrink-0 sticky top-0 h-screen relative">

      <!-- Actual sidebar – overlays the content on hover, expands to 220 px -->
      <aside
        class="absolute left-0 top-0 h-full bg-[#1A1A1A] flex flex-col overflow-hidden z-50 transition-[width] duration-200 ease-out"
        :class="open ? 'w-[220px] shadow-[4px_0_24px_rgba(0,0,0,0.28)]' : 'w-[72px]'"
        @mouseenter="open = true"
        @mouseleave="open = false"
      >
        <!-- Brandmark -->
        <div class="h-14 flex items-center flex-shrink-0 border-b border-[#2A2A2A]">
          <span class="w-[72px] flex-shrink-0 flex items-center justify-center">
            <span class="w-2 h-2 rounded-full bg-[#D97706]"></span>
          </span>
          <span
            class="font-mono text-[10px] text-[#D97706] uppercase tracking-widest font-bold whitespace-nowrap transition-opacity duration-150"
            :class="open ? 'opacity-100' : 'opacity-0'"
          >Admin Panel</span>
        </div>

        <!-- Nav -->
        <nav class="flex-1 py-2 overflow-hidden">

          <RouterLink
            to="/admin"
            exact-active-class="!bg-[#D97706]/20 !text-[#D97706]"
            class="flex items-center h-10 text-[#A3A3A3] hover:bg-[#2A2A2A] hover:text-[#FDFCFB] transition-colors"
          >
            <span class="w-[72px] flex-shrink-0 flex items-center justify-center text-[15px]">⊞</span>
            <span class="font-mono text-[11px] uppercase tracking-widest whitespace-nowrap transition-opacity duration-100" :class="open ? 'opacity-100' : 'opacity-0'">Обзор</span>
          </RouterLink>

          <RouterLink
            to="/admin/users"
            active-class="!bg-[#D97706]/20 !text-[#D97706]"
            class="flex items-center h-10 text-[#A3A3A3] hover:bg-[#2A2A2A] hover:text-[#FDFCFB] transition-colors"
          >
            <span class="w-[72px] flex-shrink-0 flex items-center justify-center text-[15px]">⊙</span>
            <span class="font-mono text-[11px] uppercase tracking-widest whitespace-nowrap transition-opacity duration-100" :class="open ? 'opacity-100' : 'opacity-0'">Пользователи</span>
          </RouterLink>

          <RouterLink
            to="/admin/shops"
            active-class="!bg-[#D97706]/20 !text-[#D97706]"
            class="flex items-center h-10 text-[#A3A3A3] hover:bg-[#2A2A2A] hover:text-[#FDFCFB] transition-colors"
          >
            <span class="w-[72px] flex-shrink-0 flex items-center justify-center text-[15px]">⬚</span>
            <span class="font-mono text-[11px] uppercase tracking-widest whitespace-nowrap transition-opacity duration-100" :class="open ? 'opacity-100' : 'opacity-0'">Магазины</span>
          </RouterLink>

          <RouterLink
            to="/admin/tokens"
            active-class="!bg-[#D97706]/20 !text-[#D97706]"
            class="flex items-center h-10 text-[#A3A3A3] hover:bg-[#2A2A2A] hover:text-[#FDFCFB] transition-colors"
          >
            <span class="w-[72px] flex-shrink-0 flex items-center justify-center text-[15px]">◈</span>
            <span class="font-mono text-[11px] uppercase tracking-widest whitespace-nowrap transition-opacity duration-100" :class="open ? 'opacity-100' : 'opacity-0'">Токены</span>
          </RouterLink>

          <!-- ── Отчёты accordion ── -->
          <div>
            <button
              @click="reportsOpen = !reportsOpen"
              class="w-full flex items-center h-10 text-[#A3A3A3] hover:bg-[#2A2A2A] hover:text-[#FDFCFB] transition-colors"
              :class="isReportsActive ? '!text-[#D97706]' : ''"
            >
              <span class="w-[72px] flex-shrink-0 flex items-center justify-center text-[15px]">≋</span>
              <span
                class="flex-1 text-left font-mono text-[11px] uppercase tracking-widest whitespace-nowrap transition-opacity duration-100"
                :class="open ? 'opacity-100' : 'opacity-0'"
              >Отчёты</span>
              <span
                class="mr-3 text-[9px] flex-shrink-0 transition-all duration-150"
                :class="[open ? 'opacity-100' : 'opacity-0', reportsOpen ? 'rotate-90' : 'rotate-0']"
              >▶</span>
            </button>

            <!-- Sub-items: animate max-height -->
            <div
              class="overflow-hidden transition-[max-height] duration-200 ease-out"
              :style="reportsOpen && open ? 'max-height: 120px' : 'max-height: 0px'"
            >
              <RouterLink
                to="/admin/returns"
                active-class="!text-[#D97706]"
                class="flex items-center h-9 pl-[72px] pr-4 text-[#737373] hover:bg-[#2A2A2A] hover:text-[#FDFCFB] transition-colors"
              >
                <span class="mr-2 text-[#444] text-[10px]">—</span>
                <span class="font-mono text-[10px] uppercase tracking-widest whitespace-nowrap">Возвраты</span>
              </RouterLink>
            </div>
          </div>

        </nav>

        <!-- User / logout -->
        <div class="border-t border-[#2A2A2A] flex items-center h-14 flex-shrink-0 overflow-hidden">
          <span class="w-[72px] flex-shrink-0 flex items-center justify-center text-[#737373] text-sm">◎</span>
          <div
            class="flex flex-col gap-0.5 min-w-0 transition-opacity duration-150"
            :class="open ? 'opacity-100' : 'opacity-0'"
          >
            <p class="font-mono text-[10px] text-[#737373] truncate max-w-[130px]">{{ authStore.user?.email }}</p>
            <button
              @click="authStore.logout()"
              class="font-mono text-[9px] uppercase tracking-wider text-[#737373] hover:text-red-400 transition-colors text-left"
            >Выйти</button>
          </div>
        </div>

      </aside>
    </div>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top bar -->
      <div class="border-b border-[#E5E5E5] bg-white px-8 py-3 flex items-center justify-between sticky top-0 z-40">
        <div class="font-mono text-[10px] text-[#A3A3A3] uppercase tracking-tighter">
          admin / {{ $route.name?.toString().replace('admin-', '') }} / 2026-v1.0.4
        </div>
        <div class="font-mono text-[10px] text-[#D97706] uppercase tracking-widest font-bold">● Admin Mode</div>
      </div>

      <!-- Page content -->
      <main class="flex-1 px-8 py-8">
        <RouterView />
      </main>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const route = useRoute()

const open = ref(false)

// Auto-open reports group when on a reports sub-route
const isReportsActive = computed(() =>
  route.path.startsWith('/admin/return') || route.path.startsWith('/admin/report')
)
const reportsOpen = ref(isReportsActive.value)
</script>
