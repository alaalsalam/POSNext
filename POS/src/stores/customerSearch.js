import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { offlineWorker } from '@/utils/offline/workerClient'
import { call } from '@/utils/apiWrapper'
import { isOffline } from '@/utils/offline'

export const useCustomerSearchStore = defineStore('customerSearch', () => {
	// State
	const allCustomers = ref([])
	const searchTerm = ref('')
	const loading = ref(false)
	const selectedIndex = ref(-1)
	const recentSearches = ref([])
	const frequentCustomers = ref([])

	// Performance optimization: Pre-computed search indices
	const searchIndex = ref(new Map())
	const resultCache = ref(new Map())

	// Ultra-fast search helper - optimized for speed
	function quickMatch(search, customer) {
		const term = search.toLowerCase()

		// Get or create cached lowercase strings for this customer
		let cached = searchIndex.value.get(customer.name)
		if (!cached) {
			cached = {
				name: (customer.customer_name || '').toLowerCase(),
				mobile: (customer.mobile_no || '').toLowerCase(),
				email: (customer.email_id || '').toLowerCase(),
				id: (customer.name || '').toLowerCase(),
				// Pre-compute word starts for super fast word matching
				nameWords: (customer.customer_name || '').toLowerCase().split(' '),
			}
			searchIndex.value.set(customer.name, cached)
		}

		// Lightning-fast checks in priority order
		// Name checks (most important)
		if (cached.name === term) return 300 // Exact name match
		if (cached.name.startsWith(term)) return 270 // Name starts with

		// Check each word start
		for (const word of cached.nameWords) {
			if (word.startsWith(term)) return 240 // Word in name starts with
		}

		if (cached.name.includes(term)) return 180 // Name contains

		// Phone checks (very important for POS)
		if (cached.mobile === term) return 250
		if (cached.mobile.startsWith(term)) return 225
		if (cached.mobile.includes(term)) return 150

		// Email checks
		if (cached.email.startsWith(term)) return 200
		if (cached.email.includes(term)) return 120

		// ID checks
		if (cached.id.startsWith(term)) return 135
		if (cached.id.includes(term)) return 90

		return 0 // No match
	}

	// Getters - ULTRA OPTIMIZED for zero delay with IndexedDB fallback for large datasets
	const filteredCustomers = computed(() => {
		const startTime = performance.now()
		const term = searchTerm.value.trim()

		// For in-memory datasets, use fast synchronous search
		// For large datasets (when allCustomers is empty), components should use searchCustomersAsync
		if (allCustomers.value.length === 0) {
			// Return empty - components must use searchCustomersAsync for large datasets
			return []
		}

		// Show recent/frequent customers when no search term (CACHED)
		if (!term) {
			const cacheKey = 'empty'
			let cached = resultCache.value.get(cacheKey)

			if (!cached) {
				// Build index maps once for O(1) lookup
				const recentSet = new Set(recentSearches.value)
				const frequentSet = new Set(frequentCustomers.value)

				// Separate into buckets
				const recent = []
				const frequent = []
				const other = []

				for (const c of allCustomers.value) {
					if (recentSet.has(c.name)) recent.push(c)
					else if (frequentSet.has(c.name)) frequent.push(c)
					else other.push(c)
				}

				cached = [...recent, ...frequent, ...other].slice(0, 50)
				resultCache.value.set(cacheKey, cached)
			}

			const elapsed = performance.now() - startTime
			console.log(`⚡⚡ Showing ${cached.length} customers in ${elapsed.toFixed(3)}ms (CACHED)`)
			return cached
		}

		// Check result cache first
		const cacheKey = term.toLowerCase()
		let cachedResult = resultCache.value.get(cacheKey)
		if (cachedResult) {
			const elapsed = performance.now() - startTime
			console.log(`⚡⚡⚡ INSTANT ${cachedResult.length} results in ${elapsed.toFixed(3)}ms (FROM CACHE: "${term}")`)
			return cachedResult
		}

		// Ultra-fast search with early exit (only for in-memory datasets)
		const results = []
		const maxResults = 50
		let scanned = 0

		// First pass: Get exact and high-scoring matches ONLY
		for (const cust of allCustomers.value) {
			scanned++
			const score = quickMatch(term, cust)

			if (score >= 240) { // High priority matches
				results.push({ customer: cust, score })
				if (results.length >= maxResults) break // Exit immediately when we have enough
			}
		}

		// Second pass: Fill remaining slots with lower scores if needed
		if (results.length < maxResults && scanned < allCustomers.value.length) {
			for (let i = scanned; i < allCustomers.value.length; i++) {
				const cust = allCustomers.value[i]
				const score = quickMatch(term, cust)

				if (score > 0 && score < 240) {
					results.push({ customer: cust, score })
					if (results.length >= maxResults) break
				}
			}
		}

		// Sort ONLY what we found (much faster than sorting everything)
		results.sort((a, b) => b.score - a.score)
		const final = results.map(r => r.customer)

		// Cache this result for instant retrieval
		resultCache.value.set(cacheKey, final)

		// Limit cache size to prevent memory bloat
		if (resultCache.value.size > 100) {
			const firstKey = resultCache.value.keys().next().value
			resultCache.value.delete(firstKey)
		}

		const elapsed = performance.now() - startTime
		console.log(`⚡⚡ Ultra-fast ${final.length} results in ${elapsed.toFixed(3)}ms (search: "${term}")`)
		return final
	})

	// Recommendations based on search patterns
	const recommendations = computed(() => {
		const term = searchTerm.value.trim().toLowerCase()
		if (!term || term.length < 2) return []

		const recs = []

		// Check if it looks like a phone number
		if (/^\d+$/.test(term)) {
			recs.push({
				type: 'phone',
				text: `Search by phone: ${term}`,
				icon: '📱'
			})
		}

		// Check if it looks like an email
		if (term.includes('@')) {
			recs.push({
				type: 'email',
				text: `Search by email: ${term}`,
				icon: '✉️'
			})
		}

		// Suggest creating new customer if no exact matches
		const exactMatch = allCustomers.value.some(c =>
			c.customer_name?.toLowerCase() === term
		)
		if (!exactMatch && filteredCustomers.value.length < 5) {
			recs.push({
				type: 'create',
				text: `Create new customer "${term}"`,
				icon: '➕'
			})
		}

		return recs
	})

	// Actions
	async function loadAllCustomers(posProfile, onProgress = null) {
		if (!posProfile) {
			return
		}

		loading.value = true
		try {
			// Check if already cached
			const cachedCount = await offlineWorker.getCachedCustomersCount()

			if (cachedCount > 0) {
				console.log(`✓ Found ${cachedCount} customers in cache`)

				// Smart strategy: Load into memory if < 10K, otherwise use IndexedDB
				if (cachedCount < 10000) {
					const customers = await offlineWorker.searchCachedCustomers('', cachedCount)
					allCustomers.value = customers || []
					console.log(`✓ Loaded ${allCustomers.value.length} customers into memory for fast search`)
				} else {
					// Large dataset - use IndexedDB for search
					allCustomers.value = []
					console.log(`✓ Large dataset (${cachedCount}) - using IndexedDB for search`)
				}
			} else if (!isOffline()) {
				// Fetch from server in batches
				console.log('📥 Fetching customers in batches from server...')

				const BATCH_SIZE = 1000
				let start = 0
				let hasMore = true
				let batchNumber = 1
				let totalCount = 0
				let smallDataset = null // Only allocate if needed

				while (hasMore) {
					const response = await call('pos_next.api.customers.get_customers', {
						pos_profile: posProfile,
						search_term: '',
						start: start,
						limit: BATCH_SIZE
					})

					const customers = response?.message || response || []

					if (customers.length > 0) {
						// Cache this batch to IndexedDB immediately
						await offlineWorker.cacheCustomers(customers)
						totalCount += customers.length

						// Only accumulate for small datasets (< 10K)
						if (totalCount <= 10000) {
							if (!smallDataset) smallDataset = []
							smallDataset.push(...customers)
						} else if (smallDataset) {
							// Just crossed threshold - discard accumulated array
							smallDataset = null
							console.log(`⚠️ Dataset exceeds 10K - switching to IndexedDB mode`)
						}

						console.log(`✓ Batch ${batchNumber}: Cached ${customers.length} customers (Total: ${totalCount})`)

						// Report progress
						if (onProgress) {
							onProgress({
								type: 'customers',
								batch: batchNumber,
								batchSize: customers.length,
								total: totalCount,
								progress: customers.length < BATCH_SIZE ? 100 : null
							})
						}

						// Check if there are more
						if (customers.length < BATCH_SIZE) {
							hasMore = false
						} else {
							start += BATCH_SIZE
							batchNumber++
						}
					} else {
						hasMore = false
					}
				}

				console.log(`✓ Completed: Cached ${totalCount} customers`)

				// Smart strategy: Load into memory if < 10K
				if (totalCount < 10000 && smallDataset) {
					allCustomers.value = smallDataset
					console.log(`✓ Loaded ${totalCount} customers into memory for fast search`)
				} else {
					allCustomers.value = []
					console.log(`✓ Large dataset (${totalCount}) - using IndexedDB for search`)
				}
			}

			// Clear caches when new data is loaded
			searchIndex.value.clear()
			resultCache.value.clear()
		} catch (error) {
			console.error('Error loading customers:', error)
			allCustomers.value = []
		} finally {
			loading.value = false
		}
	}

	async function addCustomerToCache(customer) {
		try {
			// Add to local array
			const existingWithoutNew = allCustomers.value.filter(
				(cust) => cust.name !== customer.name
			)
			allCustomers.value = [customer, ...existingWithoutNew]

			// Cache in worker
			await offlineWorker.cacheCustomers([customer])

			// Clear result cache to include new customer
			resultCache.value.clear()

			console.log('✓ New customer cached for instant search')
		} catch (error) {
			console.error('Error caching newly created customer:', error)
		}
	}

	function setSearchTerm(term) {
		searchTerm.value = term
		selectedIndex.value = -1
	}

	function clearSearch() {
		searchTerm.value = ''
		selectedIndex.value = -1
		// Don't clear resultCache on empty search - it's beneficial
	}

	function setSelectedIndex(index) {
		selectedIndex.value = index
	}

	function resetSelectedIndex() {
		selectedIndex.value = -1
	}

	function trackCustomerSelection(customerId) {
		// Add to recent searches (max 10)
		recentSearches.value = [
			customerId,
			...recentSearches.value.filter(id => id !== customerId)
		].slice(0, 10)

		// Track frequency
		const index = frequentCustomers.value.indexOf(customerId)
		if (index > -1) {
			// Move to front if already exists
			frequentCustomers.value.splice(index, 1)
		}
		frequentCustomers.value = [customerId, ...frequentCustomers.value].slice(0, 20)

		// Persist to localStorage
		try {
			localStorage.setItem('pos_recent_customers', JSON.stringify(recentSearches.value))
			localStorage.setItem('pos_frequent_customers', JSON.stringify(frequentCustomers.value))
		} catch (e) {
			console.warn('Failed to persist customer history:', e)
		}
	}

	function loadCustomerHistory() {
		try {
			const recent = localStorage.getItem('pos_recent_customers')
			const frequent = localStorage.getItem('pos_frequent_customers')

			if (recent) recentSearches.value = JSON.parse(recent)
			if (frequent) frequentCustomers.value = JSON.parse(frequent)
		} catch (e) {
			console.warn('Failed to load customer history:', e)
		}
	}

	// Async search for large datasets using IndexedDB
	async function searchCustomersAsync(term, limit = 50) {
		try {
			const startTime = performance.now()

			// Use IndexedDB search via offlineWorker
			const results = await offlineWorker.searchCachedCustomers(term, limit)

			const elapsed = performance.now() - startTime
			console.log(`⚡ IndexedDB search: ${results.length} results in ${elapsed.toFixed(3)}ms (search: "${term}")`)

			return results || []
		} catch (error) {
			console.error('Error in async customer search:', error)
			return []
		}
	}

	return {
		// State
		allCustomers,
		searchTerm,
		loading,
		selectedIndex,
		recentSearches,
		frequentCustomers,

		// Getters
		filteredCustomers,
		recommendations,

		// Actions
		loadAllCustomers,
		addCustomerToCache,
		setSearchTerm,
		clearSearch,
		setSelectedIndex,
		resetSelectedIndex,
		trackCustomerSelection,
		loadCustomerHistory,
		searchCustomersAsync,
	}
})
