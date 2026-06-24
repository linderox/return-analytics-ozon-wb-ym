<template>
  <div class="space-y-8">
    <div class="border-b border-[#1A1A1A] pb-4">
      <h1 class="text-4xl font-black uppercase tracking-tighter text-[#D97706]">Магазины</h1>
      <p class="text-[#737373] font-mono text-xs mt-1">УПРАВЛЕНИЕ МАГАЗИНАМИ ПОЛЬЗОВАТЕЛЕЙ</p>
    </div>

    <!-- Add shop form -->
    <div class="bg-white border-2 border-[#1A1A1A] p-6 shadow-[10px_10px_0px_0px_rgba(0,0,0,0.05)]">
      <h2 class="text-lg font-black uppercase tracking-tight mb-6">Добавить магазин</h2>
      <div class="space-y-3">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Пользователь *</label>
            <select v-model="newShopGlobal.userId"
              class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-white">
              <option value="">— выберите —</option>
              <option v-for="u in users" :key="u.id" :value="u.id">{{ u.email }}</option>
            </select>
          </div>
          <div>
            <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Название *</label>
            <input v-model="newShopGlobal.name" type="text"
              class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
          </div>
          <div>
            <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Маркетплейс *</label>
            <div class="flex gap-2">
              <button v-for="mp in MARKETPLACE_LIST" :key="mp.value"
                @click="selectMarketplace(mp.value)"
                class="flex items-center gap-1.5 px-3 py-2 border-2 font-mono text-xs font-bold transition-all"
                :class="newShopGlobal.marketplace === mp.value
                  ? 'border-[#1A1A1A] bg-[#1A1A1A] text-white'
                  : 'border-[#E5E5E5] hover:border-[#1A1A1A]'">
                <MarketplaceLogo :mp="mp.value" :size="16" />
                {{ mp.label }}
              </button>
            </div>
          </div>
        </div>

        <!-- Fulfillment models (multi-select) -->
        <div v-if="newShopGlobal.marketplace">
          <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Модели работы <span class="text-[#A3A3A3] normal-case">(можно выбрать несколько)</span></label>
          <div class="flex gap-3 flex-wrap">
            <label v-for="fm in fulfillmentOptionsFor(newShopGlobal.marketplace)" :key="fm.value"
              class="flex items-center gap-2 cursor-pointer px-3 py-2 border border-[#D1D5DB] hover:border-[#D97706] hover:bg-[#FFFBF0] transition-all">
              <input type="checkbox" :value="fm.value" v-model="newShopGlobal.fulfillment_models" class="accent-[#D97706]" />
              <span class="font-mono text-xs font-bold">{{ fm.value }}</span>
              <span class="font-mono text-[10px] text-[#737373]">{{ fm.desc }}</span>
            </label>
          </div>
        </div>

        <template v-if="newShopGlobal.marketplace === 'wb'">
          <input v-model="newShopGlobal.wb_token" type="text" placeholder="WB API Токен"
            class="w-full border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
        </template>
        <template v-else-if="newShopGlobal.marketplace === 'ozon'">
          <div class="space-y-2">
            <p class="text-[10px] font-mono uppercase tracking-widest text-blue-600">Seller API *</p>
            <div class="grid grid-cols-2 gap-3">
              <input v-model="newShopGlobal.ozon_client_id" type="text" placeholder="Client ID"
                class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
              <input v-model="newShopGlobal.ozon_client_secret" type="text" placeholder="API Key"
                class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
            </div>
            <p class="text-[10px] font-mono uppercase tracking-widest text-[#737373] pt-1">Performance API <span class="normal-case text-[#A3A3A3]">(необязательно)</span></p>
            <div class="grid grid-cols-2 gap-3">
              <input v-model="newShopGlobal.ozon_performance_client_id" type="text" placeholder="Perf. Client ID"
                class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
              <input v-model="newShopGlobal.ozon_performance_client_secret" type="text" placeholder="Perf. Client Secret"
                class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
            </div>
          </div>
        </template>
        <template v-else-if="newShopGlobal.marketplace === 'ym'">
          <div class="grid grid-cols-3 gap-3">
            <input v-model="newShopGlobal.ym_client_id" type="text" placeholder="OAuth Токен / API Key"
              class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
            <input v-model="newShopGlobal.ym_client_secret" type="text" placeholder="Client Secret (опц.)"
              class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
            <input v-model="newShopGlobal.ym_campaign_id" type="text" placeholder="Campaign ID"
              class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
          </div>
        </template>

        <div class="flex items-center gap-4 pt-1">
          <button @click="addShopGlobal" :disabled="!canAddShopGlobal"
            class="font-mono text-[10px] uppercase tracking-widest bg-[#D97706] text-white px-6 py-2 hover:bg-[#B45309] transition-all disabled:opacity-50">
            + Добавить магазин
          </button>
          <span v-if="addShopGlobalError" class="text-red-600 font-mono text-xs">{{ addShopGlobalError }}</span>
          <span v-if="addShopGlobalSuccess" class="text-green-700 font-mono text-xs">Магазин добавлен</span>
        </div>
      </div>
    </div>

    <!-- Shops table -->
    <div v-if="shopsLoading" class="text-center py-24 font-mono uppercase text-[10px] tracking-widest text-[#737373]">
      Загрузка магазинов...
    </div>
    <div v-else class="bg-white border-2 border-[#1A1A1A] shadow-[10px_10px_0px_0px_rgba(0,0,0,0.05)] overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b-2 border-[#1A1A1A] bg-[#FAFAFA]">
            <th class="text-left px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-[#737373]">Магазин</th>
            <th class="text-left px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-[#737373]">Пользователь</th>
            <th class="text-left px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-[#737373]">Маркетплейс / Модель</th>
            <th class="text-left px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-[#737373]">Синхронизация</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="allShops.length === 0">
            <td colspan="5" class="px-4 py-8 text-center font-mono text-[10px] text-[#A3A3A3] uppercase">Магазины не найдены</td>
          </tr>
          <tr v-for="shop in allShops" :key="shop.id" class="border-b border-[#F0F0F0] hover:bg-[#FDFCFB]">
            <td class="px-4 py-3">
              <p class="font-bold text-sm">{{ shop.name }}</p>
              <p class="font-mono text-[10px] text-[#A3A3A3]">{{ shop.id }}</p>
            </td>
            <td class="px-4 py-3">
              <p class="font-mono text-[11px] text-[#D97706]">{{ shop.user_email }}</p>
              <p class="font-mono text-[10px] text-[#A3A3A3]">{{ shop.fio || '—' }}</p>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2 flex-wrap">
                <div class="flex items-center gap-1.5">
                  <MarketplaceLogo :mp="shop.marketplace" :size="20" />
                  <span class="font-mono text-[11px] uppercase font-bold">{{ shop.marketplace.toUpperCase() }}</span>
                </div>
                <template v-if="shop.fulfillment_models && shop.fulfillment_models.length">
                  <span v-for="fm in shop.fulfillment_models" :key="fm"
                    class="font-mono text-[10px] uppercase px-1.5 py-0.5 bg-[#F5F5F5] text-[#737373] border border-[#E5E5E5]">
                    {{ fm }}
                  </span>
                </template>
              </div>
            </td>
            <td class="px-4 py-3 font-mono text-[10px] text-[#737373]">{{ shop.last_synced_at || 'Никогда' }}</td>
            <td class="px-4 py-3 text-right">
              <button @click="deleteShopGlobal(shop.user_id, shop.id)"
                class="text-[10px] font-mono uppercase tracking-widest border border-red-400 text-red-500 px-3 py-1 hover:bg-red-500 hover:text-white transition-all">
                Удалить
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { supabase } from '../../lib/supabase'

