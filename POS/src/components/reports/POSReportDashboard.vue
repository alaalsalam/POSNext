<template>
  <div class="flex flex-col h-full bg-gray-50" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between gap-3 flex-shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-green-600 flex items-center justify-center flex-shrink-0">
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
        class="h-8 px-2 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-green-400 bg-white font-semibold text-gray-800">
        <option v-for="p in profiles" :key="p.name" :value="p.name">{{ p.name }}</option>
      </select>

      <!-- Period pills -->
      <div class="flex items-center gap-1">
        <button v-for="p in periods" :key="p.key"
          @click="selectPeriod(p.key)"
          :class="[
            'h-8 px-3 text-xs font-semibold rounded-lg transition-colors',
            selectedPeriod === p.key
              ? 'bg-green-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          ]">
          {{ p.label }}
        </button>
      </div>

      <!-- Custom date range -->
      <template v-if="selectedPeriod === 'custom'">
        <input type="date" v-model="customFrom" @change="onFilterChange"
          class="h-8 px-2 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-green-400" />
        <span class="text-xs text-gray-400">–</span>
        <input type="date" v-model="customTo" @change="onFilterChange"
          class="h-8 px-2 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-green-400" />
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

      <!-- Filters/load ERROR state (distinct from "no profiles") — retryable -->
      <div v-if="filtersError && !filtersLoading" class="flex flex-col items-center justify-center py-16 text-center">
        <div class="w-14 h-14 rounded-2xl bg-red-50 flex items-center justify-center mb-3">
          <svg class="w-7 h-7 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p class="text-sm font-semibold text-gray-700">{{ __("Couldn't load reports") }}</p>
        <p class="text-xs text-gray-500 mt-1 max-w-xs">{{ filtersError }}</p>
        <button
          data-testid="reports-retry"
          @click="retryFilters"
          class="mt-4 px-4 py-2 rounded-lg bg-green-600 text-white text-xs font-semibold hover:bg-green-700 transition-colors"
        >
          {{ __("Retry") }}
        </button>
      </div>

      <!-- No profile state — only when filters SUCCEEDED and returned an empty list -->
      <div v-else-if="!selectedProfile && !filtersLoading" class="flex flex-col items-center justify-center py-16 text-center">
        <div class="w-14 h-14 rounded-2xl bg-green-50 flex items-center justify-center mb-3">
          <svg class="w-7 h-7 text-green-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <p class="text-sm font-semibold text-gray-500">{{ __("No report-enabled POS Profiles") }}</p>
        <p class="text-xs text-gray-400 mt-1">{{ __("Ask a POS manager to grant profile access and enable reports") }}</p>
      </div>

      <template v-else-if="selectedProfile">
        <!-- ── KPI Cards (with vs-previous trend chips) ── -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3">
          <!-- Gross Sales (headline, spans full width on small screens) -->
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 flex flex-col gap-1 col-span-2 lg:col-span-2 min-h-24">
            <template v-if="summaryLoading">
              <div class="h-4 w-24 bg-gray-100 rounded animate-pulse mb-2"></div>
              <div class="h-9 w-40 bg-gray-100 rounded animate-pulse"></div>
            </template>
            <template v-else>
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">{{ __("Gross Sales") }}</span>
                <span class="text-[10px] text-gray-400">{{ dateRangeLabel }}</span>
              </div>
              <div class="flex items-end justify-between gap-2 mt-1">
                <p class="text-3xl font-black text-gray-900 leading-none">{{ fmt(summary.sales_total) }}</p>
                <span :class="['text-[11px] font-bold px-2 py-0.5 rounded-full flex-shrink-0', salesDelta.cls]">{{ salesDelta.text }}</span>
              </div>
              <p class="text-[11px] text-gray-400 mt-1">{{ __("{0} · vs previous", [currency]) }}</p>
            </template>
          </div>

          <!-- Invoices count -->
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 flex flex-col gap-1 min-h-24">
            <template v-if="summaryLoading">
              <div class="h-3 w-16 bg-gray-100 rounded animate-pulse mb-2"></div>
              <div class="h-7 w-20 bg-gray-100 rounded animate-pulse"></div>
            </template>
            <template v-else>
              <span class="text-xs font-semibold text-gray-500">{{ __("Invoices") }}</span>
              <div class="flex items-end justify-between gap-1 mt-1">
                <p class="text-2xl font-bold text-gray-900 leading-none">{{ countFmt(summary.sales_count) }}</p>
                <span :class="['text-[10px] font-bold px-1.5 py-0.5 rounded-full flex-shrink-0', countDelta.cls]">{{ countDelta.text }}</span>
              </div>
            </template>
          </div>

          <!-- Avg Invoice -->
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 flex flex-col gap-1 min-h-24">
            <template v-if="summaryLoading">
              <div class="h-3 w-16 bg-gray-100 rounded animate-pulse mb-2"></div>
              <div class="h-7 w-24 bg-gray-100 rounded animate-pulse"></div>
            </template>
            <template v-else>
              <span class="text-xs font-semibold text-gray-500">{{ __("Average Invoice") }}</span>
              <div class="flex items-end justify-between gap-1 mt-1">
                <p class="text-2xl font-bold text-green-700 leading-none">{{ fmt(summary.avg_invoice) }}</p>
                <span :class="['text-[10px] font-bold px-1.5 py-0.5 rounded-full flex-shrink-0', avgDelta.cls]">{{ avgDelta.text }}</span>
              </div>
            </template>
          </div>
        </div>

        <!-- Secondary metrics: Returns + Outstanding (visually de-emphasised) -->
        <div v-if="!summaryLoading && (summary.returns_count > 0 || summary.outstanding_total > 0)"
          class="grid grid-cols-2 gap-2 sm:gap-3">
          <div v-if="summary.returns_count > 0"
            class="bg-red-50/60 border border-red-100 rounded-2xl p-3 flex items-center justify-between gap-2">
            <div>
              <p class="text-[11px] font-semibold text-red-600">{{ __("Returns") }}</p>
              <p class="text-lg font-bold text-red-700 leading-tight">{{ fmt(summary.returns_total) }}</p>
              <p class="text-[10px] text-red-400">{{ __("{0} returns", [summary.returns_count]) }}</p>
            </div>
            <span :class="['text-[10px] font-bold px-1.5 py-0.5 rounded-full flex-shrink-0', returnsDelta.cls]">{{ returnsDelta.text }}</span>
          </div>
          <div v-if="summary.outstanding_total > 0"
            class="bg-amber-50/70 border border-amber-100 rounded-2xl p-3 flex flex-col justify-center"
            :class="summary.returns_count > 0 ? '' : 'col-span-2'">
            <p class="text-[11px] font-semibold text-amber-700">{{ __("Credit / Outstanding") }}</p>
            <p class="text-lg font-bold text-amber-800 leading-tight">{{ fmt(summary.outstanding_total) }}</p>
          </div>
        </div>

        <!-- ── Sales Trend (headline visual) ── -->
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
          <div class="flex items-center justify-between gap-3 mb-2">
            <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Sales Trend") }}</h3>
            <span class="text-[10px] text-gray-400">{{ dateRangeLabel }}</span>
          </div>
          <SalesTrendChart
            :buckets="trend.buckets"
            :granularity="trend.granularity"
            :currency="currency"
            :rtl="isRTL"
            :loading="trendLoading"
          />
        </div>

        <!-- ── Reconciliation status ── -->
        <div v-if="!summaryLoading && !paymentLoading && reconStatus.ok !== null"
          :class="[
            'rounded-2xl border p-3 flex items-center gap-3',
            reconStatus.needsReview ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200',
          ]">
          <div :class="[
            'w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0',
            reconStatus.needsReview ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-700',
          ]">
            <svg v-if="reconStatus.needsReview" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M5.07 19h13.86a2 2 0 001.75-2.98l-6.93-12a2 2 0 00-3.5 0l-6.93 12A2 2 0 005.07 19z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <p :class="['text-sm font-bold', reconStatus.needsReview ? 'text-red-700' : 'text-green-800']">
              {{ reconStatus.needsReview ? __("Needs review") : __("All reconciled") }}
            </p>
            <p class="text-[11px]" :class="reconStatus.needsReview ? 'text-red-500' : 'text-green-600'">
              {{ reconStatus.needsReview
                ? __("Totals, settlement or tender do not match — review before closing")
                : __("All reconciliation checks passed") }}
            </p>
          </div>
          <span v-if="reconStatus.needsReview && Math.abs(summary.reconciliation_difference || 0) > 0"
            class="text-xs font-bold text-red-700 flex-shrink-0">
            {{ fmt(summary.reconciliation_difference) }}
          </span>
        </div>

        <!-- ── Payment Methods ── -->
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
          <div class="flex items-center justify-between gap-3 mb-3">
            <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Payment Methods") }}</h3>
            <span v-if="!paymentLoading && payment.settlement_reconciled !== undefined" :class="['text-[10px] font-semibold', payment.settlement_reconciled && payment.tender_reconciled ? 'text-green-600' : 'text-red-600']">
              {{ payment.settlement_reconciled && payment.tender_reconciled ? __("Payments reconciled") : __("Payments need review") }}
            </span>
          </div>
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
                    <span class="text-sm font-bold text-gray-900 ms-2 flex-shrink-0">{{ __("Net {0}", [fmt(m.net)]) }}</span>
                  </div>
                  <div class="flex flex-wrap gap-x-3 gap-y-0.5 mb-1 text-[10px]">
                    <span class="text-green-700">{{ __("Received {0}", [fmt(m.received)]) }}</span>
                    <span class="text-red-600">{{ __("Refunded {0}", [fmt(m.refunded)]) }}</span>
                  </div>
                  <!-- Progress bar -->
                  <div class="flex items-center gap-2">
                    <div class="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div class="h-full bg-green-500 rounded-full" :style="{ width: m.percentage + '%' }" />
                    </div>
                    <span class="text-[10px] text-gray-400 font-semibold flex-shrink-0">{{ m.percentage }}%</span>
                    <span class="text-[10px] text-gray-400 flex-shrink-0">{{ __("{0} transactions", [m.count]) }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-gray-100 text-center">
              <div><p class="text-[10px] text-gray-400">{{ __("Received") }}</p><p class="text-xs font-bold text-green-700">{{ fmt(payment.received_total) }}</p></div>
              <div><p class="text-[10px] text-gray-400">{{ __("Refunded") }}</p><p class="text-xs font-bold text-red-600">{{ fmt(payment.refunded_total) }}</p></div>
              <div><p class="text-[10px] text-gray-400">{{ __("Net") }}</p><p class="text-xs font-bold text-gray-900">{{ fmt(payment.net_total) }}</p></div>
            </div>
          </template>
        </div>

        <!-- ── Top Items / Fast Movers ── -->
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
          <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">{{ __("Top Items") }}</h3>
          <template v-if="topLoading">
            <div class="flex flex-col gap-2">
              <div v-for="i in 5" :key="i" class="h-10 bg-gray-50 rounded-xl animate-pulse" />
            </div>
          </template>
          <template v-else-if="!topItems.items?.length">
            <p class="text-xs text-gray-400 text-center py-6">{{ __("No item sales for this period") }}</p>
          </template>
          <template v-else>
            <div class="flex flex-col gap-2.5">
              <div v-for="(it, i) in topItems.items" :key="it.item_code" class="flex items-center gap-3">
                <span :class="[
                  'w-6 h-6 rounded-lg flex items-center justify-center text-[11px] font-bold flex-shrink-0',
                  i === 0 ? 'bg-amber-100 text-amber-700' : i === 1 ? 'bg-gray-100 text-gray-600' : i === 2 ? 'bg-orange-100 text-orange-700' : 'bg-gray-50 text-gray-400',
                ]">{{ i + 1 }}</span>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between gap-2 mb-1">
                    <span class="text-xs font-semibold text-gray-800 truncate">{{ it.item_name }}</span>
                    <span class="text-xs font-bold text-gray-900 flex-shrink-0">{{ fmt(it.amount) }}</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <div class="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div class="h-full bg-green-500 rounded-full transition-all" :style="{ width: topItemShare(it.amount) + '%' }" />
                    </div>
                    <span class="text-[10px] text-gray-400 flex-shrink-0">{{ __("{0} {1}", [countFmt(it.qty), it.uom || __("Nos", null, "UOM")]) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
          <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">{{ __("Detailed Reports") }}</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <a v-for="report in deskReports" :key="report.name" :href="deskReportUrl(report.name)" target="_blank" rel="noopener"
              class="min-h-11 px-3 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:border-green-300 hover:bg-green-50 flex items-center justify-between gap-2">
              <span>{{ report.label }}</span><span aria-hidden="true">↗</span>
            </a>
          </div>
        </div>

        <!-- ── Recent Transactions ── -->
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
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
                  tx.is_return ? 'bg-red-100 text-red-600' : 'bg-green-50 text-green-700'
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
import { call } from "@/utils/apiWrapper"
import { buildDeskReportUrl, isRtlLocale } from "./reportUtils"
import SalesTrendChart from "./SalesTrendChart.vue"

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
// Distinct from the "no profiles" empty state: set only when loading the filters
// (or the initial data) FAILS, so a broken call never masquerades as "no profiles".
const filtersError = ref("")
const loading = ref(false)

const summary = ref({})
const payment = ref({ methods: [] })
const transactions = ref({ transactions: [], count: 0 })
const trend = ref({ granularity: "day", buckets: [] })
const topItems = ref({ items: [] })
const summaryLoading = ref(false)
const paymentLoading = ref(false)
const txLoading = ref(false)
const trendLoading = ref(false)
const topLoading = ref(false)
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
	return p?.currency || summary.value.currency || "SAR"
})

