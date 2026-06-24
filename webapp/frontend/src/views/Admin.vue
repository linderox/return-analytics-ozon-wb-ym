<template>
  <div class="space-y-8">
    <div class="border-b border-[#1A1A1A] pb-4">
      <h1 class="text-4xl font-black uppercase tracking-tighter text-[#D97706]">Панель администратора</h1>
      <p class="text-[#737373] font-mono text-xs mt-1">УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ И МАГАЗИНАМИ СИСТЕМЫ</p>
    </div>

    <!-- Tabs -->
    <div class="flex gap-0 border-b border-[#1A1A1A]">
      <button v-for="tab in tabs" :key="tab.id"
        @click="activeTab = tab.id"
        :class="[
          'px-6 py-2 font-mono text-[11px] uppercase tracking-widest transition-all',
          activeTab === tab.id
            ? 'bg-[#1A1A1A] text-white'
            : 'text-[#737373] hover:text-[#1A1A1A]'
        ]">
        {{ tab.label }}
      </button>
    </div>

    <!-- ══ TAB: USERS ══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'users'" class="space-y-8">

      <!-- Create user form -->
      <div class="bg-white border-2 border-[#1A1A1A] p-6 shadow-[10px_10px_0px_0px_rgba(0,0,0,0.05)]">
        <h2 class="text-lg font-black uppercase tracking-tight mb-6">Создать пользователя</h2>
        <form @submit.prevent="createUser" class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Email *</label>
            <input v-model="newUser.email" type="email" required
              class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-sm focus:outline-none focus:border-[#D97706]" />
          </div>
          <div>
            <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Пароль *</label>
            <input v-model="newUser.password" type="password" required minlength="6"
              class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-sm focus:outline-none focus:border-[#D97706]" />
          </div>
          <div>
            <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">ФИО</label>
            <input v-model="newUser.fio" type="text"
              class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-sm focus:outline-none focus:border-[#D97706]" />
          </div>
          <div>
            <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Тариф</label>
            <select v-model="newUser.plan"
              class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-sm focus:outline-none focus:border-[#D97706] bg-white">
              <option value="free">Free</option>
              <option value="basic">Basic</option>
              <option value="pro">Pro</option>
            </select>
          </div>
          <div class="sm:col-span-2 flex items-center gap-4">
            <button type="submit" :disabled="creatingUser"
              class="font-mono text-[10px] uppercase tracking-widest bg-[#D97706] text-white px-6 py-2 hover:bg-[#B45309] transition-all disabled:opacity-50">
              {{ creatingUser ? 'Создание...' : 'Создать пользователя' }}
            </button>
            <span v-if="createError" class="text-red-600 font-mono text-xs">{{ createError }}</span>
            <span v-if="createSuccess" class="text-green-700 font-mono text-xs">Пользователь создан</span>
          </div>
        </form>
      </div>

      <!-- Users table -->
      <div v-if="usersLoading" class="text-center py-24 font-mono uppercase text-[10px] tracking-widest text-[#737373]">
        Загрузка пользователей...
      </div>
      <div v-else class="bg-white border-2 border-[#1A1A1A] shadow-[10px_10px_0px_0px_rgba(0,0,0,0.05)] overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b-2 border-[#1A1A1A] bg-[#FAFAFA]">
              <th class="text-left px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-[#737373]">ФИО / Email</th>
              <th class="text-left px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-[#737373]">ID</th>
              <th class="text-left px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-[#737373]">Тариф</th>
              <th class="text-left px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-[#737373]">Магазинов</th>
              <th class="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id" class="border-b border-[#F0F0F0] hover:bg-[#FDFCFB]">
              <td class="px-4 py-3">
                <p class="font-bold text-sm">{{ user.fio || '—' }}</p>
                <p class="font-mono text-[11px] text-[#D97706]">{{ user.email }}</p>
              </td>
              <td class="px-4 py-3 font-mono text-[10px] text-[#A3A3A3]">{{ user.id }}</td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-1">
                  <select v-model="planUpdates[user.id]"
                    class="border border-[#D1D5DB] px-2 py-1 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-white">
                    <option value="free">Free</option>
                    <option value="basic">Basic</option>
                    <option value="pro">Pro</option>
                  </select>
                  <button @click="updatePlan(user.id)"
                    :disabled="planUpdates[user.id] === user.plan"
                    class="text-[10px] font-mono uppercase border border-[#1A1A1A] px-2 py-1 hover:bg-[#1A1A1A] hover:text-white transition-all disabled:opacity-30">
                    ✓
                  </button>
                  <span v-if="planSuccess[user.id]" class="text-[10px] font-mono text-green-700 ml-1">✓</span>
                </div>
              </td>
              <td class="px-4 py-3 font-bold text-center">{{ user.shop_count }}</td>
              <td class="px-4 py-3"></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ══ TAB: SHOPS ══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'shops'" class="space-y-8">

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
              <select v-model="newShopGlobal.marketplace"
                class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-white">
                <option value="wb">Wildberries</option>
                <option value="ozon">Ozon</option>
                <option value="ym">Яндекс Маркет</option>
              </select>
            </div>
          </div>

          <template v-if="newShopGlobal.marketplace === 'wb'">
            <input v-model="newShopGlobal.wb_token" type="text" placeholder="WB Токен"
              class="w-full border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
          </template>
          <template v-else-if="newShopGlobal.marketplace === 'ozon'">
            <div class="grid grid-cols-2 gap-3">
              <input v-model="newShopGlobal.ozon_client_id" type="text" placeholder="Client ID"
                class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
              <input v-model="newShopGlobal.ozon_client_secret" type="text" placeholder="Client Secret"
                class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
            </div>
          </template>
          <template v-else-if="newShopGlobal.marketplace === 'ym'">
            <div class="grid grid-cols-3 gap-3">
              <input v-model="newShopGlobal.ym_client_id" type="text" placeholder="Client ID"
                class="border border-[#D1D5DB] px-3 py-2 font-mono text-xs focus:outline-none focus:border-[#D97706]" />
              <input v-model="newShopGlobal.ym_client_secret" type="text" placeholder="Client Secret"
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
              <th class="text-left px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-[#737373]">Маркетплейс</th>
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
                <span class="font-mono text-[11px] uppercase font-bold px-2 py-0.5 border"
                  :class="{
                    'border-[#D97706] text-[#D97706]': shop.marketplace === 'wb',
                    'border-blue-500 text-blue-600': shop.marketplace === 'ozon',
                    'border-purple-500 text-purple-600': shop.marketplace === 'ym',
                  }">{{ shop.marketplace }}</span>
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

    <!-- ══ TAB: TOKENS ══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'tokens'" class="space-y-4">
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { supabase } from '../lib/supabase'

const tabs = [
  { id: 'users', label: 'Пользователи' },
  { id: 'shops', label: 'Магазины' },
  { id: 'tokens', label: 'Токены' },
]
const activeTab = ref('users')

const users = ref<any[]>([])
const usersLoading = ref(true)
const allShops = ref<any[]>([])
const shopsLoading = ref(true)

type CredForm = {
  wb_token?: string
  ozon_client_id?: string
  ozon_client_secret?: string
  ym_client_id?: string
  ym_client_secret?: string
  ym_campaign_id?: string
}

const credUpdates = reactive<Record<string, CredForm>>({})
const credSuccess = reactive<Record<string, boolean>>({})
const credError = reactive<Record<string, string>>({})
const planUpdates = reactive<Record<string, string>>({})
const planSuccess = reactive<Record<string, boolean>>({})

const newUser = reactive({ email: '', password: '', fio: '', plan: 'free' })
const creatingUser = ref(false)
const createError = ref('')
const createSuccess = ref(false)

const newShopGlobal = reactive({
  userId: '',
  name: '',
  marketplace: 'wb',
  wb_token: '',
  ozon_client_id: '',
  ozon_client_secret: '',
  ym_client_id: '',
  ym_client_secret: '',
  ym_campaign_id: '',
})
const addShopGlobalError = ref('')
const addShopGlobalSuccess = ref(false)

const canAddShopGlobal = computed(() => {
  if (!newShopGlobal.userId || !newShopGlobal.name) return false
  if (newShopGlobal.marketplace === 'wb') return !!newShopGlobal.wb_token
  if (newShopGlobal.marketplace === 'ozon') return !!(newShopGlobal.ozon_client_id || newShopGlobal.ozon_client_secret)
  if (newShopGlobal.marketplace === 'ym') return !!(newShopGlobal.ym_client_id || newShopGlobal.ym_client_secret || newShopGlobal.ym_campaign_id)
  return false
})

function emptyCredForm(): CredForm {
  return { wb_token: '', ozon_client_id: '', ozon_client_secret: '', ym_client_id: '', ym_client_secret: '', ym_campaign_id: '' }
}

async function authHeaders() {
  const { data: { session } } = await supabase.auth.getSession()
  return { Authorization: `Bearer ${session?.access_token}` }
}

const fetchUsers = async () => {
  try {
    const headers = await authHeaders()
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/admin/users`, { headers })
    users.value = response.data
    response.data.forEach((u: any) => {
      if (!planUpdates[u.id]) planUpdates[u.id] = u.plan
    })
  } catch (e) {
    console.error('Admin fetch users error', e)
  } finally {
    usersLoading.value = false
  }
}

const fetchShops = async () => {
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

const createUser = async () => {
  creatingUser.value = true
  createError.value = ''
  createSuccess.value = false
  try {
    const headers = await authHeaders()
    await axios.post(`${import.meta.env.VITE_API_URL}/api/admin/users/create`, {
      email: newUser.email,
      password: newUser.password,
      fio: newUser.fio || null,
      plan: newUser.plan,
    }, { headers })
    createSuccess.value = true
    Object.assign(newUser, { email: '', password: '', fio: '', plan: 'free' })
    await fetchUsers()
  } catch (e: any) {
    createError.value = e?.response?.data?.detail || 'Ошибка создания пользователя'
  } finally {
    creatingUser.value = false
  }
}

const updatePlan = async (userId: string) => {
  try {
    const headers = await authHeaders()
    await axios.patch(`${import.meta.env.VITE_API_URL}/api/admin/user/${userId}/plan`, { plan: planUpdates[userId] }, { headers })
    const u = users.value.find(u => u.id === userId)
    if (u) u.plan = planUpdates[userId]
    planSuccess[userId] = true
    setTimeout(() => { planSuccess[userId] = false }, 2000)
  } catch (e) {
    console.error('Update plan error', e)
  }
}

const addShopGlobal = async () => {
  addShopGlobalError.value = ''
  addShopGlobalSuccess.value = false
  try {
    const headers = await authHeaders()
    const payload: Record<string, string> = { name: newShopGlobal.name, marketplace: newShopGlobal.marketplace }
    if (newShopGlobal.marketplace === 'wb') { payload.wb_token = newShopGlobal.wb_token }
    else if (newShopGlobal.marketplace === 'ozon') { payload.ozon_client_id = newShopGlobal.ozon_client_id; payload.ozon_client_secret = newShopGlobal.ozon_client_secret }
    else if (newShopGlobal.marketplace === 'ym') { payload.ym_client_id = newShopGlobal.ym_client_id; payload.ym_client_secret = newShopGlobal.ym_client_secret; payload.ym_campaign_id = newShopGlobal.ym_campaign_id }

    await axios.post(`${import.meta.env.VITE_API_URL}/api/admin/user/${newShopGlobal.userId}/shops`, payload, { headers })
    addShopGlobalSuccess.value = true
    Object.assign(newShopGlobal, { userId: '', name: '', marketplace: 'wb', wb_token: '', ozon_client_id: '', ozon_client_secret: '', ym_client_id: '', ym_client_secret: '', ym_campaign_id: '' })
    await fetchShops()
    setTimeout(() => { addShopGlobalSuccess.value = false }, 2000)
  } catch (e: any) {
    addShopGlobalError.value = e?.response?.data?.detail || 'Ошибка добавления магазина'
  }
}

const deleteShopGlobal = async (userId: string, shopId: string) => {
  if (!confirm('Удалить магазин?')) return
  try {
    const headers = await authHeaders()
    await axios.delete(`${import.meta.env.VITE_API_URL}/api/admin/user/${userId}/shops/${shopId}`, { headers })
    allShops.value = allShops.value.filter(s => s.id !== shopId)
  } catch (e) {
    console.error('Delete shop error', e)
  }
}

const updateCredentials = async (userId: string, shopId: string) => {
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

onMounted(async () => {
  await Promise.all([fetchUsers(), fetchShops()])
})
</script>