// ── Inline marketplace logo component ────────────────────────────────────────
const MarketplaceLogo = {
  props: { mp: String, size: { type: Number, default: 20 } },
  setup(props: { mp: string; size: number }) {
    const config: Record<string, { bg: string; color: string; text: string }> = {
      wb:   { bg: '#CB11AB', color: '#fff',     text: 'WB' },
      ozon: { bg: '#005BFF', color: '#fff',     text: 'O'  },
      ym:   { bg: '#FFCC00', color: '#1A1A1A',  text: 'ЯМ' },
    }
    return () => {
      const c = config[props.mp] ?? { bg: '#ccc', color: '#333', text: '?' }
      return {
        type: 'span',
        props: {
          style: `display:inline-flex;align-items:center;justify-content:center;width:${props.size}px;height:${props.size}px;background:${c.bg};color:${c.color};font-size:${Math.round(props.size * 0.45)}px;font-weight:900;font-family:monospace;flex-shrink:0;`,
        },
        children: [c.text],
      }
    }
  },
}

const MARKETPLACE_LIST = [
  { value: 'wb',   label: 'WB'   },
  { value: 'ozon', label: 'Ozon' },
  { value: 'ym',   label: 'ЯМ'   },
]

const FULFILLMENT_OPTIONS: Record<string, { value: string; desc: string }[]> = {
  wb:   [{ value: 'FBS', desc: 'Свой склад' }, { value: 'FBW', desc: 'Склад WB' }],
  ozon: [{ value: 'FBS', desc: 'Свой склад' }, { value: 'FBO', desc: 'Склад Ozon' }],
  ym:   [{ value: 'FBS', desc: 'Свой склад' }, { value: 'FBY', desc: 'Склад Яндекса' }],
}

