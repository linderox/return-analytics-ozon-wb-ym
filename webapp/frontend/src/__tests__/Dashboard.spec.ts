import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Dashboard from '../views/Dashboard.vue'

// Minimal mock for dependencies
vi.mock('../lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn(() => Promise.resolve({ data: { session: null } })),
    },
  },
}))

describe('Dashboard.vue', () => {
  it('renders correctly', () => {
    const wrapper = mount(Dashboard)
    expect(wrapper.text()).toContain('Аналитика возвратов')
  })

  it('shows loading state initially', () => {
    const wrapper = mount(Dashboard)
    // We expect loading state by default if no data
    expect(wrapper.html()).toContain('Загрузка данных')
  })
})
