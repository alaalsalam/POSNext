/**
 * Worker Client - Main thread interface to offline worker
 * Provides promise-based API to communicate with offline worker
 */

class OfflineWorkerClient {
	constructor() {
		this.worker = null
		this.messageId = 0
		this.pendingMessages = new Map()
		this.ready = false
		this.serverOnline = true
	}

	init() {
		if (this.worker) return

		// Create worker using Vite's worker import syntax
		this.worker = new Worker(
			new URL('../../workers/offline.worker.js?worker', import.meta.url),
			{ type: 'module' }
		)

		// Handle messages from worker
		this.worker.onmessage = (event) => {
			const { type, id, payload } = event.data

			if (type === 'WORKER_READY') {
				this.ready = true
				this.serverOnline = payload.serverOnline
				console.log('Offline worker ready, server online:', payload.serverOnline)
				return
			}

			if (type === 'SERVER_STATUS_CHANGE') {
				this.serverOnline = payload.serverOnline
				// Emit custom event for status changes
				window.dispatchEvent(new CustomEvent('offlineStatusChange', {
					detail: { serverOnline: payload.serverOnline }
				}))
				return
			}

			if (id !== undefined && this.pendingMessages.has(id)) {
				const { resolve, reject } = this.pendingMessages.get(id)
				this.pendingMessages.delete(id)

				if (type === 'SUCCESS') {
					resolve(payload)
				} else if (type === 'ERROR') {
					reject(new Error(payload.message))
				}
			}
		}

		// Handle worker errors
		this.worker.onerror = (error) => {
			console.error('Worker error:', error)
			console.error('Error details:', {
				message: error.message,
				filename: error.filename,
				lineno: error.lineno,
				colno: error.colno
			})
		}
	}

	async sendMessage(type, payload = {}) {
		if (!this.worker) {
			this.init()
		}

		return new Promise((resolve, reject) => {
			const id = this.messageId++
			this.pendingMessages.set(id, { resolve, reject })

			this.worker.postMessage({ type, payload, id })

			// Timeout after 30 seconds
			setTimeout(() => {
				if (this.pendingMessages.has(id)) {
					this.pendingMessages.delete(id)
					reject(new Error(`Worker message timeout: ${type}`))
				}
			}, 30000)
		})
	}

	// API Methods
	async pingServer() {
		return this.sendMessage('PING_SERVER')
	}

	async checkOffline(browserOnline) {
		return this.sendMessage('CHECK_OFFLINE', { browserOnline })
	}

	async getOfflineInvoiceCount() {
		return this.sendMessage('GET_INVOICE_COUNT')
	}

	async getOfflineInvoices() {
		return this.sendMessage('GET_INVOICES')
	}

	async saveOfflineInvoice(invoiceData) {
		return this.sendMessage('SAVE_INVOICE', { invoiceData })
	}

	async searchCachedItems(searchTerm = '', limit = 50) {
		return this.sendMessage('SEARCH_ITEMS', { searchTerm, limit })
	}

	async searchCachedCustomers(searchTerm = '', limit = 20) {
		return this.sendMessage('SEARCH_CUSTOMERS', { searchTerm, limit })
	}

	async cacheItems(items) {
		return this.sendMessage('CACHE_ITEMS', { items })
	}

	async cacheCustomers(customers) {
		return this.sendMessage('CACHE_CUSTOMERS', { customers })
	}

	async isCacheReady() {
		return this.sendMessage('IS_CACHE_READY')
	}

	async getCacheStats() {
		return this.sendMessage('GET_CACHE_STATS')
	}

	async deleteOfflineInvoice(id) {
		return this.sendMessage('DELETE_INVOICE', { id })
	}

	async setManualOffline(value) {
		return this.sendMessage('SET_MANUAL_OFFLINE', { value })
	}

	async getCachedCustomersCount() {
		return this.sendMessage('GET_CUSTOMERS_COUNT')
	}

	async getCachedItemsCount() {
		return this.sendMessage('GET_ITEMS_COUNT')
	}

	terminate() {
		if (this.worker) {
			this.worker.terminate()
			this.worker = null
			this.ready = false
		}
	}
}

// Create singleton instance
export const offlineWorker = new OfflineWorkerClient()

// Initialize worker on import
if (typeof window !== 'undefined') {
	offlineWorker.init()
}
