<!--
  CashManagement — cashier drawer cash-movement panel (Cash Management v2).
  Records Expense / Receipt / Payment / Transfer drawer movements against the open shift.
  Mobile-first: single column on phone, two columns (form · recent list) on desktop.
  Reuses the numpad idiom (amountStr/press/pressDot/backspace/clearAmount) minus the outstanding
  cap (a drawer movement has no maximum). Gated by the enable_cash_management feature flag.

  The server decides posting: "Immediate" posts to the ledger; "After Approval" saves a draft a
  manager approves/rejects. We read posting_mode/is_manager/boxes/expense-types once from
  get_cash_management_setup and derive the per-type form from there.
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
      <div class="flex items-center gap-1">
        <button
          v-if="canManageExpenseTypes"
          type="button"
          data-testid="manage-expense-types"
          @click="showExpenseTypeManager = true"
          class="h-8 px-2.5 rounded-lg flex items-center gap-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-100"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {{ __("أنواع المصاريف") }}
        </button>
        <button @click="$emit('close')" class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 max-w-5xl mx-auto">

        <!-- LEFT: entry form -->
        <div class="flex flex-col gap-3">
          <div v-if="errorMsg" class="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
            {{ errorMsg }}
          </div>

          <!-- Type toggle (4-up) -->
          <div>
            <p class="text-xs font-semibold text-gray-500 mb-1.5">{{ __("نوع الحركة") }}</p>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
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

          <!-- Posting-mode hint (only when the manager must approve) -->
          <div
            v-if="postingMode === 'After Approval'"
            class="flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-50 border border-amber-100 text-[11px] text-amber-700"
          >
            <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ __("تُعتمد من المدير قبل الترحيل") }}
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

          <!-- ── Expense: expense-type picker + FROM box ─────────────────────── -->
          <template v-if="entryType === 'Expense'">
            <!-- Empty-state: no expense types configured yet -->
            <div
              v-if="!expenseTypes.length"
              data-testid="expense-empty"
              class="p-4 rounded-xl bg-amber-50 border border-amber-100 text-center"
            >
              <p class="text-xs text-amber-800">{{ __("لا توجد أنواع مصاريف — على المدير إضافتها") }}</p>
              <button
                v-if="canManageExpenseTypes"
                type="button"
                data-testid="empty-manage-expense-types"
                @click="showExpenseTypeManager = true"
                class="mt-2 h-9 px-4 rounded-lg bg-teal-600 text-white text-xs font-bold hover:bg-teal-700"
              >
                {{ __("إدارة أنواع المصاريف") }}
              </button>
            </div>
            <template v-else>
              <div>
                <label class="label">{{ __("نوع المصروف") }} <span class="text-red-500">*</span></label>
                <select v-model="expenseType" data-testid="expense-type-select" class="field bg-white">
                  <option value="">{{ __("اختر...") }}</option>
                  <option v-for="e in expenseTypes" :key="e.name" :value="e.name">
                    {{ e.expense_type_name || e.name }}
                  </option>
                </select>
              </div>
              <div>
                <label class="label">{{ __("من صندوق") }} <span class="text-red-500">*</span></label>
                <select v-model="cashAccount" data-testid="from-box-select" class="field bg-white">
                  <option v-for="b in cashBoxes" :key="b.name" :value="b.name">
                    {{ b.account_name || b.name }}
                  </option>
                </select>
              </div>
            </template>
          </template>

          <!-- ── Receipt / Payment: party (or general account) + box ─────────── -->
          <template v-else-if="entryType === 'Receipt' || entryType === 'Payment'">
            <!-- Party / general-account toggle -->
            <div class="flex items-center gap-2">
              <button
                type="button"
                data-testid="counter-party"
                @click="counterMode = 'party'"
                :class="['flex-1 h-9 rounded-lg text-xs font-bold border', counterMode === 'party' ? 'border-teal-500 bg-teal-50 text-teal-700' : 'border-gray-200 bg-white text-gray-600']"
              >
                {{ entryType === 'Receipt' ? __("العميل") : __("الموظف") }}
              </button>
              <button
                type="button"
                data-testid="counter-account"
                @click="switchToGeneralAccount"
                :class="['flex-1 h-9 rounded-lg text-xs font-bold border', counterMode === 'account' ? 'border-teal-500 bg-teal-50 text-teal-700' : 'border-gray-200 bg-white text-gray-600']"
              >
                {{ __("حساب عام") }}
              </button>
            </div>

            <!-- Party picker (searchable) -->
            <div v-if="counterMode === 'party'">
              <label class="label">
                {{ entryType === 'Receipt' ? __("العميل") : __("الموظف") }}
                <span class="text-[10px] text-gray-400 font-normal">({{ __("اختياري") }})</span>
              </label>
              <input
                v-model="partySearch"
                data-testid="party-search"
                type="text"
                :placeholder="__('بحث...')"
                class="field mb-1"
                @input="onPartySearch"
              />
              <select v-model="party" data-testid="party-select" :disabled="partiesLoading" class="field bg-white">
                <option value="">{{ partiesLoading ? __("جاري التحميل...") : __("بدون طرف") }}</option>
                <option v-for="p in parties" :key="p.name" :value="p.name">
                  {{ p.party_name || p.name }}
                </option>
              </select>
            </div>

            <!-- General counter account -->
            <div v-else>
              <label class="label">{{ __("الحساب") }} <span class="text-red-500">*</span></label>
              <select v-model="account" data-testid="account-select" :disabled="accountsLoading" class="field bg-white">
                <option value="">{{ accountsLoading ? __("جاري التحميل...") : __("اختر الحساب...") }}</option>
                <option v-for="a in accounts" :key="a.name" :value="a.name">
                  {{ a.account_name || a.name }}
                </option>
              </select>
            </div>

            <!-- Cash box (into for Receipt / from for Payment) -->
            <div>
              <label class="label">
                {{ entryType === 'Receipt' ? __("إلى صندوق") : __("من صندوق") }} <span class="text-red-500">*</span>
              </label>
              <select v-model="cashAccount" data-testid="cash-box-select" class="field bg-white">
                <option v-for="b in cashBoxes" :key="b.name" :value="b.name">
                  {{ b.account_name || b.name }}
                </option>
              </select>
            </div>
          </template>

          <!-- ── Transfer: FROM box + TO box ─────────────────────────────────── -->
          <template v-else-if="entryType === 'Transfer'">
            <div>
              <label class="label">{{ __("من صندوق") }} <span class="text-red-500">*</span></label>
              <select v-model="cashAccount" data-testid="from-box-select" class="field bg-white">
                <option v-for="b in cashBoxes" :key="b.name" :value="b.name">
                  {{ b.account_name || b.name }}
                </option>
              </select>
            </div>
            <div>
              <label class="label">{{ __("إلى صندوق") }} <span class="text-red-500">*</span></label>
              <select v-model="toAccount" data-testid="to-box-select" class="field bg-white">
                <option value="">{{ __("اختر...") }}</option>
                <option v-for="b in cashBoxes" :key="b.name" :value="b.name" :disabled="b.name === cashAccount">
                  {{ b.account_name || b.name }}
                </option>
              </select>
            </div>
            <p v-if="transferSameBox" class="text-[11px] text-red-600">
              {{ __("يجب أن يختلف الصندوقان") }}
            </p>
          </template>

          <!-- Notes — required for Expense & Payment -->
          <div v-if="!(entryType === 'Expense' && !expenseTypes.length)">
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
            v-if="!(entryType === 'Expense' && !expenseTypes.length)"
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
            <div class="rounded-xl bg-green-50 border border-green-100 p-3">
              <p class="text-[10px] text-green-600">{{ __("قبض") }}</p>
              <p class="text-sm font-bold text-green-700">{{ formatAmount(totals.received_total) }}</p>
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

          <div class="flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("آخر الحركات") }}</h3>
            <span
              v-if="totals.pending_count > 0"
              data-testid="pending-chip"
              class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700"
            >
              {{ __("بانتظار الاعتماد") }} · {{ totals.pending_count }}
            </span>
          </div>

          <div v-if="listLoading" class="flex flex-col gap-2">
            <div v-for="i in 4" :key="i" class="h-14 bg-gray-50 rounded-xl animate-pulse" />
          </div>
          <div v-else-if="!entries.length" class="text-center py-10 text-xs text-gray-400">
            {{ __("لا توجد حركات في هذه الوردية") }}
          </div>
          <div v-else class="flex flex-col gap-2">
            <div v-for="e in entries" :key="e.name" class="flex flex-col gap-2 p-3 rounded-xl border border-gray-100">
              <div class="flex items-center gap-3">
                <span :class="['text-[10px] font-bold px-2 py-0.5 rounded-full flex-shrink-0', entryBadgeClass(e.posa_cash_entry_type)]">
                  {{ typeLabel(e.posa_cash_entry_type) }}
                </span>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-bold text-gray-900">{{ formatAmount(e.total_debit) }}</p>
                  <p v-if="e.user_remark" class="text-[11px] text-gray-500 truncate">{{ e.user_remark }}</p>
                </div>
                <div class="flex flex-col items-end gap-1 flex-shrink-0">
                  <span
                    :class="['text-[10px] font-bold px-2 py-0.5 rounded-full', e.status === 'Approved' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700']"
                  >
                    {{ e.status === 'Approved' ? __("معتمد") : __("بانتظار الاعتماد") }}
                  </span>
                  <span class="text-[10px] text-gray-400">{{ formatTime(e.creation) }}</span>
                </div>
              </div>
              <!-- Manager approve / reject on pending drafts -->
              <div v-if="isManager && e.docstatus === 0" class="flex gap-2">
                <button
                  type="button"
                  :data-testid="`approve-${e.name}`"
                  @click="approveEntry(e.name)"
                  :disabled="actingOn === e.name"
                  class="flex-1 h-8 rounded-lg bg-green-600 text-white text-xs font-bold hover:bg-green-700 disabled:opacity-50"
                >
                  {{ __("اعتماد") }}
                </button>
                <button
                  type="button"
                  :data-testid="`reject-${e.name}`"
                  @click="rejectEntry(e.name)"
                  :disabled="actingOn === e.name"
                  class="flex-1 h-8 rounded-lg bg-red-50 text-red-600 border border-red-200 text-xs font-bold hover:bg-red-100 disabled:opacity-50"
                >
                  {{ __("رفض") }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Screen 2: manager expense-type CRUD (nested overlay) -->
    <ExpenseTypeManagement
      v-if="showExpenseTypeManager"
      :pos-profile="posProfile"
      @close="onExpenseManagerClose"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from "vue"
import { call } from "@/utils/apiWrapper"
import { formatCurrency } from "@/utils/currency"
import { parseError } from "@/utils/errorHandler"
import { useToast } from "@/composables/useToast"
import { managerTranslate as __ } from "@/utils/managementI18n"
import ExpenseTypeManagement from "./ExpenseTypeManagement.vue"

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
	{ value: "Transfer", label: __("تحويل") },
]

