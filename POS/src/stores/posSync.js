/**
 * POS Sync Store
 *
 * Manages offline synchronization state and operations for the POS system.
 * Handles invoice caching, sync operations, and offline state management.
 *
 * Key Design Decision:
 * This store subscribes directly to offlineState instead of using the useOffline()
 * composable. This is intentional because Pinia stores are singletons that persist
 * across component remounts (e.g., when changing language). Using Vue lifecycle
 * hooks (onMounted/onUnmounted) from composables would cause the subscription to
 * break when components remount.
 *
 * @module stores/posSync
 */

import { useToast } from "@/composables/useToast";
import {
	cacheCustomersFromServer,
	cachePaymentMethodsFromServer,
	cacheSalesPersonsFromServer,
	syncOfflineInvoices,
	syncOfflinePayments,
	getOfflinePayments,
	getOfflinePaymentCount,
	deleteOfflinePayment as removeOfflinePayment,
	cacheInvoiceHistory,
	cacheUnpaidInvoices,
	cacheUnpaidSummary,
} from "@/utils/offline";
import { call } from "@/utils/apiWrapper";
import { logger } from "@/utils/logger";
import { offlineState } from "@/utils/offline/offlineState";
import { offlineWorker } from "@/utils/offline/workerClient";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

const log = logger.create("POSSync");

