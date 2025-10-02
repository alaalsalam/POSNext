<template>
	<div class="flex flex-col h-full bg-white">
		<!-- Header with Customer -->
		<div class="px-3 py-2.5 border-b border-gray-200">
			<div class="flex items-center justify-between mb-2">
				<h2 class="text-sm font-semibold text-gray-900">Item Cart</h2>
				<button
					@click="$emit('clear-cart')"
					v-if="items.length > 0"
					class="text-xs text-red-600 hover:text-red-700 font-medium"
				>
					Clear
				</button>
			</div>

			<!-- Inline Customer Search/Selection -->
			<div class="relative">
				<div v-if="customer" class="flex items-center justify-between bg-blue-50 rounded-lg p-2">
					<div class="flex items-center space-x-2">
						<div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
							<svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
							</svg>
						</div>
						<div class="min-w-0 flex-1">
							<p class="text-xs font-semibold text-gray-900 truncate">
								{{ customer.customer_name || customer.name }}
							</p>
							<p v-if="customer.mobile_no" class="text-[10px] text-gray-600 truncate">
								{{ customer.mobile_no }}
							</p>
						</div>
					</div>
					<button
						@click="clearCustomer"
						class="text-sm text-red-600 hover:text-red-700 flex-shrink-0"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
						</svg>
					</button>
				</div>
				<div v-else>
					<!-- Search Icon Prefix -->
					<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
						<svg v-if="customersLoaded" class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
						</svg>
						<div v-else class="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-500"></div>
					</div>

					<!-- Native Input for Instant Search -->
					<input
						id="cart-customer-search"
						name="cart-customer-search"
						:value="customerSearch"
						@input="handleSearchInput"
						type="text"
						placeholder="Search customer by name or mobile"
						class="w-full pl-10 text-xs border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						:disabled="!customersLoaded"
						@keydown="handleKeydown"
						aria-label="Search customer in cart"
					/>

					<!-- Customer Dropdown -->
					<div
						v-if="customerSearch.trim().length >= 2"
						class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-hidden"
					>
						<!-- Loading indicator -->
						<div v-if="isSearching" class="px-3 py-4 text-center">
							<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
							<p class="text-xs text-gray-600 mt-2">Searching...</p>
						</div>

						<!-- Customer Results -->
						<div v-else-if="customerResults.length > 0" class="max-h-64 overflow-y-auto">
							<button
								v-for="(cust, index) in customerResults"
								:key="cust.name"
								@click="selectCustomer(cust)"
								:class="[
									'w-full text-left px-3 py-2.5 flex items-center space-x-2 border-b border-gray-100 last:border-0 transition-colors duration-75',
									index === selectedIndex ? 'bg-blue-100' : 'hover:bg-blue-50'
								]"
							>
								<div class="w-7 h-7 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
									<span class="text-[11px] font-bold text-blue-600">{{ getInitials(cust.customer_name) }}</span>
								</div>
								<div class="flex-1 min-w-0">
									<p class="text-xs font-semibold text-gray-900 truncate">{{ cust.customer_name }}</p>
									<p v-if="cust.mobile_no" class="text-[10px] text-gray-600">{{ cust.mobile_no }}</p>
								</div>
							</button>
						</div>

						<!-- No Results + Create New Option -->
						<div v-else-if="customerSearch.trim().length >= 2 && !isSearching">
							<div class="px-3 py-2 text-center text-xs font-medium text-gray-700 border-b border-gray-100">
								No results for "{{ customerSearch }}"
							</div>
						</div>

						<!-- Create New Customer Option -->
						<button
							v-if="customerSearch.trim().length >= 2"
							@click="createNewCustomer"
							class="w-full text-left px-3 py-2.5 hover:bg-green-50 flex items-center space-x-2 transition-colors border-t border-gray-200"
						>
							<div class="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
								<svg class="w-3.5 h-3.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
								</svg>
							</div>
							<div class="flex-1">
								<p class="text-xs font-medium text-green-700">Create New Customer</p>
								<p class="text-[10px] text-green-600">"{{ customerSearch }}"</p>
							</div>
						</button>
					</div>
				</div>
			</div>
		</div>

		<!-- Cart Items -->
		<div class="flex-1 overflow-y-auto p-2.5 bg-gray-50">
			<div v-if="items.length === 0" class="text-center py-12">
				<div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
					<svg
						class="h-8 w-8 text-gray-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
						/>
					</svg>
				</div>
				<p class="text-xs font-medium text-gray-900">Your cart is empty</p>
				<p class="text-[10px] text-gray-500 mt-1">
					Select items to start
				</p>
			</div>

			<div v-else class="space-y-2">
				<div
					v-for="(item, index) in items"
					:key="index"
					class="bg-white border border-gray-200 rounded-lg p-2 hover:shadow-sm transition-shadow"
				>
					<div class="flex items-start space-x-2 mb-2">
						<!-- Item Image Thumbnail -->
						<div class="w-10 h-10 bg-gray-100 rounded-md flex-shrink-0 flex items-center justify-center overflow-hidden">
							<img
								v-if="item.image"
								:src="item.image"
								:alt="item.item_name"
								class="w-full h-full object-cover"
							/>
							<svg
								v-else
								class="h-5 w-5 text-gray-400"
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

						<!-- Item Info -->
						<div class="flex-1 min-w-0">
							<div class="flex items-start justify-between">
								<div class="flex-1 min-w-0">
									<h4 class="text-xs font-semibold text-gray-900 truncate">
										{{ item.item_name }}
									</h4>
									<p class="text-[10px] text-gray-500">
										{{ formatCurrency(item.rate) }} / {{ item.stock_uom || 'Nos' }}
									</p>
								</div>
								<button
									@click="$emit('remove-item', item.item_code)"
									class="text-gray-400 hover:text-red-600 ml-1 transition-colors flex-shrink-0"
								>
									<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
									</svg>
								</button>
							</div>
						</div>
					</div>

					<!-- Quantity Controls and Total -->
					<div class="flex items-center justify-between">
						<div class="flex items-center space-x-1.5">
							<button
								@click="decrementQuantity(item)"
								class="w-6 h-6 rounded bg-gray-100 hover:bg-gray-200 flex items-center justify-center font-bold text-gray-700 text-sm transition-colors"
							>
								−
							</button>
							<input
								:value="item.quantity"
								@input="updateQuantity(item, $event.target.value)"
								type="number"
								min="1"
								step="1"
								class="w-10 text-center border border-gray-300 rounded px-1 py-0.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-blue-500"
							/>
							<button
								@click="incrementQuantity(item)"
								class="w-6 h-6 rounded bg-gray-100 hover:bg-gray-200 flex items-center justify-center font-bold text-gray-700 text-sm transition-colors"
							>
								+
							</button>
						</div>
						<div class="text-right">
							<p class="text-xs font-bold text-gray-900">
								{{ formatCurrency(item.amount || item.rate * item.quantity) }}
							</p>
						</div>
					</div>

					<!-- Discount Badge if any -->
					<div
						v-if="item.discount_amount && item.discount_amount > 0"
						class="mt-1.5 inline-flex items-center px-1.5 py-0.5 bg-green-50 text-green-700 rounded text-[10px] font-medium"
					>
						<svg class="w-2.5 h-2.5 mr-0.5" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clip-rule="evenodd"/>
						</svg>
						{{ item.discount_percentage }}% off
					</div>
				</div>
			</div>
		</div>

		<!-- Coupons & Offers Buttons -->
		<div v-if="items.length > 0" class="px-2.5 pt-2.5 pb-1 bg-gray-50">
			<div class="flex gap-2">
				<!-- Coupons Button -->
				<button
					@click="$emit('show-coupons')"
					class="relative flex-1 flex items-center justify-between px-3 py-2 rounded-lg bg-white border border-purple-300 hover:border-purple-500 hover:bg-purple-50 transition-all group"
				>
					<div class="flex items-center space-x-2">
						<div class="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center group-hover:bg-purple-200 transition-colors">
							<svg class="w-4 h-4 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M4 2a2 2 0 00-2 2v11a3 3 0 106 0V4a2 2 0 00-2-2H4zm1 14a1 1 0 100-2 1 1 0 000 2zm5-1.757l4.9-4.9a2 2 0 000-2.828L13.485 5.1a2 2 0 00-2.828 0L10 5.757v8.486zM16 18H9.071l6-6H16a2 2 0 012 2v2a2 2 0 01-2 2z" clip-rule="evenodd"/>
							</svg>
						</div>
						<span class="text-xs font-semibold text-gray-900">Coupons</span>
					</div>
					<span v-if="availableGiftCards.length > 0" class="bg-purple-600 text-white text-[9px] font-bold rounded-full px-1.5 py-0.5 min-w-[18px] text-center">
						{{ availableGiftCards.length }}
					</span>
				</button>

				<!-- Offers Button -->
				<button
					@click="$emit('show-offers')"
					class="relative flex-1 flex items-center justify-between px-3 py-2 rounded-lg bg-white border border-green-300 hover:border-green-500 hover:bg-green-50 transition-all group"
				>
					<div class="flex items-center space-x-2">
						<div class="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center group-hover:bg-green-200 transition-colors">
							<svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
							</svg>
						</div>
						<span class="text-xs font-semibold text-gray-900">Offers</span>
					</div>
					<span v-if="availableOffers.length > 0" class="bg-green-600 text-white text-[9px] font-bold rounded-full px-1.5 py-0.5 min-w-[18px] text-center">
						{{ availableOffers.length }}
					</span>
				</button>
			</div>
		</div>

		<!-- Totals Summary -->
		<div class="p-2.5 bg-white border-t border-gray-200">
			<!-- Summary Details -->
			<div v-if="items.length > 0" class="mb-2.5">
				<div class="flex items-center justify-between text-[10px] text-gray-600 mb-1">
					<span>Total Quantity</span>
					<span class="font-medium text-gray-900">{{ totalQuantity }}</span>
				</div>
				<div class="flex items-center justify-between text-[10px] text-gray-600 mb-1">
					<span>Net Total</span>
					<span class="font-medium text-gray-900">{{ formatCurrency(subtotal) }}</span>
				</div>
				<div v-if="discountAmount > 0" class="flex items-center justify-between text-[10px] text-gray-600 mb-1">
					<span>Discount</span>
					<span class="font-semibold text-green-600">-{{ formatCurrency(discountAmount) }}</span>
				</div>
				<div class="flex items-center justify-between text-[10px] text-gray-600 mb-2">
					<button class="text-blue-600 hover:text-blue-700 flex items-center">
						<span>Total Tax</span>
						<svg class="w-3 h-3 ml-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
						</svg>
					</button>
					<span class="font-medium text-gray-900">{{ formatCurrency(taxAmount) }}</span>
				</div>
			</div>

			<!-- Grand Total -->
			<div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-2.5 mb-2.5">
				<div class="flex items-center justify-between">
					<span class="text-sm font-bold text-gray-900">Grand Total</span>
					<span class="text-lg font-bold text-blue-600">
						{{ formatCurrency(grandTotal) }}
					</span>
				</div>
			</div>

			<!-- Action Buttons -->
			<div class="space-y-1.5">
				<button
					@click="$emit('proceed-to-payment')"
					:disabled="items.length === 0"
					:class="[
						'w-full py-2 px-3 rounded-lg font-semibold text-sm text-white transition-all flex items-center justify-center',
						items.length === 0
							? 'bg-gray-300 cursor-not-allowed'
							: 'bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg'
					]"
				>
					<span>Checkout</span>
				</button>
				<button
					v-if="items.length > 0"
					@click="$emit('save-draft')"
					class="w-full py-1.5 px-3 rounded-lg font-medium text-xs text-orange-600 bg-orange-50 hover:bg-orange-100 transition-all"
				>
					Hold
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, watch } from "vue"
import { createResource } from "frappe-ui"
import { offlineWorker } from "@/utils/offline/workerClient"
import { formatCurrency as formatCurrencyUtil } from "@/utils/currency"

