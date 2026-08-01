<template>
  <div class="flex flex-col h-full bg-gray-50">
    <div class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <button @click="$emit('back')" class="w-8 h-8 rounded-lg text-gray-500 hover:bg-gray-100">→</button>
        <div>
          <h2 class="text-base font-bold text-gray-900">{{ __("دفعات الموردين") }}</h2>
          <p class="text-xs text-gray-500">{{ __("سجل الدفعات النقدية والبنكية") }}</p>
        </div>
      </div>
      <button @click="$emit('close')" class="w-8 h-8 rounded-lg text-gray-400 hover:bg-gray-100">×</button>
    </div>

    <div class="bg-white border-b border-gray-100 px-4 py-2.5 flex gap-2 flex-wrap">
      <input v-model="supplier" :placeholder="__('رمز المورد')" class="h-9 px-3 text-xs border rounded-lg flex-1 min-w-36" />
      <input v-model="fromDate" type="date" class="h-9 px-2 text-xs border rounded-lg" />
      <input v-model="toDate" type="date" class="h-9 px-2 text-xs border rounded-lg" />
      <button @click="load" class="h-9 px-4 rounded-lg bg-orange-600 text-white text-xs font-semibold">{{ __("تطبيق") }}</button>
    </div>

    <div class="flex-1 overflow-y-auto p-3">
      <div v-if="loading" class="py-12 text-center text-sm text-gray-500">{{ __("جاري التحميل...") }}</div>
      <div v-else-if="errorMessage" class="p-3 rounded-xl border border-red-200 bg-red-50 text-xs text-red-700">
        {{ errorMessage }}
      </div>
      <div v-else-if="!payments.length" class="py-16 text-center text-sm text-gray-400">{{ __("لا توجد دفعات موردين") }}</div>
      <div v-else class="space-y-2">
        <div v-for="payment in payments" :key="payment.name" class="bg-white border border-gray-100 rounded-xl p-3">
          <div class="flex justify-between gap-3">
            <div>
              <div class="flex gap-2 items-center">
                <a :href="`/app/payment-entry/${payment.name}`" target="_blank" class="text-xs font-bold text-orange-700 hover:underline">{{ payment.name }}</a>
                <span :class="statusClass(payment)" class="text-[10px] px-2 py-0.5 rounded-full font-bold">{{ statusLabel(payment) }}</span>
              </div>
              <p class="text-sm font-semibold text-gray-800 mt-1">{{ payment.party_name || payment.party }}</p>
              <p class="text-xs text-gray-400">{{ formatDate(payment.posting_date) }} · {{ payment.mode_of_payment || __("غير محدد") }}</p>
              <p v-if="payment.reference_no" class="text-[11px] text-gray-400">{{ __("المرجع: {0}", [payment.reference_no]) }}</p>
              <div v-if="payment.allocations?.length" class="mt-2 space-y-1">
                <p v-for="allocation in payment.allocations" :key="allocation.reference_name"
                  class="text-[11px] text-gray-500 bg-gray-50 rounded-md px-2 py-1">
                  {{ allocation.reference_name }} · {{ __("Allocated") }}:
                  {{ formatAmount(allocation.allocated_amount) }} {{ payment.paid_from_account_currency }}
                </p>
              </div>
              <div class="flex gap-2 mt-2">
                <button
                  v-if="payment.docstatus === 0 && canSubmit"
                  @click="changeStatus(payment, 'submit')"
                  :disabled="actionName === payment.name"
                  class="px-3 py-1 text-[11px] font-semibold rounded-lg bg-green-600 text-white disabled:opacity-50"
                >
                  {{ __("اعتماد") }}
                </button>
                <button
                  v-if="payment.docstatus === 1 && canCancel"
                  @click="changeStatus(payment, 'cancel')"
                  :disabled="actionName === payment.name"
                  class="px-3 py-1 text-[11px] font-semibold rounded-lg bg-red-50 text-red-700 disabled:opacity-50"
                >
                  {{ __("إلغاء الدفعة") }}
                </button>
              </div>
            </div>
            <p class="text-sm font-bold text-gray-900">{{ formatAmount(payment.paid_amount) }} {{ payment.paid_from_account_currency }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { managerTranslate as __ } from "@/utils/managementI18n"

const props = defineProps({
	canSubmit: { type: Boolean, default: false },
	canCancel: { type: Boolean, default: false },
	posProfile: { type: String, required: true },
})
defineEmits(["back", "close"])
const payments = ref([])
const loading = ref(false)
const supplier = ref("")
const fromDate = ref("")
const toDate = ref("")
const actionName = ref("")
const errorMessage = ref("")

async function load() {
	loading.value = true
	errorMessage.value = ""
	try {
		const response = await frappe.call({
			method: "pos_next.api.purchases.get_supplier_payments",
			args: {
				supplier: supplier.value || null,
				from_date: fromDate.value || null,
				to_date: toDate.value || null,
				pos_profile: props.posProfile,
			},
		})
		payments.value = response?.message?.payments || []
	} catch (error) {
		errorMessage.value =
			error?.message || __("Could not load supplier payments")
	} finally {
		loading.value = false
	}
}

async function changeStatus(payment, action) {
	if (action === "cancel" && !window.confirm(__("هل تريد إلغاء هذه الدفعة؟")))
		return
	actionName.value = payment.name
	try {
		await frappe.call({
			method:
				action === "submit"
					? "pos_next.api.purchases.submit_supplier_payment"
					: "pos_next.api.purchases.cancel_supplier_payment",
			args:
				action === "submit"
					? {
							name: payment.name,
							expected_modified: payment.modified,
							pos_profile: props.posProfile,
						}
					: { name: payment.name, pos_profile: props.posProfile },
		})
		await load()
	} finally {
		actionName.value = ""
	}
}

function statusLabel(row) {
	return row.docstatus === 1
		? __("معتمدة")
		: row.docstatus === 2
			? __("ملغاة")
			: __("مسودة")
}
function statusClass(row) {
	return row.docstatus === 1
		? "bg-green-100 text-green-700"
		: row.docstatus === 2
			? "bg-red-100 text-red-700"
			: "bg-gray-100 text-gray-600"
}
function formatDate(value) {
	return value
		? new Date(value).toLocaleDateString(frappe.boot?.lang || undefined)
		: ""
}
function formatAmount(value) {
	return Number(value || 0).toLocaleString(frappe.boot?.lang || undefined, {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	})
}

onMounted(load)
</script>