export const usePOSSyncStore = defineStore("posSync", () => {
	// =========================================================================
	// STATE
	// =========================================================================

	/** Current offline status - synced with offlineState singleton */
	const isOffline = ref(offlineState.isOffline);

	/** Number of invoices pending sync */
	const pendingInvoicesCount = ref(0);

	/** Whether a sync operation is in progress */
	const isSyncing = ref(false);

	/** Current connection quality metrics */
	const connectionQuality = ref(offlineState.getConnectionQuality());

	/** List of pending invoices for display */
	const pendingInvoicesList = ref([]);

	/** Track previous offline state for detecting online/offline transitions */
	let wasOffline = offlineState.isOffline;

	// =========================================================================
	// TOAST NOTIFICATIONS
	// =========================================================================

	const { showSuccess, showError, showWarning } = useToast();

	// =========================================================================
	// OFFLINE STATE SUBSCRIPTION
	// =========================================================================

	/**
	 * Subscribe to offlineState changes at the store level.
	 * This subscription persists for the app's lifetime since Pinia stores are singletons.
	 */
	offlineState.subscribe(async (state) => {
		const nowOffline = state.isOffline;

		// Update reactive state
		isOffline.value = nowOffline;
		connectionQuality.value = state.quality || offlineState.getConnectionQuality();

		// Auto-sync when transitioning from offline to online
		if (wasOffline && !nowOffline) {
			log.info("Transition to online detected, auto-syncing pending invoices");
			try {
				await syncPending();
			} catch (error) {
				log.error("Auto-sync failed on reconnection", error);
			}
		}

		wasOffline = nowOffline;
	});

	// =========================================================================
	// COMPUTED
	// =========================================================================

	/** Whether there are any pending invoices to sync */
	const hasPendingInvoices = computed(() => pendingInvoicesCount.value > 0);

	// =========================================================================
	// INTERNAL HELPERS
	// =========================================================================

	/**
	 * Update the pending invoices count from the worker
	 */
	async function updatePendingCount() {
		try {
			const [invoiceCount, paymentCount] = await Promise.all([
				offlineWorker.getOfflineInvoiceCount(),
				getOfflinePaymentCount(),
			]);
			pendingInvoicesCount.value = invoiceCount + paymentCount;
		} catch (error) {
			log.error("Failed to get pending invoice count", error);
		}
	}

	/**
	 * Sync pending invoices to the server
	 * @throws {Error} If called while offline
	 */
	async function syncPending(options = {}) {
		if (isOffline.value) {
			throw new Error("Cannot sync while offline");
		}

		isSyncing.value = true;
		try {
			const [invoiceResult, paymentResult] = await Promise.all([
				syncOfflineInvoices(),
				syncOfflinePayments(options),
			]);
			await updatePendingCount();
			return {
				success: (invoiceResult.success || 0) + (paymentResult.success || 0),
				failed: (invoiceResult.failed || 0) + (paymentResult.failed || 0),
				skipped: (invoiceResult.skipped || 0) + (paymentResult.skipped || 0),
				errors: [...(invoiceResult.errors || []), ...(paymentResult.errors || [])],
				invoices: invoiceResult,
				payments: paymentResult,
			};
		} catch (error) {
			log.error("Failed to sync invoices", error);
			throw error;
		} finally {
			isSyncing.value = false;
		}
	}

	/**
	 * Get all pending invoices from the worker
	 */
	async function getPending() {
		return await offlineWorker.getOfflineInvoices();
	}

	/**
	 * Delete a pending invoice by ID
	 * @param {string} id - Invoice ID to delete
	 */
	async function deletePending(id) {
		await offlineWorker.deleteOfflineInvoice(id);
		await updatePendingCount();
	}

	/**
	 * Cache items and customers for offline use
	 * @param {Array} items - Items to cache
	 * @param {Array} customers - Customers to cache
	 */
	async function cacheData(items, customers) {
		try {
			if (items?.length > 0) {
				await offlineWorker.cacheItems(items);
			}
			if (customers?.length > 0) {
				await offlineWorker.cacheCustomers(customers);
			}
			return true;
		} catch (error) {
			log.error("Failed to cache data", error);
			return false;
		}
	}

	// =========================================================================
	// PUBLIC ACTIONS
	// =========================================================================

	/**
	 * Save an invoice offline for later sync
	 * @param {Object} invoiceData - Invoice data to save
	 */
	async function saveInvoiceOffline(invoiceData) {
		try {
			const result = await offlineWorker.saveOfflineInvoice(invoiceData);
			await updatePendingCount();
			log.info("Invoice saved offline successfully");
			return result || { success: true };
		} catch (error) {
			log.error("Failed to save invoice offline", error);
			throw error;
		}
	}

	/**
	 * Load the list of pending invoices for display
	 */
	async function loadPendingInvoices() {
		try {
			const [invoices, payments] = await Promise.all([getPending(), getOfflinePayments()]);
			pendingInvoicesList.value = [
				...invoices.map((invoice) => ({ ...invoice, operation_type: "invoice" })),
				...payments.map((payment) => ({ ...payment, operation_type: "payment" })),
			].sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
		} catch (error) {
			log.error("Failed to load pending invoices", error);
			pendingInvoicesList.value = [];
		}
	}

	/**
	 * Delete an offline invoice by ID with user feedback
	 * @param {string} invoiceId - Invoice ID to delete
	 */
	async function deleteOfflineInvoice(invoiceId) {
		try {
			await deletePending(invoiceId);
			await loadPendingInvoices();
			showSuccess(__("Offline invoice deleted successfully"));
		} catch (error) {
			log.error("Failed to delete offline invoice", error);
			showError(error.message || __("Failed to delete offline invoice"));
			throw error;
		}
	}

	async function deleteOfflinePayment(paymentId) {
		try {
			await removeOfflinePayment(paymentId);
			await loadPendingInvoices();
			await updatePendingCount();
			showSuccess(__("Offline payment deleted successfully"));
		} catch (error) {
			log.error("Failed to delete offline payment", error);
			showError(error.message || __("Failed to delete offline payment"));
			throw error;
		}
	}

	/**
	 * Sync all pending invoices with user feedback
	 * @returns {Object} Sync result with success/failed counts
	 */
	async function syncAllPending() {
		if (isOffline.value) {
			showWarning(__("Cannot sync while offline"));
			return { success: 0, failed: 0, errors: [] };
		}

		try {
			const result = await syncPending();

			if (result.success > 0) {
				showSuccess(__("{0} offline operation(s) synced successfully", [result.success]));
				await loadPendingInvoices();
			}

			return result;
		} catch (error) {
			log.error("Sync all pending failed", error);
			throw error;
		}
	}

	async function retryFailedPending() {
		if (isOffline.value) {
			showWarning(__("Cannot retry while offline"));
			return { success: 0, failed: 0, skipped: 0, errors: [] };
		}
		const result = await syncPending({ includeFailed: true });
		await loadPendingInvoices();
		return result;
	}

	/**
	 * Preload data for offline use (payment methods, customers)
	 * @param {Object} currentProfile - Current POS profile
	 */
	let _preloadingProfile = null;
	async function preloadDataForOffline(currentProfile) {
		if (!currentProfile || isOffline.value) {
			return;
		}

		// Prevent duplicate concurrent preloads (e.g., from component remounts
		// triggered by language/translation version changes)
		if (_preloadingProfile === currentProfile.name) {
			log.debug("Preload already in progress for this profile, skipping duplicate");
			return;
		}
		_preloadingProfile = currentProfile.name;

		try {
			const cacheReady = await checkCacheReady();
			const stats = await getCacheStats();
			const needsRefresh =
				!stats.lastSync || Date.now() - stats.lastSync > 24 * 60 * 60 * 1000;

			// Always load payment methods for reliable offline support
			log.info("Loading payment methods for offline use");
			try {
				const paymentMethodsData = await cachePaymentMethodsFromServer(
					currentProfile.name
				);

				if (paymentMethodsData.payment_methods?.length > 0) {
					const methodsWithProfile = paymentMethodsData.payment_methods.map(
						(method) => ({
							...method,
							pos_profile: currentProfile.name,
						})
					);
					await offlineWorker.cachePaymentMethods(methodsWithProfile);
					log.success(`Cached ${methodsWithProfile.length} payment methods`);
				}
			} catch (error) {
				log.error("Failed to load payment methods", error);
				// Continue with other data loading
			}

			// Cache sales persons for offline use
			try {
				const salesPersonsData = await cacheSalesPersonsFromServer(currentProfile.name);
				if (salesPersonsData.sales_persons?.length > 0) {
					const personsWithProfile = salesPersonsData.sales_persons.map((person) => ({
						...person,
						pos_profile: currentProfile.name,
					}));
					await offlineWorker.cacheSalesPersons(personsWithProfile);
					log.success(`Cached ${personsWithProfile.length} sales persons`);
				}
			} catch (error) {
				log.error("Failed to load sales persons", error);
			}

			// Load customers if cache needs refresh
			if (!cacheReady || needsRefresh) {
				showSuccess(__("Loading customers for offline use..."));

				const customersData = await cacheCustomersFromServer(currentProfile.name);
				await cacheData([], customersData.customers || []);

				showSuccess(__("Data is ready for offline use"));
			}

			// Preload invoice history and unpaid invoices in parallel for faster startup
			log.info("Loading invoice data for offline use");
			try {
				const [invoices, unpaidInvoices, unpaidSummary] = await Promise.all([
					call("pos_next.api.invoices.get_invoices", {
						pos_profile: currentProfile.name,
						limit: 100,
					}).catch((err) => {
						log.error("Failed to load invoice history", err);
						return [];
					}),
					call("pos_next.api.partial_payments.get_unpaid_invoices", {
						pos_profile: currentProfile.name,
						limit: 100,
					}).catch((err) => {
						log.error("Failed to load unpaid invoices", err);
						return [];
					}),
					call("pos_next.api.partial_payments.get_unpaid_summary", {
						pos_profile: currentProfile.name,
					}).catch((err) => {
						log.error("Failed to load unpaid summary", err);
						return null;
					}),
				]);

				// Cache results in parallel
				await Promise.all([
					invoices?.length > 0
						? cacheInvoiceHistory(invoices, currentProfile.name).then(() =>
								log.success(
									`Cached ${invoices.length} invoices for offline viewing`
								)
						  )
						: Promise.resolve(),
					unpaidInvoices?.length > 0
						? cacheUnpaidInvoices(unpaidInvoices, currentProfile.name).then(() =>
								log.success(
									`Cached ${unpaidInvoices.length} unpaid invoices for offline viewing`
								)
						  )
						: Promise.resolve(),
					unpaidSummary
						? cacheUnpaidSummary(unpaidSummary, currentProfile.name).then(() =>
								log.debug("Cached unpaid invoice summary")
						  )
						: Promise.resolve(),
				]);
			} catch (error) {
				log.error("Failed to load invoice data for offline", error);
				// Continue - not critical for POS operation
			}
		} catch (error) {
			log.error("Failed to preload offline data", error);
			showWarning(__("Some data may not be available offline"));
		} finally {
			_preloadingProfile = null;
		}
	}

	/**
	 * Check if offline cache is available and warn user if not
	 * @returns {boolean} Whether cache is ready
	 */
	async function checkOfflineCacheAvailability() {
		const cacheReady = await checkCacheReady();
		if (!cacheReady && isOffline.value) {
			showWarning(__("POS is offline without cached data. Please connect to sync."));
		}
		return cacheReady;
	}

	/**
	 * Check if the offline cache is ready
	 */
	async function checkCacheReady() {
		return await offlineWorker.isCacheReady();
	}

	/**
	 * Get cache statistics
	 */
	async function getCacheStats() {
		return await offlineWorker.getCacheStats();
	}

	// =========================================================================
	// INITIALIZATION
	// =========================================================================

	// Initialize pending count on store creation, then sync immediately if
	// we're online and there's a backlog left over from a previous session.
	// The offlineState subscription above only auto-syncs on a transition
	// observed DURING this session — a fresh page load while already online
	// never sees that edge, so invoices queued in an earlier session would
	// otherwise sit stuck until the cashier happens to notice and sync
	// manually from the offline invoices dialog.
	(async () => {
		await updatePendingCount();
		if (!offlineState.isOffline && pendingInvoicesCount.value > 0) {
			log.info(
				`${pendingInvoicesCount.value} pending offline operation(s) found on startup, syncing now`
			);
			try {
				await syncPending();
			} catch (error) {
				log.error("Startup sync of pending invoices failed", error);
			}
		}
	})();

	// =========================================================================
	// EXPORTS
	// =========================================================================

	return {
		// State
		isOffline,
		pendingInvoicesCount,
		isSyncing,
		pendingInvoicesList,

		// Computed
		hasPendingInvoices,

		// Actions
		saveInvoiceOffline,
		loadPendingInvoices,
		updatePendingCount,
		deleteOfflineInvoice,
		deleteOfflinePayment,
		syncAllPending,
		retryFailedPending,
		preloadDataForOffline,
		checkOfflineCacheAvailability,
		checkCacheReady,
		getCacheStats,
	};
});