// A trend delta is a percent number, or null when there is no prior-period
// baseline. `positiveIsGood=false` inverts the color mapping for metrics where a
// rise is bad (returns): up → red, down → green.
function deltaChip(value, positiveIsGood = true) {
	if (value === null || value === undefined) {
		return { text: "—", dir: "flat", cls: "text-gray-400 bg-gray-100" }
	}
	const rounded = Math.round(Number(value) * 10) / 10
	const arrow = rounded > 0 ? "▲" : rounded < 0 ? "▼" : ""
	const text = `${arrow} ${Math.abs(rounded)}%`.trim()
	if (rounded === 0) return { text: "0%", dir: "flat", cls: "text-gray-500 bg-gray-100" }
	const good = rounded > 0 === positiveIsGood
	return {
		text,
		dir: rounded > 0 ? "up" : "down",
		cls: good ? "text-green-700 bg-green-50" : "text-red-600 bg-red-50",
	}
}

const salesDelta = computed(() => deltaChip(summary.value.delta?.sales_total))
const countDelta = computed(() => deltaChip(summary.value.delta?.sales_count))
const avgDelta = computed(() => deltaChip(summary.value.delta?.avg_invoice))
const returnsDelta = computed(() => deltaChip(summary.value.delta?.returns_total, false))

