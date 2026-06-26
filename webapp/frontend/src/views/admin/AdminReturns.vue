<template>
  <div class="space-y-8">

    <!-- ── Page header ── -->
    <div class="border-b border-[#E5E5E5] pb-4 flex items-baseline gap-4">
      <h1 class="font-mono text-[17px] font-bold text-[#1A1A1A] uppercase tracking-[0.06em]">Возвраты</h1>
      <span class="font-mono text-[10px] text-[#A3A3A3] uppercase tracking-widest">/ база данных</span>
    </div>

    <!-- ════════════════════════════════════════════════ -->
    <!-- СЕКЦИЯ 1: СИНХРОНИЗАЦИЯ                         -->
    <!-- ════════════════════════════════════════════════ -->
    <div>
      <h2 class="font-mono text-[11px] font-medium uppercase tracking-widest text-[#737373] mb-3">
        Шаг 1 — Синхронизация с маркетплейсами
      </h2>

      <div class="bg-white border border-[#E5E5E5] overflow-x-auto shadow-[6px_6px_0px_0px_rgba(0,0,0,0.05)]">
        <div v-if="allShops.length === 0" class="px-6 py-8 text-center font-mono text-xs text-[#737373]">
          Нет подключённых магазинов
        </div>

        <table v-else class="w-full text-[11px] font-mono">
          <thead>
            <tr class="border-b-2 border-[#E5E5E5] bg-[#F5F5F0]">
              <th class="px-4 py-2 text-left font-bold uppercase tracking-wider text-[10px] whitespace-nowrap">Магазин</th>
              <th class="px-4 py-2 text-left font-bold uppercase tracking-wider text-[10px] whitespace-nowrap">Маркетплейс</th>
              <th class="px-4 py-2 text-left font-bold uppercase tracking-wider text-[10px] whitespace-nowrap">Пользователь</th>
              <th class="px-4 py-2 text-left font-bold uppercase tracking-wider text-[10px] whitespace-nowrap">Синхронизация</th>
              <th class="px-4 py-2 text-left font-bold uppercase tracking-wider text-[10px] whitespace-nowrap">Статус</th>
              <th class="px-4 py-2 text-left font-bold uppercase tracking-wider text-[10px] whitespace-nowrap">Действие</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="shop in allShops"
              :key="shop.id"
              class="border-b border-[#F0F0F0] hover:bg-[#FAFAF8] transition-colors"
            >
              <td class="px-4 py-2.5 font-bold text-[#1A1A1A]">{{ shop.name }}</td>
              <td class="px-4 py-2.5">
                <span class="px-2 py-0.5 border border-[#E5E5E5] font-black text-[10px] uppercase tracking-wider">
                  {{ shop.marketplace?.toUpperCase() }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-[#737373]">{{ shop.user_email || '—' }}</td>
              <td class="px-4 py-2.5 text-[#737373]">{{ fmtLastSync(shop.last_synced_at) }}</td>
              <td class="px-4 py-2.5">
                <span
                  v-if="syncState(shop.id).msg"
                  class="font-mono text-[10px]"
                  :class="syncState(shop.id).ok ? 'text-green-600' : 'text-red-600'"
                >{{ syncState(shop.id).msg }}</span>
              </td>
              <td class="px-4 py-2.5">
                <button
                  @click="syncShopRow(shop.id)"
                  :disabled="syncState(shop.id).syncing"
                  class="border-2 border-[#D97706] px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wider text-[#D97706] hover:bg-[#D97706] hover:text-white transition-all disabled:opacity-40 whitespace-nowrap inline-flex items-center justify-center min-w-[64px]"
                >{{ syncState(shop.id).syncing ? '...' : 'Синхр.' }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════ -->
    <!-- СЕКЦИЯ 2: ДАННЫЕ ИЗ БАЗЫ                        -->
    <!-- ════════════════════════════════════════════════ -->
    <div>
      <h2 class="font-mono text-[11px] font-medium uppercase tracking-widest text-[#737373] mb-3">
        Шаг 2 — Данные из базы
      </h2>

      <!-- Marketplace tabs -->
      <div class="flex gap-2 mb-3">
        <button
          v-for="mp in MARKETPLACE_LIST"
          :key="mp.value"
          @click="switchMarketplace(mp.value)"
          class="px-3 py-1.5 font-mono text-[11px] font-bold uppercase tracking-wider border-2 transition-all"
          :class="currentMp === mp.value
            ? 'border-[#E5E5E5] bg-[#1A1A1A] text-white'
            : 'border-[#E5E5E5] text-[#737373] hover:border-[#E5E5E5]'"
        >{{ mp.label }}</button>
      </div>

      <!-- Filter row -->
      <div class="bg-white border border-[#E5E5E5] px-3 py-3 mb-3 shadow-[6px_6px_0px_0px_rgba(0,0,0,0.05)]">
        <div class="flex flex-wrap gap-2 items-end">

          <!-- User -->
          <div class="flex flex-col gap-0.5">
            <label class="font-mono text-[9px] uppercase tracking-widest text-[#A3A3A3]">Пользователь</label>
            <select
              v-model="filters.userId"
              @change="filters.shopId = ''"
              class="border border-[#E5E5E5] px-2 py-1.5 font-mono text-[11px] focus:outline-none focus:border-[#D97706] bg-white min-w-[140px]"
            >
              <option value="">— все —</option>
              <option v-for="u in allUsers" :key="u.id" :value="u.id">{{ u.email }}</option>
            </select>
          </div>

          <!-- Shop -->
          <div class="flex flex-col gap-0.5">
            <label class="font-mono text-[9px] uppercase tracking-widest text-[#A3A3A3]">Магазин</label>
            <select
              v-model="filters.shopId"
              class="border border-[#E5E5E5] px-2 py-1.5 font-mono text-[11px] focus:outline-none focus:border-[#D97706] bg-white min-w-[140px]"
            >
              <option value="">— все —</option>
              <option v-for="s in filteredShops" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>

          <!-- Date from -->
          <div class="flex flex-col gap-0.5">
            <label class="font-mono text-[9px] uppercase tracking-widest text-[#A3A3A3]">Дата с</label>
            <input
              v-model="filters.dateFrom"
              type="date"
              lang="ru"
              class="border border-[#E5E5E5] px-2 py-1.5 font-mono text-[11px] focus:outline-none focus:border-[#D97706]"
            />
          </div>

          <!-- Date to -->
          <div class="flex flex-col gap-0.5">
            <label class="font-mono text-[9px] uppercase tracking-widest text-[#A3A3A3]">Дата по</label>
            <input
              v-model="filters.dateTo"
              type="date"
              lang="ru"
              class="border border-[#E5E5E5] px-2 py-1.5 font-mono text-[11px] focus:outline-none focus:border-[#D97706]"
            />
          </div>

          <!-- Reset -->
          <button
            @click="resetFilters"
            class="border border-[#E5E5E5] px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider text-[#737373] hover:border-[#E5E5E5] hover:text-[#1A1A1A] transition-all"
          >Сброс</button>

          <!-- Load from DB -->
          <button
            @click="loadReturns"
            :disabled="loading"
            class="border border-[#E5E5E5] px-4 py-1.5 font-mono text-[11px] uppercase tracking-wider font-bold bg-[#1A1A1A] text-white hover:bg-white hover:text-[#1A1A1A] transition-all disabled:opacity-40"
          >{{ loading ? 'Загрузка...' : 'Показать из БД' }}</button>

        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="border-2 border-red-400 bg-red-50 px-4 py-3 font-mono text-xs text-red-700 mb-3">
        {{ error }}
      </div>

      <!-- Table + column picker -->
      <div class="bg-white border border-[#E5E5E5] overflow-x-auto shadow-[6px_6px_0px_0px_rgba(0,0,0,0.05)]">

        <div v-if="loading && returns.length === 0" class="px-6 py-12 text-center font-mono text-xs text-[#737373]">
          Загрузка...
        </div>

        <div v-else-if="!dataLoaded" class="px-6 py-12 text-center font-mono text-xs text-[#737373]">
          Выберите фильтры и нажмите «Показать из БД»
        </div>

        <div v-else-if="returns.length === 0" class="px-6 py-12 text-center font-mono text-xs text-[#737373]">
          Нет данных для выбранных фильтров
        </div>

        <table v-else class="w-full text-[11px] font-mono">
          <thead>
            <tr class="border-b-2 border-[#E5E5E5] bg-[#F5F5F0]">
              <th
                v-for="col in activeCols"
                :key="col.key"
                v-show="isColVisible(col.key)"
                class="px-3 py-2 font-bold uppercase tracking-wider text-[10px] whitespace-nowrap"
                :class="col.align === 'right' ? 'text-right' : 'text-left'"
                :style="col.minWidth ? `min-width: ${col.minWidth}` : ''"
              >{{ col.label }}</th>
              <!-- Column picker lives in the header -->
              <th class="px-3 py-2 text-right w-0">
                <div class="relative inline-block">
                  <button
                    @click="showColPicker = !showColPicker"
                    class="border px-2 py-0.5 font-mono text-[9px] uppercase tracking-wider transition-all whitespace-nowrap"
                    :class="showColPicker
                      ? 'border-[#E5E5E5] bg-[#1A1A1A] text-white'
                      : 'border-[#D0D0D0] text-[#A3A3A3] hover:border-[#E5E5E5] hover:text-[#1A1A1A]'"
                  >⊞ Столбцы</button>
                  <div v-if="showColPicker" class="fixed inset-0 z-20" @click="showColPicker = false" />
                  <div
                    v-if="showColPicker"
                    class="absolute right-0 top-full mt-1 bg-white border border-[#E5E5E5] shadow-[4px_4px_0px_0px_rgba(0,0,0,0.08)] z-30 p-3 min-w-[180px]"
                  >
                    <p class="font-mono text-[9px] uppercase tracking-widest text-[#A3A3A3] mb-2">Показать столбцы</p>
                    <label
                      v-for="col in activeCols"
                      :key="col.key"
                      class="flex items-center gap-2 py-1 cursor-pointer font-mono text-[10px] text-[#737373] hover:text-[#1A1A1A] transition-colors"
                    >
                      <input
                        type="checkbox"
                        :checked="isColVisible(col.key)"
                        @change="toggleCol(col.key)"
                        class="accent-[#D97706]"
                      />
                      {{ col.label }}
                    </label>
                  </div>
                </div>
              </th>
            </tr>
          </thead>

          <tbody>
            <!-- WB -->
            <template v-if="currentMp === 'wb'">
              <tr
                v-for="row in returns"
                :key="row.id"
                class="border-b border-[#F0F0F0] hover:bg-[#FAFAF8] transition-colors"
              >
                <td v-show="isColVisible('srid')" class="px-3 py-1.5 text-[#1A1A1A]">{{ row.srid }}</td>
                <td v-show="isColVisible('order_dt')" class="px-3 py-1.5 text-[#737373]">{{ fmtDate(row.order_dt) }}</td>
                <td v-show="isColVisible('brand')" class="px-3 py-1.5 font-medium">{{ row.brand }}</td>
                <td v-show="isColVisible('subject_name')" class="px-3 py-1.5 max-w-[200px] truncate" :title="row.subject_name">{{ row.subject_name }}</td>
                <td v-show="isColVisible('status')" class="px-3 py-1.5">
                  <span class="px-1.5 py-0.5 bg-[#F5F5F0] border border-[#E5E5E5]">{{ row.status }}</span>
                </td>
                <td v-show="isColVisible('reason')" class="px-3 py-1.5 text-[#737373]">{{ row.reason }}</td>
                <td v-show="isColVisible('barcode')" class="px-3 py-1.5">{{ row.barcode }}</td>
                <td v-show="isColVisible('user_status')" class="px-3 py-1.5 text-[#D97706]">{{ row.user_status }}</td>
                <td v-show="isColVisible('comment')" class="px-3 py-1.5 text-[#737373] max-w-[160px] truncate" :title="row.user_comment">{{ row.user_comment }}</td>
                <td></td>
              </tr>
            </template>

            <!-- OZON -->
            <template v-else-if="currentMp === 'ozon'">
              <tr
                v-for="row in returns"
                :key="row.id"
                class="border-b border-[#F0F0F0] hover:bg-[#FAFAF8] transition-colors"
              >
                <td v-show="isColVisible('posting_number')" class="px-3 py-1.5 text-[#1A1A1A]">{{ row.posting_number }}</td>
                <td v-show="isColVisible('added_at')" class="px-3 py-1.5 text-[#737373]">{{ fmtDate(row.added_at) }}</td>
                <td v-show="isColVisible('offer_id')" class="px-3 py-1.5">{{ row.offer_id }}</td>
                <td v-show="isColVisible('status')" class="px-3 py-1.5">
                  <span class="px-1.5 py-0.5 bg-[#F5F5F0] border border-[#E5E5E5]">{{ row.status }}</span>
                </td>
                <td v-show="isColVisible('return_reason')" class="px-3 py-1.5 text-[#737373] max-w-[180px] truncate" :title="row.return_reason">{{ row.return_reason }}</td>
                <td v-show="isColVisible('price')" class="px-3 py-1.5 text-right tabular-nums">{{ fmtMoney(row.price) }}</td>
                <td v-show="isColVisible('user_status')" class="px-3 py-1.5 text-[#D97706]">{{ row.user_status }}</td>
                <td v-show="isColVisible('comment')" class="px-3 py-1.5 text-[#737373] max-w-[160px] truncate" :title="row.user_comment">{{ row.user_comment }}</td>
                <td></td>
              </tr>
            </template>

            <!-- YM -->
            <template v-else>
              <tr
                v-for="row in returns"
                :key="row.id"
                class="border-b border-[#F0F0F0] hover:bg-[#FAFAF8] transition-colors"
              >
                <td v-show="isColVisible('ym_return_id')" class="px-3 py-1.5 text-[#1A1A1A]">{{ row.ym_return_id }}</td>
                <td v-show="isColVisible('order_id')" class="px-3 py-1.5">{{ row.order_id }}</td>
                <td v-show="isColVisible('return_type')" class="px-3 py-1.5">{{ row.return_type }}</td>
                <td v-show="isColVisible('shipment_status')" class="px-3 py-1.5">
                  <span class="px-1.5 py-0.5 bg-[#F5F5F0] border border-[#E5E5E5]">{{ row.shipment_status }}</span>
                </td>
                <td v-show="isColVisible('refund_status')" class="px-3 py-1.5">{{ row.refund_status }}</td>
                <td v-show="isColVisible('amount')" class="px-3 py-1.5 text-right tabular-nums">{{ fmtMoney(row.amount) }}</td>
                <td v-show="isColVisible('user_status')" class="px-3 py-1.5 text-[#D97706]">{{ row.user_status }}</td>
                <td v-show="isColVisible('comment')" class="px-3 py-1.5 text-[#737373] max-w-[160px] truncate" :title="row.user_comment">{{ row.user_comment }}</td>
                <td></td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- Footer -->
      <div v-if="dataLoaded" class="flex items-center justify-between mt-3">
        <span class="font-mono text-[11px] text-[#A3A3A3]">
          {{ loading ? 'Загрузка...' : `${returns.length} записей` }}
        </span>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { supabase } from '../../lib/supabase'

const API = import.meta.env.VITE_API_URL

// ── Marketplace config ─────────────────────────────────────────────────────────

const MARKETPLACE_LIST = [
  { value: 'wb',   label: 'WB'   },
  { value: 'ozon', label: 'Ozon' },
  { value: 'ym',   label: 'ЯМ'   },
] as const

type Mp = 'wb' | 'ozon' | 'ym'

// ── Column definitions per marketplace ────────────────────────────────────────

interface ColDef {
  key: string
  label: string
  minWidth?: string
  align?: 'left' | 'right'
}

const MP_COLS: Record<string, ColDef[]> = {
  wb: [
    { key: 'srid',         label: 'SRID',          minWidth: '200px' },
    { key: 'order_dt',     label: 'Дата заказа' },
    { key: 'brand',        label: 'Бренд',          minWidth: '160px' },
    { key: 'subject_name', label: 'Товар' },
    { key: 'status',       label: 'Статус',         minWidth: '160px' },
    { key: 'reason',       label: 'Причина' },
    { key: 'barcode',      label: 'Штрихкод' },
    { key: 'user_status',  label: 'Мой статус',     minWidth: '130px' },
    { key: 'comment',      label: 'Комментарий' },
  ],
  ozon: [
    { key: 'posting_number', label: 'Номер отправления', minWidth: '190px' },
    { key: 'added_at',       label: 'Добавлен' },
    { key: 'offer_id',       label: 'Артикул' },
    { key: 'status',         label: 'Статус' },
    { key: 'return_reason',  label: 'Причина возврата',  minWidth: '180px' },
    { key: 'price',          label: 'Цена',               align: 'right' },
    { key: 'user_status',    label: 'Мой статус',         minWidth: '130px' },
    { key: 'comment',        label: 'Комментарий' },
  ],
  ym: [
    { key: 'ym_return_id',    label: 'ID возврата' },
    { key: 'order_id',        label: 'Заказ' },
    { key: 'return_type',     label: 'Тип' },
    { key: 'shipment_status', label: 'Статус отправки' },
    { key: 'refund_status',   label: 'Статус возврата' },
    { key: 'amount',          label: 'Сумма', align: 'right' },
    { key: 'user_status',     label: 'Мой статус', minWidth: '130px' },
    { key: 'comment',         label: 'Комментарий' },
  ],
}

// ── Column visibility ──────────────────────────────────────────────────────────

const hiddenCols = reactive<Set<string>>(new Set())
const showColPicker = ref(false)

const activeCols = computed<ColDef[]>(() => MP_COLS[currentMp.value] ?? [])

function colId(key: string) { return `${currentMp.value}:${key}` }
function isColVisible(key: string) { return !hiddenCols.has(colId(key)) }
function toggleCol(key: string) {
  const id = colId(key)
  if (hiddenCols.has(id)) hiddenCols.delete(id)
  else hiddenCols.add(id)
}

// ── Shared state ───────────────────────────────────────────────────────────────

const allShops = ref<any[]>([])
const allUsers = ref<any[]>([])

// ── Section 1: per-shop sync ───────────────────────────────────────────────────

interface ShopSyncState { syncing: boolean; msg: string; ok: boolean }
const syncingShops = reactive<Record<string, ShopSyncState>>({})

function syncState(shopId: string): ShopSyncState {
  if (!syncingShops[shopId]) syncingShops[shopId] = { syncing: false, msg: '', ok: false }
  return syncingShops[shopId]
}

async function syncShopRow(shopId: string) {
  const state = syncState(shopId)
  if (state.syncing) return
  state.syncing = true; state.msg = ''; state.ok = false
  try {
    const headers = await authHeaders()
    const res = await axios.post(`${API}/api/admin/sync/${shopId}`, {}, { headers })
    const d = res.data
    if (d.error) {
      state.msg = `Ошибка ${d.status_code ?? ''}: ${String(d.error).slice(0, 100)}`
      state.ok = false
    } else {
      state.msg = `В БД: ${d.db_before ?? '?'} / API: ${d.api_fetched ?? '?'} / Новых: ${d.added ?? 0} / Обн: ${d.updated ?? 0}`
      state.ok = true
    }
    const shop = allShops.value.find(s => s.id === shopId)
    if (shop) shop.last_synced_at = new Date().toISOString()
  } catch (e: any) {
    state.msg = `Ошибка: ${e?.response?.data?.detail ?? (e as Error).message}`
    state.ok = false
  } finally {
    state.syncing = false
  }
}

// ── Section 2: data view ───────────────────────────────────────────────────────

const currentMp  = ref<Mp>('wb')
const returns    = ref<any[]>([])
const loading    = ref(false)
const error      = ref('')
const dataLoaded = ref(false)

const filters = reactive({ userId: '', shopId: '', dateFrom: '', dateTo: '' })

const filteredShops = computed(() =>
  allShops.value.filter(s =>
    s.marketplace === currentMp.value && (!filters.userId || s.user_id === filters.userId)
  )
)

async function authHeaders() {
  const { data: { session } } = await supabase.auth.getSession()
  return { Authorization: `Bearer ${session?.access_token}` }
}

function defaultDates() {
  const to = new Date(); const from = new Date()
  from.setDate(from.getDate() - 30)
  filters.dateTo   = to.toISOString().slice(0, 10)
  filters.dateFrom = from.toISOString().slice(0, 10)
}

function fmtLastSync(iso: string | null | undefined): string {
  if (!iso) return 'Никогда'
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function fmtDate(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso.slice(0, 10)
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function fmtMoney(val: number | string | null | undefined): string {
  if (val == null || val === '') return '—'
  const n = Number(val)
  if (isNaN(n)) return String(val)
  return n.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function fetchAll(url: string, headers: any, params: Record<string, any>): Promise<any[]> {
  const CHUNK = 500
  const all: any[] = []
  let off = 0
  while (true) {
    const res = await axios.get<any[]>(url, { headers, params: { ...params, limit: CHUNK, offset: off } })
    all.push(...res.data)
    if (res.data.length < CHUNK) break
    off += res.data.length
  }
  return all
}

async function loadReturns() {
  error.value = ''; returns.value = []; loading.value = true; dataLoaded.value = false
  const headers = await authHeaders()
  const params: Record<string, string> = {}
  if (filters.userId)   params.user_id   = filters.userId
  if (filters.shopId)   params.shop_id   = filters.shopId
  if (filters.dateFrom) params.date_from = filters.dateFrom
  if (filters.dateTo)   params.date_to   = filters.dateTo

  try {
    returns.value = await fetchAll(`${API}/api/admin/${currentMp.value}/returns`, headers, params)
    dataLoaded.value = true
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Ошибка загрузки данных'
  } finally {
    loading.value = false
  }
}

function switchMarketplace(mp: Mp) {
  currentMp.value = mp
  filters.userId = ''; filters.shopId = ''
  returns.value = []; error.value = ''; dataLoaded.value = false
}

function resetFilters() {
  filters.userId = ''; filters.shopId = ''
  defaultDates()
}

onMounted(async () => {
  defaultDates()
  try {
    const headers = await authHeaders()
    const [shopsRes, usersRes] = await Promise.all([
      axios.get(`${API}/api/admin/shops`, { headers }),
      axios.get(`${API}/api/admin/users`, { headers }),
    ])
    allShops.value = shopsRes.data
    allUsers.value = usersRes.data
  } catch {
    // non-fatal
  }
})
</script>
