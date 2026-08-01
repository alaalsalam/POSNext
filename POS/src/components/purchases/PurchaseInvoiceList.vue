<template>
  <div class="flex flex-col h-full bg-gray-50">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between gap-3 flex-shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-orange-600 flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <div>
          <h2 class="text-base font-bold text-gray-900">{{ __("فواتير الشراء") }}</h2>
          <p class="text-xs text-gray-500">{{ __("إدارة المشتريات") }}</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-if="canReadPayments"
          @click="$emit('open-payments')"
          class="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-2 rounded-lg transition-colors"
        >
          {{ __("دفعات الموردين") }}
        </button>
        <button
          v-if="canCreate"
          @click="$emit('new-invoice')"
          class="flex items-center gap-1.5 bg-orange-600 hover:bg-orange-700 text-white text-xs font-semibold px-3 py-2 rounded-lg transition-colors"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          {{ __("فاتورة جديدة") }}
        </button>
        <button @click="$emit('close')" class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <div v-if="summary" class="bg-white border-b border-gray-100 px-4 py-2 grid grid-cols-3 gap-2 text-center">
      <div class="rounded-lg bg-red-50 p-2">
        <p class="text-[10px] text-gray-500">{{ __("إجمالي المستحق") }}</p>
        <p class="text-xs font-bold text-red-600">{{ formatAmount(summary.total_outstanding) }}</p>
      </div>
      <div class="rounded-lg bg-orange-50 p-2">
        <p class="text-[10px] text-gray-500">{{ __("غير مدفوعة") }}</p>
        <p class="text-xs font-bold text-orange-700">{{ summary.unpaid_count }}</p>
      </div>
      <div class="rounded-lg bg-blue-50 p-2">
        <p class="text-[10px] text-gray-500">{{ __("مدفوعة جزئيًا") }}</p>
        <p class="text-xs font-bold text-blue-700">{{ summary.partial_count }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white border-b border-gray-100 px-4 py-2.5 flex flex-wrap items-center gap-2 flex-shrink-0">
      <!-- Search -->
      <div class="relative flex-1 min-w-36">
        <svg class="absolute end-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input v-model="search" @input="debouncedLoad" :placeholder="__('بحث...')"
          class="w-full h-8 pe-8 px-3 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-orange-400" />
      </div>
      <!-- Status filter -->
      <select v-model="statusFilter" @change="load" class="h-8 px-2 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white">
        <option value="">{{ __("كل الحالات") }}</option>
        <option value="Draft">{{ __("مسودة") }}</option>
        <option value="Submitted">{{ __("معتمدة") }}</option>
        <option value="Unpaid">{{ __("غير مدفوعة") }}</option>
        <option value="Paid">{{ __("مدفوعة") }}</option>
        <option value="Overdue">{{ __("متأخرة") }}</option>
        <option value="Cancelled">{{ __("ملغاة") }}</option>
      </select>
      <!-- Date range -->
      <input type="date" v-model="fromDate" @change="load" :title="__('من تاريخ')"
        class="h-8 px-2 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-orange-400" />
      <input type="date" v-model="toDate" @change="load" :title="__('إلى تاريخ')"
        class="h-8 px-2 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-orange-400" />
      <button @click="resetFilters" class="h-8 px-2 text-xs text-gray-500 hover:text-gray-700 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
        {{ __("إعادة") }}
      </button>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-3">
      <!-- Loading -->
      <div v-if="loading" class="flex flex-col gap-2">
        <div v-for="i in 5" :key="i" class="h-16 bg-white rounded-xl animate-pulse border border-gray-100" />
      </div>

      <!-- Empty -->
      <div v-else-if="!invoices.length" class="flex flex-col items-center justify-center py-16 text-center">
        <div class="w-14 h-14 rounded-2xl bg-orange-50 flex items-center justify-center mb-3">
          <svg class="w-7 h-7 text-orange-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <p class="text-sm font-semibold text-gray-500">{{ __("لا توجد فواتير شراء") }}</p>
        <p class="text-xs text-gray-400 mt-1">{{ __("أنشئ فاتورة جديدة للبدء") }}</p>
        <button v-if="canCreate" @click="$emit('new-invoice')" class="mt-4 bg-orange-600 text-white text-xs font-semibold px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors">
          {{ __("فاتورة شراء جديدة") }}
        </button>
      </div>

      <!-- Invoice list -->
      <div v-else class="flex flex-col gap-2">
        <div
          v-for="inv in invoices" :key="inv.name"
          @click="$emit('open-invoice', inv)"
          class="bg-white rounded-xl border border-gray-100 p-3 cursor-pointer hover:border-orange-200 hover:shadow-sm transition-all"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs font-bold text-gray-900">{{ inv.name }}</span>
                <span v-if="inv.bill_no" class="text-xs text-gray-400">({{ inv.bill_no }})</span>
                <span :class="statusClass(inv)" class="text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                  {{ statusLabel(inv) }}
                </span>
              </div>
              <p class="text-sm font-semibold text-gray-800 mt-0.5 truncate">{{ inv.supplier_name || inv.supplier }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ formatDate(inv.posting_date) }}</p>
            </div>
            <div class="text-end flex-shrink-0">
              <p class="text-sm font-bold text-gray-900">{{ formatAmount(inv.grand_total) }}</p>
              <p v-if="inv.outstanding_amount > 0" class="text-xs text-red-500 font-medium">
                {{ __("متبقي: {0}", [formatAmount(inv.outstanding_amount)]) }}
              </p>
              <p v-else-if="inv.docstatus === 1" class="text-xs text-green-600 font-medium">{{ __("مدفوع") }}</p>
              <button
                v-if="canCreatePayment && inv.docstatus === 1 && inv.outstanding_amount > 0"
                @click.stop="$emit('pay-invoice', inv)"
                class="mt-2 px-3 py-1.5 text-[11px] font-semibold text-white bg-orange-600 hover:bg-orange-700 rounded-lg"
              >
                {{ __("تسجيل دفعة") }}
              </button>
            </div>
          </div>
        </div>

        <!-- Load more -->
        <button v-if="invoices.length < total" @click="loadMore" :disabled="loadingMore"
          class="w-full py-2.5 text-xs text-orange-600 font-semibold rounded-xl border border-orange-200 hover:bg-orange-50 transition-colors disabled:opacity-50">
          {{ loadingMore ? __("جاري التحميل...") : __("تحميل المزيد ({0} متبقية)", [total - invoices.length]) }}
        </button>
      </div>
    </div>

    <!-- Footer total -->
    <div v-if="total > 0" class="bg-white border-t border-gray-100 px-4 py-2 flex items-center justify-between text-xs text-gray-500 flex-shrink-0">
      <span>{{ __("إجمالي النتائج: {0}", [total]) }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { managerTranslate as __ } from "@/utils/managementI18n"

const props = defineProps({
	canCreate: { type: Boolean, default: false },
	canCreatePayment: { type: Boolean, default: false },
	canReadPayments: { type: Boolean, default: false },
	posProfile: { type: String, required: true },
})
const emit = defineEmits([
	"close",
	"new-invoice",
	"open-invoice",
	"pay-invoice",
	"open-payments",
])

const invoices = ref([])
const total = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const summary = ref(null)
const search = ref("")
const statusFilter = ref("")
const fromDate = ref("")
const toDate = ref("")
const PAGE_SIZE = 20

let debounceTimer = null
function debouncedLoad() {
	clearTimeout(debounceTimer)
	debounceTimer = setTimeout(load, 350)
}

async function load() {
	loading.value = true
	try {
		const res = await frappe.call({
			method: "pos_next.api.purchases.get_purchase_invoices",
			args: {
				search: search.value || null,
				status: statusFilter.value || null,
				from_date: fromDate.value || null,
				to_date: toDate.value || null,
				limit: PAGE_SIZE,
				start: 0,
				pos_profile: props.posProfile,
			},
			error: (r) => {
				console.error("Error loading purchase invoices", r)
			},
		})
		invoices.value = res?.message?.invoices || []
		total.value = res?.message?.total || 0
		const summaryResponse = await frappe.call({
			method: "pos_next.api.purchases.get_purchase_outstanding_summary",
			args: {
				from_date: fromDate.value || null,
				to_date: toDate.value || null,
				pos_profile: props.posProfile,
			},
		})
		summary.value = summaryResponse?.message || null
	} catch (e) {
		console.error(e)
	} finally {
		loading.value = false
	}
}

async function loadMore() {
	loadingMore.value = true
	try {
		const res = await frappe.call({
			method: "pos_next.api.purchases.get_purchase_invoices",
			args: {
				search: search.value || null,
				status: statusFilter.value || null,
				from_date: fromDate.value || null,
				to_date: toDate.value || null,
				limit: PAGE_SIZE,
				start: invoices.value.length,
				pos_profile: props.posProfile,
			},
		})
		invoices.value.push(...(res?.message?.invoices || []))
		total.value = res?.message?.total || 0
	} finally {
		loadingMore.value = false
	}
}

function resetFilters() {
	search.value = ""
	statusFilter.value = ""
	fromDate.value = ""
	toDate.value = ""
	load()
}

function statusLabel(inv) {
	if (inv.docstatus === 0) return __("مسودة")
	if (inv.docstatus === 2) return __("ملغاة")
	const s = inv.status || ""
	const map = {
		Paid: __("مدفوعة"),
		Unpaid: __("غير مدفوعة"),
		Overdue: __("متأخرة"),
		"Partly Paid": __("مدفوعة جزئيًا"),
		Return: __("مرتجع"),
	}
	return map[s] || s
}

function statusClass(inv) {
	if (inv.docstatus === 0) return "bg-gray-100 text-gray-600"
	if (inv.docstatus === 2) return "bg-red-100 text-red-600"
	const s = inv.status || ""
	if (s === "Paid") return "bg-green-100 text-green-700"
	if (s === "Partly Paid") return "bg-blue-100 text-blue-700"
	if (s === "Overdue") return "bg-red-100 text-red-700"
	return "bg-orange-100 text-orange-700"
}

function formatDate(d) {
	if (!d) return ""
	return new Date(d).toLocaleDateString(frappe.boot?.lang || undefined, {
		year: "numeric",
		month: "short",
		day: "numeric",
	})
}

function formatAmount(v) {
	if (v === null || v === undefined) return "0.00"
	return Number.parseFloat(v).toLocaleString(frappe.boot?.lang || undefined, {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	})
}

onMounted(load)
</script>