// Reconciliation: red when ANY of the three flags the backend returns is false.
// Renders partial state — a failed summary/payment call leaves its flags undefined,
// which we treat as "unknown" (not a failure) rather than crashing.
const reconStatus = computed(() => {
	const flags = [
		summary.value.reconciled,
		payment.value.settlement_reconciled,
		payment.value.tender_reconciled,
	]
	const known = flags.filter((f) => f !== undefined)
	if (!known.length) return { ok: null, needsReview: false }
	const needsReview = known.some((f) => f === false)
	return { ok: !needsReview, needsReview }
})

// Top items: proportional bar as a share of the leading item's amount.
const topItemsMax = computed(() =>
	(topItems.value.items || []).reduce((m, it) => Math.max(m, Number(it.amount) || 0), 0),
)
function topItemShare(amount) {
	const max = topItemsMax.value
	if (max <= 0) return 0
	return Math.max(Math.round(((Number(amount) || 0) / max) * 100), 4)
}

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

function countFmt(val) {
	// parseFloat (not parseInt) so decimal quantities for weighed items aren't truncated.
	return Number.parseFloat(val || 0).toLocaleString(locale.value, {
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
	filtersError.value = ""
	try {
		const res = await call("pos_next.api.reports.get_report_filters")
		profiles.value = res?.pos_profiles || []
		periods.value = res?.periods || []
		deskReports.value = res?.desk_reports || []
		// Auto-select first profile
		if (profiles.value.length) selectedProfile.value = profiles.value[0].name
	} catch (e) {
		// A failed load must NOT look like "no profiles enabled" — surface a
		// distinct, retryable error state instead.
		filtersError.value = e?.message || __("Failed to load report filters")
	} finally {
		filtersLoading.value = false
	}
}

async function retryFilters() {
	await loadFilters()
	if (selectedProfile.value) loadAll()
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
	trendLoading.value = true
	topLoading.value = true

	// Each call catches its own failure so one broken endpoint can't blank the rest;
	// only the summary failure surfaces the top-level error banner.
	const [sumRes, payRes, txRes, trendRes, topRes] = await Promise.all([
		call("pos_next.api.reports.get_daily_summary", args).catch((e) => {
			errorMsg.value = e?.message || __("Failed to load report summary")
			return null
		}),
		call("pos_next.api.reports.get_payment_breakdown", args).catch((e) => {
			console.error(e)
			return null
		}),
		call("pos_next.api.reports.get_recent_transactions", { ...args, limit: 20 }).catch(
			(e) => {
				console.error(e)
				return null
			},
		),
		call("pos_next.api.reports.get_sales_trend", args).catch((e) => {
			console.error(e)
			return null
		}),
		call("pos_next.api.reports.get_top_items", { ...args, limit: 8 }).catch((e) => {
			console.error(e)
			return null
		}),
	])

	summaryLoading.value = false
	paymentLoading.value = false
	txLoading.value = false
	trendLoading.value = false
	topLoading.value = false
	loading.value = false

	if (sumRes) summary.value = sumRes
	if (payRes) payment.value = payRes
	if (txRes) transactions.value = txRes
	if (trendRes) trend.value = trendRes
	if (topRes) topItems.value = topRes
}

function openInvoice(tx) {
	window.open(`/app/sales-invoice/${encodeURIComponent(tx.name)}`, "_blank")
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
	await loadFilters()
	// Best-effort: pre-select the profile of the current open shift.
	try {
		const shiftRes = await call("pos_next.api.reports.get_current_shift_profile")
		if (shiftRes?.pos_profile) {
			const p = shiftRes.pos_profile
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