const props = defineProps({
	items: {
		type: Array,
		default: () => [],
	},
	customer: Object,
	subtotal: {
		type: Number,
		default: 0,
	},
	taxAmount: {
		type: Number,
		default: 0,
	},
	discountAmount: {
		type: Number,
		default: 0,
	},
	grandTotal: {
		type: Number,
		default: 0,
	},
	posProfile: String,
	currency: {
		type: String,
		default: 'USD'
	}
})

const emit = defineEmits([
	"update-quantity",
	"remove-item",
	"select-customer",
	"create-customer",
	"proceed-to-payment",
	"clear-cart",
	"save-draft",
	"apply-coupon",
	"show-coupons",
	"show-offers",
])

const customerSearch = ref("")
const customersLoaded = ref(false)
const selectedIndex = ref(-1)
const availableOffers = ref([])
const availableGiftCards = ref([])
const isSearching = ref(false)

// For large datasets, we use IndexedDB-based async search instead of loading all into memory
// Check if customers are cached on mount
async function initializeCustomers() {
	try {
		const count = await offlineWorker.getCachedCustomersCount()
		if (count > 0) {
			console.log(`✓ Found ${count} customers in cache - using async search`)
			customersLoaded.value = true
		} else {
			// Load from server in batches
			await loadCustomersInBatches()
		}
	} catch (error) {
		console.error("Error initializing customers:", error)
		customersLoaded.value = true // Set to true to avoid loading spinner
	}
}

