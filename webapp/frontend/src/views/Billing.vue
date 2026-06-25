<template>
  <div class="space-y-12">
    <div class="border-b border-[#1A1A1A] pb-4">
      <h1 class="text-4xl font-black uppercase tracking-tighter">Тарифные планы</h1>
      <p class="text-[#737373] font-mono text-xs mt-1">ВЫБЕРИТЕ УРОВЕНЬ ДОСТУПА ДЛЯ ВАШЕЙ ОРГАНИЗАЦИИ</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div v-for="(price, plan) in plans" :key="plan" class="relative group">
        <div class="absolute -inset-0.5 bg-[#1A1A1A] opacity-0 group-hover:opacity-10 transition-opacity"></div>
        <div class="relative bg-white border-2 border-[#1A1A1A] p-10 h-full flex flex-col">
          <div class="flex justify-between items-start mb-8">
            <h2 class="text-2xl font-black uppercase tracking-tight">{{ plan }}</h2>
            <div class="w-10 h-10 bg-[#FBF0D3] flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="m17 5-5-3-5 3"/><path d="m17 19-5 3-5-3"/><path d="M2 12h20"/><path d="m5 7-3 5 3 5"/><path d="m19 7 3 5-3 5"/></svg>
            </div>
          </div>

          <div class="mb-10">
            <span class="text-6xl font-black tracking-tighter">{{ price }}</span>
            <span class="text-xl font-bold ml-2">₽/МЕС</span>
          </div>

          <ul class="space-y-4 mb-12 flex-grow font-mono text-xs uppercase tracking-widest text-[#737373]">
            <li class="flex items-center gap-3">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#1A1A1A" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              До {{ plan === 'basic' ? '5' : 'Безлимит' }} магазинов
            </li>
            <li class="flex items-center gap-3">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#1A1A1A" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              {{ plan === 'basic' ? '10 000' : 'Безлимит' }} строк в месяц
            </li>
            <li class="flex items-center gap-3">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#1A1A1A" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              Обновление каждые 30 минут
            </li>
          </ul>

          <button
            @click="initiatePayment(plan)"
            class="w-full py-4 bg-[#1A1A1A] text-white font-bold uppercase text-xs tracking-[0.2em] hover:bg-[#D97706] transition-colors active:scale-[0.98]"
            :disabled="loading"
          >
            {{ loading ? 'Запрос системы...' : 'Активировать план' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="paymentInfo" class="fixed inset-0 bg-[#FDFCFB]/90 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div class="bg-white border-2 border-[#1A1A1A] w-full max-w-lg p-12 shadow-[20px_20px_0px_0px_rgba(0,0,0,0.05)]">
        <div class="flex justify-between items-center mb-10">
          <h2 class="text-2xl font-black uppercase tracking-tight">Оплата через СБП</h2>
          <button @click="paymentInfo = null" class="text-[#A3A3A3] hover:text-[#1A1A1A]">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        <div class="flex flex-col items-center">
          <div class="relative mb-8 p-4 border border-[#F5F5F5]">
            <img :src="paymentInfo.sbp_qr_code" alt="SBP QR Code" class="w-64 h-64 grayscale contrast-125"/>
            <div class="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-[#1A1A1A]"></div>
            <div class="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-[#1A1A1A]"></div>
            <div class="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-[#1A1A1A]"></div>
            <div class="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-[#1A1A1A]"></div>
          </div>

          <a
            :href="paymentInfo.confirmation_url"
            target="_blank"
            class="w-full py-4 text-center border-2 border-[#1A1A1A] font-bold uppercase text-xs tracking-widest hover:bg-[#FBF0D3] transition-colors"
          >
            Перейти в приложение банка
          </a>

          <div class="mt-8 flex items-center gap-3 animate-pulse">
            <div class="w-2 h-2 bg-[#D97706] rounded-full"></div>
            <p class="font-mono text-[10px] uppercase tracking-widest text-[#737373]">Ожидание подтверждения от ЮKassa...</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { supabase } from '../lib/supabase'

const plans = { basic: 499, pro: 999 }
const loading = ref(false)
const paymentInfo = ref<{ sbp_qr_code: string; confirmation_url: string } | null>(null)

const initiatePayment = async (plan: string) => {
  loading.value = true
  const { data: { session } } = await supabase.auth.getSession()

  try {
    const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/billing/create?plan=${plan}`, {}, {
      headers: { Authorization: `Bearer ${session?.access_token}` }
    })
    paymentInfo.value = response.data
    startPolling(response.data.payment_id)
  } catch (error) {
    console.error('Payment error:', error)
  } finally {
    loading.value = false
  }
}

const startPolling = (paymentId: string) => {
  const interval = setInterval(async () => {
    const { data: { session } } = await supabase.auth.getSession()
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/billing/status/${paymentId}`, {
        headers: { Authorization: `Bearer ${session?.access_token}` }
      })
      if (response.data.status === 'succeeded') {
        clearInterval(interval)
        alert('Платеж успешно подтвержден!')
        window.location.reload()
      }
    } catch (e) {
      console.error('Polling error', e)
    }
  }, 5000)
}
</script>
