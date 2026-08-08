<!--
  CashManagement — cashier drawer cash-movement panel (Expense / Receipt / Payment).
  Mobile-first: single column on phone, two columns (form · recent list) on desktop.
  Reuses the SupplierPaymentDialog numpad idiom (amountStr/syncAmount/press/…) minus
  the outstanding cap (a drawer movement has no maximum) and the «إضافة» key.
  Gated by the enable_cash_management feature flag (checked by the parent before render).
-->
<template>
  <div class="absolute inset-0 z-[300] bg-white flex flex-col">
    <!-- Header -->
    <div class="border-b border-gray-200 px-4 py-3 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <div>
          <h2 class="text-base font-bold text-gray-900">{{ __("إدارة الصندوق") }}</h2>
          <p class="text-xs text-gray-500">{{ __("تسجيل حركات النقدية في الوردية") }}</p>
        </div>
      </div>
      <button @click="$emit('close')" class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <div class="flex-1 overflow-y-auto">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 max-w-5xl mx-auto">

        <!-- LEFT: entry form -->
        <div class="flex flex-col gap-3">
          <div v-if="errorMsg" class="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
            {{ errorMsg }}
          </div>

          <!-- Type toggle -->
          <div>
            <p class="text-xs font-semibold text-gray-500 mb-1.5">{{ __("نوع الحركة") }}</p>
            <div class="grid grid-cols-3 gap-2">
              <button
                v-for="t in ENTRY_TYPES"
                :key="t.value"
                type="button"
                :data-testid="`type-${t.value}`"
                @click="selectType(t.value)"
                :class="[
                  'h-11 rounded-xl border-2 text-xs font-bold transition-all touch-manipulation',
                  entryType === t.value
                    ? 'border-teal-500 bg-teal-50 text-teal-700 shadow-sm'
                    : 'border-gray-200 bg-white text-gray-600 hover:border-teal-300 hover:bg-teal-50/40',
                ]"
              >
                {{ t.label }}
              </button>
            </div>
          </div>

          <!-- Amount display -->
          <div class="rounded-xl bg-gray-50 border border-gray-200 h-14 flex items-center justify-center">
            <span data-testid="amount-display" class="text-2xl font-black text-gray-900 tracking-wide">
              {{ formatAmount(amountValue) }}
            </span>
          </div>

          <!-- Numpad (3-wide + backspace/C; no outstanding cap) -->
          <div class="grid grid-cols-3 gap-2">
            <button type="button" @click="press('7')" class="numkey">7</button>
            <button type="button" @click="press('8')" class="numkey">8</button>
            <button type="button" @click="press('9')" class="numkey">9</button>
            <button type="button" @click="press('4')" class="numkey">4</button>
            <button type="button" @click="press('5')" class="numkey">5</button>
            <button type="button" @click="press('6')" class="numkey">6</button>
            <button type="button" @click="press('1')" class="numkey">1</button>
            <button type="button" @click="press('2')" class="numkey">2</button>
            <button type="button" @click="press('3')" class="numkey">3</button>
            <button type="button" @click="pressDot" class="numkey">.</button>
            <button type="button" @click="press('0')" class="numkey">0</button>
            <button type="button" data-testid="key-backspace" @click="backspace" class="numkey bg-red-50 text-red-500 hover:bg-red-100">
              <svg class="w-5 h-5 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l-7-7 7-7m8 14l-7-7 7-7" />
              </svg>
            </button>
            <button type="button" @click="press('00')" class="numkey">00</button>
            <button type="button" data-testid="key-clear" @click="clearAmount" class="numkey col-span-2 bg-amber-50 text-amber-600 hover:bg-amber-100 text-sm">
              {{ __("مسح") }}
            </button>
          </div>

          <!-- Account -->
          <div>
            <label class="label">{{ __("الحساب") }} <span class="text-red-500">*</span></label>
            <select
              v-model="account"
              :disabled="accountsLoading"
              data-testid="account-select"
              class="field bg-white"
            >
              <option value="">
                {{ accountsLoading ? __("جاري التحميل...") : __("اختر الحساب...") }}
              </option>
              <option v-for="a in accounts" :key="a.name" :value="a.name">
                {{ a.account_name || a.name }}
              </option>
            </select>
          </div>

          <!-- Notes — required for Expense & Payment -->
          <div>
            <label class="label">
              {{ __("ملاحظة") }}
              <span v-if="noteRequired" class="text-red-500">*</span>
            </label>
            <textarea
              v-model="remarks"
              data-testid="remarks"
              rows="2"
              :placeholder="noteRequired ? __('سبب الحركة (مطلوب)') : __('ملاحظة اختيارية')"
              class="field py-2 resize-none"
            />
          </div>

          <!-- Submit -->
          <button
            type="button"
            data-testid="cash-submit"
            @click="submit"
            :disabled="!canSubmit || submitting"
            class="w-full py-3 rounded-xl bg-teal-600 text-white text-base font-bold hover:bg-teal-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            {{ submitting ? __("جاري الحفظ...") : __("تسجيل الحركة") }}
          </button>
        </div>

        <!-- RIGHT: recent entries + totals -->
        <div class="flex flex-col gap-3">
          <!-- Totals strip -->
          <div class="grid grid-cols-3 gap-2 text-center">
            <div class="rounded-xl bg-emerald-50 border border-emerald-100 p-3">
              <p class="text-[10px] text-emerald-600">{{ __("قبض") }}</p>
              <p class="text-sm font-bold text-emerald-700">{{ formatAmount(totals.received_total) }}</p>
            </div>
            <div class="rounded-xl bg-red-50 border border-red-100 p-3">
              <p class="text-[10px] text-red-500">{{ __("صرف") }}</p>
              <p class="text-sm font-bold text-red-600">{{ formatAmount(totals.paid_total) }}</p>
            </div>
            <div class="rounded-xl bg-gray-50 border border-gray-200 p-3">
              <p class="text-[10px] text-gray-500">{{ __("الصافي") }}</p>
              <p :class="['text-sm font-bold', Number(totals.net_total) >= 0 ? 'text-gray-900' : 'text-red-600']">
                {{ formatAmount(totals.net_total) }}
              </p>
            </div>
          </div>

          <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("آخر الحركات") }}</h3>

          <div v-if="listLoading" class="flex flex-col gap-2">
            <div v-for="i in 4" :key="i" class="h-14 bg-gray-50 rounded-xl animate-pulse" />
          </div>
          <div v-else-if="!entries.length" class="text-center py-10 text-xs text-gray-400">
            {{ __("لا توجد حركات في هذه الوردية") }}
          </div>
          <div v-else class="flex flex-col gap-2">
            <div v-for="e in entries" :key="e.name" class="flex items-center gap-3 p-3 rounded-xl border border-gray-100">
              <span :class="['text-[10px] font-bold px-2 py-0.5 rounded-full flex-shrink-0', entryBadgeClass(e.posa_cash_entry_type)]">
                {{ typeLabel(e.posa_cash_entry_type) }}
              </span>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-bold text-gray-900">{{ formatAmount(e.total_debit) }}</p>
                <p v-if="e.user_remark" class="text-[11px] text-gray-500 truncate">{{ e.user_remark }}</p>
              </div>
              <span class="text-[10px] text-gray-400 flex-shrink-0">{{ formatTime(e.creation) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue"
import { call } from "@/utils/apiWrapper"
import { formatCurrency } from "@/utils/currency"
import { parseError } from "@/utils/errorHandler"
import { useToast } from "@/composables/useToast"
import { managerTranslate as __ } from "@/utils/managementI18n"

const props = defineProps({
	posProfile: { type: String, required: true },
})
defineEmits(["close"])

const { showSuccess, showError } = useToast()

// Backend expects the exact English entry_type; labels are Arabic.
const ENTRY_TYPES = [
	{ value: "Expense", label: __("صرف مصروف") },
	{ value: "Receipt", label: __("قبض") },
	{ value: "Payment", label: __("دفع") },
]

const entryType = ref("Expense")
const amountStr = ref("0")
const account = ref("")
const remarks = ref("")
const accounts = ref([])
const currency = ref("")
const entries = ref([])
const totals = reactive({ received_total: 0, paid_total: 0, net_total: 0 })
const accountsLoading = ref(false)
const listLoading = ref(false)
const submitting = ref(false)
const errorMsg = ref("")

const amountValue = computed(() => Number(amountStr.value) || 0)
// Notes are mandatory for money leaving the drawer (Expense / Payment).
const noteRequired = computed(() => entryType.value !== "Receipt")
const canSubmit = computed(
	() =>
		amountValue.value > 0 &&
		!!account.value &&
		(!noteRequired.value || remarks.value.trim().length > 0),
)

function formatAmount(v) {
	return formatCurrency(Number(v || 0), currency.value || undefined)
}
function formatTime(dt) {
	if (!dt) return ""
	return new Date(dt).toLocaleTimeString(frappe.boot?.lang || undefined, {
		hour: "2-digit",
		minute: "2-digit",
	})
}

function typeLabel(v) {
	return ENTRY_TYPES.find((t) => t.value === v)?.label || v
}
function entryBadgeClass(v) {
	// Receipt = money in (green); Expense/Payment = money out (red).
	return v === "Receipt" ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-600"
}

// ── Numpad (no outstanding cap — a drawer movement has no maximum) ───────────
function press(d) {
	if (amountStr.value === "0" && d !== ".") amountStr.value = ""
	if (amountStr.value.includes(".")) {
		const dec = amountStr.value.split(".")[1] || ""
		if (dec.length >= 2) return
		if (d === "00") return
	}
	amountStr.value += d
}
function pressDot() {
	if (!amountStr.value.includes(".")) amountStr.value = (amountStr.value || "0") + "."
}
function backspace() {
	amountStr.value = amountStr.value.slice(0, -1) || "0"
}
function clearAmount() {
	amountStr.value = "0"
}

async function selectType(value) {
	if (entryType.value === value) return
	entryType.value = value
	account.value = "" // the previous account may be invalid for the new type
	await loadAccounts()
}

async function loadAccounts() {
	accountsLoading.value = true
	try {
		const res = await call("pos_next.api.cash_management.get_cash_entry_accounts", {
			entry_type: entryType.value,
			pos_profile: props.posProfile,
		})
		accounts.value = res?.accounts || []
		currency.value = res?.currency || currency.value
	} catch (error) {
		errorMsg.value = parseError(error).message || __("تعذر تحميل الحسابات")
	} finally {
		accountsLoading.value = false
	}
}

async function loadEntries() {
	listLoading.value = true
	try {
		const res = await call("pos_next.api.cash_management.get_cash_entries", {
			pos_profile: props.posProfile,
		})
		entries.value = res?.entries || []
		totals.received_total = res?.received_total || 0
		totals.paid_total = res?.paid_total || 0
		totals.net_total = res?.net_total || 0
	} catch (error) {
		console.error("Error loading cash entries", error)
	} finally {
		listLoading.value = false
	}
}

async function submit() {
	if (!canSubmit.value || submitting.value) return
	errorMsg.value = ""
	// Set synchronously before the await — these entries are NOT idempotent server-side.
	submitting.value = true
	try {
		await call("pos_next.api.cash_management.create_cash_entry", {
			entry_type: entryType.value,
			amount: amountValue.value,
			account: account.value,
			remarks: remarks.value.trim() || null,
			pos_profile: props.posProfile,
		})
		showSuccess(__("تم تسجيل الحركة"))
		// Clear the amount + note; keep type + account for consecutive entries.
		amountStr.value = "0"
		remarks.value = ""
		await loadEntries()
	} catch (error) {
		errorMsg.value = parseError(error).message || __("تعذر تسجيل الحركة")
		showError(errorMsg.value)
	} finally {
		submitting.value = false
	}
}

onMounted(async () => {
	await Promise.all([loadAccounts(), loadEntries()])
})
</script>

<style scoped>
.label {
  @apply block text-xs font-semibold text-gray-700 mb-1;
}
.field {
  @apply w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400;
}
.numkey {
  @apply h-12 rounded-xl bg-white border border-gray-200 text-lg font-bold text-gray-800 hover:bg-gray-50 active:bg-gray-100 transition-colors touch-manipulation;
}
</style>