const entryType = ref("Expense")
const amountStr = ref("0")
const remarks = ref("")

// Setup (loaded once on open).
const postingMode = ref("Immediate")
const isManager = ref(false)
// Own capability — expense-type editing (enable_expense_types flag + manager), separate from isManager.
const canManageExpenseTypes = ref(false)
const cashBoxes = ref([])
const expenseTypes = ref([])
const defaultCashAccount = ref("")
const currency = ref("")

// Form fields per type.
const expenseType = ref("")
const cashAccount = ref("") // FROM/INTO box
const toAccount = ref("") // Transfer destination
const counterMode = ref("party") // "party" | "account" for Receipt/Payment
const party = ref("")
const partySearch = ref("")
const parties = ref([])
const account = ref("") // general counter account
const accounts = ref([])

// List + totals.
const entries = ref([])
const totals = reactive({
	received_total: 0,
	paid_total: 0,
	net_total: 0,
	pending_count: 0,
})

const setupLoading = ref(false)
const partiesLoading = ref(false)
const accountsLoading = ref(false)
const listLoading = ref(false)
const submitting = ref(false)
const actingOn = ref("")
const errorMsg = ref("")
const showExpenseTypeManager = ref(false)

const amountValue = computed(() => Number(amountStr.value) || 0)
// Notes are mandatory for money leaving the drawer (Expense / Payment).
const noteRequired = computed(
	() => entryType.value === "Expense" || entryType.value === "Payment",
)
const transferSameBox = computed(
	() =>
		entryType.value === "Transfer" &&
		!!cashAccount.value &&
		cashAccount.value === toAccount.value,
)

