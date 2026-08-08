<template>
  <div class="absolute inset-0 z-[360] bg-black/45 flex items-center justify-center p-3">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[94vh] overflow-y-auto">
      <div class="sticky top-0 bg-white border-b border-gray-100 px-4 py-3 flex items-center justify-between z-10">
        <div>
          <h3 class="font-bold text-gray-900">{{ __("تسجيل دفعة للمورد") }}</h3>
          <p class="text-xs text-gray-500">{{ invoice?.name }}</p>
        </div>
        <button @click="$emit('close')" class="w-8 h-8 rounded-lg text-gray-400 hover:bg-gray-100">×</button>
      </div>

      <div v-if="loading" class="p-8 text-center text-sm text-gray-500">{{ __("جاري تحميل بيانات الدفع...") }}</div>
      <div v-else class="p-4 space-y-4">
        <div v-if="errorMsg" class="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
          {{ errorMsg }}
        </div>

        <!-- Supplier + outstanding summary -->
        <div class="grid grid-cols-2 gap-3 p-3 bg-orange-50 rounded-xl border border-orange-100">
          <div>
            <p class="text-[10px] text-gray-500">{{ __("المورد") }}</p>
            <p class="text-sm font-semibold">{{ details.supplier_name || details.supplier }}</p>
          </div>
          <div>
            <p class="text-[10px] text-gray-500">{{ __("الرصيد المستحق") }}</p>
            <p class="text-sm font-bold text-red-600">{{ formatAmount(outstanding) }}</p>
          </div>
        </div>

        <!-- Payment method tiles (from the profile's configured methods) -->
        <div>
          <label class="label">{{ __("طريقة الدفع") }} <span class="text-red-500">*</span></label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="m in paymentMethods"
              :key="m.mode_of_payment"
              type="button"
              :data-testid="`pay-method-${m.mode_of_payment}`"
              :disabled="m.account_missing"
              @click="selectMethod(m)"
              :class="[
                'inline-flex flex-col items-center justify-center gap-0.5 rounded-xl border-2 px-3 py-2 min-w-[84px] transition-all text-xs font-semibold touch-manipulation',
                m.account_missing
                  ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed opacity-70'
                  : form.mode_of_payment === m.mode_of_payment
                    ? 'border-orange-500 bg-orange-50 text-orange-700 shadow-sm'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-orange-300 hover:bg-orange-50/50',
              ]"
            >
              <span class="text-base">{{ methodIcon(m.mode_of_payment) }}</span>
              <span class="truncate max-w-[90px]">{{ __(m.mode_of_payment) }}</span>
              <span v-if="m.account_missing" class="text-[8px] font-medium text-gray-400 leading-tight">
                {{ __("غير مهيأ في الإعدادات") }}
              </span>
            </button>
          </div>
        </div>

        <!-- Amount + fill-full -->
        <div>
          <label class="label">{{ __("مبلغ الدفعة") }} <span class="text-red-500">*</span></label>
          <div class="flex gap-2">
            <input
              v-model.number="form.amount"
              @input="capAmount"
              type="number"
              min="0.01"
              :max="outstanding"
              step="0.01"
              class="field flex-1"
            />
            <button
              type="button"
              @click="fillFull"
              class="px-3 text-xs font-semibold rounded-lg bg-orange-100 text-orange-700 hover:bg-orange-200"
            >
              {{ __("كامل") }}
            </button>
          </div>
        </div>

        <!-- «الفروقات» / remaining — the headline of the redesign -->
        <div
          data-testid="remaining-panel"
          :class="[
            'rounded-xl border p-3 flex items-center justify-between gap-3',
            isPaidInFull ? 'bg-emerald-50 border-emerald-200' : 'bg-amber-50 border-amber-200',
          ]"
        >
          <div class="flex items-center gap-2 min-w-0">
            <div :class="[
              'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
              isPaidInFull ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700',
            ]">
              <svg v-if="isPaidInFull" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span :class="['text-xs font-semibold', isPaidInFull ? 'text-emerald-700' : 'text-amber-700']">
              {{ isPaidInFull ? __("مسدَّد بالكامل") : __("المتبقي بعد الدفع") }}
            </span>
          </div>
          <span v-if="!isPaidInFull" class="text-base font-bold text-amber-800 flex-shrink-0">
            {{ formatAmount(remaining) }}
          </span>
        </div>

        <!-- Posting date -->
        <div>
          <label class="label">{{ __("تاريخ الدفع") }}</label>
          <input v-model="form.posting_date" type="date" class="field" />
        </div>

        <!-- Additional details disclosure (reference no + date + notes) -->
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

      <div v-if="!loading" class="sticky bottom-0 bg-white border-t border-gray-100 p-4 flex gap-2">
        <button @click="$emit('close')" class="px-4 py-2.5 rounded-xl bg-gray-100 text-gray-700 text-sm font-semibold">
          {{ __("إلغاء") }}
        </button>
        <button
          @click="save(false)"
          :disabled="saving || !canPay"
          class="flex-1 px-4 py-2.5 rounded-xl bg-slate-700 text-white text-sm font-semibold disabled:opacity-50"
        >
          {{ __("حفظ كمسودة") }}
        </button>
        <button
          v-if="canSubmit"
          @click="save(true)"
          :disabled="saving || !canPay"
          class="flex-1 px-4 py-2.5 rounded-xl bg-orange-600 text-white text-sm font-semibold disabled:opacity-50"
        >
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
const remaining = computed(() =>
	Math.max(Number((outstanding.value - Number(form.amount || 0)).toFixed(2)), 0),
)
const isPaidInFull = computed(
	() => Number(form.amount || 0) > 0 && remaining.value <= 0.005,
)
// UI overpayment guard (backend also validates): a method must be picked, the
// amount positive, and never above the outstanding balance.
const canPay = computed(
	() =>
		!!form.mode_of_payment &&
		Number(form.amount || 0) > 0 &&
		Number(form.amount || 0) <= outstanding.value + 0.005,
)

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

function fillFull() {
	form.amount = outstanding.value
}

// Cap the typed amount at the outstanding balance (prevent overpayment in the UI).
function capAmount() {
	const v = Number(form.amount || 0)
	if (v > outstanding.value) form.amount = outstanding.value
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
		form.amount = Number(details.outstanding_amount || 0)
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
	const amount = Number(form.amount || 0)
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
</style>