async function loadCustomersInBatches() {
	try {
		console.log('📥 Loading customers in batches...')
		const BATCH_SIZE = 1000
		let start = 0
		let hasMore = true
		let totalLoaded = 0

		while (hasMore) {
			const response = await createResource({
				url: "pos_next.api.customers.get_customers",
				makeParams() {
					return {
						search_term: "",
						pos_profile: props.posProfile,
						start: start,
						limit: BATCH_SIZE
					}
				}
			}).submit()

			const customers = response?.message || response || []

			if (customers.length > 0) {
				// Cache batch immediately
				await offlineWorker.cacheCustomers(customers)
				totalLoaded += customers.length
				console.log(`✓ Cached batch: ${customers.length} customers (Total: ${totalLoaded})`)

				if (customers.length < BATCH_SIZE) {
					hasMore = false
				} else {
					start += BATCH_SIZE
				}
			} else {
				hasMore = false
			}
		}

		console.log(`✓ Completed: Loaded ${totalLoaded} customers`)
		customersLoaded.value = true
	} catch (error) {
		console.error("Error loading customers in batches:", error)
		customersLoaded.value = true
	}
}

// Initialize on mount
if (props.posProfile) {
	initializeCustomers()
}

// Load offers resource
const offersResource = createResource({
	url: "pos_next.api.offers.get_offers",
	makeParams() {
		return {
			pos_profile: props.posProfile
		}
	},
	auto: true,
	onSuccess(data) {
		const offers = data?.message || data || []
		console.log('✓ Loaded offers:', offers.length, offers)

		// Filter only auto-apply offers that are eligible
		const eligible = offers.filter(offer =>
			offer.auto && !offer.coupon_based &&
			checkOfferEligibility(offer)
		)

		console.log('✓ Eligible offers:', eligible.length, eligible)
		availableOffers.value = eligible.slice(0, 3) // Show top 3
	},
	onError(error) {
		console.error('Error loading offers:', error)
	}
})

