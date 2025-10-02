/**
 * Offline Worker - Handles all offline operations in background thread
 * - Server ping and connectivity checks
 * - IndexedDB operations
 * - Invoice sync operations
 * - Cache management
 */

// Import Dexie using importScripts for worker context
// Note: In Vite, worker imports work differently
let Dexie
let db = null
let dbInitialized = false

// Initialize IndexedDB in worker context
async function initDB() {
	if (db && dbInitialized) return db

	try {
		// Dynamic import for worker context (Vite handles this)
		const dexieModule = await import('dexie')
		Dexie = dexieModule.default || dexieModule

		db = new Dexie('pos_next_offline')

		db.version(1).stores({
			settings: 'key',
			invoice_queue: '++id, synced, timestamp',
			payment_queue: '++id, synced, timestamp',
			items: '&item_code, item_group, *item_name, barcode',
			customers: '&name, *customer_name, customer_group',
			stock: '[item_code+warehouse]',
		})

		await db.open()
		dbInitialized = true
		console.log('Worker: Database initialized successfully')
		return db
	} catch (error) {
		console.error('Worker: Failed to initialize database:', error)
		throw error
	}
}

// Server connectivity state
let serverOnline = true
let manualOffline = false

// Ping server to check connectivity
async function pingServer() {
	try {
		const controller = new AbortController()
		const timeoutId = setTimeout(() => controller.abort(), 3000)

		const response = await fetch('/api/method/ping', {
			method: 'GET',
			signal: controller.signal,
		})

		clearTimeout(timeoutId)
		serverOnline = response.ok
		return serverOnline
	} catch (error) {
		serverOnline = false
		return false
	}
}

// Check offline status
function isOffline(browserOnline) {
	if (manualOffline) return true
	return !browserOnline || !serverOnline
}

// Get offline invoice count
async function getOfflineInvoiceCount() {
	try {
		const db = await initDB()
		const count = await db.invoice_queue
			.filter(invoice => invoice.synced === false)
			.count()
		return count
	} catch (error) {
		console.error('Worker: Error getting offline invoice count:', error)
		return 0
	}
}

// Get offline invoices
async function getOfflineInvoices() {
	try {
		const db = await initDB()
		const invoices = await db.invoice_queue
			.filter(invoice => invoice.synced === false)
			.toArray()
		return invoices
	} catch (error) {
		console.error('Worker: Error getting offline invoices:', error)
		return []
	}
}

// Save invoice to offline queue
async function saveOfflineInvoice(invoiceData) {
	try {
		const db = await initDB()

		if (!invoiceData.items || invoiceData.items.length === 0) {
			throw new Error('Cannot save empty invoice')
		}

		const id = await db.invoice_queue.add({
			data: invoiceData,
			timestamp: Date.now(),
			synced: false,
			retry_count: 0,
		})

		// Update local stock
		await updateLocalStock(invoiceData.items)

		return { success: true, id }
	} catch (error) {
		console.error('Worker: Error saving offline invoice:', error)
		throw error
	}
}

// Update local stock
async function updateLocalStock(items) {
	try {
		const db = await initDB()

		for (const item of items) {
			const currentStock = await db.stock.get({
				item_code: item.item_code,
				warehouse: item.warehouse
			})

			const qty = item.quantity || item.qty || 0
			const newQty = (currentStock?.qty || 0) - qty

			await db.stock.put({
				item_code: item.item_code,
				warehouse: item.warehouse,
				qty: newQty,
				updated_at: Date.now()
			})
		}
	} catch (error) {
		console.error('Worker: Error updating local stock:', error)
	}
}

// Search cached items
async function searchCachedItems(searchTerm = '', limit = 50) {
	try {
		const db = await initDB()
		const term = searchTerm.toLowerCase()

		if (!term) {
			return await db.items.limit(limit).toArray()
		}

		const results = await db.items
			.where('item_code').startsWithIgnoreCase(term)
			.or('item_name').startsWithIgnoreCase(term)
			.limit(limit)
			.toArray()

		return results
	} catch (error) {
		console.error('Worker: Error searching cached items:', error)
		return []
	}
}

// Search cached customers
async function searchCachedCustomers(searchTerm = '', limit = 20) {
	try {
		const db = await initDB()
		const term = searchTerm.toLowerCase()

		if (!term) {
			return await db.customers.limit(limit).toArray()
		}

		// Get all customers and filter in memory for 'includes' behavior
		// This is fast because IndexedDB is already in-memory for small datasets
		const allCustomers = await db.customers.toArray()

		const results = allCustomers.filter(cust => {
			const name = (cust.customer_name || '').toLowerCase()
			const mobile = (cust.mobile_no || '').toLowerCase()
			const id = (cust.name || '').toLowerCase()

			return name.includes(term) ||
			       mobile.includes(term) ||
			       id.includes(term)
		}).slice(0, limit)

		return results
	} catch (error) {
		console.error('Worker: Error searching cached customers:', error)
		return []
	}
}

