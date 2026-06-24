<template>
  <div class="space-y-8">
    <div class="border-b border-[#1A1A1A] pb-4">
      <h1 class="text-4xl font-black uppercase tracking-tighter text-[#D97706]">Пользователи</h1>
      <p class="text-[#737373] font-mono text-xs mt-1">УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ СИСТЕМЫ</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- Create user with password -->
      <div class="bg-white border-2 border-[#1A1A1A] p-6 shadow-[10px_10px_0px_0px_rgba(0,0,0,0.05)]">
        <h2 class="text-lg font-black uppercase tracking-tight mb-1">Создать пользователя</h2>
        <p class="font-mono text-[10px] text-[#737373] mb-6">С паролем — аккаунт сразу активен</p>
        <form @submit.prevent="createUser" class="space-y-3">
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
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
          </div>
          <div class="flex items-center gap-4 pt-1">
            <button type="submit" :disabled="creatingUser"
              class="font-mono text-[10px] uppercase tracking-widest bg-[#D97706] text-white px-6 py-2 hover:bg-[#B45309] transition-all disabled:opacity-50">
              {{ creatingUser ? 'Создание...' : 'Создать пользователя' }}
            </button>
            <span v-if="createError" class="text-red-600 font-mono text-xs">{{ createError }}</span>
            <span v-if="createSuccess" class="text-green-700 font-mono text-xs">Пользователь создан</span>
          </div>
        </form>
      </div>

      <!-- Invite user — generate link -->
      <div class="bg-white border-2 border-[#1A1A1A] p-6 shadow-[10px_10px_0px_0px_rgba(0,0,0,0.05)]">
        <h2 class="text-lg font-black uppercase tracking-tight mb-1">Пригласить по ссылке</h2>
        <p class="font-mono text-[10px] text-[#737373] mb-6">Пользователь сам задаст пароль — email не отправляется</p>
        <form @submit.prevent="generateInvite" class="space-y-3">
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Email *</label>
              <input v-model="inviteForm.email" type="email" required
                class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-sm focus:outline-none focus:border-[#D97706]" />
            </div>
            <div>
              <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">Тариф</label>
              <select v-model="inviteForm.plan"
                class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-sm focus:outline-none focus:border-[#D97706] bg-white">
                <option value="free">Free</option>
                <option value="basic">Basic</option>
                <option value="pro">Pro</option>
              </select>
            </div>
            <div class="sm:col-span-2">
              <label class="block text-[10px] font-mono uppercase tracking-widest text-[#737373] mb-1">ФИО</label>
              <input v-model="inviteForm.fio" type="text"
                class="w-full border-2 border-[#1A1A1A] px-3 py-2 font-mono text-sm focus:outline-none focus:border-[#D97706]" />
            </div>
          </div>
          <div class="flex items-center gap-4 pt-1">
            <button type="submit" :disabled="inviting"
              class="font-mono text-[10px] uppercase tracking-widest bg-[#1A1A1A] text-white px-6 py-2 hover:bg-[#333] transition-all disabled:opacity-50">
              {{ inviting ? 'Генерация...' : 'Сгенерировать ссылку' }}
            </button>
            <span v-if="inviteError" class="text-red-600 font-mono text-xs">{{ inviteError }}</span>
          </div>
        </form>

        <!-- Generated invite link -->
        <div v-if="inviteLink" class="mt-4 border-2 border-[#D97706] bg-[#FFFBF0] p-4 space-y-2">
          <p class="font-mono text-[10px] uppercase tracking-widest text-[#D97706] font-bold">Ссылка для подтверждения аккаунта</p>
          <p class="font-mono text-[10px] text-[#737373]">Отправьте эту ссылку пользователю. Действует ограниченное время.</p>
          <div class="flex items-center gap-2 mt-2">
            <input :value="inviteLink" readonly
              class="flex-1 border border-[#D97706] px-3 py-2 font-mono text-[10px] bg-white focus:outline-none text-[#1A1A1A] truncate" />
            <button @click="copyInviteLink"
              class="font-mono text-[10px] uppercase tracking-widest border-2 border-[#D97706] text-[#D97706] px-4 py-2 hover:bg-[#D97706] hover:text-white transition-all whitespace-nowrap">
              {{ copied ? '✓ Скопировано' : 'Копировать' }}
            </button>
          </div>
        </div>
      </div>

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
          <tr v-for="u in users" :key="u.id" class="border-b border-[#F0F0F0] hover:bg-[#FDFCFB]">
            <td class="px-4 py-3">
              <p class="font-bold text-sm">{{ u.fio || '—' }}</p>
              <p class="font-mono text-[11px] text-[#D97706]">{{ u.email }}</p>
            </td>
            <td class="px-4 py-3 font-mono text-[10px] text-[#A3A3A3]">{{ u.id }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-1">
                <select v-model="planUpdates[u.id]"
                  class="border border-[#D1D5DB] px-2 py-1 font-mono text-xs focus:outline-none focus:border-[#D97706] bg-white">
                  <option value="free">Free</option>
                  <option value="basic">Basic</option>
                  <option value="pro">Pro</option>
                </select>
                <button @click="updatePlan(u.id)"
                  :disabled="planUpdates[u.id] === u.plan"
                  class="text-[10px] font-mono uppercase border border-[#1A1A1A] px-2 py-1 hover:bg-[#1A1A1A] hover:text-white transition-all disabled:opacity-30">
                  ✓
                </button>
                <span v-if="planSuccess[u.id]" class="text-[10px] font-mono text-green-700 ml-1">✓</span>
              </div>
            </td>
            <td class="px-4 py-3 font-bold text-center">{{ u.shop_count }}</td>
            <td class="px-4 py-3"></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { supabase } from '../../lib/supabase'

const users = ref<any[]>([])
const usersLoading = ref(true)
const planUpdates = reactive<Record<string, string>>({})
const planSuccess = reactive<Record<string, boolean>>({})
const newUser = reactive({ email: '', password: '', fio: '', plan: 'free' })
const creatingUser = ref(false)
const createError = ref('')
const createSuccess = ref(false)

const inviteForm = reactive({ email: '', fio: '', plan: 'free' })
const inviting = ref(false)
const inviteError = ref('')
const inviteLink = ref('')
const copied = ref(false)

async function authHeaders() {
  const { data: { session } } = await supabase.auth.getSession()
  return { Authorization: `Bearer ${session?.access_token}` }
}

async function fetchUsers() {
  usersLoading.value = true
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

async function createUser() {
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

async function generateInvite() {
  inviting.value = true
  inviteError.value = ''
  inviteLink.value = ''
  copied.value = false
  try {
    const headers = await authHeaders()
    const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/admin/users/invite`, {
      email: inviteForm.email,
      fio: inviteForm.fio || null,
      plan: inviteForm.plan,
    }, { headers })
    inviteLink.value = res.data.action_link || ''
    Object.assign(inviteForm, { email: '', fio: '', plan: 'free' })
    await fetchUsers()
  } catch (e: any) {
    inviteError.value = e?.response?.data?.detail || 'Ошибка генерации ссылки'
  } finally {
    inviting.value = false
  }
}

async function copyInviteLink() {
  try {
    await navigator.clipboard.writeText(inviteLink.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 3000)
  } catch {
    // fallback — select the input text manually
  }
}

async function updatePlan(userId: string) {
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

onMounted(fetchUsers)
</script>
