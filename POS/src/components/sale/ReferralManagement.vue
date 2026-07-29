<template>
  <div class="flex flex-1 overflow-hidden">

    <!-- LEFT SIDE: Referral Code List -->
    <div class="w-80 flex-shrink-0 border-e bg-gray-50 flex flex-col">

      <!-- Search + filter -->
      <div class="p-4 bg-white border-b flex flex-col gap-3">
        <FormControl
          type="text"
          v-model="searchQuery"
          :placeholder="__('Search referral codes...')"
          size="sm"
        />
        <div class="flex gap-2">
          <button
            v-for="f in statusFilters"
            :key="f.value"
            @click="statusFilter = f.value"
            :class="['px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
              statusFilter === f.value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200']"
          >{{ __(f.label) }}</button>
        </div>
      </div>

      <!-- New Referral button (shown only if user has create permission) -->
      <div class="p-3 bg-white border-b">
        <button v-if="props.permissions?.create !== false" @click="startCreate"
          class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          {{ __("New Referral Code") }}
        </button>
        <div v-else class="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700 text-center">
          {{ __("View only — contact your manager to create referral codes") }}
        </div>
      </div>

      <!-- List -->
      <div class="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
        <div v-if="listLoading" class="flex justify-center py-8">
          <LoadingIndicator class="w-6 h-6" />
        </div>
        <div v-else-if="filteredReferrals.length === 0" class="text-center py-8 text-gray-500 text-sm">
          {{ __("No referral codes found") }}
        </div>
        <button
          v-for="ref in filteredReferrals"
          :key="ref.name"
          @click="selectReferral(ref)"
          :class="['w-full text-start p-3 rounded-lg border transition-all',
            selectedReferral?.name === ref.name
              ? 'bg-blue-50 border-blue-200'
              : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50']"
        >
          <div class="flex items-center justify-between mb-1">
            <span class="text-sm font-semibold text-gray-900 truncate">{{ ref.customer_name || ref.customer }}</span>
            <span :class="['text-[10px] font-semibold px-1.5 py-0.5 rounded-full',
              ref.disabled ? 'bg-gray-100 text-gray-500' : 'bg-green-100 text-green-700']">
              {{ ref.disabled ? __('Disabled') : __('Active') }}
            </span>
          </div>
          <div class="flex items-center gap-1.5">
            <code class="text-xs font-mono bg-gray-100 px-1.5 py-0.5 rounded text-gray-700">{{ ref.referral_code }}</code>
            <span class="text-xs text-gray-400">·</span>
            <span class="text-xs text-gray-500">{{ ref.referrals_count || 0 }} {{ __('uses') }}</span>
          </div>
        </button>
      </div>
    </div>

    <!-- RIGHT SIDE: Detail / Create -->
    <div class="flex-1 overflow-y-auto bg-white">

      <!-- Empty state -->
      <div v-if="!selectedReferral && !isCreating" class="flex flex-col items-center justify-center h-full text-center p-8">
        <svg class="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
        </svg>
        <p class="text-gray-500 font-medium">{{ __("Select a referral code or create a new one") }}</p>
      </div>

      <!-- CREATE FORM -->
      <div v-if="isCreating" class="p-6 max-w-xl mx-auto flex flex-col gap-5">
        <div class="flex items-center gap-3 pb-4 border-b border-gray-100">
          <div class="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
          </div>
          <div>
            <h3 class="text-base font-bold text-gray-900">{{ __("New Referral Code") }}</h3>
            <p class="text-xs text-gray-500">{{ __("Customer will receive a shareable referral link") }}</p>
          </div>
        </div>

        <!-- Customer -->
        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Customer (Referrer)") }} <span class="text-red-500">*</span></label>
          <input v-model="newForm.customer" type="text"
            :placeholder="__('Customer name or ID')"
            class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Campaign -->
        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1.5">{{ __("Campaign (optional)") }}</label>
          <input v-model="newForm.campaign" type="text"
            :placeholder="__('Campaign name')"
            class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Referrer rewards -->
        <div class="bg-amber-50 rounded-xl p-4 border border-amber-100">
          <h4 class="text-xs font-bold text-amber-700 mb-3 flex items-center gap-1.5">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
            </svg>
            {{ __("Referrer Reward (the customer who shares)") }}
          </h4>
          <div class="flex gap-2 mb-3">
            <button v-for="t in discountTypes" :key="t" @click="newForm.referrer_discount_type = t"
              :class="['flex-1 py-2 text-xs font-semibold rounded-lg border transition-all',
                newForm.referrer_discount_type === t
                  ? 'bg-amber-500 border-amber-500 text-white'
                  : 'border-gray-200 text-gray-600 hover:bg-amber-50']"
            >{{ __(t) }}</button>
          </div>
          <input v-if="newForm.referrer_discount_type === 'Percentage'"
            v-model.number="newForm.referrer_discount_percentage" type="number" min="1" max="100"
            :placeholder="__('Discount %')"
            class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
          />
          <input v-else
            v-model.number="newForm.referrer_discount_amount" type="number" min="0.01" step="0.01"
            :placeholder="__('Discount amount')"
            class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
          />
          <div class="mt-2">
            <label class="text-xs text-amber-700 font-medium">{{ __("Coupon valid for") }}</label>
            <div class="flex items-center gap-2 mt-1">
              <input v-model.number="newForm.referrer_coupon_valid_days" type="number" min="1" max="365"
                class="w-24 h-9 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
              />
              <span class="text-xs text-gray-500">{{ __("days") }}</span>
            </div>
          </div>
        </div>

        <!-- Referee rewards -->
        <div class="bg-blue-50 rounded-xl p-4 border border-blue-100">
          <h4 class="text-xs font-bold text-blue-700 mb-3 flex items-center gap-1.5">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/>
            </svg>
            {{ __("New Customer Reward (the friend who joins)") }}
          </h4>
          <div class="flex gap-2 mb-3">
            <button v-for="t in discountTypes" :key="t" @click="newForm.referee_discount_type = t"
              :class="['flex-1 py-2 text-xs font-semibold rounded-lg border transition-all',
                newForm.referee_discount_type === t
                  ? 'bg-blue-600 border-blue-600 text-white'
                  : 'border-gray-200 text-gray-600 hover:bg-blue-50']"
            >{{ __(t) }}</button>
          </div>
          <input v-if="newForm.referee_discount_type === 'Percentage'"
            v-model.number="newForm.referee_discount_percentage" type="number" min="1" max="100"
            :placeholder="__('Discount %')"
            class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input v-else
            v-model.number="newForm.referee_discount_amount" type="number" min="0.01" step="0.01"
            :placeholder="__('Discount amount')"
            class="w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div class="mt-2">
            <label class="text-xs text-blue-700 font-medium">{{ __("Coupon valid for") }}</label>
            <div class="flex items-center gap-2 mt-1">
              <input v-model.number="newForm.referee_coupon_valid_days" type="number" min="1" max="365"
                class="w-24 h-9 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span class="text-xs text-gray-500">{{ __("days") }}</span>
            </div>
          </div>
        </div>

        <!-- Error -->
        <div v-if="createError" class="flex items-start gap-2 px-3 py-2.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
          <svg class="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          {{ createError }}
        </div>

        <!-- Actions -->
        <div class="flex gap-3">
          <button @click="cancelCreate"
            class="flex-1 h-11 rounded-xl border border-gray-200 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
          >{{ __("Cancel") }}</button>
          <button @click="submitCreate" :disabled="createLoading"
            class="flex-1 h-11 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <div v-if="createLoading" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>
            {{ createLoading ? __("Creating...") : __("Create Referral Code") }}
          </button>
        </div>
      </div>

      <!-- DETAIL VIEW -->
      <div v-if="selectedReferral && !isCreating && detailData" class="p-6 max-w-xl mx-auto flex flex-col gap-5">

        <!-- Header with code + copy -->
        <div class="flex items-start justify-between pb-4 border-b border-gray-100">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <code class="text-xl font-mono font-bold text-gray-900 bg-gray-100 px-3 py-1 rounded-lg">{{ detailData.referral_code }}</code>
              <button @click="copyCode(detailData.referral_code)"
                class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                :title="__('Copy code')"
              >
                <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                </svg>
              </button>
            </div>
            <p class="text-sm text-gray-600">{{ detailData.customer_name || detailData.customer }}</p>
          </div>
          <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full',
            detailData.disabled ? 'bg-gray-100 text-gray-600' : 'bg-green-100 text-green-700']">
            {{ detailData.disabled ? __('Disabled') : __('Active') }}
          </span>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-amber-50 rounded-xl p-4 border border-amber-100 text-center">
            <p class="text-2xl font-bold text-amber-700">{{ detailData.referrals_count || 0 }}</p>
            <p class="text-xs text-amber-600 mt-1">{{ __("Total Referrals") }}</p>
          </div>
          <div class="bg-blue-50 rounded-xl p-4 border border-blue-100 text-center">
            <p class="text-2xl font-bold text-blue-700">{{ generatedCoupons.length }}</p>
            <p class="text-xs text-blue-600 mt-1">{{ __("Coupons Generated") }}</p>
          </div>
        </div>

        <!-- Reward summary -->
        <div class="bg-gray-50 rounded-xl p-4 border border-gray-200">
          <h4 class="text-xs font-bold text-gray-700 mb-3">{{ __("Reward Configuration") }}</h4>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <p class="text-[10px] text-gray-500 uppercase font-semibold mb-1">{{ __("Referrer gets") }}</p>
              <p class="text-sm font-bold text-amber-700">
                {{ detailData.referrer_discount_type === 'Percentage'
                  ? (detailData.referrer_discount_percentage + '%')
                  : currency + ' ' + detailData.referrer_discount_amount }}
              </p>
              <p class="text-xs text-gray-400">{{ __("Valid {0} days", [detailData.referrer_coupon_valid_days || 30]) }}</p>
            </div>
            <div>
              <p class="text-[10px] text-gray-500 uppercase font-semibold mb-1">{{ __("New customer gets") }}</p>
              <p class="text-sm font-bold text-blue-700">
                {{ detailData.referee_discount_type === 'Percentage'
                  ? (detailData.referee_discount_percentage + '%')
                  : currency + ' ' + detailData.referee_discount_amount }}
              </p>
              <p class="text-xs text-gray-400">{{ __("Valid {0} days", [detailData.referee_coupon_valid_days || 30]) }}</p>
            </div>
          </div>
        </div>

        <!-- Generated coupons list -->
        <div v-if="generatedCoupons.length > 0">
          <h4 class="text-xs font-bold text-gray-700 mb-2">{{ __("Generated Coupons") }}</h4>
          <div class="flex flex-col gap-2">
            <div v-for="c in generatedCoupons" :key="c.name"
              class="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg border border-gray-200"
            >
              <div>
                <code class="text-xs font-mono text-gray-800">{{ c.coupon_code }}</code>
                <span :class="['ms-2 text-[10px] font-semibold px-1.5 py-0.5 rounded-full',
                  c.coupon_type === 'Gift Card' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700']">
                  {{ __(c.coupon_type) }}
                </span>
              </div>
              <div class="text-right">
                <p class="text-xs text-gray-500">{{ c.customer_name || c.customer }}</p>
                <p class="text-[10px] text-gray-400">{{ __("Used: {0}", [c.used || 0]) }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Copy notification -->
        <transition name="fade">
          <div v-if="copied" class="flex items-center gap-2 px-3 py-2.5 bg-green-50 border border-green-200 rounded-lg text-xs font-semibold text-green-700">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            {{ __("Code copied to clipboard!") }}
          </div>
        </transition>

        <!-- Actions -->
        <div class="flex gap-3 pt-2 border-t border-gray-100">
          <button @click="handleToggle"
            :class="['flex-1 h-10 rounded-xl text-sm font-semibold border transition-colors',
              detailData.disabled
                ? 'border-green-200 text-green-700 hover:bg-green-50'
                : 'border-gray-200 text-gray-700 hover:bg-gray-50']"
          >
            {{ detailData.disabled ? __("Enable") : __("Disable") }}
          </button>
          <button v-if="!detailData.referrals_count" @click="handleDelete"
            class="flex-1 h-10 rounded-xl text-sm font-semibold border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
          >
            {{ __("Delete") }}
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { call } from 'frappe-ui'
import { FormControl, LoadingIndicator } from 'frappe-ui'
import { __ } from '@/utils/translation'