const canSubmit = computed(() => {
	if (amountValue.value <= 0 || !cashAccount.value) return false
	if (noteRequired.value && remarks.value.trim().length === 0) return false
	if (entryType.value === "Expense") return !!expenseType.value
	if (entryType.value === "Transfer")
		return !!toAccount.value && !transferSameBox.value
	if (entryType.value === "Receipt" || entryType.value === "Payment") {
		// Party is optional; a general account (when chosen) is required by the server.
		return counterMode.value === "party" ? true : !!account.value
	}
	return true
})

function formatAmount(v) {
	return formatCurrency(Number(v || 0), currency.value || undefined)
}
function formatTime(dt) {
	if (!dt) return ""
	return new Date(dt).toLocaleTimeString(
		globalThis.frappe?.boot?.lang || undefined,
		{
			hour: "2-digit",
			minute: "2-digit",
		},
	)
}

function typeLabel(v) {
	return ENTRY_TYPES.find((t) => t.value === v)?.label || v
}
function entryBadgeClass(v) {
	// Receipt = money in (green); Expense/Payment = money out (red); Transfer = neutral (blue).
	if (v === "Receipt") return "bg-green-100 text-green-700"
	if (v === "Transfer") return "bg-blue-100 text-blue-700"
	return "bg-red-100 text-red-600"
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
	if (!amountStr.value.includes("."))
		amountStr.value = `${amountStr.value || "0"}.`
}
function backspace() {
	amountStr.value = amountStr.value.slice(0, -1) || "0"
}
function clearAmount() {
	amountStr.value = "0"
}

