<template>
  <div class="absolute inset-0 z-[360] bg-black/45 flex items-center justify-center p-2 sm:p-4">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[96vh] overflow-hidden flex flex-col">
      <!-- Title bar -->
      <div class="border-b border-gray-100 px-4 py-3 flex items-center justify-between flex-shrink-0">
        <h3 class="text-lg font-bold text-gray-900">{{ __("تسجيل دفعة للمورد") }}</h3>
        <button @click="$emit('close')" class="w-8 h-8 rounded-lg text-gray-400 hover:bg-gray-100 text-xl leading-none">×</button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="p-12 text-center">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-orange-500 mx-auto"></div>
        <p class="mt-3 text-sm text-gray-500">{{ __("جاري تحميل بيانات الدفع...") }}</p>
      </div>

      <div v-else class="flex-1 overflow-y-auto">
        <div v-if="errorMsg" class="mx-4 mt-3 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
          {{ errorMsg }}
        </div>

        <!-- Two columns: LEFT input (numpad) · RIGHT summary -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4">

          <!-- LEFT: method tiles + quick amounts + numpad -->
          <div class="order-2 lg:order-1 flex flex-col gap-3">
            <!-- Method tiles -->
            <div>
              <p class="text-xs font-semibold text-gray-500 mb-1.5">{{ __("طريقة الدفع") }}</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="m in paymentMethods"
                  :key="m.mode_of_payment"
                  type="button"
                  :data-testid="`pay-method-${m.mode_of_payment}`"
                  :disabled="m.account_missing"
                  @click="selectMethod(m)"
                  :class="[
                    'inline-flex items-center gap-1.5 rounded-xl border-2 px-3 h-10 transition-all text-xs font-semibold touch-manipulation',
                    m.account_missing
                      ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed opacity-70'
                      : form.mode_of_payment === m.mode_of_payment
                        ? 'border-orange-500 bg-orange-50 text-orange-700 shadow-sm'
                        : 'border-gray-200 bg-white text-gray-700 hover:border-orange-300 hover:bg-orange-50/50',
                  ]"
                >
                  <span class="text-sm">{{ methodIcon(m.mode_of_payment) }}</span>
                  <span class="truncate max-w-[90px]">{{ __(m.mode_of_payment) }}</span>
                  <span v-if="m.account_missing" class="text-[8px] font-medium text-gray-400 leading-tight ms-0.5">
                    {{ __("غير مهيأ في الإعدادات") }}
                  </span>
                </button>
              </div>
            </div>

            <!-- Quick amounts -->
            <div>
              <p class="text-xs font-semibold text-gray-500 mb-1.5">{{ __("مبالغ سريعة") }}</p>
              <div class="grid grid-cols-4 gap-2">
                <button
                  v-for="qa in quickAmounts"
                  :key="qa.key"
                  type="button"
                  :data-testid="`quick-${qa.key}`"
                  @click="setAmount(qa.value)"
                  class="h-10 rounded-xl border border-gray-200 bg-white text-xs font-semibold text-gray-700 hover:border-orange-300 hover:bg-orange-50 transition-colors truncate px-1"
                >
                  {{ qa.label }}
                </button>
              </div>
            </div>

            <!-- Amount display -->
            <div class="rounded-xl bg-gray-50 border border-gray-200 h-14 flex items-center justify-center">
              <span data-testid="amount-display" class="text-2xl font-black text-gray-900 tracking-wide">
                {{ formatAmount(amountValue) }}
              </span>
            </div>

            <!-- Numpad — 4 columns: [actions][7-9][4-6][1-3][.-00] like the sales pad -->
            <div class="grid grid-cols-4 gap-2">
              <!-- Row 1 -->
              <button type="button" data-testid="key-backspace" @click="backspace" class="numkey bg-red-50 text-red-500 hover:bg-red-100">
                <svg class="w-5 h-5 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l-7-7 7-7m8 14l-7-7 7-7" />
                </svg>
              </button>
              <button type="button" @click="press('9')" class="numkey">9</button>
              <button type="button" @click="press('8')" class="numkey">8</button>
              <button type="button" @click="press('7')" class="numkey">7</button>

              <!-- Row 2 -->
              <button type="button" data-testid="key-clear" @click="clearAmount" class="numkey bg-amber-50 text-amber-600 hover:bg-amber-100">C</button>
              <button type="button" @click="press('6')" class="numkey">6</button>
              <button type="button" @click="press('5')" class="numkey">5</button>
              <button type="button" @click="press('4')" class="numkey">4</button>

              <!-- Row 3 — «إضافة» (fill full) spans down into row 4 -->
              <button type="button" data-testid="key-add" @click="fillFull" class="numkey row-span-2 bg-gray-50 text-gray-500 hover:bg-gray-100 text-sm font-semibold">
                {{ __("إضافة") }}
              </button>
              <button type="button" @click="press('3')" class="numkey">3</button>
              <button type="button" @click="press('2')" class="numkey">2</button>
              <button type="button" @click="press('1')" class="numkey">1</button>

              <!-- Row 4 -->
              <button type="button" @click="pressDot" class="numkey">.</button>
              <button type="button" @click="press('0')" class="numkey">0</button>
              <button type="button" @click="press('00')" class="numkey">00</button>
            </div>

            <!-- Posting date -->
            <div>
              <label class="label">{{ __("تاريخ الدفع") }}</label>
              <input v-model="form.posting_date" type="date" class="field" />
            </div>

            <!-- Additional details disclosure -->
            <div class="rounded-xl border border-gray-100">
              <button
                type="button"
                data-testid="additional-details-toggle"
                @click="showDetails = !showDetails"
                class="w-full flex items-center justify-between px-3 py-2.5 text-xs font-semibold text-gray-600 hover:bg-gray-50 rounded-xl"
              >
                <span>{{ __("تفاصيل إضافية") }}</span>
                <svg :class="['w-4 h-4 transition-transform', showDetails ? 'rotate-180' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div v-if="showDetails" class="px-3 pb-3 space-y-3 border-t border-gray-100 pt-3">
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="label">{{ __("رقم المرجع") }}</label>
                    <input v-model="form.reference_no" class="field" :placeholder="__('شيك/تحويل/إيصال')" />
                  </div>
                  <div>
                    <label class="label">{{ __("تاريخ المرجع") }}</label>
                    <input v-model="form.reference_date" type="date" class="field" />
                  </div>
                </div>
                <div>
                  <label class="label">{{ __("ملاحظات") }}</label>
                  <textarea v-model="form.remarks" rows="2" class="field py-2 resize-none" />
                </div>
              </div>
            </div>
          </div>

          <!-- RIGHT: supplier summary + totals + remaining/paid tiles -->
          <div class="order-1 lg:order-2 flex flex-col gap-3">
            <div class="rounded-xl bg-gradient-to-r rtl:bg-gradient-to-l from-orange-50 to-amber-50 border border-orange-100 p-4">
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <p class="text-sm font-bold text-gray-900 truncate">{{ details.supplier_name || details.supplier }}</p>
                  <p class="text-xs text-gray-500">{{ details.name }}</p>
                </div>
                <span class="text-[10px] font-semibold text-gray-500 flex-shrink-0">{{ __("المورد") }}</span>
              </div>
            </div>

            <!-- Outstanding + totals -->
            <div class="rounded-xl border border-gray-200 divide-y divide-gray-100">
              <div class="flex items-center justify-between px-4 py-3">
                <span class="text-sm text-gray-600">{{ __("الرصيد المستحق") }}</span>
                <span class="text-sm font-bold text-red-600">{{ formatAmount(outstanding) }}</span>
              </div>
              <div class="flex items-center justify-between px-4 py-3">
                <span class="text-sm font-semibold text-gray-900">{{ __("المجموع الكلي") }}</span>
                <span class="text-base font-bold text-gray-900">{{ formatAmount(grandTotal) }}</span>
              </div>
            </div>

            <!-- Remaining / Paid tiles (mirror sales) -->
            <div class="grid grid-cols-2 gap-3">
              <div
                data-testid="remaining-panel"
                :class="[
                  'rounded-xl border p-4 text-center',
                  isPaidInFull ? 'bg-emerald-50 border-emerald-200' : 'bg-amber-50 border-amber-200',
                ]"
              >
                <p :class="['text-[11px] font-semibold mb-0.5', isPaidInFull ? 'text-emerald-600' : 'text-amber-600']">
                  {{ isPaidInFull ? __("مسدَّد بالكامل") : __("المتبقي") }}
                </p>
                <p :class="['text-lg font-black', isPaidInFull ? 'text-emerald-700' : 'text-amber-800']">
                  {{ formatAmount(remaining) }}
                </p>
              </div>
              <div class="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-center">
                <p class="text-[11px] font-semibold text-emerald-600 mb-0.5">{{ __("مدفوع") }}</p>
                <p class="text-lg font-black text-emerald-700">{{ formatAmount(amountValue) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer: large primary + secondary draft -->
      <div v-if="!loading" class="border-t border-gray-100 p-4 flex flex-col sm:flex-row gap-2 flex-shrink-0">
        <button @click="$emit('close')" class="sm:w-auto px-4 py-3 rounded-xl bg-gray-100 text-gray-700 text-sm font-semibold order-3 sm:order-1">
          {{ __("إلغاء") }}
        </button>
        <button
          @click="save(false)"
          :disabled="saving || !canPay"
          class="sm:w-auto px-4 py-3 rounded-xl bg-slate-700 text-white text-sm font-semibold disabled:opacity-50 order-2"
        >
          {{ __("حفظ كمسودة") }}
        </button>
        <button
          v-if="canSubmit"
          @click="save(true)"
          :disabled="saving || !canPay"
          class="flex-1 px-4 py-3 rounded-xl bg-orange-600 text-white text-base font-bold hover:bg-orange-700 disabled:opacity-50 flex items-center justify-center gap-2 order-1 sm:order-3"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ saving ? __("جاري الحفظ...") : __("اعتماد الدفعة") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from "vue"
import { call } from "@/utils/apiWrapper"
import { formatCurrency } from "@/utils/currency"
import { managerTranslate as __ } from "@/utils/managementI18n"

const props = defineProps({
	invoice: { type: Object, required: true },
	posProfile: { type: String, required: true },
})
const emit = defineEmits(["close", "created"])

const loading = ref(true)
const saving = ref(false)
const errorMsg = ref("")
const details = reactive({})
const paymentMethods = ref([])
const canSubmit = ref(false)
const showDetails = ref(false)
// Numpad-driven amount string (source of truth for typing); form.amount mirrors it.
const amountStr = ref("0")
const form = reactive({
	amount: 0,
	posting_date: "",
	mode_of_payment: "",
	reference_no: "",
	reference_date: "",
	remarks: "",
})
const paymentIdempotencyKey =
	globalThis.crypto?.randomUUID?.() ||
	`payment-${Date.now()}-${Math.random().toString(16).slice(2)}`

const outstanding = computed(() => Number(details.outstanding_amount || 0))
const grandTotal = computed(() => Number(details.grand_total || details.outstanding_amount || 0))
const amountValue = computed(() => Number(form.amount || 0))
const remaining = computed(() =>
	Math.max(Number((outstanding.value - amountValue.value).toFixed(2)), 0),
)
const isPaidInFull = computed(() => amountValue.value > 0 && remaining.value <= 0.005)
// UI overpayment guard (backend also validates): a method must be picked, the
// amount positive, and never above the outstanding balance.
const canPay = computed(
	() =>
		!!form.mode_of_payment &&
		amountValue.value > 0 &&
		amountValue.value <= outstanding.value + 0.005,
)

// Quick-amount chips: «كامل» (= outstanding) + presets that never exceed it.
const quickAmounts = computed(() => {
	const full = outstanding.value
	const chips = [{ key: "full", label: __("كامل"), value: full }]
	for (const frac of [0.75, 0.5, 0.25]) {
		const v = Math.round(full * frac * 100) / 100
		if (v > 0 && v < full) {
			chips.push({ key: `p${Math.round(frac * 100)}`, label: formatAmount(v), value: v })
		}
	}
	return chips.slice(0, 4)
})

const METHOD_ICONS = {
	Cash: "💵", كاش: "💵", نقد: "💵", نقدي: "💵",
	Card: "💳", مدى: "💳", Mada: "💳",
	Transfer: "🏦", تحويل: "🏦", "Bank Transfer": "🏦",
	Wallet: "👛", محفظة: "👛", جيب: "👛", "ون كاش": "📱", فلوسك: "📱", جوالي: "📱",
}
function methodIcon(mode) {
	return METHOD_ICONS[mode] || "💰"
}

function messageFrom(error, fallback) {
	return error?.message || error?._server_messages || fallback
}

function selectMethod(m) {
	if (m.account_missing) return
	form.mode_of_payment = m.mode_of_payment
}

// ── Amount input (numpad + chips), always capped at outstanding ──────────────
function syncAmount() {
	let v = Number.parseFloat(amountStr.value)
	if (Number.isNaN(v)) v = 0
	if (v > outstanding.value) {
		v = outstanding.value
		amountStr.value = String(v)
	}
	form.amount = v
}

function press(d) {
	// Avoid a leading-zero pile-up ("000") — replace a bare "0".
	if (amountStr.value === "0" && d !== ".") amountStr.value = ""
	// Limit to 2 decimal places.
	if (amountStr.value.includes(".")) {
		const dec = amountStr.value.split(".")[1] || ""
		if (dec.length >= 2) return
		if (d === "00") return
	}
	amountStr.value += d
	syncAmount()
}

function pressDot() {
	if (!amountStr.value.includes(".")) {
		amountStr.value = (amountStr.value || "0") + "."
	}
}

function backspace() {
	amountStr.value = amountStr.value.slice(0, -1) || "0"
	syncAmount()
}

function clearAmount() {
	amountStr.value = "0"
	syncAmount()
}

function setAmount(value) {
	const v = Math.min(Number(value || 0), outstanding.value)
	amountStr.value = String(v)
	syncAmount()
}

function fillFull() {
	setAmount(outstanding.value)
}

async function loadDefaults() {
	loading.value = true
	try {
		const data = (await call("pos_next.api.purchases.get_supplier_payment_defaults", {
			invoice_name: props.invoice.name,
			pos_profile: props.posProfile,
		})) || {}
		Object.assign(details, data.invoice || {})
		paymentMethods.value = data.payment_methods || []
		canSubmit.value = Boolean(data.can_submit)
		setAmount(Number(details.outstanding_amount || 0))
		form.posting_date = data.posting_date
		form.reference_date = data.posting_date
		// Pre-select the profile's default method (skip a missing-account one).
		const preferred =
			paymentMethods.value.find((m) => m.default && !m.account_missing) ||
			paymentMethods.value.find((m) => !m.account_missing)
		if (preferred) form.mode_of_payment = preferred.mode_of_payment
	} catch (error) {
		errorMsg.value = messageFrom(error, __("تعذر تحميل بيانات الدفع"))
	} finally {
		loading.value = false
	}
}

function validate() {
	const amount = amountValue.value
	if (!form.mode_of_payment) return __("اختر طريقة الدفع")
	if (amount <= 0) return __("أدخل مبلغ دفع أكبر من صفر")
	if (amount > outstanding.value + 0.005) return __("مبلغ الدفع أكبر من الرصيد المستحق")
	return ""
}

async function save(submit) {
	errorMsg.value = validate()
	if (errorMsg.value) return
	saving.value = true
	try {
		const result = await call("pos_next.api.purchases.create_supplier_payment", {
			invoice_name: details.name,
			amount: form.amount,
			mode_of_payment: form.mode_of_payment,
			posting_date: form.posting_date,
			// Reference only carries through when the disclosure was actually used.
			reference_no: (showDetails.value && form.reference_no) || null,
			reference_date: form.reference_date || form.posting_date,
			remarks: form.remarks || null,
			submit: submit ? 1 : 0,
			idempotency_key: paymentIdempotencyKey,
			pos_profile: props.posProfile,
		})
		emit("created", result || {})
	} catch (error) {
		errorMsg.value = messageFrom(error, __("تعذر إنشاء دفعة المورد"))
	} finally {
		saving.value = false
	}
}

function formatAmount(value) {
	return formatCurrency(Number(value || 0), details.currency || undefined)
}

onMounted(loadDefaults)
</script>

<style scoped>
.label {
  @apply block text-xs font-semibold text-gray-700 mb-1;
}
.field {
  @apply w-full h-10 px-3 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400;
}
.numkey {
  @apply h-12 rounded-xl bg-white border border-gray-200 text-lg font-bold text-gray-800 hover:bg-gray-50 active:bg-gray-100 transition-colors touch-manipulation;
}
</style>