const props = defineProps({
  company: String,
  currency: { type: String, default: 'SAR' },
  permissions: Object,
})

const emit = defineEmits(['referral-saved'])

// State
const searchQuery = ref('')
const statusFilter = ref('all')
const listLoading = ref(false)
const referrals = ref([])
const selectedReferral = ref(null)
const detailData = ref(null)
const generatedCoupons = ref([])
const isCreating = ref(false)
const createLoading = ref(false)
const createError = ref('')
const copied = ref(false)

const discountTypes = ['Percentage', 'Amount']
const statusFilters = [
  { label: 'All', value: 'all' },
  { label: 'Active', value: 'active' },
  { label: 'Disabled', value: 'disabled' },
]

const newForm = ref({
  customer: '',
  campaign: '',
  referrer_discount_type: 'Percentage',
  referrer_discount_percentage: 10,
  referrer_discount_amount: null,
  referrer_coupon_valid_days: 30,
  referee_discount_type: 'Percentage',
  referee_discount_percentage: 10,
  referee_discount_amount: null,
  referee_coupon_valid_days: 30,
})

const filteredReferrals = computed(() => {
  return referrals.value.filter(r => {
    const matchSearch = !searchQuery.value
      || r.customer?.toLowerCase().includes(searchQuery.value.toLowerCase())
      || r.customer_name?.toLowerCase().includes(searchQuery.value.toLowerCase())
      || r.referral_code?.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchStatus = statusFilter.value === 'all'
      || (statusFilter.value === 'active' && !r.disabled)
      || (statusFilter.value === 'disabled' && r.disabled)
    return matchSearch && matchStatus
  })
})