function selectType(value) {
	if (entryType.value === value) return
	entryType.value = value
	// Reset type-specific selections; keep the box default.
	expenseType.value = ""
	toAccount.value = ""
	counterMode.value = "party"
	party.value = ""
	partySearch.value = ""
	parties.value = []
	account.value = ""
	if (value === "Receipt" || value === "Payment") loadParties()
}

async function loadSetup() {
	setupLoading.value = true
	try {
		const res = await call(
			"pos_next.api.cash_management.get_cash_management_setup",
			{
				pos_profile: props.posProfile,
			},
		)
		postingMode.value = res?.posting_mode || "Immediate"
		isManager.value = !!res?.is_manager
		canManageExpenseTypes.value = !!res?.can_manage_expense_types
		cashBoxes.value = res?.cash_boxes || []
		expenseTypes.value = res?.expense_types || []
		defaultCashAccount.value = res?.default_cash_account || ""
		currency.value = res?.currency || currency.value
		if (!cashAccount.value) cashAccount.value = defaultCashAccount.value
	} catch (error) {
		errorMsg.value = parseError(error).message
		showError(errorMsg.value)
	} finally {
		setupLoading.value = false
	}
}

let partyDebounce = null
function onPartySearch() {
	// Debounce keystrokes so we hit the party endpoint at most ~3x/second (house rule ≥300ms).
	if (partyDebounce) clearTimeout(partyDebounce)
	partyDebounce = setTimeout(loadParties, 300)
}

