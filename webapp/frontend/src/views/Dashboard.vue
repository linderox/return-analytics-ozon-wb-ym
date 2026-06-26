<template>
  <div class="space-y-6">
    <!-- Header + marketplace tabs -->
    <div class="flex justify-between items-end border-b border-[#E5E5E5] pb-4">
      <div>
        <h1 class="text-4xl font-black uppercase tracking-tighter">Аналитика возвратов</h1>
        <p class="text-[#737373] font-mono text-xs mt-1">ОБНОВЛЕНИЕ: {{ lastUpdate }}</p>
      </div>
      <div class="flex gap-2 p-1 bg-[#F5F5F5] rounded-sm">
        <button
          v-for="mp in marketplaces"
          :key="mp"
          @click="switchMp(mp)"
          :class="['px-6 py-1.5 text-[10px] font-mono uppercase tracking-widest transition-all', currentMp === mp ? 'bg-white shadow-sm text-[#D97706] font-bold' : 'text-[#737373] hover:text-[#1A1A1A]']"
        >
          {{ mp }}
        </button>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="flex flex-wrap gap-2 items-center bg-[#FAFAFA] border border-[#E5E5E5] p-3">
      <select
        v-model="filters.shopId"
        class="border border-[#E5E5E5] px-3 py-1.5 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-white min-w-[160px]"
      >
        <option value="">Все магазины</option>
        <option v-for="shop in shopsForMp" :key="shop.id" :value="shop.id">{{ shop.name }}</option>
      </select>

      <input
        v-model="skuInput"
        placeholder="SKU / артикул..."
        class="border border-[#E5E5E5] px-3 py-1.5 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-white min-w-[160px]"
      />

      <input
        type="date"
        v-model="filters.dateFrom"
        class="border border-[#E5E5E5] px-3 py-1.5 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-white"
      />
      <span class="font-mono text-[10px] text-[#A3A3A3]">—</span>
      <input
        type="date"
        v-model="filters.dateTo"
        class="border border-[#E5E5E5] px-3 py-1.5 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-white"
      />

      <select
        v-model="filters.status"
        class="border border-[#E5E5E5] px-3 py-1.5 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-white min-w-[160px]"
      >
        <option value="">Все статусы</option>
        <option v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
      </select>

      <button
        @click="resetFilters"
        class="border border-[#E5E5E5] px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest hover:border-[#E5E5E5] transition-all"
      >
        Сбросить
      </button>

      <span class="ml-auto font-mono text-[10px] text-[#A3A3A3]" v-if="returns.length">
        {{ returns.length }} записей
      </span>
    </div>

    <!-- Loading -->
    <div v-if="loading && returns.length === 0" class="flex flex-col items-center justify-center py-24 space-y-4">
      <div class="w-8 h-8 border-2 border-[#D97706] border-t-transparent rounded-full animate-spin"></div>
      <p class="font-mono text-[10px] uppercase tracking-widest text-[#737373]">Загрузка данных...</p>
    </div>

    <!-- Error -->
    <div v-else-if="fetchError" class="flex flex-col items-center justify-center py-24 border-2 border-dashed border-[#FCA5A5] bg-[#FFF5F5]">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#F87171" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-4"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <p class="font-mono text-[10px] uppercase tracking-widest text-[#EF4444] mb-1">Ошибка загрузки</p>
      <p class="font-mono text-[10px] text-[#A3A3A3]">{{ fetchError }}</p>
    </div>

    <!-- Empty -->
    <div v-else-if="returns.length === 0" class="flex flex-col items-center justify-center py-24 border-2 border-dashed border-[#E5E5E5] bg-white">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#D4D4D4" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-4"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
      <p class="font-mono text-[10px] uppercase tracking-widest text-[#A3A3A3]">Данных нет — добавьте магазин и запустите синхронизацию</p>
    </div>

    <!-- Table -->
    <div v-else class="bg-white border border-[#E5E5E5] overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-[#FBF0D3]/50 border-b border-[#E5E5E5]">
              <th
                v-for="col in columns[currentMp]"
                :key="col"
                class="py-4 px-4 font-mono text-[10px] uppercase tracking-widest text-[#737373] font-normal whitespace-nowrap"
              >
                {{ translateHeader(col) }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[#F5F5F5]">
            <tr
              v-for="row in returns"
              :key="row.id"
              class="hover:bg-[#FDFCFB] transition-colors group"
            >
              <td
                v-for="col in columns[currentMp]"
                :key="col"
                class="py-3 px-4 text-sm"
                :class="col === 'user_comment' ? 'min-w-[180px]' : ''"
              >
                <!-- Editable: user_status -->
                <template v-if="col === 'user_status'">
                  <input
                    v-if="editing?.rowId === row.id && editing?.field === 'user_status'"
                    :ref="el => focusIfEditing(el, row.id, 'user_status')"
                    :value="row.user_status || ''"
                    @blur="saveEdit(row, 'user_status', ($event.target as HTMLInputElement).value)"
                    @keydown.enter="($event.target as HTMLInputElement).blur()"
                    @keydown.escape="editing = null"
                    class="w-full border border-[#D97706] px-2 py-0.5 font-mono text-xs focus:outline-none bg-[#FFFBF0]"
                  />
                  <span
                    v-else
                    @click="editing = { rowId: row.id, field: 'user_status' }"
                    class="cursor-pointer font-mono text-xs px-2 py-0.5 rounded-sm block min-w-[80px]"
                    :class="row.user_status ? 'bg-[#FBF0D3] text-[#92400E]' : 'text-[#D4D4D4] hover:text-[#A3A3A3]'"
                  >
                    {{ row.user_status || '+ статус' }}
                  </span>
                </template>

                <!-- Editable: user_comment -->
                <template v-else-if="col === 'user_comment'">
                  <textarea
                    v-if="editing?.rowId === row.id && editing?.field === 'user_comment'"
                    :ref="el => focusIfEditing(el, row.id, 'user_comment')"
                    :value="row.user_comment || ''"
                    rows="2"
                    @blur="saveEdit(row, 'user_comment', ($event.target as HTMLTextAreaElement).value)"
                    @keydown.escape="editing = null"
                    class="w-full border border-[#D97706] px-2 py-1 font-mono text-xs focus:outline-none bg-[#FFFBF0] resize-none"
                  />
                  <span
                    v-else
                    @click="editing = { rowId: row.id, field: 'user_comment' }"
                    class="cursor-pointer font-mono text-xs block min-w-[120px] whitespace-pre-wrap"
                    :class="row.user_comment ? 'text-[#1A1A1A]' : 'text-[#D4D4D4] hover:text-[#A3A3A3]'"
                  >
                    {{ row.user_comment || '+ комментарий' }}
                  </span>
                </template>

                <!-- Status badge -->
                <template v-else-if="col === 'status' || col === 'shipment_status' || col === 'refund_status'">
                  <span class="bg-[#F5F5F5] px-2 py-0.5 rounded-sm font-mono text-xs whitespace-nowrap">
                    {{ row[col] || '—' }}
                  </span>
                </template>

                <!-- Price / amount -->
                <template v-else-if="col === 'price' || col === 'amount'">
                  <span class="font-mono text-xs">
                    {{ row[col] != null ? Number(row[col]).toLocaleString('ru-RU') : '—' }}
                  </span>
                </template>

                <!-- Default -->
                <template v-else>
                  <span class="font-mono text-xs">{{ row[col] ?? '—' }}</span>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Load more -->
    <div v-if="hasMore" class="flex justify-center pt-2">
      <button
        @click="loadMore"
        :disabled="loading"
        class="border border-[#E5E5E5] px-6 py-2 font-mono text-[10px] uppercase tracking-widest hover:bg-[#1A1A1A] hover:text-white transition-all disabled:opacity-40"
      >
        {{ loading ? 'Загрузка...' : 'Загрузить ещё' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { supabase } from '../lib/supabase'
import { useRouter } from 'vue-router'

const router = useRouter()
const marketplaces = ['ozon', 'wb', 'ym']
const currentMp = ref('ozon')
const returns = ref<any[]>([])
const shops = ref<any[]>([])
const loading = ref(false)
const fetchError = ref('')
const lastUpdate = ref(new Date().toLocaleString('ru-RU'))
const offset = ref(0)
const PAGE_SIZE = 200
const hasMore = ref(false)

const editing = ref<{ rowId: string; field: string } | null>(null)

const filters = reactive({
  shopId:   '',
  dateFrom: '',
  dateTo:   '',
  status:   '',
  sku:      '',
})
const skuInput = ref('')

let skuDebounce: ReturnType<typeof setTimeout> | null = null
watch(skuInput, val => {
  if (skuDebounce) clearTimeout(skuDebounce)
  skuDebounce = setTimeout(() => {
    filters.sku = val
  }, 400)
})

const shopsForMp = computed(() => shops.value.filter(s => s.marketplace === currentMp.value))

const STATUS_OPTIONS: Record<string, { value: string; label: string }[]> = {
  wb: [
    { value: 'Waiting',      label: 'Ожидание' },
    { value: 'ReadyForPickup', label: 'Готов к выдаче' },
    { value: 'Accepted',     label: 'Принят WB' },
    { value: 'Cancelled',    label: 'Отменён' },
    { value: 'Defect',       label: 'Дефект' },
    { value: 'RealDefect',   label: 'Подтверждённый дефект' },
  ],
  ozon: [
    { value: 'waiting_for_seller',   label: 'Ожидает продавца' },
    { value: 'accepted_from_customer', label: 'Принят от покупателя' },
    { value: 'returned_to_seller',   label: 'Возвращён продавцу' },
    { value: 'cancelled',            label: 'Отменён' },
  ],
  ym: [
    { value: 'CREATED',          label: 'Создан' },
    { value: 'IN_TRANSIT',       label: 'В доставке' },
    { value: 'DELIVERED',        label: 'Доставлен' },
    { value: 'RECEIVED_RETURN',  label: 'Возврат получен' },
    { value: 'CANCELLED',        label: 'Отменён' },
  ],
}
const statusOptions = computed(() => STATUS_OPTIONS[currentMp.value] ?? [])

const columns: Record<string, string[]> = {
  wb:   ['srid', 'order_dt', 'brand', 'subject_name', 'status', 'reason', 'barcode', 'user_status', 'user_comment'],
  ozon: ['posting_number', 'added_at', 'offer_id', 'status', 'return_reason', 'price', 'user_status', 'user_comment'],
  ym:   ['ym_return_id', 'order_id', 'return_type', 'shipment_status', 'refund_status', 'amount', 'user_status', 'user_comment'],
}

const headerTranslations: Record<string, string> = {
  srid:           'ID Возврата',
  order_dt:       'Дата заказа',
  brand:          'Бренд',
  subject_name:   'Категория',
  status:         'Статус',
  reason:         'Причина',
  barcode:        'Штрихкод',
  posting_number: 'Номер отправления',
  added_at:       'Добавлено',
  offer_id:       'Артикул',
  return_reason:  'Причина возврата',
  price:          'Цена',
  ym_return_id:   'ID Возврата',
  order_id:       'ID Заказа',
  return_type:    'Тип',
  shipment_status:'Статус доставки',
  refund_status:  'Статус возврата',
  amount:         'Сумма',
  user_status:    'Мой статус',
  user_comment:   'Комментарий',
}

const translateHeader = (col: string) => headerTranslations[col] || col

async function authHeaders() {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) {
    router.push('/login')
    return null
  }
  return { Authorization: `Bearer ${session.access_token}` }
}

async function fetchShops() {
  const headers = await authHeaders()
  if (!headers) return
  try {
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/shops/`, { headers })
    shops.value = res.data
  } catch {
    // shops unavailable — filter bar will just be empty
  }
}

async function fetchReturns(append = false) {
  const headers = await authHeaders()
  if (!headers) return

  if (!append) {
    offset.value = 0
    returns.value = []
  }

  loading.value = true
  fetchError.value = ''

  const params: Record<string, string> = {
    limit:  String(PAGE_SIZE),
    offset: String(offset.value),
  }
  if (filters.shopId)   params.shop_id   = filters.shopId
  if (filters.dateFrom) params.date_from = filters.dateFrom
  if (filters.dateTo)   params.date_to   = filters.dateTo
  if (filters.status)   params.status    = filters.status
  if (filters.sku)      params.sku       = filters.sku

  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_URL}/api/returns/${currentMp.value}`,
      { headers, params }
    )
    const data: any[] = response.data
    if (append) {
      returns.value.push(...data)
    } else {
      returns.value = data
    }
    hasMore.value = data.length === PAGE_SIZE
    lastUpdate.value = new Date().toLocaleString('ru-RU')
  } catch (error: any) {
    const status = error?.response?.status
    if (status === 401 || status === 403) {
      await supabase.auth.signOut()
      router.push('/login')
      return
    }
    fetchError.value = error?.response?.data?.detail || 'Не удалось подключиться к серверу'
    returns.value = []
  } finally {
    loading.value = false
  }
}

function switchMp(mp: string) {
  currentMp.value = mp
  filters.status = ''
  filters.sku = ''
  skuInput.value = ''
  filters.shopId = ''
  editing.value = null
}

function resetFilters() {
  filters.shopId   = ''
  filters.dateFrom = ''
  filters.dateTo   = ''
  filters.status   = ''
  filters.sku      = ''
  skuInput.value   = ''
}

async function loadMore() {
  offset.value += PAGE_SIZE
  await fetchReturns(true)
}

async function saveEdit(row: any, field: string, value: string) {
  editing.value = null
  const trimmed = value.trim()
  const prev = row[field]
  if (trimmed === (prev ?? '')) return

  row[field] = trimmed || null
  try {
    const headers = await authHeaders()
    if (!headers) return
    await axios.patch(
      `${import.meta.env.VITE_API_URL}/api/returns/${currentMp.value}/${row.id}`,
      { [field]: trimmed || null },
      { headers }
    )
  } catch {
    row[field] = prev
  }
}

function focusIfEditing(el: any, rowId: string, field: string) {
  if (el && editing.value?.rowId === rowId && editing.value?.field === field) {
    el.focus?.()
  }
}

// Re-fetch when filters change (except SKU which is debounced separately via skuInput watcher)
watch(
  () => [filters.shopId, filters.dateFrom, filters.dateTo, filters.status, filters.sku],
  () => fetchReturns()
)
watch(currentMp, () => fetchReturns())

onMounted(async () => {
  await fetchShops()
  await fetchReturns()
})
</script>
