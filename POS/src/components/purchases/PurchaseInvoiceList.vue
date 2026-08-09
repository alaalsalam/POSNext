<!--
  Purchase invoice list, embedded inside Invoice Management's Purchases mode.
  The parent tab fixes the scope via `fixedStatus`:
    "unpaid"  → submitted invoices with a remaining balance (paging continues
                until every outstanding invoice is reachable)
    "history" → all invoices
    "drafts"  → docstatus 0
  Row click opens the invoice; the pay action opens the supplier-payment dialog.
  Creating a purchase invoice happens from the main POS screen (rail → purchase
  mode), never from here — so there is no "new invoice" action.
-->
<template>
  <div class="flex flex-col h-full bg-gray-50">
    <!-- Outstanding summary (Unpaid tab only) -->
    <div v-if="summary && fixedStatus === 'unpaid'" class="bg-white border-b border-gray-100 px-4 py-2 grid grid-cols-3 gap-2 text-center">
      <div class="rounded-lg bg-red-50 p-2">
        <p class="text-[10px] text-gray-500">{{ __("إجمالي المستحق") }}</p>
        <p class="text-xs font-bold text-red-600">{{ formatAmount(summary.total_outstanding) }}</p>
      </div>
      <div class="rounded-lg bg-blue-50 p-2">
        <p class="text-[10px] text-gray-500">{{ __("غير مدفوعة") }}</p>
        <p class="text-xs font-bold text-blue-700">{{ summary.unpaid_count }}</p>
      </div>
      <div class="rounded-lg bg-blue-50 p-2">
        <p class="text-[10px] text-gray-500">{{ __("مدفوعة جزئيًا") }}</p>
        <p class="text-xs font-bold text-blue-700">{{ summary.partial_count }}</p>
      </div>
    </div>

    <!-- Filters (search + date range) -->
    <div class="bg-white border-b border-gray-100 px-4 py-2.5 flex flex-wrap items-center gap-2 flex-shrink-0">
      <div class="relative flex-1 min-w-36">
        <svg class="absolute end-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input v-model="search" @input="debouncedLoad" :placeholder="__('بحث...')"
          class="w-full h-8 pe-8 px-3 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <input type="date" v-model="fromDate" @change="load" :title="__('من تاريخ')"
        class="h-8 px-2 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500" />
      <input type="date" v-model="toDate" @change="load" :title="__('إلى تاريخ')"
        class="h-8 px-2 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500" />
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-3">
      <!-- Loading -->
      <div v-if="loading" class="flex flex-col gap-2">
        <div v-for="i in 5" :key="i" class="h-16 bg-white rounded-xl animate-pulse border border-gray-100" />
      </div>

      <!-- Error -->
      <div v-else-if="errorMessage" class="p-3 rounded-xl border border-red-200 bg-red-50 text-xs text-red-700">
        {{ errorMessage }}
      </div>

      <!-- Empty (only when nothing is visible AND the server is exhausted) -->
      <div v-else-if="!visibleInvoices.length && !hasMore" class="flex flex-col items-center justify-center py-16 text-center">
        <div class="w-14 h-14 rounded-2xl bg-blue-50 flex items-center justify-center mb-3">
          <svg class="w-7 h-7 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <p class="text-sm font-semibold text-gray-500">{{ __("لا توجد فواتير شراء") }}</p>
      </div>

      <!-- Invoice list -->
      <div v-else class="flex flex-col gap-2">
        <div
          v-for="inv in visibleInvoices" :key="inv.name"
          @click="$emit('open-invoice', inv)"
          class="bg-white rounded-xl border border-gray-100 p-3 cursor-pointer hover:border-blue-200 hover:shadow-sm transition-all"
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
                class="mt-2 px-3 py-1.5 text-[11px] font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg"
              >
                {{ __("تسجيل دفعة") }}
              </button>
            </div>
          </div>
        </div>

        <!-- Load more — reachable on every tab so outstanding invoices beyond the
             first page are never hidden behind an empty state. -->
        <button v-if="hasMore" @click="loadMore" :disabled="loadingMore"
          class="w-full py-2.5 text-xs text-blue-600 font-semibold rounded-xl border border-blue-200 hover:bg-blue-50 transition-colors disabled:opacity-50">
          {{ loadingMore ? __("جاري التحميل...") : __("تحميل المزيد ({0} متبقية)", [total - invoices.length]) }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { call } from "@/utils/apiWrapper"
import { managerTranslate as __ } from "@/utils/managementI18n"

const props = defineProps({
	canCreatePayment: { type: Boolean, default: false },
	posProfile: { type: String, required: true },
	// "" (all) | "unpaid" (outstanding only) | "drafts" (docstatus 0).
	fixedStatus: { type: String, default: "" },
})

defineEmits(["open-invoice", "pay-invoice"])

const invoices = ref([])
const total = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const summary = ref(null)
const errorMessage = ref("")
const search = ref("")
const fromDate = ref("")
const toDate = ref("")
const PAGE_SIZE = 20

// The Unpaid tab shows only submitted invoices that still owe money. The backend
// `status` filter is literal (misses Partly Paid / Overdue), so outstanding is
// filtered client-side; paging (below) keeps every outstanding invoice reachable.
const visibleInvoices = computed(() => {
	if (props.fixedStatus === "unpaid") {
		return invoices.value.filter(
			(inv) => inv.docstatus === 1 && Number.parseFloat(inv.outstanding_amount) > 0,
		)
	}
	return invoices.value
})

// More server rows remain to fetch (independent of client-side filtering).
const hasMore = computed(() => invoices.value.length < total.value)

// Drafts map to a literal server status; unpaid/history fetch without a status
// filter (unpaid is narrowed client-side).
const effectiveStatus = computed(() => (props.fixedStatus === "drafts" ? "Draft" : ""))

// Fetch a full page up front for Unpaid (backend caps at 100) so the common case
// surfaces every outstanding invoice without needing "load more".
const firstPageLimit = computed(() => (props.fixedStatus === "unpaid" ? 100 : PAGE_SIZE))

let debounceTimer = null
function debouncedLoad() {
	clearTimeout(debounceTimer)
	debounceTimer = setTimeout(load, 350)
}

async function fetchInvoices(start, limit) {
	const result = await call("pos_next.api.purchases.get_purchase_invoices", {
		search: search.value || null,
		status: effectiveStatus.value || null,
		from_date: fromDate.value || null,
		to_date: toDate.value || null,
		limit,
		start,
		pos_profile: props.posProfile,
	})
	return result || { invoices: [], total: 0 }
}

async function load() {
	loading.value = true
	errorMessage.value = ""
	try {
		const page = await fetchInvoices(0, firstPageLimit.value)
		invoices.value = page.invoices || []
		total.value = page.total || 0
		if (props.fixedStatus === "unpaid") {
			summary.value =
				(await call("pos_next.api.purchases.get_purchase_outstanding_summary", {
					from_date: fromDate.value || null,
					to_date: toDate.value || null,
					pos_profile: props.posProfile,
				})) || null
		}
	} catch (error) {
		errorMessage.value = error?.message || __("تعذر تحميل فواتير الشراء")
	} finally {
		loading.value = false
	}
}

async function loadMore() {
	loadingMore.value = true
	try {
		const page = await fetchInvoices(invoices.value.length, PAGE_SIZE)
		invoices.value.push(...(page.invoices || []))
		total.value = page.total || 0
	} finally {
		loadingMore.value = false
	}
}

function statusLabel(inv) {
	if (inv.docstatus === 0) return __("مسودة")
	if (inv.docstatus === 2) return __("ملغاة")
	const map = {
		Paid: __("مدفوعة"),
		Unpaid: __("غير مدفوعة"),
		Overdue: __("متأخرة"),
		"Partly Paid": __("مدفوعة جزئيًا"),
		Return: __("مرتجع"),
	}
	return map[inv.status] || inv.status || ""
}

function statusClass(inv) {
	if (inv.docstatus === 0) return "bg-gray-100 text-gray-600"
	if (inv.docstatus === 2) return "bg-red-100 text-red-600"
	const s = inv.status || ""
	if (s === "Paid") return "bg-green-100 text-green-700"
	if (s === "Partly Paid") return "bg-blue-100 text-blue-700"
	if (s === "Overdue") return "bg-red-100 text-red-700"
	return "bg-blue-100 text-blue-700"
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