// Cache items from server
async function cacheItemsFromServer(items) {
	try {
		const db = await initDB()
		await db.items.bulkPut(items)

		// Update settings
		await db.settings.put({
			key: 'items_last_sync',
			value: Date.now()
		})

		return { success: true, count: items.length }
	} catch (error) {
		console.error('Worker: Error caching items:', error)
		throw error
	}
}

// Cache customers from server
async function cacheCustomersFromServer(customers) {
	try {
		const db = await initDB()
		await db.customers.bulkPut(customers)

		// Update settings
		await db.settings.put({
			key: 'customers_last_sync',
			value: Date.now()
		})

		return { success: true, count: customers.length }
	} catch (error) {
		console.error('Worker: Error caching customers:', error)
		throw error
	}
}

// Check if cache is ready
async function isCacheReady() {
	try {
		const db = await initDB()
		const itemCount = await db.items.count()
		return itemCount > 0
	} catch (error) {
		return false
	}
}

// Get customers count
async function getCustomersCount() {
	try {
		const db = await initDB()
		const count = await db.customers.count()
		return count
	} catch (error) {
		console.error('Worker: Error getting customers count:', error)
		return 0
	}
}

// Get items count
async function getItemsCount() {
	try {
		const db = await initDB()
		const count = await db.items.count()
		return count
	} catch (error) {
		console.error('Worker: Error getting items count:', error)
		return 0
	}
}

// Get cache stats
async function getCacheStats() {
	try {
		const db = await initDB()

		const [itemCount, customerCount, queuedInvoices, lastSyncSetting] = await Promise.all([
			db.items.count(),
			db.customers.count(),
			getOfflineInvoiceCount(),
			db.settings.get('items_last_sync')
		])

		return {
			items: itemCount,
			customers: customerCount,
			queuedInvoices,
			cacheReady: itemCount > 0,
			lastSync: lastSyncSetting?.value || null
		}
	} catch (error) {
		console.error('Worker: Error getting cache stats:', error)
		return {
			items: 0,
			customers: 0,
			queuedInvoices: 0,
			cacheReady: false,
			lastSync: null
		}
	}
}

// Delete offline invoice
async function deleteOfflineInvoice(id) {
	try {
		const db = await initDB()
		await db.invoice_queue.delete(id)
		return { success: true }
	} catch (error) {
		console.error('Worker: Error deleting offline invoice:', error)
		throw error
	}
}

// Message handler
self.onmessage = async (event) => {
	const { type, payload, id } = event.data

	try {
		let result

		switch (type) {
			case 'PING_SERVER':
				result = await pingServer()
				break

			case 'CHECK_OFFLINE':
				result = isOffline(payload.browserOnline)
				break

			case 'GET_INVOICE_COUNT':
				result = await getOfflineInvoiceCount()
				break

			case 'GET_INVOICES':
				result = await getOfflineInvoices()
				break

			case 'SAVE_INVOICE':
				result = await saveOfflineInvoice(payload.invoiceData)
				break

			case 'SEARCH_ITEMS':
				result = await searchCachedItems(payload.searchTerm, payload.limit)
				break

			case 'SEARCH_CUSTOMERS':
				result = await searchCachedCustomers(payload.searchTerm, payload.limit)
				break

			case 'CACHE_ITEMS':
				result = await cacheItemsFromServer(payload.items)
				break

			case 'CACHE_CUSTOMERS':
				result = await cacheCustomersFromServer(payload.customers)
				break

			case 'IS_CACHE_READY':
				result = await isCacheReady()
				break

			case 'GET_CACHE_STATS':
				result = await getCacheStats()
				break

			case 'DELETE_INVOICE':
				result = await deleteOfflineInvoice(payload.id)
				break

			case 'SET_MANUAL_OFFLINE':
				manualOffline = payload.value
				result = { success: true, manualOffline }
				break

			case 'GET_CUSTOMERS_COUNT':
				result = await getCustomersCount()
				break

			case 'GET_ITEMS_COUNT':
				result = await getItemsCount()
				break

			default:
				throw new Error(`Unknown message type: ${type}`)
		}

		self.postMessage({
			type: 'SUCCESS',
			id,
			payload: result
		})
	} catch (error) {
		self.postMessage({
			type: 'ERROR',
			id,
			payload: {
				message: error.message,
				stack: error.stack
			}
		})
	}
}

// Initialize worker
async function initialize() {
	try {
		// Initialize database first
		await initDB()
		console.log('Offline worker: Database ready')

		// Start periodic server ping (every 30 seconds)
		setInterval(async () => {
			const isOnline = await pingServer()
			self.postMessage({
				type: 'SERVER_STATUS_CHANGE',
				payload: { serverOnline: isOnline }
			})
		}, 30000)

		// Initial ping
		const isOnline = await pingServer()

		self.postMessage({
			type: 'WORKER_READY',
			payload: { serverOnline: isOnline }
		})

		console.log('Offline worker initialized and ready')
	} catch (error) {
		console.error('Offline worker initialization failed:', error)
		self.postMessage({
			type: 'ERROR',
			payload: {
				message: `Worker initialization failed: ${error.message}`,
				stack: error.stack
			}
		})
	}
}

// Start initialization
initialize()
