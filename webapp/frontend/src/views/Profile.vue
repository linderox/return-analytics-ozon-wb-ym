<template>
  <div class="space-y-8">
    <div class="border-b border-[#1A1A1A] pb-4">
      <h1 class="text-4xl font-black uppercase tracking-tighter">Профиль</h1>
      <p class="text-[#737373] font-mono text-xs mt-1">НАСТРОЙКИ АККАУНТА</p>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-24">
      <div class="w-8 h-8 border-2 border-[#D97706] border-t-transparent rounded-full animate-spin"></div>
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Left: account info + shops -->
      <div class="lg:col-span-2 space-y-6">

        <!-- Account card -->
        <div class="bg-white border-2 border-[#1A1A1A] p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,0.05)]">
          <div class="flex justify-between items-start mb-6">
            <h2 class="text-sm font-black uppercase tracking-tight">Личные данные</h2>
            <button v-if="!editing" @click="startEdit"
              class="font-mono text-[10px] uppercase tracking-widest border border-[#1A1A1A] px-3 py-1 hover:bg-[#1A1A1A] hover:text-white transition-all">
              Редактировать
            </button>
          </div>
          <div class="space-y-4">
            <div>
              <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Email</label>
              <p class="font-mono text-sm text-[#1A1A1A]">{{ authStore.user?.email }}</p>
            </div>
            <div>
              <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">ФИО</label>
              <input v-if="editing" v-model="editForm.fio" type="text"
                class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-sm focus:outline-none focus:border-[#D97706]"
                placeholder="Иванов Иван Иванович" />
              <p v-else class="font-mono text-sm">{{ profile?.fio || '—' }}</p>
            </div>
            <div>
              <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Телефон</label>
              <input v-if="editing" v-model="editForm.phone" type="tel"
                class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-sm focus:outline-none focus:border-[#D97706]"
                placeholder="+7 900 000-00-00" />
              <p v-else class="font-mono text-sm">{{ profile?.phone || '—' }}</p>
            </div>
            <div v-if="editing" class="flex items-center gap-3 pt-2">
              <button @click="saveProfile" :disabled="saving"
                class="font-mono text-[10px] uppercase tracking-widest bg-[#D97706] text-white px-6 py-2 hover:bg-[#B45309] transition-all disabled:opacity-50">
                {{ saving ? 'Сохранение...' : 'Сохранить' }}
              </button>
              <button @click="cancelEdit"
                class="font-mono text-[10px] uppercase tracking-widest border border-[#1A1A1A] px-4 py-2 hover:bg-[#F5F5F5] transition-all">
                Отмена
              </button>
              <span v-if="saveError" class="text-red-600 font-mono text-xs">{{ saveError }}</span>
            </div>
            <div v-if="saveSuccess" class="text-green-700 font-mono text-xs">Данные сохранены</div>
          </div>
        </div>

        <!-- Shops card -->
        <div class="bg-white border-2 border-[#1A1A1A] shadow-[8px_8px_0px_0px_rgba(0,0,0,0.05)]">
          <div class="px-6 py-4 border-b border-[#E5E5E5] flex items-center justify-between">
            <div>
              <h2 class="text-sm font-black uppercase tracking-tight">Мои магазины</h2>
              <p class="text-[10px] font-mono text-[#737373] mt-0.5">{{ shops.length }} {{ pluralShops(shops.length) }}</p>
            </div>
            <button @click="openAddModal"
              class="font-mono text-[10px] uppercase tracking-widest bg-[#D97706] text-white px-4 py-2 hover:bg-[#B45309] transition-all">
              + Добавить
            </button>
          </div>

          <div v-if="shopsLoading" class="flex items-center justify-center py-12">
            <div class="w-5 h-5 border-2 border-[#D97706] border-t-transparent rounded-full animate-spin"></div>
          </div>

          <div v-else-if="shops.length === 0" class="px-6 py-16 text-center">
            <p class="font-mono text-[10px] text-[#A3A3A3] uppercase tracking-widest mb-4">Нет подключённых магазинов</p>
            <button @click="openAddModal"
              class="font-mono text-[10px] uppercase tracking-widest border border-[#D97706] text-[#D97706] px-4 py-2 hover:bg-[#FBF0D3] transition-all">
              Подключить первый магазин
            </button>
          </div>

          <div v-else class="divide-y divide-[#F0F0F0]">
            <div v-for="shop in shops" :key="shop.id" class="px-6 py-4 flex items-center gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap mb-1">
                  <p class="font-bold text-sm">{{ shop.name }}</p>
                  <span :style="mpLogoStyle(shop.marketplace, 18)">{{ mpLabel(shop.marketplace) === 'Ozon' ? 'O' : mpLabel(shop.marketplace) }}</span>
                  <span class="font-mono text-[10px] uppercase font-bold">{{ mpLabel(shop.marketplace) }}</span>
                  <template v-if="shop.fulfillment_models && shop.fulfillment_models.length">
                    <span v-for="fm in shop.fulfillment_models" :key="fm"
                      class="font-mono text-[10px] uppercase px-2 py-0.5 bg-[#F5F5F5] text-[#737373] border border-[#E5E5E5]">
                      {{ fm }}
                    </span>
                  </template>
                </div>
                <p class="font-mono text-[10px] text-[#A3A3A3]">
                  Синхронизация: {{ shop.last_synced_at ? formatDate(shop.last_synced_at) : 'Никогда' }}
                </p>
              </div>
              <button @click="deleteShop(shop.id)"
                class="flex-shrink-0 font-mono text-[10px] uppercase tracking-widest border border-red-300 text-red-400 px-3 py-1.5 hover:bg-red-500 hover:text-white hover:border-red-500 transition-all">
                Удалить
              </button>
            </div>
          </div>
        </div>

      </div>

      <!-- Right: plan & status -->
      <div class="space-y-6">
        <div class="bg-white border-2 border-[#1A1A1A] p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,0.05)]">
          <h2 class="text-sm font-black uppercase tracking-tight mb-4">Тариф</h2>
          <div class="flex items-center gap-3">
            <span class="font-mono text-xl font-black uppercase">{{ profile?.plan || 'free' }}</span>
            <span class="font-mono text-[10px] uppercase tracking-widest bg-[#FBF0D3] text-[#D97706] px-2 py-0.5">Активен</span>
          </div>
          <RouterLink to="/billing"
            class="mt-4 block w-full text-center font-mono text-[10px] uppercase tracking-widest border border-[#1A1A1A] py-2 hover:bg-[#1A1A1A] hover:text-white transition-all">
            Изменить тариф
          </RouterLink>
        </div>

        <div class="bg-white border-2 border-[#1A1A1A] p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,0.05)]">
          <h2 class="text-sm font-black uppercase tracking-tight mb-4">Аккаунт</h2>
          <div class="space-y-2">
            <div class="flex justify-between items-center">
              <span class="font-mono text-[10px] text-[#737373] uppercase tracking-wider">Магазинов</span>
              <span class="font-bold">{{ shops.length }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="font-mono text-[10px] text-[#737373] uppercase tracking-wider">Статус</span>
              <span class="font-mono text-[10px] text-green-700 uppercase">Активен</span>
            </div>
          </div>
          <button @click="authStore.logout()"
            class="mt-6 w-full font-mono text-[10px] uppercase tracking-widest border border-red-400 text-red-500 py-2 hover:bg-red-500 hover:text-white transition-all">
            Выйти из аккаунта
          </button>
        </div>
      </div>

    </div>
  </div>

  <!-- Add Shop Modal -->
  <Teleport to="body">
    <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/60" @click="closeAddModal"></div>
      <div class="relative bg-white border-2 border-[#1A1A1A] w-full max-w-lg shadow-[12px_12px_0px_0px_rgba(0,0,0,0.15)] max-h-[90vh] flex flex-col">

        <!-- Modal header -->
        <div class="flex items-center justify-between px-6 py-4 border-b-2 border-[#1A1A1A]">
          <div>
            <h3 class="font-black uppercase text-sm tracking-tight">Добавить магазин</h3>
            <p class="font-mono text-[10px] text-[#737373] mt-0.5">Шаг {{ addStep }} из 3</p>
          </div>
          <button @click="closeAddModal" class="text-[#737373] hover:text-[#1A1A1A] font-bold text-lg leading-none">✕</button>
        </div>

        <!-- Step progress bar -->
        <div class="flex gap-1 px-6 pt-3">
          <div v-for="n in 3" :key="n" class="h-1 flex-1 transition-all duration-300"
            :class="n <= addStep ? 'bg-[#D97706]' : 'bg-[#E5E5E5]'"></div>
        </div>

        <!-- Modal body -->
        <div class="overflow-y-auto flex-1 px-6 py-5 space-y-5">

          <!-- ── Step 1: Маркетплейс, название, модель работы ── -->
          <template v-if="addStep === 1">
            <div>
              <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-2">Маркетплейс *</label>
              <div class="grid grid-cols-3 gap-3">
                <button v-for="mp in MARKETPLACES" :key="mp.value"
                  @click="selectMarketplace(mp.value)"
                  class="border-2 py-4 text-center transition-all font-mono text-xs font-black uppercase tracking-wider flex flex-col items-center gap-2"
                  :class="addForm.marketplace === mp.value
                    ? 'border-[#1A1A1A] bg-[#1A1A1A] text-white'
                    : 'border-[#E5E5E5] hover:border-[#1A1A1A] text-[#1A1A1A]'">
                  <span :style="mpLogoStyle(mp.value, 28)">{{ mp.label === 'Ozon' ? 'O' : mp.label }}</span>
                  {{ mp.label }}
                </button>
              </div>
            </div>

            <div>
              <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Название магазина *</label>
              <input v-model="addForm.name" type="text"
                class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-sm focus:outline-none focus:border-[#D97706]"
                placeholder="Мой магазин" />
            </div>

            <div v-if="fulfillmentOptions.length">
              <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-2">
                Модель работы * <span class="text-[#A3A3A3] normal-case">(можно выбрать несколько)</span>
              </label>
              <div class="grid grid-cols-2 gap-3">
                <label v-for="fm in fulfillmentOptions" :key="fm.value"
                  class="flex items-start gap-2 border-2 p-3 cursor-pointer transition-all"
                  :class="addForm.fulfillment_models.includes(fm.value)
                    ? 'border-[#D97706] bg-[#FBF0D3]'
                    : 'border-[#E5E5E5] hover:border-[#D97706]'">
                  <input type="checkbox" :value="fm.value" v-model="addForm.fulfillment_models"
                    class="mt-0.5 accent-[#D97706]" />
                  <div>
                    <p class="font-mono text-sm font-black uppercase">{{ fm.value }}</p>
                    <p class="font-mono text-[10px] text-[#737373] mt-0.5">{{ fm.desc }}</p>
                  </div>
                </label>
              </div>
            </div>
          </template>

          <!-- ── Step 2: API Ключи ── -->
          <template v-if="addStep === 2">

            <!-- WB -->
            <template v-if="addForm.marketplace === 'wb'">
              <div>
                <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">
                  API Токен *
                </label>
                <input v-model="addForm.wb_token" type="password" autocomplete="off"
                  class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]"
                  placeholder="eyJhbGci..." />
                <p class="font-mono text-[10px] text-[#A3A3A3] mt-1">
                  Личный кабинет WB → Настройки → Доступ к API
                </p>
              </div>
            </template>

            <!-- Ozon -->
            <template v-else-if="addForm.marketplace === 'ozon'">
              <div class="border border-blue-200 bg-blue-50 p-4 space-y-3">
                <p class="font-mono text-[10px] font-black uppercase tracking-widest text-blue-700">Seller API *</p>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Client ID</label>
                    <input v-model="addForm.ozon_client_id" type="text" autocomplete="off"
                      class="w-full border border-[#D1D5DB] bg-white px-3 py-2 font-mono text-xs focus:outline-none focus:border-blue-400"
                      placeholder="123456" />
                  </div>
                  <div>
                    <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">API Key</label>
                    <input v-model="addForm.ozon_client_secret" type="password" autocomplete="off"
                      class="w-full border border-[#D1D5DB] bg-white px-3 py-2 font-mono text-xs focus:outline-none focus:border-blue-400"
                      placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
                  </div>
                </div>
                <p class="font-mono text-[10px] text-blue-500">Личный кабинет Ozon → Настройки → API ключи</p>
              </div>

              <div class="border border-[#E5E5E5] p-4 space-y-3">
                <div class="flex items-center gap-2">
                  <p class="font-mono text-[10px] font-black uppercase tracking-widest text-[#737373]">Performance API</p>
                  <span class="font-mono text-[10px] text-[#A3A3A3] border border-[#E5E5E5] px-2 py-0.5">необязательно</span>
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Client ID</label>
                    <input v-model="addForm.ozon_performance_client_id" type="text" autocomplete="off"
                      class="w-full border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]"
                      placeholder="p-123456" />
                  </div>
                  <div>
                    <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Client Secret</label>
                    <input v-model="addForm.ozon_performance_client_secret" type="password" autocomplete="off"
                      class="w-full border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]"
                      placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" />
                  </div>
                </div>
              </div>
            </template>

            <!-- YM -->
            <template v-else-if="addForm.marketplace === 'ym'">
              <div class="space-y-3">
                <div>
                  <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">
                    OAuth Токен / API Ключ *
                  </label>
                  <input v-model="addForm.ym_client_id" type="password" autocomplete="off"
                    class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]"
                    placeholder="AQAAAAAB..." />
                  <p class="font-mono text-[10px] text-[#A3A3A3] mt-1">
                    Яндекс.OAuth → выдать токен для приложения партнёра
                  </p>
                </div>
                <div>
                  <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">
                    ID кампании (бизнеса) *
                  </label>
                  <input v-model="addForm.ym_campaign_id" type="text" autocomplete="off"
                    class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]"
                    placeholder="12345678" />
                  <p class="font-mono text-[10px] text-[#A3A3A3] mt-1">
                    Личный кабинет Яндекс.Маркет → URL кабинета содержит ID
                  </p>
                </div>
                <div>
                  <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">
                    Client Secret <span class="text-[#A3A3A3]">(необязательно)</span>
                  </label>
                  <input v-model="addForm.ym_client_secret" type="password" autocomplete="off"
                    class="w-full border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]"
                    placeholder="для автообновления токена" />
                </div>
              </div>
            </template>

          </template>

          <!-- ── Step 3: Фильтры ── -->
          <template v-if="addStep === 3">
            <div>
              <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">
                Фильтр статусов возвратов <span class="text-[#A3A3A3]">(необязательно)</span>
              </label>
              <p class="font-mono text-[10px] text-[#A3A3A3] mb-3">
                Если не выбрано — синхронизируются все статусы
              </p>
              <div class="grid grid-cols-2 gap-2">
                <label v-for="s in statusOptions" :key="s.value"
                  class="flex items-center gap-2 cursor-pointer p-2 border border-[#E5E5E5] hover:border-[#D97706] hover:bg-[#FFFBF0] transition-all">
                  <input type="checkbox" :value="s.value" v-model="addForm.status_filter"
                    class="w-3 h-3 accent-[#D97706]" />
                  <span class="font-mono text-[10px]">{{ s.label }}</span>
                </label>
              </div>
            </div>
          </template>

        </div>

        <!-- Modal footer -->
        <div class="px-6 py-4 border-t border-[#E5E5E5] flex items-center justify-between">
          <button v-if="addStep > 1" @click="addStep--"
            class="font-mono text-[10px] uppercase tracking-widest border border-[#1A1A1A] px-4 py-2 hover:bg-[#F5F5F5] transition-all">
            ← Назад
          </button>
          <div v-else></div>

          <div class="flex items-center gap-3">
            <span v-if="addError" class="font-mono text-[10px] text-red-500 max-w-[200px] text-right">{{ addError }}</span>
            <button v-if="addStep < 3" @click="nextStep" :disabled="!canProceed"
              class="font-mono text-[10px] uppercase tracking-widest bg-[#D97706] text-white px-6 py-2 hover:bg-[#B45309] transition-all disabled:opacity-40 disabled:cursor-not-allowed">
              Далее →
            </button>
            <button v-else @click="submitShop" :disabled="addLoading"
              class="font-mono text-[10px] uppercase tracking-widest bg-[#1A1A1A] text-white px-6 py-2 hover:bg-[#333] transition-all disabled:opacity-40">
              {{ addLoading ? 'Сохранение...' : 'Сохранить магазин' }}
            </button>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import axios from 'axios'
import { supabase } from '../lib/supabase'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const loading = ref(true)
const shopsLoading = ref(true)
const profile = ref<any>(null)
const shops = ref<any[]>([])
const editing = ref(false)
const saving = ref(false)
const saveError = ref('')
const saveSuccess = ref(false)
const editForm = reactive({ fio: '', phone: '' })

const showAddModal = ref(false)
const addStep = ref(1)
const addLoading = ref(false)
const addError = ref('')

const EMPTY_FORM = {
  name: '',
  marketplace: '',
  fulfillment_models: [] as string[],
  wb_token: '',
  ozon_client_id: '',
  ozon_client_secret: '',
  ozon_performance_client_id: '',
  ozon_performance_client_secret: '',
  ym_client_id: '',
  ym_client_secret: '',
  ym_campaign_id: '',
  status_filter: [] as string[],
}

const addForm = reactive({ ...EMPTY_FORM })

const MARKETPLACES = [
  { value: 'wb',   label: 'WB',   bg: '#CB11AB', color: '#fff'     },
  { value: 'ozon', label: 'Ozon', bg: '#005BFF', color: '#fff'     },
  { value: 'ym',   label: 'ЯМ',   bg: '#FFCC00', color: '#1A1A1A' },
]

function mpLogoStyle(mp: string, size = 24) {
  const map: Record<string, { bg: string; color: string }> = {
    wb:   { bg: '#CB11AB', color: '#fff'    },
    ozon: { bg: '#005BFF', color: '#fff'    },
    ym:   { bg: '#FFCC00', color: '#1A1A1A' },
  }
  const c = map[mp] ?? { bg: '#ccc', color: '#333' }
  return `display:inline-flex;align-items:center;justify-content:center;width:${size}px;height:${size}px;background:${c.bg};color:${c.color};font-size:${Math.round(size * 0.42)}px;font-weight:900;font-family:monospace;flex-shrink:0;`
}

const FULFILLMENT_OPTIONS: Record<string, { value: string; desc: string }[]> = {
  wb: [
    { value: 'FBS', desc: 'Продажа со своего склада' },
    { value: 'FBW', desc: 'Склад Wildberries' },
  ],
  ozon: [
    { value: 'FBS', desc: 'Продажа со своего склада' },
    { value: 'FBO', desc: 'Склад Ozon' },
  ],
  ym: [
    { value: 'FBS', desc: 'Продажа со своего склада' },
    { value: 'FBY', desc: 'Склад Яндекса' },
  ],
}

const STATUS_OPTIONS: Record<string, { value: string; label: string }[]> = {
  wb: [
    { value: 'Waiting', label: 'Ожидание' },
    { value: 'ReadyForPickup', label: 'Готов к выдаче' },
    { value: 'Accepted', label: 'Принят WB' },
    { value: 'Cancelled', label: 'Отменён' },
    { value: 'Defect', label: 'Дефект' },
    { value: 'RealDefect', label: 'Подтверждённый дефект' },
  ],
  ozon: [
    { value: 'waiting_for_seller', label: 'Ожидает продавца' },
    { value: 'accepted_from_customer', label: 'Принят от покупателя' },
    { value: 'returned_to_seller', label: 'Возвращён продавцу' },
    { value: 'cancelled', label: 'Отменён' },
  ],
  ym: [
    { value: 'CREATED', label: 'Создан' },
    { value: 'IN_TRANSIT', label: 'В доставке' },
    { value: 'DELIVERED', label: 'Доставлен' },
    { value: 'RECEIVED_RETURN', label: 'Возврат получен' },
    { value: 'CANCELLED', label: 'Отменён' },
  ],
}

const fulfillmentOptions = computed(() => FULFILLMENT_OPTIONS[addForm.marketplace] ?? [])
const statusOptions = computed(() => STATUS_OPTIONS[addForm.marketplace] ?? [])

const canProceed = computed(() => {
  if (addStep.value === 1) {
    return !!addForm.marketplace && !!addForm.name.trim() && addForm.fulfillment_models.length > 0
  }
  if (addStep.value === 2) {
    if (addForm.marketplace === 'wb') return !!addForm.wb_token.trim()
    if (addForm.marketplace === 'ozon') return !!(addForm.ozon_client_id.trim() && addForm.ozon_client_secret.trim())
    if (addForm.marketplace === 'ym') return !!(addForm.ym_client_id.trim() && addForm.ym_campaign_id.trim())
  }
  return true
})

async function authHeaders() {
  const { data: { session } } = await supabase.auth.getSession()
  return { Authorization: `Bearer ${session?.access_token}` }
}

async function fetchProfile() {
  try {
    const headers = await authHeaders()
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/profile`, { headers })
    profile.value = res.data
  } catch (e) {
    console.error('Profile fetch error', e)
  } finally {
    loading.value = false
  }
}

async function fetchShops() {
  shopsLoading.value = true
  try {
    const headers = await authHeaders()
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/shops/`, { headers })
    shops.value = res.data
  } catch (e) {
    console.error('Shops fetch error', e)
  } finally {
    shopsLoading.value = false
  }
}

