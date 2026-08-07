import { call } from "@/utils/apiWrapper";
import { computed, ref } from "vue";

/**
 * Composable for checking user permissions
 * Provides reactive permission checks for doctypes
 */

// Cache permissions to avoid repeated API calls
const permissionCache = ref({});

// Shared POS permissions state — loaded once from get_pos_permissions()
const _posPerms = ref(null);
const _posPermsLoading = ref(false);
// The POS Profile the cached permissions were loaded for. Feature-gated flags
// (Catalog, Reports, Purchases…) are profile-specific, so a result loaded for an
// empty/other profile must NOT be reused for a real one — otherwise an early
// permission load (before the shift's profile is ready) would cache a degraded,
// all-flags-off result and spuriously hide those buttons.
let _posPermsProfile;

/**
 * Load all POS permissions in one API call.
 * Cached per profile; re-fetches when the requested profile differs from the cache.
 */
export async function loadPOSPermissions({ force = false, posProfile = null } = {}) {
	if (_posPermsLoading.value) {
		// Wait for in-flight request
		await new Promise((resolve) => {
			const stop = setInterval(() => {
				if (!_posPermsLoading.value) { clearInterval(stop); resolve(); }
			}, 50);
		});
		if (!force && _posPerms.value && _posPermsProfile === posProfile) return _posPerms.value;
	}
	if (force || _posPermsProfile !== posProfile) _posPerms.value = null;
	if (_posPerms.value) return _posPerms.value;
	_posPermsLoading.value = true;
	try {
		const result = await call("pos_next.api.permissions.get_pos_permissions", {
			pos_profile: posProfile,
		});
		// Never cache an empty/failed result — a transient hiccup during startup
		// (e.g. a CSRF/session blip) would otherwise leave every gated button
		// permanently hidden. Leaving _posPerms null lets the next call retry.
		if (result && Object.keys(result).length) {
			_posPerms.value = result;
			_posPermsProfile = posProfile;
		}
	} catch (e) {
		console.error("[POS Permissions] Failed to load:", e);
	} finally {
		_posPermsLoading.value = false;
	}
	return _posPerms.value || {};
}

export function invalidatePOSPermissions() {
	_posPerms.value = null;
	_posPermsProfile = undefined;
	permissionCache.value = {};
}

export async function refreshPOSPermissions(posProfile = null) {
	invalidatePOSPermissions();
	return loadPOSPermissions({ force: true, posProfile });
}

/** Reactive ref to the loaded POS permissions object */
export const posPermissions = computed(() => _posPerms.value || {});

export function usePermissions() {
	/**
	 * Check if the current user has a specific permission for a doctype
	 * @param {string} doctype - The doctype to check (e.g., 'Customer', 'Promotional Scheme')
	 * @param {string} permType - Permission type: 'create', 'write', 'read', 'delete', 'submit'
	 * @param {string} docname - Optional document name (null for create operations)
	 * @returns {Promise<boolean>} - True if user has permission
	 */
	async function checkPermission(doctype, permType = "create", docname = null) {
		try {
			// Check cache first
			const cacheKey = `${doctype}:${permType}`;
			if (permissionCache.value[cacheKey] !== undefined) {
				return permissionCache.value[cacheKey];
			}

			// Call backend to check permission
			const result = await call("frappe.client.has_permission", {
				doctype: doctype,
				docname: docname || "",
				perm_type: permType,
			});

			// Extract has_permission from response object
			const hasPermission = Boolean(result?.has_permission);

			// Cache the result
			permissionCache.value[cacheKey] = hasPermission;
			return hasPermission;
		} catch (error) {
			console.error(`Error checking permission for ${doctype}:${permType}`, error);
			// Default to false on error (safer)
			return false;
		}
	}

	/**
	 * Check multiple permissions at once
	 * @param {Array} checks - Array of {doctype, permType} objects
	 * @returns {Promise<Object>} - Object with results keyed by "doctype:permType"
	 */
	async function checkMultiplePermissions(checks) {
		const results = {};

		await Promise.all(
			checks.map(async ({ doctype, permType = "create" }) => {
				const key = `${doctype}:${permType}`;
				results[key] = await checkPermission(doctype, permType);
			})
		);

		return results;
	}

	/**
	 * Create a reactive permission check
	 * @param {string} doctype - The doctype to check
	 * @param {string} permType - Permission type
	 * @returns {Object} - { hasPermission, loading, checkPermission }
	 */
	function usePermissionCheck(doctype, permType = "create") {
		const hasPermission = ref(false);
		const loading = ref(false);

		const check = async () => {
			loading.value = true;
			try {
				hasPermission.value = await checkPermission(doctype, permType);
			} finally {
				loading.value = false;
			}
		};

		// Check immediately
		check();

		return {
			hasPermission: computed(() => hasPermission.value),
			loading: computed(() => loading.value),
			refresh: check,
		};
	}

	/**
	 * Clear permission cache (useful after role changes)
	 */
	function clearCache() {
		permissionCache.value = {};
	}

	/**
	 * Preload common POS permissions for better UX
	 */
	async function preloadCommonPermissions() {
		const commonChecks = [
			{ doctype: "Customer", permType: "create" },
			{ doctype: "Customer", permType: "write" },
			{ doctype: "Promotional Scheme", permType: "create" },
			{ doctype: "Promotional Scheme", permType: "write" },
			{ doctype: "Promotional Scheme", permType: "delete" },
			{ doctype: "POS Coupon", permType: "create" },
			{ doctype: "POS Coupon", permType: "write" },
			{ doctype: "Sales Invoice", permType: "create" },
			{ doctype: "Sales Invoice", permType: "submit" },
		];

		await checkMultiplePermissions(commonChecks);
	}

	return {
		checkPermission,
		checkMultiplePermissions,
		usePermissionCheck,
		clearCache,
		preloadCommonPermissions,
	};
}

/**
 * Permission helper for common POS operations
 */
export function usePOSPermissions() {
	const { checkPermission, preloadCommonPermissions } = usePermissions();

	// Customer permissions
	const canCreateCustomer = async () => await checkPermission("Customer", "create");
	const canEditCustomer = async () => await checkPermission("Customer", "write");

	// Promotion permissions
	const canCreatePromotion = async () => await checkPermission("Promotional Scheme", "create");
	const canEditPromotion = async () => await checkPermission("Promotional Scheme", "write");
	const canDeletePromotion = async () => await checkPermission("Promotional Scheme", "delete");

	// Coupon permissions
	const canCreateCoupon = async () => await checkPermission("POS Coupon", "create");
	const canApplyCoupon = async () => await checkPermission("POS Coupon", "write");

	// Invoice permissions
	const canCreateInvoice = async () => await checkPermission("Sales Invoice", "create");
	const canSubmitInvoice = async () => await checkPermission("Sales Invoice", "submit");

	// Settings permissions
	const canEditSettings = async () => await checkPermission("POS Settings", "write");

	return {
		canCreateCustomer,
		canEditCustomer,
		canCreatePromotion,
		canEditPromotion,
		canDeletePromotion,
		canCreateCoupon,
		canApplyCoupon,
		canCreateInvoice,
		canSubmitInvoice,
		canEditSettings,
		preloadCommonPermissions,
	};
}
