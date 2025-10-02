<template>
	<div class="flex flex-col h-full bg-gray-50">
		<!-- Item Groups Filter Tabs -->
		<div class="px-3 pt-3 pb-2 bg-white border-b border-gray-200">
			<div class="flex items-center space-x-2 overflow-x-auto pb-1">
				<button
					@click="itemStore.setSelectedItemGroup(null)"
					:class="[
						'flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all',
						!selectedItemGroup
							? 'bg-blue-50 text-blue-600 border border-blue-200'
							: 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50',
					]"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
					</svg>
					<span>All Items</span>
				</button>
				<button
					v-for="group in itemGroups"
					:key="group.item_group"
					@click="itemStore.setSelectedItemGroup(group.item_group)"
					:class="[
						'flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all',
						selectedItemGroup === group.item_group
							? 'bg-blue-50 text-blue-600 border border-blue-200'
							: 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50',
					]"
				>
					<span>{{ group.item_group }}</span>
				</button>
			</div>
		</div>

		<!-- Search Bar with Barcode Scanner and View Controls -->
		<div class="px-3 py-2 bg-white border-b border-gray-200">
			<div class="flex items-center space-x-2">
				<div class="flex-1 relative">
					<!-- Search Icon -->
					<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
						<svg
							class="h-4 w-4 text-gray-400"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
							/>
						</svg>
					</div>
					<!-- Search Input -->
					<input
						id="item-search"
						name="item-search"
						:value="searchTerm"
						@input="handleSearchInput"
						type="text"
						placeholder="Search by item code, name or scan barcode"
						class="w-full text-sm border border-gray-300 rounded-md px-3 py-2 pl-10 pr-10 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						@keyup.enter="handleBarcodeSearch"
						aria-label="Search items"
					/>
					<!-- Barcode Scan Icon -->
					<div class="absolute inset-y-0 right-0 pr-3 flex items-center">
						<button
							@click="handleBarcodeScan"
							class="p-1 hover:bg-gray-100 rounded transition-colors"
							title="Scan Barcode"
						>
							<svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"/>
							</svg>
						</button>
					</div>
				</div>
				<div class="flex items-center space-x-0.5 bg-gray-100 rounded-md p-0.5">
					<button
						@click="viewMode = 'grid'"
						:class="[
							'p-1.5 rounded transition-all',
							viewMode === 'grid' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'
						]"
						title="Grid View"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
						</svg>
					</button>
					<button
						@click="viewMode = 'list'"
						:class="[
							'p-1.5 rounded transition-all',
							viewMode === 'list' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'
						]"
						title="List View"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
						</svg>
					</button>
				</div>
			</div>
		</div>

		<!-- Loading State (includes async search) -->
		<div v-if="loading || isSearchingAsync" class="flex-1 flex items-center justify-center p-3">
			<div class="text-center py-8">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
				<p class="mt-3 text-xs text-gray-500">
					{{ isSearchingAsync ? 'Searching items...' : 'Loading items...' }}
				</p>
			</div>
		</div>

		<!-- Empty State -->
		<div
			v-else-if="!items || items.length === 0"
			class="flex-1 flex items-center justify-center p-3"
		>
			<div class="text-center py-8">
				<svg
					class="mx-auto h-8 w-8 text-gray-400"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
					/>
				</svg>
				<p v-if="searchTerm || selectedItemGroup" class="mt-2 text-xs font-medium text-gray-700">
					No results for <span v-if="searchTerm">"{{ searchTerm }}"</span><span v-if="searchTerm && selectedItemGroup"> in </span><span v-if="selectedItemGroup">{{ selectedItemGroup }}</span>
				</p>
				<p v-else class="mt-2 text-xs text-gray-500">No items available</p>
			</div>
		</div>

		<!-- Grid View -->
		<div v-else-if="viewMode === 'grid'" class="flex-1 overflow-y-auto p-3">
			<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2.5">
				<div
					v-for="item in items"
					:key="item.item_code"
					@click="handleItemClick(item)"
					class="relative bg-white border border-gray-200 rounded-lg p-2.5 cursor-pointer hover:border-blue-400 hover:shadow-md transition-all"
				>
					<!-- Item Image with Stock Badge -->
					<div class="relative aspect-square bg-gray-100 rounded-md mb-2 flex items-center justify-center overflow-hidden">
						<!-- Stock Badge -->
						<div
							:class="[
								'absolute top-1 right-1 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full',
								(item.actual_qty || item.stock_qty || 0) > 0 ? 'bg-green-500' : 'bg-red-500'
							]"
						>
							{{ Math.floor(item.actual_qty || item.stock_qty || 0) }}
						</div>

						<img
							v-if="item.image"
							:src="item.image"
							:alt="item.item_name"
							class="w-full h-full object-cover"
							@error="handleImageError"
						/>
						<svg
							v-else
							class="h-10 w-10 text-gray-300"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
							/>
						</svg>
					</div>

					<!-- Item Details -->
					<div>
						<h3 class="text-xs font-semibold text-gray-900 truncate mb-0.5 leading-tight">
							{{ item.item_name }}
						</h3>
						<p class="text-[10px] text-gray-500">
							{{ formatCurrency(item.rate || item.price_list_rate || 0) }}
							<span class="text-gray-400">/ {{ item.stock_uom || 'Nos' }}</span>
						</p>
					</div>
				</div>
			</div>
		</div>

		<!-- Table View -->
		<div v-else class="flex-1 flex flex-col overflow-hidden">
			<div class="flex-1 overflow-y-auto">
				<table class="min-w-full divide-y divide-gray-200">
					<thead class="bg-gray-50 sticky top-0 z-0">
						<tr>
							<th scope="col" class="px-3 py-2.5 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider bg-gray-50 border-b-2 border-gray-200">Image</th>
							<th scope="col" class="px-3 py-2.5 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider bg-gray-50 border-b-2 border-gray-200">Name</th>
							<th scope="col" class="px-3 py-2.5 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider bg-gray-50 border-b-2 border-gray-200">Code</th>
							<th scope="col" class="px-3 py-2.5 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider bg-gray-50 border-b-2 border-gray-200">Rate</th>
							<th scope="col" class="px-3 py-2.5 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider bg-gray-50 border-b-2 border-gray-200">Available QTY</th>
							<th scope="col" class="px-3 py-2.5 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider bg-gray-50 border-b-2 border-gray-200">UOM</th>
						</tr>
					</thead>
					<tbody class="bg-white divide-y divide-gray-200">
						<tr
							v-for="item in items"
							:key="item.item_code"
							@click="handleItemClick(item)"
							class="cursor-pointer hover:bg-blue-50 transition-colors"
						>
							<td class="px-3 py-2 whitespace-nowrap">
								<div class="w-10 h-10 bg-gray-100 rounded flex items-center justify-center overflow-hidden">
									<img v-if="item.image" :src="item.image" :alt="item.item_name" class="w-full h-full object-cover" @error="handleImageError" />
									<svg v-else class="h-5 w-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
									</svg>
								</div>
							</td>
							<td class="px-3 py-2"><div class="text-sm font-medium text-gray-900">{{ item.item_name }}</div></td>
							<td class="px-3 py-2 whitespace-nowrap"><div class="text-sm text-gray-500">{{ item.item_code }}</div></td>
							<td class="px-3 py-2 whitespace-nowrap"><div class="text-sm font-semibold text-blue-600">{{ formatCurrency(item.rate || item.price_list_rate || 0) }}</div></td>
							<td class="px-3 py-2 whitespace-nowrap">
								<span :class="['text-sm font-medium', (item.actual_qty || item.stock_qty || 0) > 0 ? 'text-green-600' : 'text-red-600']">
									{{ Math.floor(item.actual_qty || item.stock_qty || 0) }}
								</span>
							</td>
							<td class="px-3 py-2 whitespace-nowrap"><div class="text-sm text-gray-500">{{ item.stock_uom || 'Nos' }}</div></td>
						</tr>
					</tbody>
				</table>
				<div v-if="items.length === 0" class="text-center py-8 text-gray-500">No items found</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue"
