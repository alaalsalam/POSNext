<template>
  <div class="flex flex-col h-full bg-gray-50" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between gap-3 flex-shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-emerald-600 flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <div>
          <h2 class="text-base font-bold text-gray-900">{{ __("Reports") }}</h2>
          <p class="text-xs text-gray-500">{{ profileLabel }}</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button @click="loadAll" :disabled="loading" class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100 disabled:opacity-40">
          <svg :class="['w-4 h-4', loading ? 'animate-spin' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        <button @click="$emit('close')" class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Filters bar -->
    <div class="bg-white border-b border-gray-100 px-3 py-2 flex flex-wrap items-center gap-2 flex-shrink-0">
      <!-- POS Profile selector (only if >1) -->
      <select v-if="profiles.length > 1" v-model="selectedProfile" @change="onFilterChange"
        class="h-8 px-2 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white font-semibold text-gray-800">
        <option v-for="p in profiles" :key="p.name" :value="p.name">{{ p.name }}</option>
      </select>

      <!-- Period pills -->
      <div class="flex items-center gap-1">
        <button v-for="p in periods" :key="p.key"
          @click="selectPeriod(p.key)"
          :class="[
            'h-8 px-3 text-xs font-semibold rounded-lg transition-colors',
            selectedPeriod === p.key
              ? 'bg-emerald-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          ]">
          {{ p.label }}
        </button>
      </div>

      <!-- Custom date range -->
      <template v-if="selectedPeriod === 'custom'">
        <input type="date" v-model="customFrom" @change="onFilterChange"
          class="h-8 px-2 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-emerald-400" />
        <span class="text-xs text-gray-400">–</span>
        <input type="date" v-model="customTo" @change="onFilterChange"
          class="h-8 px-2 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-emerald-400" />
      </template>
    </div>

    <!-- Error banner -->
    <div v-if="errorMsg" class="mx-3 mt-3 p-3 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2 flex-shrink-0">
      <svg class="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-xs text-red-700 flex-1">{{ errorMsg }}</p>
      <button @click="errorMsg=''" class="text-red-400 hover:text-red-600 text-lg leading-none">×</button>
    </div>

    <!-- Scrollable content -->
    <div class="flex-1 overflow-y-auto p-3 flex flex-col gap-3">

      <!-- No profile state -->
      <div v-if="!selectedProfile && !filtersLoading" class="flex flex-col items-center justify-center py-16 text-center">
        <div class="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center mb-3">
          <svg class="w-7 h-7 text-emerald-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <p class="text-sm font-semibold text-gray-500">{{ __("No report-enabled POS Profiles") }}</p>
        <p class="text-xs text-gray-400 mt-1">{{ __("Ask a POS manager to grant profile access and enable reports") }}</p>
      </div>

      <template v-else-if="selectedProfile">
        <!-- ── KPI Cards ── -->
        <div class="grid grid-cols-2 gap-2">
          <!-- Sales Total -->
          <div class="bg-white rounded-2xl border border-gray-100 p-4 flex flex-col gap-1 col-span-2 min-h-24">
            <template v-if="summaryLoading">
              <div class="h-4 w-24 bg-gray-100 rounded animate-pulse mb-2"></div>
              <div class="h-8 w-36 bg-gray-100 rounded animate-pulse"></div>
            </template>
            <template v-else>
              <div class="flex items-center justify-between">
                <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">{{ __("Gross Sales") }}</span>
                <span class="text-[10px] text-gray-400">{{ dateRangeLabel }}</span>
              </div>
              <p class="text-3xl font-black text-gray-900 mt-1">{{ fmt(summary.sales_total) }}</p>
              <p class="text-xs text-gray-500">{{ __("{0} invoices", [summary.sales_count]) }}</p>
            </template>
          </div>

          <!-- Avg Invoice -->
          <div class="bg-white rounded-2xl border border-gray-100 p-4 flex flex-col gap-1 min-h-24">
            <template v-if="summaryLoading">
              <div class="h-3 w-20 bg-gray-100 rounded animate-pulse mb-2"></div>
              <div class="h-7 w-28 bg-gray-100 rounded animate-pulse"></div>
            </template>
            <template v-else>
              <span class="text-xs font-semibold text-gray-500">{{ __("Average Invoice") }}</span>
              <p class="text-2xl font-bold text-emerald-700 mt-1">{{ fmt(summary.avg_invoice) }}</p>
            </template>
          </div>

          <!-- Net Sales -->
          <div class="bg-white rounded-2xl border border-gray-100 p-4 flex flex-col gap-1 min-h-24">
            <template v-if="summaryLoading">
              <div class="h-3 w-20 bg-gray-100 rounded animate-pulse mb-2"></div>
              <div class="h-7 w-28 bg-gray-100 rounded animate-pulse"></div>
            </template>
            <template v-else>
              <span class="text-xs font-semibold text-gray-500">{{ __("Net Sales") }}</span>
              <p class="text-2xl font-bold text-gray-900 mt-1">{{ fmt(summary.net_sales) }}</p>
            </template>
          </div>

          <!-- Returns (only if any) -->
          <div v-if="!summaryLoading && summary.returns_count > 0"
            class="bg-red-50 border border-red-100 rounded-2xl p-4 flex flex-col gap-1 min-h-20">
            <span class="text-xs font-semibold text-red-600">{{ __("Returns") }}</span>
            <p class="text-xl font-bold text-red-700">{{ fmt(summary.returns_total) }}</p>
            <p class="text-[10px] text-red-400">{{ __("{0} returns", [summary.returns_count]) }}</p>
          </div>

          <!-- Outstanding -->
          <div v-if="!summaryLoading && summary.outstanding_total > 0"
            class="bg-amber-50 border border-amber-100 rounded-2xl p-4 flex flex-col gap-1 min-h-20"
            :class="summary.returns_count > 0 ? '' : 'col-span-2'">
            <span class="text-xs font-semibold text-amber-700">{{ __("Credit / Outstanding") }}</span>
            <p class="text-xl font-bold text-amber-800">{{ fmt(summary.outstanding_total) }}</p>
          </div>
        </div>

        <!-- ── Payment Methods ── -->
        <div class="bg-white rounded-2xl border border-gray-100 p-4">
          <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">{{ __("Payment Methods") }}</h3>
          <template v-if="paymentLoading">
            <div class="flex flex-col gap-2">
              <div v-for="i in 3" :key="i" class="h-12 bg-gray-50 rounded-xl animate-pulse" />
            </div>
          </template>
          <template v-else-if="!payment.methods?.length">
            <p class="text-xs text-gray-400 text-center py-4">{{ __("No payment data for this period") }}</p>
          </template>
          <template v-else>
            <div class="flex flex-col gap-2">
              <div v-for="m in payment.methods" :key="m.mode"
                class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <div class="w-9 h-9 rounded-lg bg-white border border-gray-100 flex items-center justify-center flex-shrink-0 text-base">
                  {{ paymentIcon(m.mode) }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-sm font-semibold text-gray-800 truncate">{{ m.mode }}</span>
                    <span class="text-sm font-bold text-gray-900 ms-2 flex-shrink-0">{{ fmt(m.amount) }}</span>
                  </div>
                  <!-- Progress bar -->
                  <div class="flex items-center gap-2">
                    <div class="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div class="h-full bg-emerald-500 rounded-full" :style="{ width: m.percentage + '%' }" />
                    </div>
                    <span class="text-[10px] text-gray-400 font-semibold flex-shrink-0">{{ m.percentage }}%</span>
                    <span class="text-[10px] text-gray-400 flex-shrink-0">{{ __("{0} transactions", [m.count]) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <div class="bg-white rounded-2xl border border-gray-100 p-4">
          <div class="flex items-center justify-between gap-3 mb-3">
            <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Detailed Reports") }}</h3>
            <span :class="['text-[10px] font-semibold', summary.reconciled ? 'text-emerald-600' : 'text-red-600']">
              {{ summary.reconciled ? __("ERPNext totals reconciled") : __("Totals need review") }}
            </span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <a v-for="report in deskReports" :key="report.name" :href="deskReportUrl(report.name)" target="_blank" rel="noopener"
              class="min-h-11 px-3 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:border-emerald-300 hover:bg-emerald-50 flex items-center justify-between gap-2">
              <span>{{ report.label }}</span><span aria-hidden="true">↗</span>
            </a>
          </div>
        </div>

        <!-- ── Recent Transactions ── -->
        <div class="bg-white rounded-2xl border border-gray-100 p-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Recent Transactions") }}</h3>
            <span v-if="transactions.count > 0" class="text-[10px] text-gray-400">{{ __("Latest {0}", [transactions.count]) }}</span>
          </div>
          <template v-if="txLoading">
            <div class="flex flex-col gap-2">
              <div v-for="i in 5" :key="i" class="h-14 bg-gray-50 rounded-xl animate-pulse" />
            </div>
          </template>
          <template v-else-if="!transactions.transactions?.length">
            <div class="text-center py-8">
              <p class="text-xs text-gray-400">{{ __("No invoices for this period") }}</p>
            </div>
          </template>
          <template v-else>
            <div class="flex flex-col gap-1.5">
              <div v-for="tx in transactions.transactions" :key="tx.name"
                class="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer group"
                @click="openInvoice(tx)">
                <!-- Return indicator OR normal -->
                <div :class="[
                  'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-sm',
                  tx.is_return ? 'bg-red-100 text-red-600' : 'bg-emerald-50 text-emerald-700'
                ]">
                  {{ tx.is_return ? '↩' : '✓' }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-1.5 flex-wrap">
                    <span class="text-xs font-bold text-gray-800">{{ tx.name }}</span>
                    <span v-if="tx.is_return" class="text-[9px] bg-red-100 text-red-600 font-bold px-1 rounded">{{ __("Return") }}</span>
                  </div>
                  <div class="flex items-center gap-2 mt-0.5">
                    <span class="text-[10px] text-gray-400">{{ formatTime(tx.posting_datetime) }}</span>
                    <span v-if="tx.customer_name && tx.customer_name !== 'Guest'" class="text-[10px] text-gray-500 truncate max-w-20">{{ tx.customer_name }}</span>
                    <span v-if="tx.payment_method" class="text-[10px] text-gray-400">· {{ tx.payment_method }}</span>
                  </div>
                </div>
                <div class="text-end flex-shrink-0">
                  <p :class="['text-sm font-bold', tx.is_return ? 'text-red-600' : 'text-gray-900']">
                    {{ tx.is_return ? '-' : '' }}{{ fmt(Math.abs(tx.grand_total)) }}
                  </p>
                  <p v-if="tx.outstanding_amount > 0" class="text-[10px] text-amber-600">{{ __("Outstanding") }}</p>
                </div>
                <!-- Open arrow -->
                <svg class="w-3.5 h-3.5 text-gray-300 group-hover:text-gray-500 flex-shrink-0 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
              </div>
            </div>
          </template>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue"
import { buildDeskReportUrl, isRtlLocale } from "./reportUtils"

const emit = defineEmits(["close"])

// ─── State ────────────────────────────────────────────────────────────────────
const profiles = ref([])
const periods = ref([])
const deskReports = ref([])
const selectedProfile = ref(null)
const selectedPeriod = ref("today")
const customFrom = ref("")
const customTo = ref("")
const filtersLoading = ref(false)
const loading = ref(false)

const summary = ref({})
const payment = ref({ methods: [] })
const transactions = ref({ transactions: [], count: 0 })
const summaryLoading = ref(false)
const paymentLoading = ref(false)
const txLoading = ref(false)
const errorMsg = ref("")
const isRTL = computed(() =>
	isRtlLocale(frappe.boot?.lang, document.documentElement.dir),
)
const locale = computed(() => (isRTL.value ? "ar-SA" : "en-US"))

// ─── Computed ─────────────────────────────────────────────────────────────────
const profileLabel = computed(() => {
	if (!selectedProfile.value) return __("Select POS Profile")
	const p = profiles.value.find((x) => x.name === selectedProfile.value)
	return p ? p.name : selectedProfile.value
})

const dateRangeLabel = computed(() => {
	if (!summary.value.from_date) return ""
	const fd = summary.value.from_date
	const td = summary.value.to_date
	if (fd === td) return formatDate(fd)
	return `${formatDate(fd)} – ${formatDate(td)}`
})

const currency = computed(() => {
	const p = profiles.value.find((x) => x.name === selectedProfile.value)
	return p?.currency || "SAR"
})

// ─── Helpers ──────────────────────────────────────────────────────────────────
const PAYMENT_ICONS = {
	Cash: "💵",
	كاش: "💵",
	نقد: "💵",
	Card: "💳",
	"Debit Card": "💳",
	"Credit Card": "💳",
	مدى: "💳",
	Mada: "💳",
	مدي: "💳",
	Transfer: "🏦",
	"Bank Transfer": "🏦",
	تحويل: "🏦",
	Wallet: "👛",
	محفظة: "👛",
}
function paymentIcon(mode) {
	return PAYMENT_ICONS[mode] || "💰"
}

function fmt(val) {
	if (val === null || val === undefined) return "0.00"
	return Number.parseFloat(val).toLocaleString(locale.value, {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	})
}

function formatDate(d) {
	if (!d) return ""
	return new Date(`${d}T00:00:00`).toLocaleDateString(locale.value, {
		year: "numeric",
		month: "short",
		day: "numeric",
	})
}

function formatTime(dt) {
	if (!dt) return ""
	return new Date(dt).toLocaleTimeString(locale.value, {
		hour: "2-digit",
		minute: "2-digit",
	})
}

function deskReportUrl(name) {
	return buildDeskReportUrl(
		name,
		selectedProfile.value,
		summary.value.from_date,
		summary.value.to_date,
	)
}

// ─── Actions ──────────────────────────────────────────────────────────────────
function selectPeriod(key) {
	selectedPeriod.value = key
	if (key !== "custom") onFilterChange()
}

function onFilterChange() {
	if (!selectedProfile.value) return
	if (
		selectedPeriod.value === "custom" &&
		(!customFrom.value || !customTo.value)
	)
		return
	loadAll()
}

async function loadFilters() {
	filtersLoading.value = true
	try {
		const res = await frappe.call({
			method: "pos_next.api.reports.get_report_filters",
			error: (r) => {
				errorMsg.value = r?.message || __("Failed to load report filters")
			},
		})
		if (res?.message) {
			profiles.value = res.message.pos_profiles || []
			periods.value = res.message.periods || []
			deskReports.value = res.message.desk_reports || []
			// Auto-select first profile
			if (profiles.value.length) selectedProfile.value = profiles.value[0].name
		}
	} catch (e) {
		console.error(e)
	} finally {
		filtersLoading.value = false
	}
}

async function loadAll() {
	if (!selectedProfile.value) return
	loading.value = true
	errorMsg.value = ""
	const args = {
		pos_profile: selectedProfile.value,
		period: selectedPeriod.value,
		from_date: selectedPeriod.value === "custom" ? customFrom.value : null,
		to_date: selectedPeriod.value === "custom" ? customTo.value : null,
	}

	summaryLoading.value = true
	paymentLoading.value = true
	txLoading.value = true

	const [sumRes, payRes, txRes] = await Promise.all([
		frappe.call({
			method: "pos_next.api.reports.get_daily_summary",
			args,
			error: (r) => {
				errorMsg.value = r?.message || __("Failed to load report summary")
			},
		}),
		frappe.call({
			method: "pos_next.api.reports.get_payment_breakdown",
			args,
			error: (r) => {
				console.error(r)
			},
		}),
		frappe.call({
			method: "pos_next.api.reports.get_recent_transactions",
			args: { ...args, limit: 20 },
			error: (r) => {
				console.error(r)
			},
		}),
	])

	summaryLoading.value = false
	paymentLoading.value = false
	txLoading.value = false
	loading.value = false

	if (sumRes?.message) summary.value = sumRes.message
	if (payRes?.message) payment.value = payRes.message
	if (txRes?.message) transactions.value = txRes.message
}

function openInvoice(tx) {
	try {
		const url = frappe.utils.get_url_to_form("Sales Invoice", tx.name)
		window.open(url, "_blank")
	} catch (e) {
		// Fallback
		window.open(`/app/sales-invoice/${tx.name}`, "_blank")
	}
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
	await loadFilters()
	// Try to pre-select the profile of the current open shift
	try {
		const shiftRes = await frappe.call({
			method: "pos_next.api.reports.get_current_shift_profile",
		})
		if (shiftRes?.message?.pos_profile) {
			const p = shiftRes.message.pos_profile
			if (profiles.value.find((x) => x.name === p)) selectedProfile.value = p
		}
	} catch (e) {
		/* ignore */
	}
	if (selectedProfile.value) loadAll()
})

watch(selectedProfile, () => {
	if (selectedProfile.value) loadAll()
})
</script>
