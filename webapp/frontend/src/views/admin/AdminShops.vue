<template>
  <div class="space-y-8">
    <div class="border-b border-[#E5E5E5] pb-4 flex items-baseline gap-4">
      <h1 class="font-mono text-[17px] font-bold text-[#1A1A1A] uppercase tracking-[0.06em]">Магазины</h1>
      <span class="font-mono text-[10px] text-[#A3A3A3] uppercase tracking-widest">/ управление</span>
    </div>

    <!-- Add shop form -->
    <div class="bg-white border border-[#E5E5E5] p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.03)]">
      <h2 class="font-mono text-[13px] font-bold uppercase tracking-[0.06em] text-[#1A1A1A] mb-1">Добавить магазин</h2>
      <p class="font-mono text-[10px] text-[#A3A3A3] mb-5">Заполните поля и нажмите «Добавить»</p>

      <div class="space-y-4">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Пользователь *</label>
            <select v-model="newShopGlobal.userId"
              @change="newShopGlobal.shopId = ''"
              class="w-full border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-white">
              <option value="">— выберите —</option>
              <option v-for="u in users" :key="u.id" :value="u.id">{{ u.email }}</option>
            </select>
          </div>
          <div>
            <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Название *</label>
            <input v-model="newShopGlobal.name" type="text"
              class="w-full border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
          </div>
          <div>
            <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Маркетплейс *</label>
            <div class="flex gap-2">
              <button v-for="mp in MARKETPLACE_LIST" :key="mp.value"
                @click="selectMarketplace(mp.value)"
                class="flex items-center gap-1.5 px-3 py-2 border font-mono text-xs font-bold transition-all"
                :class="newShopGlobal.marketplace === mp.value
                  ? 'border-[#E5E5E5] bg-[#1A1A1A] text-white'
                  : 'border-[#D1D5DB] text-[#555] hover:border-[#E5E5E5]'">
                <MpBadge :mp="mp.value" :size="14" />
                {{ mp.label }}
              </button>
            </div>
          </div>
        </div>

        <!-- Fulfillment models -->
        <div v-if="newShopGlobal.marketplace">
          <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">
            Модели работы <span class="text-[#A3A3A3] normal-case">(можно несколько)</span>
          </label>
          <div class="flex gap-2 flex-wrap">
            <label v-for="fm in fulfillmentOptionsFor(newShopGlobal.marketplace)" :key="fm.value"
              class="flex items-center gap-2 cursor-pointer px-3 py-1.5 border border-[#E5E5E5] hover:border-[#D97706] hover:bg-[#FFFBF0] transition-all">
              <input type="checkbox" :value="fm.value" v-model="newShopGlobal.fulfillment_models" class="accent-[#D97706]" />
              <span class="font-mono text-xs font-bold">{{ fm.value }}</span>
              <span class="font-mono text-[10px] text-[#A3A3A3]">{{ fm.desc }}</span>
            </label>
          </div>
        </div>

        <!-- Credentials by marketplace -->
        <template v-if="newShopGlobal.marketplace === 'wb'">
          <div>
            <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">WB API Токен *</label>
            <input v-model="newShopGlobal.wb_token" type="text"
              class="w-full border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
          </div>
        </template>
        <template v-else-if="newShopGlobal.marketplace === 'ozon'">
          <div class="space-y-3">
            <div>
              <label class="block text-[10px] font-mono uppercase tracking-widest text-blue-500 mb-1">Seller API *</label>
              <div class="grid grid-cols-2 gap-3">
                <input v-model="newShopGlobal.ozon_client_id" type="text" placeholder="Client ID"
                  class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
                <input v-model="newShopGlobal.ozon_client_secret" type="text" placeholder="API Key"
                  class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
              </div>
            </div>
            <div>
              <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">
                Performance API <span class="normal-case text-[#A3A3A3]">(необязательно)</span>
              </label>
              <div class="grid grid-cols-2 gap-3">
                <input v-model="newShopGlobal.ozon_performance_client_id" type="text" placeholder="Perf. Client ID"
                  class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
                <input v-model="newShopGlobal.ozon_performance_client_secret" type="text" placeholder="Perf. Client Secret"
                  class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
              </div>
            </div>
          </div>
        </template>
        <template v-else-if="newShopGlobal.marketplace === 'ym'">
          <div>
            <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Учётные данные *</label>
            <div class="grid grid-cols-3 gap-3">
              <input v-model="newShopGlobal.ym_client_id" type="text" placeholder="OAuth Токен / API Key"
                class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
              <input v-model="newShopGlobal.ym_client_secret" type="text" placeholder="Client Secret (опц.)"
                class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
              <input v-model="newShopGlobal.ym_campaign_id" type="text" placeholder="Campaign ID"
                class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
            </div>
          </div>
        </template>

        <div class="flex items-center gap-4 pt-1">
          <button @click="addShopGlobal" :disabled="!canAddShopGlobal"
            class="font-mono text-[10px] uppercase tracking-widest bg-[#D97706] text-white px-6 py-2 hover:bg-[#B45309] transition-all disabled:opacity-40">
            + Добавить магазин
          </button>
          <span v-if="addShopGlobalError" class="text-red-600 font-mono text-xs">{{ addShopGlobalError }}</span>
          <span v-if="addShopGlobalSuccess" class="text-green-700 font-mono text-xs">Магазин добавлен</span>
        </div>
      </div>
    </div>

    <!-- Shops table -->
    <div v-if="shopsLoading" class="text-center py-24 font-mono uppercase text-[10px] tracking-widest text-[#A3A3A3]">
      Загрузка магазинов...
    </div>
    <div v-else class="bg-white border border-[#E5E5E5] shadow-[4px_4px_0px_0px_rgba(0,0,0,0.03)] overflow-x-auto">
      <table class="w-full font-mono text-[11px]">
        <thead>
          <tr class="border-b border-[#E5E5E5] bg-[#FAFAFA]">
            <th class="text-left px-4 py-3 text-[10px] uppercase tracking-widest text-[#A3A3A3]">Магазин</th>
            <th class="text-left px-4 py-3 text-[10px] uppercase tracking-widest text-[#A3A3A3]">Пользователь</th>
            <th class="text-left px-4 py-3 text-[10px] uppercase tracking-widest text-[#A3A3A3]">Маркетплейс / Модель</th>
            <th class="text-left px-4 py-3 text-[10px] uppercase tracking-widest text-[#A3A3A3]">Синхронизация</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="allShops.length === 0">
            <td colspan="5" class="px-4 py-10 text-center text-[10px] text-[#A3A3A3] uppercase tracking-widest">
              Магазины не найдены
            </td>
          </tr>
          <tr v-for="shop in allShops" :key="shop.id" class="border-b border-[#F5F5F5] hover:bg-[#FDFCFB] transition-colors">
            <td class="px-4 py-3">
              <p class="font-bold text-[#1A1A1A]">{{ shop.name }}</p>
              <p class="text-[10px] text-[#C0C0C0] mt-0.5">{{ shop.id }}</p>
            </td>
            <td class="px-4 py-3">
              <p class="text-[#D97706]">{{ shop.user_email }}</p>
              <p class="text-[10px] text-[#A3A3A3]">{{ shop.fio || '—' }}</p>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2 flex-wrap">
                <div class="flex items-center gap-1.5">
                  <MpBadge :mp="shop.marketplace" :size="18" />
                  <span class="uppercase font-bold text-[#1A1A1A]">{{ shop.marketplace.toUpperCase() }}</span>
                </div>
                <template v-if="shop.fulfillment_models && shop.fulfillment_models.length">
                  <span v-for="fm in shop.fulfillment_models" :key="fm"
                    class="text-[10px] uppercase px-1.5 py-0.5 bg-[#F5F5F5] text-[#737373] border border-[#EBEBEB]">
                    {{ fm }}
                  </span>
                </template>
              </div>
            </td>
            <td class="px-4 py-3 text-[#A3A3A3]">{{ shop.last_synced_at || 'Никогда' }}</td>
            <td class="px-4 py-3 text-right">
              <button @click="deleteShopGlobal(shop.user_id, shop.id)"
                class="text-[10px] uppercase tracking-widest border border-red-300 text-red-400 px-3 py-1 hover:bg-red-500 hover:text-white hover:border-red-500 transition-all">
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
import { ref, reactive, computed, onMounted, h } from 'vue'
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
  if (newShopGlobal.marketplace === 'wb')   return !!newShopGlobal.wb_token
  if (newShopGlobal.marketplace === 'ozon') return !!(newShopGlobal.ozon_client_id && newShopGlobal.ozon_client_secret)
  if (newShopGlobal.marketplace === 'ym')   return !!(newShopGlobal.ym_client_id && newShopGlobal.ym_campaign_id)
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
