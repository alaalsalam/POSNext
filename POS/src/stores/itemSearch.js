import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { offlineWorker } from '@/utils/offline/workerClient'
import { isOffline } from '@/utils/offline'
import { call } from '@/utils/apiWrapper'
import { createResource } from 'frappe-ui'

export const useItemSearchStore = defineStore('itemSearch', () => {
	// State
	const allItems = ref([])
	const searchTerm = ref('')
	const selectedItemGroup = ref(null)
	const itemGroups = ref([])
	const loading = ref(false)
	const posProfile = ref(null)
	const cartItems = ref([])

	// Performance optimization: Result cache for instant searches
	const resultCache = ref(new Map())

	// Resources (for server-side operations)
	const itemGroupsResource = createResource({
		url: 'pos_next.api.items.get_item_groups',
		makeParams() {
			return {
				pos_profile: posProfile.value,
			}
		},
		auto: false,
		onSuccess(data) {
			itemGroups.value = data?.message || data || []
		},
		onError(error) {
			console.error('Error fetching item groups:', error)
			itemGroups.value = []
		},
	})

	const searchByBarcodeResource = createResource({
		url: 'pos_next.api.items.search_by_barcode',
		auto: false,
	})

	// Getters
	const filteredItems = computed(() => {
		const startTime = performance.now()

		// For in-memory datasets, use fast synchronous filtering
		// For large datasets (when allItems is empty), components should use searchItemsAsync
		if (!allItems.value || allItems.value.length === 0) {
			// Return empty - components must use searchItemsAsync for large datasets
			return []
		}

		let filtered = allItems.value

		// Filter by item group
		if (selectedItemGroup.value) {
			filtered = filtered.filter(
				(item) => item.item_group === selectedItemGroup.value
			)
		}

		// Filter by search term
		if (searchTerm.value && searchTerm.value.length > 0) {
			const term = searchTerm.value.toLowerCase()
			filtered = filtered.filter(
				(item) =>
					item.item_name?.toLowerCase().includes(term) ||
					item.item_code?.toLowerCase().includes(term) ||
					item.barcode?.toLowerCase().includes(term)
			)
		}

		// Limit results for performance
		filtered = filtered.slice(0, 100)

		// Create a map of cart items for faster lookup
		const cartItemsMap = new Map()
		if (cartItems.value.length > 0) {
			cartItems.value.forEach(ci => {
				cartItemsMap.set(ci.item_code, ci.quantity)
			})
		}

		// Adjust stock quantities based on cart items
		const result = filtered.map(item => {
			const cartQty = cartItemsMap.get(item.item_code)
			if (cartQty) {
				const originalStock = item.actual_qty || item.stock_qty || 0
				const availableStock = originalStock - cartQty
				return {
					...item,
					actual_qty: availableStock,
					stock_qty: availableStock,
					original_stock: originalStock
				}
			}
			return item
		})

		const elapsed = performance.now() - startTime
		console.log(`⚡ Filtered ${result.length} items in ${elapsed.toFixed(2)}ms (search: "${searchTerm.value}")`)

		return result
	})

	// Actions
	async function loadAllItems(profile, onProgress = null) {
		if (!profile) {
			return
		}

		posProfile.value = profile
		loading.value = true

		try {
			// Check if already cached
			const cachedCount = await offlineWorker.getCachedItemsCount()

			if (cachedCount > 0) {
				console.log(`✓ Found ${cachedCount} items in cache`)

				// Smart strategy: Load into memory if < 20K, otherwise use IndexedDB
				if (cachedCount < 20000) {
					const items = await offlineWorker.searchCachedItems('', cachedCount)
					allItems.value = items || []
					console.log(`✓ Loaded ${allItems.value.length} items into memory for fast search`)
				} else {
					// Large dataset - use IndexedDB for search
					allItems.value = []
					console.log(`✓ Large dataset (${cachedCount}) - using IndexedDB for search`)
				}
			} else if (!isOffline()) {
				// Fetch from server in batches
				console.log('📥 Fetching items in batches from server...')

				const BATCH_SIZE = 1000
				let start = 0
				let hasMore = true
				let batchNumber = 1
				let totalCount = 0
				let smallDataset = null // Only allocate if needed

				while (hasMore) {
					const response = await call('pos_next.api.items.get_items', {
						pos_profile: profile,
						search_term: '',
						item_group: null,
						start: start,
						limit: BATCH_SIZE
					})

					const items = response?.message || response || []

					if (items.length > 0) {
						// Cache this batch to IndexedDB immediately
						await offlineWorker.cacheItems(items)
						totalCount += items.length

						// Only accumulate for small datasets (< 20K)
						if (totalCount <= 20000) {
							if (!smallDataset) smallDataset = []
							smallDataset.push(...items)
						} else if (smallDataset) {
							// Just crossed threshold - discard accumulated array
							smallDataset = null
							console.log(`⚠️ Dataset exceeds 20K - switching to IndexedDB mode`)
						}

						console.log(`✓ Batch ${batchNumber}: Cached ${items.length} items (Total: ${totalCount})`)

						// Report progress
						if (onProgress) {
							onProgress({
								type: 'items',
								batch: batchNumber,
								batchSize: items.length,
								total: totalCount,
								progress: items.length < BATCH_SIZE ? 100 : null
							})
						}

						// Check if there are more
						if (items.length < BATCH_SIZE) {
							hasMore = false
						} else {
							start += BATCH_SIZE
							batchNumber++
						}
					} else {
						hasMore = false
					}
				}

				console.log(`✓ Completed: Cached ${totalCount} items`)

				// Smart strategy: Load into memory if < 20K
				if (totalCount < 20000 && smallDataset) {
					allItems.value = smallDataset
					console.log(`✓ Loaded ${totalCount} items into memory for fast search`)
				} else {
					allItems.value = []
					console.log(`✓ Large dataset (${totalCount}) - using IndexedDB for search`)
				}
			}

			// Clear result cache when new data is loaded
			resultCache.value.clear()
		} catch (error) {
			console.error('Error loading items:', error)
			allItems.value = []
		} finally {
			loading.value = false
		}
	}

	function loadItemGroups() {
		if (posProfile.value) {
			itemGroupsResource.reload()
		}
	}

	async function searchByBarcode(barcode) {
		try {
			const result = await searchByBarcodeResource.submit({
				barcode,
				pos_profile: posProfile.value,
			})
			return result?.message || result
		} catch (error) {
			console.error('Error searching by barcode:', error)
			return null
		}
	}

	async function getItem(itemCode) {
		try {
			const cacheReady = await offlineWorker.isCacheReady()
			if (isOffline() || cacheReady) {
				const items = await offlineWorker.searchCachedItems(itemCode, 1)
				return items?.[0] || null
			} else {
				// Fallback to server (implement if needed)
				return null
			}
		} catch (error) {
			console.error('Error getting item:', error)
			return null
		}
	}

	function setSearchTerm(term) {
		searchTerm.value = term
	}

	function clearSearch() {
		searchTerm.value = ''
	}

	function setSelectedItemGroup(group) {
		selectedItemGroup.value = group
		// Clear result cache when item group changes to force re-filtering
		resultCache.value.clear()
		console.log('📂 Item group changed to:', group || 'All Items')
	}

	function setCartItems(items) {
		cartItems.value = items
	}

	function setPosProfile(profile) {
		posProfile.value = profile
	}

	// Async search for large datasets using IndexedDB
	async function searchItemsAsync(term, limit = 100) {
		try {
			const startTime = performance.now()

			// Use IndexedDB search via offlineWorker
			const results = await offlineWorker.searchCachedItems(term, limit)

			// Filter by item group if selected
			let filtered = results
			if (selectedItemGroup.value) {
				filtered = results.filter(item => item.item_group === selectedItemGroup.value)
			}

			// Adjust stock based on cart
			const cartItemsMap = new Map()
			if (cartItems.value.length > 0) {
				cartItems.value.forEach(ci => {
					cartItemsMap.set(ci.item_code, ci.quantity)
				})
			}

			const final = filtered.map(item => {
				const cartQty = cartItemsMap.get(item.item_code)
				if (cartQty) {
					const originalStock = item.actual_qty || item.stock_qty || 0
					const availableStock = originalStock - cartQty
					return {
						...item,
						actual_qty: availableStock,
						stock_qty: availableStock,
						original_stock: originalStock
					}
				}
				return item
			})

			const elapsed = performance.now() - startTime
			console.log(`⚡ IndexedDB search: ${final.length} results in ${elapsed.toFixed(3)}ms (search: "${term}")`)

			return final || []
		} catch (error) {
			console.error('Error in async item search:', error)
			return []
		}
	}

	return {
		// State
		allItems,
		searchTerm,
		selectedItemGroup,
		itemGroups,
		loading,
		posProfile,
		cartItems,

		// Getters
		filteredItems,

		// Actions
		loadAllItems,
		loadItemGroups,
		searchByBarcode,
		getItem,
		setSearchTerm,
		clearSearch,
		setSelectedItemGroup,
		setCartItems,
		setPosProfile,
		searchItemsAsync,

		// Resources
		itemGroupsResource,
		searchByBarcodeResource,
	}
})