// Load gift cards resource
const giftCardsResource = createResource({
	url: "pos_next.api.offers.get_active_coupons",
	makeParams() {
		return {
			customer: props.customer?.name || props.customer,
			company: props.posProfile // Will get company from profile
		}
	},
	auto: false,
	onSuccess(data) {
		availableGiftCards.value = data?.message || data || []
	}
})

// Watch for customer changes to load their gift cards
watch(() => props.customer, (newCustomer) => {
	if (newCustomer && props.posProfile) {
		giftCardsResource.reload()
	} else {
		availableGiftCards.value = []
	}
})

// Watch for cart changes to update eligible offers
watch(() => props.grandTotal, () => {
	if (offersResource.data) {
		const offers = offersResource.data?.message || offersResource.data || []
		availableOffers.value = offers.filter(offer =>
			offer.auto && !offer.coupon_based &&
			checkOfferEligibility(offer)
		).slice(0, 3)
	}
})

function checkOfferEligibility(offer) {
	if (offer.min_amt && props.grandTotal < offer.min_amt) {
		return false
	}
	if (offer.max_amt && props.grandTotal > offer.max_amt) {
		return false
	}
	return true
}

// Async search results for large datasets
const customerResults = ref([])
let searchDebounceTimer = null

// Watch search term and trigger async search
watch(customerSearch, async (newValue) => {
	const searchValue = newValue.trim()

	if (searchValue.length < 2) {
		customerResults.value = []
		return
	}

	// Debounce search for better performance
	clearTimeout(searchDebounceTimer)
	searchDebounceTimer = setTimeout(async () => {
		isSearching.value = true
		try {
			// Use async IndexedDB search for large datasets
			const results = await offlineWorker.searchCachedCustomers(searchValue, 20)
			customerResults.value = results || []
		} catch (error) {
			console.error('Error searching customers:', error)
			customerResults.value = []
		} finally {
			isSearching.value = false
		}
	}, 150) // 150ms debounce
})