function fulfillmentOptionsFor(mp: string) {
  return FULFILLMENT_OPTIONS[mp] ?? []
}

const users = ref<any[]>([])
const allShops = ref<any[]>([])
const shopsLoading = ref(true)

const newShopGlobal = reactive({
  userId: '',
  name: '',
  marketplace: 'wb',
  fulfillment_models: [] as string[],
  wb_token: '',
  ozon_client_id: '',
  ozon_client_secret: '',
  ozon_performance_client_id: '',
  ozon_performance_client_secret: '',
  ym_client_id: '',
  ym_client_secret: '',
  ym_campaign_id: '',
})
const addShopGlobalError = ref('')
const addShopGlobalSuccess = ref(false)

const canAddShopGlobal = computed(() => {
  if (!newShopGlobal.userId || !newShopGlobal.name) return false
  if (newShopGlobal.marketplace === 'wb') return !!newShopGlobal.wb_token
  if (newShopGlobal.marketplace === 'ozon') return !!(newShopGlobal.ozon_client_id && newShopGlobal.ozon_client_secret)
  if (newShopGlobal.marketplace === 'ym') return !!(newShopGlobal.ym_client_id && newShopGlobal.ym_campaign_id)
  return false
})

function selectMarketplace(mp: string) {
  newShopGlobal.marketplace = mp
  newShopGlobal.fulfillment_models = []
}

async function authHeaders() {
  const { data: { session } } = await supabase.auth.getSession()
  return { Authorization: `Bearer ${session?.access_token}` }
}

async function fetchData() {
  shopsLoading.value = true
  try {
    const headers = await authHeaders()
    const [usersRes, shopsRes] = await Promise.all([
      axios.get(`${import.meta.env.VITE_API_URL}/api/admin/users`, { headers }),
      axios.get(`${import.meta.env.VITE_API_URL}/api/admin/shops`, { headers }),
    ])
    users.value = usersRes.data
    allShops.value = shopsRes.data
  } catch (e) {
    console.error('Admin shops fetch error', e)
  } finally {
    shopsLoading.value = false
  }
}

async function addShopGlobal() {
  addShopGlobalError.value = ''
  addShopGlobalSuccess.value = false
  try {
    const headers = await authHeaders()
    const payload: Record<string, any> = {
      name: newShopGlobal.name,
      marketplace: newShopGlobal.marketplace,
      ...(newShopGlobal.fulfillment_models.length ? { fulfillment_models: newShopGlobal.fulfillment_models } : {}),
    }
    if (newShopGlobal.marketplace === 'wb') {
      payload.wb_token = newShopGlobal.wb_token
    } else if (newShopGlobal.marketplace === 'ozon') {
      payload.ozon_client_id = newShopGlobal.ozon_client_id
      payload.ozon_client_secret = newShopGlobal.ozon_client_secret
      if (newShopGlobal.ozon_performance_client_id) payload.ozon_performance_client_id = newShopGlobal.ozon_performance_client_id
      if (newShopGlobal.ozon_performance_client_secret) payload.ozon_performance_client_secret = newShopGlobal.ozon_performance_client_secret
    } else if (newShopGlobal.marketplace === 'ym') {
      payload.ym_client_id = newShopGlobal.ym_client_id
      payload.ym_campaign_id = newShopGlobal.ym_campaign_id
      if (newShopGlobal.ym_client_secret) payload.ym_client_secret = newShopGlobal.ym_client_secret
    }

    await axios.post(`${import.meta.env.VITE_API_URL}/api/admin/user/${newShopGlobal.userId}/shops`, payload, { headers })
    addShopGlobalSuccess.value = true
    Object.assign(newShopGlobal, {
      userId: '', name: '', marketplace: 'wb', fulfillment_models: [],
      wb_token: '', ozon_client_id: '', ozon_client_secret: '',
      ozon_performance_client_id: '', ozon_performance_client_secret: '',
      ym_client_id: '', ym_client_secret: '', ym_campaign_id: '',
    })
    await fetchData()
    setTimeout(() => { addShopGlobalSuccess.value = false }, 2000)
  } catch (e: any) {
    addShopGlobalError.value = e?.response?.data?.detail || 'Ошибка добавления магазина'
  }
}

async function deleteShopGlobal(userId: string, shopId: string) {
  if (!confirm('Удалить магазин?')) return
  try {
    const headers = await authHeaders()
    await axios.delete(`${import.meta.env.VITE_API_URL}/api/admin/user/${userId}/shops/${shopId}`, { headers })
    allShops.value = allShops.value.filter(s => s.id !== shopId)
  } catch (e) {
    console.error('Delete shop error', e)
  }
}

onMounted(fetchData)
</script>