import { toast } from "frappe-ui"
import { formatCurrency as formatCurrencyUtil } from "@/utils/currency"
import { useItemSearchStore } from "@/stores/itemSearch"
import { storeToRefs } from "pinia"

const props = defineProps({
	posProfile: String,
	cartItems: {
		type: Array,
		default: () => []
	},
	currency: {
		type: String,
		default: 'USD'
	}
})

const emit = defineEmits(["item-selected"])

// Use Pinia store
const itemStore = useItemSearchStore()
const { filteredItems, searchTerm, selectedItemGroup, itemGroups, loading, allItems } = storeToRefs(itemStore)

// Local state for async search (large datasets)
const asyncResults = ref([])
const isSearchingAsync = ref(false)
const viewMode = ref('grid')

// Computed items - use async results for large datasets, otherwise use fast filtered
const items = computed(() => {
	// If allItems is empty (large dataset), use async results
	if (allItems.value.length === 0 && asyncResults.value.length > 0) {
		return asyncResults.value
	}
	// Otherwise use fast in-memory filtered results
	return filteredItems.value
})

// Watch for cart items and pos profile changes
watch(() => props.cartItems, (newCartItems) => {
	itemStore.setCartItems(newCartItems)
}, { immediate: true, deep: true })

watch(() => props.posProfile, (newProfile) => {
	if (newProfile) {
		itemStore.setPosProfile(newProfile)
	}
}, { immediate: true })

