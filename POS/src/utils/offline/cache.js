import { db, getSetting, setSetting } from './db'
import { call } from '@/utils/apiWrapper'

// Cache structure definition - modify this when cache structure changes
const CACHE_STRUCTURE = {
	// Define what gets cached
	items: ['item_code', 'item_name', 'item_group', 'barcodes', 'price', 'stock'],
	customers: ['name', 'customer_name', 'mobile_no', 'email_id'],
	item_prices: ['price_list', 'item_code', 'price'],
	local_stock: ['item_code', 'warehouse', 'actual_qty'],
}

// Generate cache version from structure hash
function getCacheStructureHash(structure) {
	const structureString = JSON.stringify(structure)
	let hash = 0
	for (let i = 0; i < structureString.length; i++) {
		const char = structureString.charCodeAt(i)
		hash = ((hash << 5) - hash) + char
		hash = hash & hash
	}
	return Math.abs(hash)
}

// Auto-increment cache version based on structure changes
function getCacheVersion() {
	const structureHash = getCacheStructureHash(CACHE_STRUCTURE)
	const storedHash = localStorage.getItem('pos_next_cache_structure_hash')
	const storedVersion = parseInt(localStorage.getItem('pos_next_cache_version') || '1')

	if (storedHash !== structureHash.toString()) {
		const newVersion = storedVersion + 1
		console.log(`Cache structure changed. Upgrading from v${storedVersion} to v${newVersion}`)
		localStorage.setItem('pos_next_cache_structure_hash', structureHash.toString())
		localStorage.setItem('pos_next_cache_version', newVersion.toString())
		return newVersion
	}

	return storedVersion
}

export const CACHE_VERSION = getCacheVersion()

// In-memory cache for fast access
export const memory = {
	// Offline queues
	offline_invoices: [],
	offline_customers: [],
	offline_payments: [],

	// Cached data
	items: [],
	customers: [],
	item_prices: {},
	local_stock: {},

	// Metadata
	items_last_sync: null,
	customers_last_sync: null,
	cache_ready: false,
	stock_cache_ready: false,
	manual_offline: false,

	// Cache version
	cache_version: CACHE_VERSION,
}

// Initialize memory cache from IndexedDB
export const initMemoryCache = async () => {
	try {
		console.log('Initializing memory cache...')

		// Load cache version
		const storedVersion = await getSetting('cache_version', CACHE_VERSION)
		if (storedVersion !== CACHE_VERSION) {
			console.log('Cache version mismatch, clearing cache...')
			await clearAllCache()
			await setSetting('cache_version', CACHE_VERSION)
			memory.cache_version = CACHE_VERSION
		}

		// Load items last sync timestamp
		memory.items_last_sync = await getSetting('items_last_sync', null)
		memory.customers_last_sync = await getSetting('customers_last_sync', null)
		memory.cache_ready = await getSetting('cache_ready', false)
		memory.stock_cache_ready = await getSetting('stock_cache_ready', false)
		memory.manual_offline = await getSetting('manual_offline', false)

		// Load items count (don't load all items into memory, too heavy)
		const itemsCount = await db.items.count()
		const customersCount = await db.customers.count()

		console.log(`Cache initialized: ${itemsCount} items, ${customersCount} customers`)
		console.log(`Cache ready: ${memory.cache_ready}, Stock ready: ${memory.stock_cache_ready}`)

		return true
	} catch (error) {
		console.error('Failed to initialize memory cache:', error)
		return false
	}
}

// Check if cache is ready for offline use
export const isCacheReady = () => {
	return memory.cache_ready
}

// Check if stock cache is ready
export const isStockCacheReady = () => {
	return memory.stock_cache_ready
}

// Get manual offline state
export const isManualOffline = () => {
	return memory.manual_offline
}

// Set manual offline state
export const setManualOffline = async (state) => {
	memory.manual_offline = !!state
	await setSetting('manual_offline', memory.manual_offline)
}

// Toggle manual offline
export const toggleManualOffline = async () => {
	await setManualOffline(!memory.manual_offline)
	return memory.manual_offline
}

