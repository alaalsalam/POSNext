<!--
  Read-only purchase invoice review view. Mirrors the sales InvoiceDetailDialog's
  layout language (header card, clean sections, formatCurrency, RTL, loading state)
  with the shared POS blue accent. Editing lives in PurchaseInvoiceForm and is only
  reachable from the «تعديل» action on a draft — reviewing is never the raw form.
-->
<template>
  <div class="absolute inset-0 z-[355] bg-black/45 flex items-center justify-center p-3" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[94vh] overflow-y-auto flex flex-col">
      <!-- Title bar -->
      <div class="sticky top-0 bg-white border-b border-gray-100 px-4 py-3 flex items-center justify-between z-10">
        <h3 class="font-bold text-gray-900">{{ __("تفاصيل الفاتورة") }}</h3>
        <button @click="$emit('close')" class="w-8 h-8 rounded-lg text-gray-400 hover:bg-gray-100">×</button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="p-10 text-center">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto"></div>
        <p class="mt-3 text-sm text-gray-500">{{ __("جاري تحميل بيانات الفاتورة...") }}</p>
      </div>

      <!-- Error -->
      <div v-else-if="!invoice" class="p-10 text-center">
        <svg class="mx-auto h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="mt-2 text-sm text-gray-500">{{ __("تعذر تحميل بيانات الفاتورة") }}</p>
      </div>

      <template v-else>
        <div class="flex-1 p-4 flex flex-col gap-4">
          <!-- Header card -->
          <div class="bg-gradient-to-r rtl:bg-gradient-to-l from-blue-50 to-gray-50 rounded-xl p-4 border border-blue-100">
            <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-2 flex-wrap">
                  <h4 class="text-lg font-bold text-gray-900">{{ invoice.name }}</h4>
                  <span :class="['px-2.5 py-0.5 text-[11px] font-bold rounded-full', statusClass]">
                    {{ statusLabel }}
                  </span>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-sm">
                  <div><span class="text-gray-500">{{ __("المورد") }}:</span>
                    <span class="ms-2 font-semibold text-gray-900">{{ invoice.supplier_name || invoice.supplier }}</span></div>
                  <div><span class="text-gray-500">{{ __("تاريخ الفاتورة") }}:</span>
                    <span class="ms-2 font-medium text-gray-900">{{ formatDate(invoice.posting_date) }}</span></div>
                </div>
                <!-- Secondary line: bill no + due date -->
                <div v-if="invoice.bill_no || invoice.due_date" class="mt-1.5 flex flex-wrap gap-x-4 gap-y-0.5 text-[11px] text-gray-400">
                  <span v-if="invoice.bill_no">{{ __("رقم فاتورة المورد") }}: {{ invoice.bill_no }}</span>
                  <span v-if="invoice.due_date">{{ __("تاريخ الاستحقاق") }}: {{ formatDate(invoice.due_date) }}</span>
                </div>
              </div>
              <div class="text-start sm:text-end flex-shrink-0">
                <p class="text-[11px] text-gray-500 mb-0.5">{{ __("الإجمالي الكلي") }}</p>
                <p class="text-xl font-bold text-blue-700">{{ fmt(invoice.grand_total) }}</p>
              </div>
            </div>
          </div>

          <!-- Payment status panel -->
          <div class="grid grid-cols-3 gap-2 text-center">
            <div class="rounded-xl bg-gray-50 border border-gray-100 p-3">
              <p class="text-[10px] text-gray-500">{{ __("الإجمالي") }}</p>
              <p class="text-sm font-bold text-gray-900">{{ fmt(invoice.grand_total) }}</p>
            </div>
            <div class="rounded-xl bg-green-50 border border-green-100 p-3">
              <p class="text-[10px] text-green-600">{{ __("المدفوع") }}</p>
              <p class="text-sm font-bold text-green-700">{{ fmt(paidAmount) }}</p>
            </div>
            <div :class="['rounded-xl border p-3', outstanding > 0 ? 'bg-red-50 border-red-100' : 'bg-gray-50 border-gray-100']">
              <p :class="['text-[10px]', outstanding > 0 ? 'text-red-500' : 'text-gray-500']">{{ __("المتبقي") }}</p>
              <p :class="['text-sm font-bold', outstanding > 0 ? 'text-red-600' : 'text-gray-400']">{{ fmt(outstanding) }}</p>
            </div>
          </div>

          <!-- Items -->
          <div>
            <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">{{ __("الأصناف") }}</h4>
            <!-- Desktop table -->
            <div class="hidden sm:block border border-gray-200 rounded-xl overflow-hidden">
              <table class="min-w-full divide-y divide-gray-200 text-sm">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-2 text-start text-[11px] font-semibold text-gray-600">{{ __("الصنف") }}</th>
                    <th class="px-3 py-2 text-center text-[11px] font-semibold text-gray-600">{{ __("الكمية") }}</th>
                    <th class="px-3 py-2 text-center text-[11px] font-semibold text-gray-600">{{ __("سعر الشراء") }}</th>
                    <th class="px-3 py-2 text-end text-[11px] font-semibold text-gray-600">{{ __("الإجمالي") }}</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-100">
                  <tr v-for="(it, i) in invoice.items" :key="i">
                    <td class="px-3 py-2">
                      <div class="font-medium text-gray-900">{{ it.item_name }}</div>
                      <div class="text-[10px] text-gray-400">{{ it.item_code }}</div>
                    </td>
                    <td class="px-3 py-2 text-center text-gray-900">{{ countFmt(it.qty) }} {{ it.uom }}</td>
                    <td class="px-3 py-2 text-center text-gray-900">{{ fmt(it.rate) }}</td>
                    <td class="px-3 py-2 text-end font-semibold text-gray-900">{{ fmt(it.amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <!-- Mobile cards -->
            <div class="sm:hidden flex flex-col gap-2">
              <div v-for="(it, i) in invoice.items" :key="i" class="border border-gray-200 rounded-xl p-3">
                <div class="font-semibold text-gray-900 text-sm">{{ it.item_name }}</div>
                <div class="text-[10px] text-gray-400 mb-2">{{ it.item_code }}</div>
                <div class="grid grid-cols-3 gap-2 text-center border-t border-gray-100 pt-2 text-xs">
                  <div><div class="text-[10px] text-gray-500">{{ __("الكمية") }}</div><div class="font-medium">{{ countFmt(it.qty) }} {{ it.uom }}</div></div>
                  <div><div class="text-[10px] text-gray-500">{{ __("سعر الشراء") }}</div><div class="font-medium">{{ fmt(it.rate) }}</div></div>
                  <div><div class="text-[10px] text-gray-500">{{ __("الإجمالي") }}</div><div class="font-semibold">{{ fmt(it.amount) }}</div></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Totals -->
          <div class="bg-gray-50 rounded-xl border border-gray-200 p-4 flex flex-col gap-2">
            <div class="flex justify-between text-sm">
              <span class="text-gray-600">{{ __("المجموع قبل الضريبة") }}</span>
              <span class="font-medium text-gray-900">{{ fmt(invoice.total) }}</span>
            </div>
            <div v-if="Number(invoice.total_taxes_and_charges) > 0" class="flex justify-between text-sm">
              <span class="text-gray-600">{{ __("الضريبة") }}</span>
              <span class="font-medium text-gray-900">{{ fmt(invoice.total_taxes_and_charges) }}</span>
            </div>
            <div class="pt-2 border-t border-gray-300 flex justify-between">
              <span class="font-semibold text-gray-900">{{ __("الإجمالي الكلي") }}</span>
              <span class="font-bold text-lg text-blue-700">{{ fmt(invoice.grand_total) }}</span>
            </div>
          </div>
        </div>

        <!-- Footer actions -->
        <div class="sticky bottom-0 bg-white border-t border-gray-100 p-4 flex items-center gap-2">
          <button @click="$emit('close')" class="px-4 py-2.5 rounded-xl bg-gray-100 text-gray-700 text-sm font-semibold">
            {{ __("إغلاق") }}
          </button>
          <div class="flex-1"></div>
          <!-- Cancel is a subtle secondary action, never the primary review CTA -->
          <button
            v-if="isSubmitted && canCancel"
            data-testid="detail-cancel"
            @click="$emit('cancel-invoice', invoice)"
            class="px-3 py-2 text-xs font-medium text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg"
          >
            {{ __("إلغاء الفاتورة") }}
          </button>
          <button
            v-if="isDraft && canWrite"
            data-testid="detail-edit"
            @click="$emit('edit-invoice', invoice)"
            class="px-4 py-2.5 rounded-xl bg-gray-700 text-white text-sm font-semibold hover:bg-gray-800"
          >
            {{ __("تعديل") }}
          </button>
          <button
            v-if="isSubmitted && outstanding > 0 && canPay"
            data-testid="detail-pay"
            @click="$emit('pay-invoice', invoice)"
            class="px-4 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700"
          >
            {{ __("تسجيل دفعة") }}
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { call } from "@/utils/apiWrapper"
import { formatCurrency } from "@/utils/currency"
import { managerTranslate as __ } from "@/utils/managementI18n"

const props = defineProps({
	invoiceName: { type: String, required: true },
	posProfile: { type: String, required: true },
	canPay: { type: Boolean, default: false },
	canWrite: { type: Boolean, default: false },
	canCancel: { type: Boolean, default: false },
})
defineEmits(["close", "pay-invoice", "edit-invoice", "cancel-invoice"])

const loading = ref(true)
const invoice = ref(null)

const outstanding = computed(() => Number(invoice.value?.outstanding_amount || 0))
const grandTotal = computed(() => Number(invoice.value?.grand_total || 0))
const paidAmount = computed(() => Math.max(grandTotal.value - outstanding.value, 0))
const isDraft = computed(() => invoice.value?.docstatus === 0)
const isSubmitted = computed(() => invoice.value?.docstatus === 1)

// Status derived from docstatus + outstanding vs grand total (not the raw ERPNext status).
const statusLabel = computed(() => {
	if (!invoice.value) return ""
	if (invoice.value.docstatus === 0) return __("مسودة")
	if (invoice.value.docstatus === 2) return __("ملغاة")
	if (outstanding.value <= 0.005) return __("مدفوعة")
	if (outstanding.value < grandTotal.value - 0.005) return __("مدفوعة جزئيًا")
	return __("معتمدة")
})
const statusClass = computed(() => {
	if (!invoice.value) return "bg-gray-100 text-gray-600"
	if (invoice.value.docstatus === 0) return "bg-gray-100 text-gray-600"
	if (invoice.value.docstatus === 2) return "bg-red-100 text-red-600"
	if (outstanding.value <= 0.005) return "bg-green-100 text-green-700"
	if (outstanding.value < grandTotal.value - 0.005) return "bg-blue-100 text-blue-700"
	return "bg-blue-100 text-blue-700"
})

function fmt(v) {
	return formatCurrency(Number(v || 0), invoice.value?.currency || undefined)
}
function countFmt(v) {
	return Number.parseFloat(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })
}
function formatDate(d) {
	if (!d) return ""
	return new Date(`${d}T00:00:00`).toLocaleDateString(frappe.boot?.lang || undefined, {
		year: "numeric",
		month: "short",
		day: "numeric",
	})
}

async function load() {
	loading.value = true
	try {
		invoice.value = await call("pos_next.api.purchases.get_purchase_invoice", {
			name: props.invoiceName,
			pos_profile: props.posProfile,
		})
	} catch (error) {
		console.error("Error loading purchase invoice", error)
		invoice.value = null
	} finally {
		loading.value = false
	}
}

onMounted(load)
</script>