// Reset selection when results change
watch(customerResults, () => {
	selectedIndex.value = -1
}, { deep: true })

const totalQuantity = computed(() => {
	return props.items.reduce((sum, item) => sum + (item.quantity || 0), 0)
})

// Handle search input with instant reactivity
function handleSearchInput(event) {
	customerSearch.value = event.target.value
}

// Keyboard navigation
function handleKeydown(event) {
	if (customerResults.value.length === 0) return

	if (event.key === 'ArrowDown') {
		event.preventDefault()
		selectedIndex.value = Math.min(selectedIndex.value + 1, customerResults.value.length - 1)
	} else if (event.key === 'ArrowUp') {
		event.preventDefault()
		selectedIndex.value = Math.max(selectedIndex.value - 1, -1)
	} else if (event.key === 'Enter') {
		event.preventDefault()
		if (selectedIndex.value >= 0 && selectedIndex.value < customerResults.value.length) {
			selectCustomer(customerResults.value[selectedIndex.value])
		} else if (customerResults.value.length === 1) {
			// Auto-select if only one result
			selectCustomer(customerResults.value[0])
		}
	} else if (event.key === 'Escape') {
		customerSearch.value = ""
	}
}

function selectCustomer(cust) {
	emit("select-customer", cust)
	customerSearch.value = ""
	selectedIndex.value = -1
}

function clearCustomer() {
	emit("select-customer", null)
}

function createNewCustomer() {
	// Emit event to open customer creation dialog
	emit("create-customer", customerSearch.value)
	customerSearch.value = ""
}

function getInitials(name) {
	if (!name) return "?"
	const parts = name.split(" ")
	if (parts.length >= 2) {
		return (parts[0][0] + parts[1][0]).toUpperCase()
	}
	return name.substring(0, 2).toUpperCase()
}

function formatCurrency(amount) {
	return formatCurrencyUtil(parseFloat(amount || 0), props.currency)
}

function incrementQuantity(item) {
	emit("update-quantity", item.item_code, item.quantity + 1)
}

function decrementQuantity(item) {
	if (item.quantity > 1) {
		emit("update-quantity", item.item_code, item.quantity - 1)
	}
}

function updateQuantity(item, value) {
	const qty = parseInt(value) || 1
	if (qty > 0) {
		emit("update-quantity", item.item_code, qty)
	}
}

// Close dropdown when clicking outside
if (typeof document !== 'undefined') {
	document.addEventListener('click', (e) => {
		if (!e.target.closest('.relative')) {
			customerSearch.value = ""
		}
	})
}
</script>