// Load items from server in batches (streams to IndexedDB without retaining in memory)
export const cacheItemsFromServer = async (posProfile, onProgress = null) => {
	try {
		console.log('Fetching items from server in batches...')

		const BATCH_SIZE = 1000 // Fetch 1000 items per batch
		let totalCount = 0
		let start = 0
		let hasMore = true
		let batchNumber = 1

		while (hasMore) {
			const response = await call('pos_next.api.items.get_items', {
				pos_profile: posProfile,
				start: start,
				limit: BATCH_SIZE
			})

			const items = response?.message || response || []

			if (items.length > 0) {
				// Process items to add searchable fields
				const processedItems = items.map(item => ({
					...item,
					barcodes: item.item_barcode
						? Array.isArray(item.item_barcode)
							? item.item_barcode.map(b => b.barcode).filter(Boolean)
							: [item.item_barcode]
						: []
				}))

				// Cache this batch immediately to IndexedDB
				await db.items.bulkPut(processedItems)

				totalCount += processedItems.length

				console.log(`✓ Batch ${batchNumber}: Fetched and cached ${processedItems.length} items (Total: ${totalCount})`)

				// Call progress callback if provided
				if (onProgress) {
					onProgress({
						type: 'items',
						batch: batchNumber,
						batchSize: processedItems.length,
						total: totalCount,
						progress: items.length < BATCH_SIZE ? 100 : null
					})
				}

				// Check if there are more items
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

		console.log(`✓ Completed: Fetched and cached ${totalCount} items in ${batchNumber} batches`)

		// Update metadata to mark cache as fresh
		const now = Date.now()
		await setSetting('items_last_sync', now)
		await setSetting('cache_ready', true)

		// Update in-memory cache
		memory.items_last_sync = now
		memory.cache_ready = true

		console.log(`✓ Cache metadata updated: items_last_sync=${new Date(now).toISOString()}`)

		return { totalCount }
	} catch (error) {
		console.error('Error fetching items from server:', error)
		throw error
	}
}

// Load customers from server in batches (streams to IndexedDB without retaining in memory)
export const cacheCustomersFromServer = async (posProfile, onProgress = null) => {
	try {
		console.log('Fetching customers from server in batches...')

		const BATCH_SIZE = 1000 // Fetch 1000 customers per batch
		let totalCount = 0
		let start = 0
		let hasMore = true
		let batchNumber = 1

		while (hasMore) {
			const response = await call('pos_next.api.customers.get_customers', {
				pos_profile: posProfile,
				start: start,
				limit: BATCH_SIZE
			})

			const customers = response?.message || response || []

			if (customers.length > 0) {
				// Cache this batch immediately to IndexedDB
				await db.customers.bulkPut(customers)

				totalCount += customers.length

				console.log(`✓ Batch ${batchNumber}: Fetched and cached ${customers.length} customers (Total: ${totalCount})`)

				// Call progress callback if provided
				if (onProgress) {
					onProgress({
						type: 'customers',
						batch: batchNumber,
						batchSize: customers.length,
						total: totalCount,
						progress: customers.length < BATCH_SIZE ? 100 : null
					})
				}

				// Check if there are more customers
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

		console.log(`✓ Completed: Fetched and cached ${totalCount} customers in ${batchNumber} batches`)

		// Update metadata to mark cache as fresh
		const now = Date.now()
		await setSetting('customers_last_sync', now)
		await setSetting('cache_ready', true)

		// Update in-memory cache
		memory.customers_last_sync = now
		memory.cache_ready = true

		console.log(`✓ Cache metadata updated: customers_last_sync=${new Date(now).toISOString()}`)

		return { totalCount }
	} catch (error) {
		console.error('Error fetching customers from server:', error)
		throw error
	}
}

// Search items in cache
export const searchCachedItems = async (searchTerm = '', limit = 50) => {
	try {
		if (!searchTerm) {
			return await db.items.limit(limit).toArray()
		}

		const term = searchTerm.toLowerCase()

		// Search by item code, name, or barcode
		const results = await db.items
			.where('item_code').startsWithIgnoreCase(term)
			.or('item_name').startsWithIgnoreCase(term)
			.or('barcodes').equals(term)
			.limit(limit)
			.toArray()

		return results
	} catch (error) {
		console.error('Error searching cached items:', error)
		return []
	}
}

// Search customers in cache
export const searchCachedCustomers = async (searchTerm = '', limit = 50) => {
	try {
		if (!searchTerm) {
			return await db.customers.limit(limit).toArray()
		}

		const term = searchTerm.toLowerCase()

		// Search by name, mobile, or email
		const results = await db.customers
			.where('customer_name').startsWithIgnoreCase(term)
			.or('mobile_no').startsWithIgnoreCase(term)
			.or('email_id').startsWithIgnoreCase(term)
			.limit(limit)
			.toArray()

		return results
	} catch (error) {
		console.error('Error searching cached customers:', error)
		return []
	}
}

// Get item from cache by code
export const getCachedItem = async (itemCode) => {
	try {
		return await db.items.get(itemCode)
	} catch (error) {
		console.error('Error getting cached item:', error)
		return null
	}
}

// Get customer from cache by name
export const getCachedCustomer = async (customerName) => {
	try {
		return await db.customers.get(customerName)
	} catch (error) {
		console.error('Error getting cached customer:', error)
		return null
	}
}

// Check if cache needs refresh (older than 24 hours)
export const needsCacheRefresh = () => {
	if (!memory.items_last_sync) return true

	const ONE_DAY = 24 * 60 * 60 * 1000
	const now = Date.now()
	return (now - memory.items_last_sync) > ONE_DAY
}

// Clear all cached data
export const clearAllCache = async () => {
	try {
		console.log('Clearing all cache...')

		// Clear IndexedDB tables
		await db.items.clear()
		await db.customers.clear()
		await db.item_prices.clear()
		await db.stock.clear()

		// Reset memory
		memory.items = []
		memory.customers = []
		memory.item_prices = {}
		memory.local_stock = {}
		memory.items_last_sync = null
		memory.customers_last_sync = null
		memory.cache_ready = false
		memory.stock_cache_ready = false

		// Update settings
		await setSetting('items_last_sync', null)
		await setSetting('customers_last_sync', null)
		await setSetting('cache_ready', false)
		await setSetting('stock_cache_ready', false)

		console.log('Cache cleared successfully')
		return true
	} catch (error) {
		console.error('Error clearing cache:', error)
		return false
	}
}

// Get cache stats
export const getCacheStats = async () => {
	try {
		const itemsCount = await db.items.count()
		const customersCount = await db.customers.count()
		const queuedInvoices = await db.invoice_queue
			.filter(inv => inv.synced === false)
			.count()

		return {
			items: itemsCount,
			customers: customersCount,
			queuedInvoices,
			cacheReady: memory.cache_ready,
			stockReady: memory.stock_cache_ready,
			lastSync: memory.items_last_sync
				? new Date(memory.items_last_sync).toLocaleString()
				: 'Never'
		}
	} catch (error) {
		console.error('Error getting cache stats:', error)
		return {
			items: 0,
			customers: 0,
			queuedInvoices: 0,
			cacheReady: false,
			stockReady: false,
			lastSync: 'Error'
		}
	}
}

// Initialize cache on import
initMemoryCache()