onMounted(() => {
	if (props.posProfile) {
		itemStore.loadAllItems(props.posProfile)
		itemStore.loadItemGroups()
	}
})

// Handle search input with instant reactivity
let searchTimeout = null
async function handleSearchInput(event) {
	const value = event.target.value
	itemStore.setSearchTerm(value)

	// If we have in-memory data, use the fast computed
	if (allItems.value.length > 0) {
		return
	}

	// For large datasets, use async IndexedDB search
	if (value.trim().length > 0) {
		// Debounce async search
		clearTimeout(searchTimeout)
		searchTimeout = setTimeout(async () => {
			isSearchingAsync.value = true
			try {
				const results = await itemStore.searchItemsAsync(value.trim(), 100)
				asyncResults.value = results
			} catch (error) {
				console.error('Async item search error:', error)
				asyncResults.value = []
			} finally {
				isSearchingAsync.value = false
			}
		}, 200)
	} else {
		asyncResults.value = []
	}
}

function handleItemClick(item) {
	emit("item-selected", item)
}

function handleBarcodeSearch() {
	if (!searchTerm.value.trim()) return

	// If only one item matches, auto-select it
	const currentItems = items.value
	if (currentItems.length === 1) {
		emit("item-selected", currentItems[0])
		itemStore.clearSearch()
		toast.create({
			title: "Item Added",
			text: `${currentItems[0].item_name} added to cart`,
			icon: "check",
			iconClasses: "text-green-600",
		})
	}
}

function handleBarcodeScan() {
	// Focus on search input for barcode scanner
	const input = document.querySelector('input[type="text"]')
	if (input) {
		input.focus()
	}

	toast.create({
		title: "Scan Barcode",
		text: "Ready to scan barcode or enter manually",
		icon: "alert-circle",
		iconClasses: "text-blue-600",
	})
}

function formatCurrency(amount) {
	return formatCurrencyUtil(parseFloat(amount || 0), props.currency)
}

// Expose methods for parent component
defineExpose({
	loadItems: () => itemStore.loadAllItems(props.posProfile),
	loadItemGroups: () => itemStore.loadItemGroups(),
})

function handleImageError(event) {
	event.target.style.display = "none"
}
</script>
