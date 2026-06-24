<template>
  <div class="space-y-8">
    <div class="border-b border-[#1A1A1A] pb-4">
      <h1 class="text-4xl font-black uppercase tracking-tighter text-[#D97706]">Токены</h1>
      <p class="text-[#737373] font-mono text-xs mt-1">УПРАВЛЕНИЕ УЧЁТНЫМИ ДАННЫМИ МАГАЗИНОВ</p>
    </div>

    <div v-if="shopsLoading" class="text-center py-24 font-mono uppercase text-[10px] tracking-widest text-[#737373]">
      Загрузка токенов...
    </div>
    <template v-else>
      <div v-if="allShops.length === 0" class="text-center py-24 font-mono uppercase text-[10px] tracking-widest text-[#737373]">
        Магазины не найдены
      </div>
      <div v-for="shop in allShops" :key="shop.id"
        class="bg-white border-2 border-[#1A1A1A] p-5 shadow-[6px_6px_0px_0px_rgba(0,0,0,0.04)]">
        <div class="flex justify-between items-start mb-4">
          <div>
            <p class="font-black text-base uppercase">{{ shop.name }}</p>
            <p class="font-mono text-[11px] text-[#D97706]">{{ shop.user_email }}</p>
            <p class="font-mono text-[10px] text-[#A3A3A3]">{{ shop.id }}</p>
          </div>
          <span class="font-mono text-[11px] uppercase font-bold px-2 py-0.5 border"
            :class="{
              'border-[#D97706] text-[#D97706]': shop.marketplace === 'wb',
              'border-blue-500 text-blue-600': shop.marketplace === 'ozon',
              'border-purple-500 text-purple-600': shop.marketplace === 'ym',
            }">{{ shop.marketplace }}</span>
        </div>

        <div class="space-y-2">
          <p class="text-[10px] font-mono uppercase tracking-widest text-[#737373]">Учётные данные</p>

          <!-- WB -->
          <template v-if="shop.marketplace === 'wb'">
            <div class="flex gap-2">
              <input v-model="credUpdates[shop.id].wb_token" type="text" placeholder="WB Токен"
                class="flex-1 border border-[#D1D5DB] px-2 py-1.5 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
              <button @click="updateCredentials(shop.user_id, shop.id)"
                :disabled="!credUpdates[shop.id]?.wb_token"
                class="text-[10px] font-mono uppercase border border-[#1A1A1A] px-3 py-1 hover:bg-[#1A1A1A] hover:text-white transition-all disabled:opacity-40">
                Обновить
              </button>
            </div>
          </template>

          <!-- Ozon -->
          <template v-else-if="shop.marketplace === 'ozon'">
            <div class="flex gap-2 items-end">
              <div class="grid grid-cols-2 gap-2 flex-1">
                <input v-model="credUpdates[shop.id].ozon_client_id" type="text" placeholder="Client ID"
                  class="border border-[#D1D5DB] px-2 py-1.5 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
                <input v-model="credUpdates[shop.id].ozon_client_secret" type="text" placeholder="Client Secret"
                  class="border border-[#D1D5DB] px-2 py-1.5 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
              </div>
              <button @click="updateCredentials(shop.user_id, shop.id)"
                :disabled="!credUpdates[shop.id]?.ozon_client_id && !credUpdates[shop.id]?.ozon_client_secret"
                class="text-[10px] font-mono uppercase border border-[#1A1A1A] px-3 py-1.5 hover:bg-[#1A1A1A] hover:text-white transition-all disabled:opacity-40">
                Обновить
              </button>
            </div>
          </template>

          <!-- YM -->
          <template v-else-if="shop.marketplace === 'ym'">
            <div class="flex gap-2 items-end">
              <div class="grid grid-cols-3 gap-2 flex-1">
                <input v-model="credUpdates[shop.id].ym_client_id" type="text" placeholder="Client ID"
                  class="border border-[#D1D5DB] px-2 py-1.5 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
                <input v-model="credUpdates[shop.id].ym_client_secret" type="text" placeholder="Client Secret"
                  class="border border-[#D1D5DB] px-2 py-1.5 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
                <input v-model="credUpdates[shop.id].ym_campaign_id" type="text" placeholder="Campaign ID"
                  class="border border-[#D1D5DB] px-2 py-1.5 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
              </div>
              <button @click="updateCredentials(shop.user_id, shop.id)"
                :disabled="!credUpdates[shop.id]?.ym_client_id && !credUpdates[shop.id]?.ym_client_secret && !credUpdates[shop.id]?.ym_campaign_id"
                class="text-[10px] font-mono uppercase border border-[#1A1A1A] px-3 py-1.5 hover:bg-[#1A1A1A] hover:text-white transition-all disabled:opacity-40">
                Обновить
              </button>
            </div>
          </template>

          <div class="flex gap-3">
            <span v-if="credSuccess[shop.id]" class="text-[10px] font-mono text-green-700">Токены обновлены</span>
            <span v-if="credError[shop.id]" class="text-[10px] font-mono text-red-600">{{ credError[shop.id] }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { supabase } from '../../lib/supabase'

type CredForm = {
  wb_token?: string
  ozon_client_id?: string
  ozon_client_secret?: string
  ym_client_id?: string
  ym_client_secret?: string
  ym_campaign_id?: string
}

const allShops = ref<any[]>([])
const shopsLoading = ref(true)
const credUpdates = reactive<Record<string, CredForm>>({})
const credSuccess = reactive<Record<string, boolean>>({})
const credError = reactive<Record<string, string>>({})

function emptyCredForm(): CredForm {
  return { wb_token: '', ozon_client_id: '', ozon_client_secret: '', ym_client_id: '', ym_client_secret: '', ym_campaign_id: '' }
}

async function authHeaders() {
  const { data: { session } } = await supabase.auth.getSession()
  return { Authorization: `Bearer ${session?.access_token}` }
}

async function fetchShops() {
  shopsLoading.value = true
  try {
    const headers = await authHeaders()
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/admin/shops`, { headers })
    allShops.value = response.data
    response.data.forEach((shop: any) => {
      if (!credUpdates[shop.id]) credUpdates[shop.id] = emptyCredForm()
    })
  } catch (e) {
    console.error('Admin fetch shops error', e)
  } finally {
    shopsLoading.value = false
  }
}

async function updateCredentials(userId: string, shopId: string) {
  credError[shopId] = ''
  credSuccess[shopId] = false
  try {
    const headers = await authHeaders()
    const creds = credUpdates[shopId]
    const payload: Record<string, string> = {}
    Object.entries(creds).forEach(([k, v]) => { if (v) payload[k] = v })

    await axios.patch(`${import.meta.env.VITE_API_URL}/api/admin/user/${userId}/shops/${shopId}/token`, payload, { headers })
    credSuccess[shopId] = true
    credUpdates[shopId] = emptyCredForm()
    setTimeout(() => { credSuccess[shopId] = false }, 2000)
  } catch (e: any) {
    credError[shopId] = e?.response?.data?.detail || 'Ошибка обновления токена'
  }
}

onMounted(fetchShops)
</script>