function startEdit() {
  editForm.fio = profile.value?.fio || ''
  editForm.phone = profile.value?.phone || ''
  editing.value = true
  saveSuccess.value = false
  saveError.value = ''
}

function cancelEdit() {
  editing.value = false
  saveError.value = ''
}

async function saveProfile() {
  saving.value = true
  saveError.value = ''
  try {
    const headers = await authHeaders()
    const res = await axios.patch(
      `${import.meta.env.VITE_API_URL}/api/profile`,
      { fio: editForm.fio || null, phone: editForm.phone || null },
      { headers },
    )
    profile.value = res.data
    editing.value = false
    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 3000)
  } catch (e: any) {
    saveError.value = e?.response?.data?.detail || 'Ошибка сохранения'
  } finally {
    saving.value = false
  }
}

function openAddModal() {
  Object.assign(addForm, { ...EMPTY_FORM, fulfillment_models: [], status_filter: [] })
  addStep.value = 1
  addError.value = ''
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
}

function selectMarketplace(mp: string) {
  addForm.marketplace = mp
  addForm.fulfillment_models = []
  addForm.status_filter = []
}

function nextStep() {
  if (!canProceed.value) return
  addError.value = ''
  addStep.value++
}

async function submitShop() {
  addLoading.value = true
  addError.value = ''
  try {
    const headers = await authHeaders()
    const payload: Record<string, any> = {
      name: addForm.name.trim(),
      marketplace: addForm.marketplace,
      ...(addForm.fulfillment_models.length ? { fulfillment_models: addForm.fulfillment_models } : {}),
    }

    if (addForm.marketplace === 'wb') {
      payload.wb_token = addForm.wb_token
    } else if (addForm.marketplace === 'ozon') {
      payload.ozon_client_id = addForm.ozon_client_id
      payload.ozon_client_secret = addForm.ozon_client_secret
      if (addForm.ozon_performance_client_id) payload.ozon_performance_client_id = addForm.ozon_performance_client_id
      if (addForm.ozon_performance_client_secret) payload.ozon_performance_client_secret = addForm.ozon_performance_client_secret
    } else if (addForm.marketplace === 'ym') {
      payload.ym_client_id = addForm.ym_client_id
      payload.ym_campaign_id = addForm.ym_campaign_id
      if (addForm.ym_client_secret) payload.ym_client_secret = addForm.ym_client_secret
    }

    if (addForm.status_filter.length) payload.status_filter = addForm.status_filter

    await axios.post(`${import.meta.env.VITE_API_URL}/api/shops/`, payload, { headers })
    await fetchShops()
    closeAddModal()
  } catch (e: any) {
    addError.value = e?.response?.data?.detail || 'Ошибка при добавлении магазина'
  } finally {
    addLoading.value = false
  }
}

async function deleteShop(shopId: string) {
  if (!confirm('Удалить магазин? Это действие необратимо.')) return
  try {
    const headers = await authHeaders()
    await axios.delete(`${import.meta.env.VITE_API_URL}/api/shops/${shopId}`, { headers })
    shops.value = shops.value.filter(s => s.id !== shopId)
  } catch (e: any) {
    alert(e?.response?.data?.detail || 'Ошибка при удалении магазина')
  }
}

function mpLabel(mp: string) {
  const map: Record<string, string> = { wb: 'WB', ozon: 'Ozon', ym: 'ЯМ' }
  return map[mp] ?? mp.toUpperCase()
}

function formatDate(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleString('ru-RU', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return dateStr
  }
}

function pluralShops(n: number) {
  if (n % 10 === 1 && n % 100 !== 11) return 'магазин'
  if ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100)) return 'магазина'
  return 'магазинов'
}

onMounted(async () => {
  await Promise.all([fetchProfile(), fetchShops()])
})
</script>
