<!--
  SalesTrendChart — self-contained, dependency-free bar chart for the POS reports
  dashboard, built from CSS flex bars (no SVG, no echarts). Buckets are few (≤31)
  and simple, so plain divs keep the PWA lean and inherit RTL from the ancestor
  `dir="rtl"` for free — the flex row already lays bars right-to-left in Arabic.
  Bars are tap-to-select (touch POS) with a readout line; a native title gives
  desktop hover. The all-zero case renders a clean empty state, never a blank box.
-->
<template>
	<div class="w-full">
		<!-- Loading skeleton -->
		<div v-if="loading" class="h-44 flex items-end gap-1.5 px-1">
			<div
				v-for="i in 8"
				:key="i"
				class="flex-1 bg-gray-100 rounded-t-md animate-pulse"
				:style="{ height: `${25 + ((i * 37) % 60)}%` }"
			/>
		</div>

		<!-- All-zero empty state -->
		<div
			v-else-if="isEmpty"
			data-testid="trend-empty"
			class="h-44 flex flex-col items-center justify-center text-center gap-1"
		>
			<div class="w-11 h-11 rounded-2xl bg-gray-50 flex items-center justify-center">
				<svg class="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 12l3-3 3 3 4-4M3 3v18h18" />
				</svg>
			</div>
			<p class="text-xs font-medium text-gray-400">{{ __("No sales in this period") }}</p>
		</div>

		<!-- Chart -->
		<div v-else>
			<!-- Selected-bar readout -->
			<div class="flex items-baseline justify-between mb-2 min-h-5">
				<span class="text-[11px] font-semibold text-gray-500">{{ activeLabel }}</span>
				<span class="text-sm font-bold text-green-700">
					{{ fmt(activeBucket.sales) }}
					<span class="text-[10px] font-normal text-gray-400">
						· {{ __("{0} invoices", [activeBucket.count]) }}
					</span>
				</span>
			</div>

			<div class="flex items-end gap-1.5 h-40" role="img" :aria-label="__('Sales trend')">
				<button
					v-for="(b, i) in orderedBuckets"
					:key="b.label"
					type="button"
					@click="activeIndex = i"
					:class="[
						'flex-1 h-full flex flex-col items-center justify-end gap-1 group focus:outline-none min-w-0',
					]"
					:title="`${axisLabel(b.label)} · ${fmt(b.sales)}`"
				>
					<!-- Bar track -->
					<div class="w-full flex-1 flex items-end">
						<div
							class="w-full rounded-t-md transition-all duration-200"
							:class="
								i === activeIndex
									? 'bg-green-600'
									: b.sales > 0
										? 'bg-green-400/70 group-hover:bg-green-500'
										: 'bg-gray-100'
							"
							:style="{ height: barHeight(b.sales) }"
						/>
					</div>
					<!-- Axis label -->
					<span
						class="text-[9px] leading-none truncate w-full text-center"
						:class="i === activeIndex ? 'text-green-700 font-bold' : 'text-gray-400'"
					>
						{{ axisLabel(b.label) }}
					</span>
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"

const props = defineProps({
	buckets: { type: Array, default: () => [] },
	granularity: { type: String, default: "day" }, // "hour" | "day"
	currency: { type: String, default: "SAR" },
	rtl: { type: Boolean, default: false },
	loading: { type: Boolean, default: false },
})

const locale = computed(() => (props.rtl ? "ar-SA" : "en-US"))

const isEmpty = computed(
	() => !props.buckets.length || props.buckets.every((b) => !b.sales && !b.count),
)

// RTL flow comes for free: the ancestor sets dir="rtl", so this flex row already
// lays bars right-to-left. Reversing the array too would double-flip it.
const orderedBuckets = computed(() => props.buckets)

const maxSales = computed(() =>
	orderedBuckets.value.reduce((m, b) => Math.max(m, Number(b.sales) || 0), 0),
)

// Default the readout to the tallest bar so the chart opens on the peak.
const activeIndex = ref(0)
watch(
	orderedBuckets,
	(list) => {
		if (!list.length) return
		let peak = 0
		list.forEach((b, i) => {
			if ((Number(b.sales) || 0) > (Number(list[peak].sales) || 0)) peak = i
		})
		activeIndex.value = peak
	},
	{ immediate: true },
)

const activeBucket = computed(
	() => orderedBuckets.value[activeIndex.value] || { sales: 0, count: 0, label: "" },
)
const activeLabel = computed(() => axisLabel(activeBucket.value.label))

function barHeight(sales) {
	const max = maxSales.value
	// A zero-sales day still gets a hairline stub so the day is visible on the axis.
	if (!sales || max <= 0) return "3px"
	const pct = (Number(sales) || 0) / max
	// Keep a visible floor so tiny non-zero bars still register.
	return `${Math.max(pct * 100, 6)}%`
}

function axisLabel(label) {
	if (!label) return ""
	if (props.granularity === "hour") return label // already "14:00"
	// Day buckets arrive as ISO "2026-08-05" → short day/month.
	const d = new Date(`${label}T00:00:00`)
	if (Number.isNaN(d.getTime())) return label
	return d.toLocaleDateString(locale.value, { day: "numeric", month: "short" })
}

function fmt(val) {
	if (val === null || val === undefined) return "0"
	return Number.parseFloat(val).toLocaleString(locale.value, {
		minimumFractionDigits: 0,
		maximumFractionDigits: 0,
	})
}
</script>
