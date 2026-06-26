<template>
  <div class="space-y-8">
    <div class="border-b border-[#E5E5E5] pb-4 flex items-baseline gap-4">
      <h1 class="font-mono text-[17px] font-bold text-[#1A1A1A] uppercase tracking-[0.06em]">Обзор</h1>
      <span class="font-mono text-[10px] text-[#A3A3A3] uppercase tracking-widest">/ общая статистика</span>
    </div>

    <div v-if="loading" class="text-center py-24 font-mono uppercase text-[10px] tracking-widest text-[#737373]">
      Загрузка...
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-3 gap-6">
      <div class="bg-white border border-[#E5E5E5] p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,0.05)]">
        <p class="font-mono text-[10px] uppercase tracking-widest text-[#737373] mb-2">Пользователи</p>
        <p class="text-5xl font-black text-[#1A1A1A]">{{ stats.users }}</p>
      </div>
      <div class="bg-white border border-[#E5E5E5] p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,0.05)]">
        <p class="font-mono text-[10px] uppercase tracking-widest text-[#737373] mb-2">Магазины</p>
        <p class="text-5xl font-black text-[#1A1A1A]">{{ stats.shops }}</p>
      </div>
      <div class="bg-white border border-[#E5E5E5] p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,0.05)]">
        <p class="font-mono text-[10px] uppercase tracking-widest text-[#737373] mb-2">Маркетплейсы</p>
        <div class="flex gap-3 mt-2">
          <span v-for="(count, mp) in stats.byMarketplace" :key="mp"
            class="font-mono text-[11px] uppercase font-bold px-2 py-0.5 border"
            :class="{
              'border-[#D97706] text-[#D97706]': mp === 'wb',
              'border-blue-500 text-blue-600': mp === 'ozon',
              'border-purple-500 text-purple-600': mp === 'ym',
            }">{{ mp }}: {{ count }}</span>
        </div>
      </div>
    </div>

    <div v-if="!loading" class="bg-white border border-[#E5E5E5] p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,0.05)]">
      <h2 class="text-sm font-black uppercase tracking-tight mb-4">Тарифы пользователей</h2>
      <div class="flex gap-6">
        <div v-for="(count, plan) in stats.byPlan" :key="plan" class="text-center">
          <p class="text-3xl font-black">{{ count }}</p>
          <p class="font-mono text-[10px] uppercase tracking-widest text-[#737373] mt-1">{{ plan }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { supabase } from '../../lib/supabase'

const loading = ref(true)
const stats = reactive({
  users: 0,
  shops: 0,
  byMarketplace: {} as Record<string, number>,
  byPlan: {} as Record<string, number>,
})

async function authHeaders() {
  const { data: { session } } = await supabase.auth.getSession()
  return { Authorization: `Bearer ${session?.access_token}` }
}

onMounted(async () => {
  try {
    const headers = await authHeaders()
    const [usersRes, shopsRes] = await Promise.all([
      axios.get(`${import.meta.env.VITE_API_URL}/api/admin/users`, { headers }),
      axios.get(`${import.meta.env.VITE_API_URL}/api/admin/shops`, { headers }),
    ])

    stats.users = usersRes.data.length
    stats.shops = shopsRes.data.length

    const mpCounts: Record<string, number> = {}
    shopsRes.data.forEach((s: any) => {
      mpCounts[s.marketplace] = (mpCounts[s.marketplace] || 0) + 1
    })
    stats.byMarketplace = mpCounts

    const planCounts: Record<string, number> = {}
    usersRes.data.forEach((u: any) => {
      planCounts[u.plan] = (planCounts[u.plan] || 0) + 1
    })
    stats.byPlan = planCounts
  } catch (e) {
    console.error('Dashboard stats error', e)
  } finally {
    loading.value = false
  }
})
</script>