onMounted(loadReferrals)

async function loadReferrals() {
  listLoading.value = true
  try {
    const result = await call('pos_next.api.promotions.get_referral_codes', {
      company: props.company,
      include_disabled: true,
    })
    referrals.value = result || []
  } catch (e) {
    console.error('Failed to load referrals:', e)
  } finally {
    listLoading.value = false
  }
}

async function selectReferral(ref) {
  selectedReferral.value = ref
  isCreating.value = false
  detailData.value = null
  generatedCoupons.value = []
  try {
    const result = await call('pos_next.api.promotions.get_referral_details', {
      referral_name: ref.name,
    })
    detailData.value = result
    generatedCoupons.value = result?.generated_coupons || []
  } catch (e) {
    console.error('Failed to load referral details:', e)
  }
}

function startCreate() {
  selectedReferral.value = null
  detailData.value = null
  isCreating.value = true
  createError.value = ''
  newForm.value = {
    customer: '', campaign: '',
    referrer_discount_type: 'Percentage', referrer_discount_percentage: 10,
    referrer_discount_amount: null, referrer_coupon_valid_days: 30,
    referee_discount_type: 'Percentage', referee_discount_percentage: 10,
    referee_discount_amount: null, referee_coupon_valid_days: 30,
  }
}

function cancelCreate() {
  isCreating.value = false
}

