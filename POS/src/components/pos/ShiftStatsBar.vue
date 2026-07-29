<template>
	<div
		v-if="hasOpenShift && currentShiftName"
		class="bg-gradient-to-r from-emerald-950 to-slate-900 border-b border-emerald-800/40 px-3 py-1.5 flex items-center gap-0 overflow-x-auto no-scrollbar"
	>
		<!-- Loading skeleton -->
		<template v-if="loading && !stats">
			<div class="flex items-center gap-4 w-full">
				<div v-for="i in 4" :key="i" class="h-5 w-24 bg-white/10 rounded animate-pulse flex-shrink-0"></div>
			</div>
		</template>

		<!-- Stats pills -->
		<template v-else-if="stats">
			<!-- Invoices -->
			<div class="flex items-center gap-1.5 px-3 py-0.5 flex-shrink-0">
				<svg class="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
				</svg>
				<span class="text-[11px] text-emerald-300/70 font-medium whitespace-nowrap">{{ __("Invoices") }}</span>
				<span class="text-[12px] text-white font-bold">{{ stats.sales_count }}</span>
			</div>

			<div class="w-px h-3.5 bg-white/15 flex-shrink-0"></div>

			<!-- Net Sales -->
			<div class="flex items-center gap-1.5 px-3 py-0.5 flex-shrink-0">
				<svg class="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				<span class="text-[11px] text-emerald-300/70 font-medium whitespace-nowrap">{{ __("Net Sales") }}</span>
				<span class="text-[12px] text-white font-bold">{{ formattedNetTotal }}</span>
			</div>

			<!-- Returns (only if any) -->
			<template v-if="stats.returns_count > 0">
				<div class="w-px h-3.5 bg-white/15 flex-shrink-0"></div>
				<div class="flex items-center gap-1.5 px-3 py-0.5 flex-shrink-0">
					<svg class="w-3.5 h-3.5 text-rose-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
					</svg>
					<span class="text-[11px] text-rose-300/70 font-medium whitespace-nowrap">{{ __("Returns") }}</span>
					<span class="text-[12px] text-rose-300 font-bold">{{ stats.returns_count }}</span>
				</div>
			</template>

			<div class="w-px h-3.5 bg-white/15 flex-shrink-0"></div>

			<!-- Payment breakdown pills (top methods only) -->
			<template v-for="(entry, idx) in topPayments" :key="idx">
				<div class="flex items-center gap-1.5 px-3 py-0.5 flex-shrink-0">
					<span class="text-base leading-none flex-shrink-0">{{ entry.icon }}</span>
					<span class="text-[11px] text-slate-400 font-medium whitespace-nowrap">{{ entry.mode }}</span>
					<span class="text-[12px] text-slate-200 font-bold">{{ formatCompact(entry.total) }}</span>
				</div>
				<div v-if="idx < topPayments.length - 1" class="w-px h-3.5 bg-white/15 flex-shrink-0"></div>
			</template>

			<!-- Last invoice time (right-aligned) -->
			<div class="ms-auto flex items-center gap-1.5 px-3 py-0.5 flex-shrink-0">
				<svg class="w-3 h-3 text-slate-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				<span class="text-[10px] text-slate-500 whitespace-nowrap">
					{{ lastInvoiceLabel }}
				</span>
				<!-- Refresh indicator -->
				<button
					@click="refresh"
					:class="['rounded p-0.5 transition-colors', refreshing ? 'animate-spin text-emerald-400' : 'text-slate-600 hover:text-slate-400']"
					:title="__('Refresh stats')"
					:aria-label="__('Refresh stats')"
				>
					<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
					</svg>
				</button>
			</div>
		</template>
	</div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { formatCurrency } from "@/utils/currency";

const props = defineProps({
	hasOpenShift: { type: Boolean, default: false },
	currentShiftName: { type: String, default: null },
	currency: { type: String, default: "SAR" },
});

const emit = defineEmits(["stats-loaded"]);

const stats = ref(null);
const loading = ref(false);
const refreshing = ref(false);
let pollInterval = null;

// Payment method icon map
const PAYMENT_ICONS = {
	Cash: "💵",
	كاش: "💵",
	"نقد": "💵",
	"بطاقة": "💳",
	Card: "💳",
	"Debit Card": "💳",
	"Credit Card": "💳",
	"مدى": "💳",
	Mada: "💳",
	Transfer: "🏦",
	"Bank Transfer": "🏦",
	"تحويل": "🏦",
	Wallet: "👛",
	"محفظة": "👛",
};

function getPaymentIcon(mode) {
	return PAYMENT_ICONS[mode] || "💰";
}

// Show top 3 payment methods with actual amounts
const topPayments = computed(() => {
	if (!stats.value?.payment_totals) return [];
	return Object.entries(stats.value.payment_totals)
		.filter(([, total]) => total > 0)
		.sort(([, a], [, b]) => b - a)
		.slice(0, 3)
		.map(([mode, total]) => ({ mode, total, icon: getPaymentIcon(mode) }));
});

const formattedNetTotal = computed(() => {
	if (!stats.value) return "-";
	return formatCurrency(stats.value.net_total, props.currency);
});

const lastInvoiceLabel = computed(() => {
	if (!stats.value?.last_invoice_time) return __("No invoices yet");
	const d = new Date(stats.value.last_invoice_time);
	return __("Last: {0}", [d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })]);
});

function formatCompact(value) {
	if (!value && value !== 0) return "-";
	const num = parseFloat(value);
	if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
	if (num >= 1000) return (num / 1000).toFixed(1) + "K";
	return num.toFixed(0);
}

async function fetchStats() {
	if (!props.currentShiftName) return;
	try {
		const res = await frappe.call({
			method: "pos_next.api.shifts.get_shift_stats",
			args: { opening_shift: props.currentShiftName },
		});
		if (res?.message) {
			stats.value = res.message;
			emit("stats-loaded", res.message);
		}
	} catch (e) {
		// Silent: stats bar is informational; don't surface errors to user
	}
}

async function refresh() {
	refreshing.value = true;
	await fetchStats();
	refreshing.value = false;
}

async function load() {
	loading.value = true;
	await fetchStats();
	loading.value = false;
}

// Re-fetch when shift changes (covers the case where onMounted fires before shiftName is available)
watch(() => props.currentShiftName, (val) => {
	if (val) { load(); startPolling(); }
	else { stats.value = null; stopPolling(); }
}, { immediate: false });

// Poll every 45 seconds for live updates
function startPolling() {
	stopPolling();
	pollInterval = setInterval(fetchStats, 45_000);
}

function stopPolling() {
	if (pollInterval) {
		clearInterval(pollInterval);
		pollInterval = null;
	}
}

onMounted(() => {
	if (props.hasOpenShift && props.currentShiftName) {
		load();
		startPolling();
	}
});

onUnmounted(() => {
	stopPolling();
});

// Expose refresh so parent can trigger after invoice submission
defineExpose({ refresh });
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