async function loadParties() {
	if (entryType.value !== "Receipt" && entryType.value !== "Payment") return
	partiesLoading.value = true
	try {
		const res = await call("pos_next.api.cash_management.get_parties", {
			party_type: entryType.value === "Receipt" ? "Customer" : "Employee",
			search: partySearch.value || "",
			pos_profile: props.posProfile,
		})
		parties.value = res?.parties || []
	} catch (error) {
		errorMsg.value = parseError(error).message
	} finally {
		partiesLoading.value = false
	}
}

async function switchToGeneralAccount() {
	counterMode.value = "account"
	party.value = ""
	if (accounts.value.length) return
	accountsLoading.value = true
	try {
		const res = await call(
			"pos_next.api.cash_management.get_cash_entry_accounts",
			{
				entry_type: entryType.value,
				pos_profile: props.posProfile,
			},
		)
		accounts.value = res?.accounts || []
	} catch (error) {
		errorMsg.value = parseError(error).message
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
		totals.pending_count = res?.pending_count || 0
		if (typeof res?.is_manager === "boolean") isManager.value = res.is_manager
		if (typeof res?.can_manage_expense_types === "boolean")
			canManageExpenseTypes.value = res.can_manage_expense_types
	} catch (error) {
		console.error("Error loading cash entries", error)
	} finally {
		listLoading.value = false
	}
}

function buildPayload() {
	const payload = {
		entry_type: entryType.value,
		amount: amountValue.value,
		cash_account: cashAccount.value,
		remarks: remarks.value.trim() || null,
		pos_profile: props.posProfile,
	}
	if (entryType.value === "Expense") {
		payload.expense_type = expenseType.value
	} else if (entryType.value === "Transfer") {
		payload.to_account = toAccount.value
	} else if (entryType.value === "Receipt" || entryType.value === "Payment") {
		if (counterMode.value === "party" && party.value) {
			payload.party_type =
				entryType.value === "Receipt" ? "Customer" : "Employee"
			payload.party = party.value
		} else if (counterMode.value === "account") {
			payload.account = account.value
		}
	}
	return payload
}

async function submit() {
	if (!canSubmit.value || submitting.value) return
	errorMsg.value = ""
	// Set synchronously before the await — these entries are NOT idempotent server-side.
	submitting.value = true
	try {
		const res = await call(
			"pos_next.api.cash_management.create_cash_entry",
			buildPayload(),
		)
		// The SERVER decides posting; trust its status over the cached posting mode.
		showSuccess(
			res?.status === "Pending Approval"
				? __("تم الحفظ — بانتظار الاعتماد")
				: __("تم تسجيل الحركة"),
		)
		// Clear amount + note; keep type + box for consecutive entries.
		amountStr.value = "0"
		remarks.value = ""
		await loadEntries()
	} catch (error) {
		errorMsg.value = parseError(error).message
		showError(errorMsg.value)
	} finally {
		submitting.value = false
	}
}

async function approveEntry(name) {
	if (actingOn.value) return
	actingOn.value = name
	try {
		await call("pos_next.api.cash_management.approve_cash_entry", {
			name,
			pos_profile: props.posProfile,
		})
		showSuccess(__("تم اعتماد الحركة"))
		await loadEntries()
	} catch (error) {
		showError(parseError(error).message)
	} finally {
		actingOn.value = ""
	}
}

async function rejectEntry(name) {
	if (actingOn.value) return
	actingOn.value = name
	try {
		await call("pos_next.api.cash_management.reject_cash_entry", {
			name,
			pos_profile: props.posProfile,
		})
		showSuccess(__("تم رفض الحركة"))
		await loadEntries()
	} catch (error) {
		showError(parseError(error).message)
	} finally {
		actingOn.value = ""
	}
}

async function onExpenseManagerClose() {
	showExpenseTypeManager.value = false
	// A newly created type must be usable immediately — refresh the setup.
	await loadSetup()
}

onMounted(async () => {
	await Promise.all([loadSetup(), loadEntries()])
})

onBeforeUnmount(() => {
	if (partyDebounce) clearTimeout(partyDebounce)
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
