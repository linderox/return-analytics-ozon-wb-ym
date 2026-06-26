<template>
  <div class="space-y-6">
    <div class="border-b border-[#E5E5E5] pb-4 flex items-baseline gap-4">
      <h1 class="font-mono text-[17px] font-bold text-[#1A1A1A] uppercase tracking-[0.06em]">Токены</h1>
      <span class="font-mono text-[10px] text-[#A3A3A3] uppercase tracking-widest">/ учётные данные</span>
    </div>

    <div v-if="shopsLoading" class="text-center py-24 font-mono uppercase text-[10px] tracking-widest text-[#A3A3A3]">
      Загрузка токенов...
    </div>
    <template v-else>
      <div v-if="allShops.length === 0" class="text-center py-24 font-mono uppercase text-[10px] tracking-widest text-[#A3A3A3]">
        Магазины не найдены
      </div>

      <div v-for="shop in allShops" :key="shop.id"
        class="bg-white border border-[#E5E5E5] shadow-[4px_4px_0px_0px_rgba(0,0,0,0.02)] overflow-hidden">

        <!-- Shop header bar -->
        <div class="flex items-center justify-between px-5 py-3 bg-[#FAFAFA] border-b border-[#F0F0F0]">
          <div class="flex items-center gap-3">
            <MpBadge :mp="shop.marketplace" :size="22" />
            <div>
              <p class="font-mono text-[13px] font-bold text-[#1A1A1A] uppercase tracking-[0.04em]">{{ shop.name }}</p>
              <p class="font-mono text-[10px] text-[#D97706]">{{ shop.user_email }}</p>
            </div>
          </div>
          <p class="font-mono text-[10px] text-[#C0C0C0] hidden sm:block">{{ shop.id }}</p>
        </div>

        <!-- Credentials section -->
        <div class="px-5 py-4">
          <p class="font-mono text-[9px] uppercase tracking-widest text-[#A3A3A3] mb-3">Учётные данные</p>

          <!-- WB -->
          <template v-if="shop.marketplace === 'wb'">
            <div class="flex gap-2">
              <input v-model="credUpdates[shop.id].wb_token" type="text" placeholder="WB Токен"
                class="flex-1 border border-[#E5E5E5] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-[#FAFAFA]" />
              <button @click="updateCredentials(shop.user_id, shop.id)"
                :disabled="!credUpdates[shop.id]?.wb_token"
                class="font-mono text-[10px] uppercase tracking-wider border border-[#E5E5E5] px-4 py-2 hover:bg-[#1A1A1A] hover:text-white transition-all disabled:opacity-30">
                Обновить
              </button>
            </div>
          </template>

          <!-- Ozon -->
          <template v-else-if="shop.marketplace === 'ozon'">
            <div class="flex gap-2 items-end">
              <div class="grid grid-cols-2 gap-2 flex-1">
                <input v-model="credUpdates[shop.id].ozon_client_id" type="text" placeholder="Client ID"
                  class="border border-[#E5E5E5] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-[#FAFAFA]" />
                <input v-model="credUpdates[shop.id].ozon_client_secret" type="text" placeholder="Client Secret"
                  class="border border-[#E5E5E5] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-[#FAFAFA]" />
              </div>
              <button @click="updateCredentials(shop.user_id, shop.id)"
                :disabled="!credUpdates[shop.id]?.ozon_client_id && !credUpdates[shop.id]?.ozon_client_secret"
                class="font-mono text-[10px] uppercase tracking-wider border border-[#E5E5E5] px-4 py-2 hover:bg-[#1A1A1A] hover:text-white transition-all disabled:opacity-30">
                Обновить
              </button>
            </div>
          </template>

          <!-- YM -->
          <template v-else-if="shop.marketplace === 'ym'">
            <div class="flex gap-2 items-end">
              <div class="grid grid-cols-3 gap-2 flex-1">
                <input v-model="credUpdates[shop.id].ym_client_id" type="text" placeholder="Client ID"
                  class="border border-[#E5E5E5] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-[#FAFAFA]" />
                <input v-model="credUpdates[shop.id].ym_client_secret" type="text" placeholder="Client Secret"
                  class="border border-[#E5E5E5] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-[#FAFAFA]" />
                <input v-model="credUpdates[shop.id].ym_campaign_id" type="text" placeholder="Campaign ID"
                  class="border border-[#E5E5E5] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-[#FAFAFA]" />
              </div>
              <button @click="updateCredentials(shop.user_id, shop.id)"
                :disabled="!credUpdates[shop.id]?.ym_client_id && !credUpdates[shop.id]?.ym_client_secret && !credUpdates[shop.id]?.ym_campaign_id"
                class="font-mono text-[10px] uppercase tracking-wider border border-[#E5E5E5] px-4 py-2 hover:bg-[#1A1A1A] hover:text-white transition-all disabled:opacity-30">
                Обновить
              </button>
            </div>
          </template>

          <div class="mt-2 h-4">
            <span v-if="credSuccess[shop.id]" class="font-mono text-[10px] text-green-600">Токены обновлены</span>
            <span v-if="credError[shop.id]" class="font-mono text-[10px] text-red-500">{{ credError[shop.id] }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import axios from 'axios'
import { supabase } from '../../lib/supabase'

// ── Marketplace badge ──────────────────────────────────────────────────────────
const MpBadge = {
  props: { mp: String, size: { type: Number, default: 20 } },
  setup(props: { mp: string; size: number }) {
    const cfg: Record<string, { bg: string; color: string; text: string }> = {
      wb:   { bg: '#CB11AB', color: '#fff',    text: 'WB' },
      ozon: { bg: '#005BFF', color: '#fff',    text: 'O'  },
      ym:   { bg: '#FFCC00', color: '#1A1A1A', text: 'ЯМ' },
    }
    return () => {
      const c = cfg[props.mp] ?? { bg: '#ccc', color: '#333', text: '?' }
      return h('span', {
        style: `display:inline-flex;align-items:center;justify-content:center;width:${props.size}px;height:${props.size}px;background:${c.bg};color:${c.color};font-size:${Math.round(props.size * 0.44)}px;font-weight:900;font-family:monospace;flex-shrink:0;`,
      }, c.text)
    }
  },
}

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
