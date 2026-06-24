<template>
  <div class="space-y-12">
    <div class="border-b border-[#1A1A1A] pb-4">
      <h1 class="text-4xl font-black uppercase tracking-tighter text-[#D97706]">Панель администратора</h1>
      <p class="text-[#737373] font-mono text-xs mt-1">УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ И МАГАЗИНАМИ СИСТЕМЫ</p>
    </div>

    <div v-if="loading" class="text-center py-24 font-mono uppercase text-[10px] tracking-widest text-[#737373]">
      Загрузка базы пользователей...
    </div>

    <div v-else class="grid grid-cols-1 gap-8">
      <div v-for="user in users" :key="user.id" class="bg-white border-2 border-[#1A1A1A] p-6 shadow-[10px_10px_0px_0px_rgba(0,0,0,0.05)]">
        <div class="flex justify-between items-start mb-6">
          <div>
            <h2 class="text-xl font-bold uppercase">{{ user.fio || 'Без имени' }}</h2>
            <p class="text-xs font-mono text-[#737373]">{{ user.id }}</p>
          </div>
          <div class="flex gap-4">
            <div class="text-right">
              <p class="text-[10px] font-mono text-[#737373] uppercase">Тариф</p>
              <p class="font-bold text-[#D97706] uppercase">{{ user.plan }}</p>
            </div>
            <div class="text-right">
              <p class="text-[10px] font-mono text-[#737373] uppercase">Магазинов</p>
              <p class="font-bold">{{ user.shop_count }}</p>
            </div>
          </div>
        </div>

        <button
          @click="toggleUserShops(user.id)"
          class="text-[10px] font-mono uppercase tracking-widest border border-[#1A1A1A] px-4 py-1 hover:bg-[#1A1A1A] hover:text-white transition-all"
        >
          {{ expandedUser === user.id ? 'Скрыть детали' : 'Показать магазины' }}
        </button>

        <div v-if="expandedUser === user.id" class="mt-8 border-t border-[#F5F5F5] pt-6">
          <div v-if="shopsLoading" class="animate-pulse font-mono text-[10px] text-[#A3A3A3]">Запрос данных SQLite...</div>
          <div v-else-if="userShops.length === 0" class="font-mono text-[10px] text-[#A3A3A3]">У пользователя нет активных магазинов</div>
          <div v-else class="space-y-4">
            <div v-for="shop in userShops" :key="shop.id" class="flex justify-between items-center p-3 bg-[#FDFCFB] border border-[#E5E5E5]">
              <div>
                <p class="font-bold text-sm uppercase">{{ shop.name }} ({{ shop.marketplace }})</p>
                <p class="text-[10px] font-mono text-[#737373]">Последняя синхронизация: {{ shop.last_synced_at || 'Никогда' }}</p>
              </div>
              <div class="text-right">
                <p class="text-[10px] font-mono text-[#737373] uppercase">Строк в БД</p>
                <p class="font-bold text-[#D97706]">{{ shop.row_count.toLocaleString() }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { supabase } from '../lib/supabase'

const users = ref([])
const loading = ref(true)
const expandedUser = ref(null)
const userShops = ref([])
const shopsLoading = ref(false)

const fetchUsers = async () => {
  const { data: { session } } = await supabase.auth.getSession()
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/admin/users`, {
      headers: { Authorization: `Bearer ${session?.access_token}` }
    })
    users.value = response.data
  } catch (e) {
    console.error('Admin fetch error', e)
  } finally {
    loading.value = false
  }
}

const toggleUserShops = async (userId: string) => {
  if (expandedUser.value === userId) {
    expandedUser.value = null
    return
  }

  expandedUser.value = userId
  shopsLoading.value = true
  const { data: { session } } = await supabase.auth.getSession()

  try {
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/admin/user/${userId}/shops`, {
      headers: { Authorization: `Bearer ${session?.access_token}` }
    })
    userShops.value = response.data
  } catch (e) {
    console.error('User shops fetch error', e)
  } finally {
    shopsLoading.value = false
  }
}

onMounted(fetchUsers)
</script>