async function submitCreate() {
  createError.value = ''
  if (!newForm.value.customer) {
    createError.value = __('Customer is required')
    return
  }
  createLoading.value = true
  try {
    const result = await call('pos_next.api.promotions.create_referral_code_api', {
      customer: newForm.value.customer,
      campaign: newForm.value.campaign || null,
      referrer_discount_type: newForm.value.referrer_discount_type,
      referrer_discount_percentage: newForm.value.referrer_discount_type === 'Percentage' ? newForm.value.referrer_discount_percentage : null,
      referrer_discount_amount: newForm.value.referrer_discount_type === 'Amount' ? newForm.value.referrer_discount_amount : null,
      referrer_coupon_valid_days: newForm.value.referrer_coupon_valid_days,
      referee_discount_type: newForm.value.referee_discount_type,
      referee_discount_percentage: newForm.value.referee_discount_type === 'Percentage' ? newForm.value.referee_discount_percentage : null,
      referee_discount_amount: newForm.value.referee_discount_type === 'Amount' ? newForm.value.referee_discount_amount : null,
      referee_coupon_valid_days: newForm.value.referee_coupon_valid_days,
    })
    await loadReferrals()
    isCreating.value = false
    const found = referrals.value.find(r => r.name === result.name)
    if (found) selectReferral(found)
    emit('referral-saved', result)
  } catch (e) {
    createError.value = e?.message || e?.exc_type || __('Failed to create referral code')
  } finally {
    createLoading.value = false
  }
}

async function handleToggle() {
  if (!detailData.value) return
  try {
    const result = await call('pos_next.api.promotions.toggle_referral', {
      referral_name: detailData.value.name,
    })
    detailData.value.disabled = result.disabled
    const idx = referrals.value.findIndex(r => r.name === detailData.value.name)
    if (idx >= 0) referrals.value[idx].disabled = result.disabled
  } catch (e) {
    console.error('Toggle failed:', e)
  }
}

async function handleDelete() {
  if (!detailData.value) return
  try {
    await call('pos_next.api.promotions.delete_referral', {
      referral_name: detailData.value.name,
    })
    referrals.value = referrals.value.filter(r => r.name !== detailData.value.name)
    selectedReferral.value = null
    detailData.value = null
  } catch (e) {
    alert(e?.message || __('Failed to delete'))
  }
}

async function copyCode(code) {
  try {
    await navigator.clipboard.writeText(code)
    copied.value = true
    setTimeout(() => { copied.value = false }, 3000)
  } catch {
    // fallback: clipboard not available
  }
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
