<template>
  <div class="space-y-8">
    <div class="flex justify-between items-end border-b border-[#1A1A1A] pb-4">
      <div>
        <h1 class="text-4xl font-black uppercase tracking-tighter">Аналитика возвратов</h1>
        <p class="text-[#737373] font-mono text-xs mt-1">ОБНОВЛЕНИЕ: {{ lastUpdate }}</p>
      </div>
      <div class="flex gap-2 p-1 bg-[#F5F5F5] rounded-sm">
        <button
          v-for="mp in marketplaces"
          :key="mp"
          @click="currentMp = mp"
          :class="['px-6 py-1.5 text-[10px] font-mono uppercase tracking-widest transition-all', currentMp === mp ? 'bg-white shadow-sm text-[#D97706] font-bold' : 'text-[#737373] hover:text-[#1A1A1A]']"
        >
          {{ mp }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="flex flex-col items-center justify-center py-24 space-y-4">
      <div class="w-8 h-8 border-2 border-[#D97706] border-t-transparent rounded-full animate-spin"></div>
      <p class="font-mono text-[10px] uppercase tracking-widest text-[#737373]">Загрузка данных...</p>
    </div>

    <div v-else-if="returns.length === 0" class="flex flex-col items-center justify-center py-24 border-2 border-dashed border-[#E5E5E5] bg-white">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#D4D4D4" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-4"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
      <p class="font-mono text-[10px] uppercase tracking-widest text-[#A3A3A3]">Данные отсутствуют</p>
    </div>

    <div v-else class="bg-white border border-[#E5E5E5] overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-[#FBF0D3]/50 border-b border-[#E5E5E5]">
              <th v-for="col in columns[currentMp]" :key="col" class="py-4 px-6 font-mono text-[10px] uppercase tracking-widest text-[#737373] font-normal">
                {{ translateHeader(col) }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[#F5F5F5]">
            <tr v-for="row in returns" :key="row.id || row.srid || row.posting_number" class="hover:bg-[#FDFCFB] transition-colors group">
              <td v-for="col in columns[currentMp]" :key="col" class="py-4 px-6 text-sm">
                <span :class="['font-mono text-xs', col === 'status' || col === 'shipmentStatus' ? 'bg-[#F5F5F5] px-2 py-0.5 rounded-sm' : '']">
                  {{ row[col] }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { supabase } from '../lib/supabase'

const marketplaces = ['ozon', 'wb', 'ym']
const currentMp = ref('ozon')
const returns = ref([])
const loading = ref(false)
const lastUpdate = ref(new Date().toLocaleString('ru-RU'))

const columns = {
  wb: ['srid', 'orderDt', 'brand', 'status', 'reason'],
  ozon: ['posting_number', 'added_at', 'status', 'return_reason'],
  ym: ['id', 'orderId', 'returnType', 'shipmentStatus', 'amount']
}

const headerTranslations = {
  srid: 'ID Возврата',
  orderDt: 'Дата заказа',
  brand: 'Бренд',
  status: 'Статус',
  reason: 'Причина',
  posting_number: 'Номер отправления',
  added_at: 'Добавлено',
  return_reason: 'Причина возврата',
  id: 'ID',
  orderId: 'ID Заказа',
  returnType: 'Тип',
  shipmentStatus: 'Статус доставки',
  amount: 'Сумма'
}

const translateHeader = (col: string) => headerTranslations[col] || col

const fetchReturns = async () => {
  loading.value = true
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) return

  try {
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/returns/${currentMp.value}`, {
      headers: { Authorization: `Bearer ${session.access_token}` }
    })
    returns.value = response.data
    lastUpdate.value = new Date().toLocaleString('ru-RU')
  } catch (error) {
    console.error('Error fetching returns:', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchReturns)
watch(currentMp, fetchReturns)
</script>
