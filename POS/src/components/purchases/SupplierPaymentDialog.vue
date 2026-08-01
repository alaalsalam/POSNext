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

        <div class="grid grid-cols-2 gap-3 p-3 bg-orange-50 rounded-xl border border-orange-100">
          <div>
            <p class="text-[10px] text-gray-500">{{ __("المورد") }}</p>
            <p class="text-sm font-semibold">{{ details.supplier_name || details.supplier }}</p>
          </div>
          <div>
            <p class="text-[10px] text-gray-500">{{ __("الرصيد المستحق") }}</p>
            <p class="text-sm font-bold text-red-600">{{ formatAmount(details.outstanding_amount) }} {{ details.currency }}</p>
          </div>
        </div>

        <div>
          <label class="label">{{ __("مبلغ الدفعة") }} <span class="text-red-500">*</span></label>
          <div class="flex gap-2">
            <input v-model.number="form.amount" type="number" min="0.01" :max="details.outstanding_amount" step="0.01" class="field flex-1" />
            <button @click="form.amount = details.outstanding_amount" class="px-3 text-xs font-semibold rounded-lg bg-orange-100 text-orange-700 hover:bg-orange-200">
              {{ __("كامل") }}
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">{{ __("تاريخ الدفع") }}</label>
            <input v-model="form.posting_date" type="date" class="field" />
          </div>
          <div>
            <label class="label">{{ __("طريقة الدفع") }}</label>
            <select v-model="form.mode_of_payment" @change="applyModeAccount" class="field bg-white">
              <option value="">{{ __("اختر...") }}</option>
              <option v-for="mode in modes" :key="mode.name" :value="mode.name">{{ mode.name }}</option>
            </select>
          </div>
        </div>

        <div>
          <label class="label">{{ __("حساب الصندوق أو البنك") }} <span class="text-red-500">*</span></label>
          <select v-model="form.paid_from" class="field bg-white">
            <option value="">{{ __("اختر الحساب...") }}</option>
            <option v-for="account in accounts" :key="account.name" :value="account.name">
              {{ account.account_name || account.name }} — {{ account.account_type }}
            </option>
          </select>
        </div>

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

      <div v-if="!loading" class="sticky bottom-0 bg-white border-t border-gray-100 p-4 flex gap-2">
        <button @click="$emit('close')" class="px-4 py-2.5 rounded-xl bg-gray-100 text-gray-700 text-sm font-semibold">
          {{ __("إلغاء") }}
        </button>
        <button @click="save(false)" :disabled="saving" class="flex-1 px-4 py-2.5 rounded-xl bg-slate-700 text-white text-sm font-semibold disabled:opacity-50">
          {{ __("حفظ كمسودة") }}
        </button>
        <button v-if="canSubmit" @click="save(true)" :disabled="saving" class="flex-1 px-4 py-2.5 rounded-xl bg-orange-600 text-white text-sm font-semibold disabled:opacity-50">
          {{ saving ? __("جاري الحفظ...") : __("اعتماد الدفعة") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from "vue"
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
const accounts = ref([])
const modes = ref([])
const canSubmit = ref(false)
const form = reactive({
	amount: 0,
	posting_date: "",
	mode_of_payment: "",
	paid_from: "",
	reference_no: "",
	reference_date: "",
	remarks: "",
})
const paymentIdempotencyKey =
	globalThis.crypto?.randomUUID?.() ||
	`payment-${Date.now()}-${Math.random().toString(16).slice(2)}`

function messageFrom(error, fallback) {
	return error?.message || error?._server_messages || fallback
}

async function loadDefaults() {
	loading.value = true
	try {
		const response = await frappe.call({
			method: "pos_next.api.purchases.get_supplier_payment_defaults",
			args: { invoice_name: props.invoice.name, pos_profile: props.posProfile },
		})
		const data = response?.message || {}
		Object.assign(details, data.invoice || {})
		accounts.value = data.accounts || []
		modes.value = data.modes_of_payment || []
		canSubmit.value = Boolean(data.can_submit)
		form.amount = Number(details.outstanding_amount || 0)
		form.posting_date = data.posting_date
		form.reference_date = data.posting_date
	} catch (error) {
		errorMsg.value = messageFrom(error, __("تعذر تحميل بيانات الدفع"))
	} finally {
		loading.value = false
	}
}

function applyModeAccount() {
	const mode = modes.value.find((row) => row.name === form.mode_of_payment)
	if (
		mode?.default_account &&
		accounts.value.some((row) => row.name === mode.default_account)
	) {
		form.paid_from = mode.default_account
	}
}

function validate() {
	const amount = Number(form.amount || 0)
	if (amount <= 0) return __("أدخل مبلغ دفع أكبر من صفر")
	if (amount > Number(details.outstanding_amount || 0) + 0.005)
		return __("مبلغ الدفع أكبر من الرصيد المستحق")
	if (!form.paid_from) return __("اختر حساب الصندوق أو البنك")
	return ""
}

async function save(submit) {
	errorMsg.value = validate()
	if (errorMsg.value) return
	saving.value = true
	try {
		const response = await frappe.call({
			method: "pos_next.api.purchases.create_supplier_payment",
			args: {
				invoice_name: details.name,
				amount: form.amount,
				posting_date: form.posting_date,
				mode_of_payment: form.mode_of_payment || null,
				paid_from: form.paid_from,
				reference_no: form.reference_no || null,
				reference_date: form.reference_date || form.posting_date,
				remarks: form.remarks || null,
				submit: submit ? 1 : 0,
				idempotency_key: paymentIdempotencyKey,
				pos_profile: props.posProfile,
			},
		})
		emit("created", response?.message || {})
	} catch (error) {
		errorMsg.value = messageFrom(error, __("تعذر إنشاء دفعة المورد"))
	} finally {
		saving.value = false
	}
}

function formatAmount(value) {
	return Number(value || 0).toLocaleString(frappe.boot?.lang || undefined, {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	})
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
