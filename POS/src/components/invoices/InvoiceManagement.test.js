// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { setActivePinia, createPinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import InvoiceManagement from "./InvoiceManagement.vue";

// Global translate shim used by compiled templates across the module graph.
globalThis.__ = (value) => value;

// --- Mocks: keep the component light, focus on the Sales/Purchases toggle. ---

// Mock the heavy children at the module level so their import chains
// (AutocompleteSelect, PaymentDialog, PurchaseInvoiceList) never evaluate.
vi.mock("@/components/invoices/InvoiceFilters.vue", () => ({
	default: { name: "InvoiceFilters", template: "<div />" },
}));
vi.mock("@/components/sale/PaymentDialog.vue", () => ({
	default: { name: "PaymentDialog", template: "<div />" },
}));
vi.mock("@/components/purchases/PurchaseInvoiceList.vue", () => ({
	default: {
		name: "PurchaseInvoiceList",
		props: ["fixedStatus", "canCreatePayment", "posProfile"],
		template: '<div data-testid="stub-purchase-list" :data-fixed-status="fixedStatus" />',
	},
}));

vi.mock("@/composables/useInvoiceFilters", () => ({
	useInvoiceFilters: () => ({
		filteredInvoices: { value: [] },
		uniqueCustomers: { value: [] },
		uniqueProducts: { value: [] },
		filterStats: { value: {} },
	}),
}));

vi.mock("@/stores/invoiceFilters", () => ({
	useInvoiceFiltersStore: () => ({
		$reset: vi.fn(),
		loadSavedFiltersFromStorage: vi.fn(),
	}),
}));

vi.mock("@/composables/useFormatters", () => ({
	useFormatters: () => ({
		formatDate: (v) => v,
		formatDateTime: (v) => v,
		formatTime: (v) => v,
	}),
}));

vi.mock("@/composables/useToast", () => ({
	useToast: () => ({ showSuccess: vi.fn(), showError: vi.fn() }),
}));

vi.mock("@/utils/offline/offlineState", () => ({ isOffline: () => false }));

vi.mock("@/utils/offline/sync", () => ({
	cacheUnpaidInvoices: vi.fn(),
	getCachedUnpaidInvoices: vi.fn(async () => []),
	cacheUnpaidSummary: vi.fn(),
	getCachedUnpaidSummary: vi.fn(async () => null),
	saveOfflinePayment: vi.fn(),
}));

vi.mock("frappe-ui", () => ({
	Button: { template: "<button><slot /></button>" },
	LoadingIndicator: { template: "<span />" },
	// get_unpaid_invoices returns an array; get_unpaid_summary an object.
	call: vi.fn(async (method) => {
		if (typeof method === "string" && method.endsWith("get_unpaid_summary")) {
			return { count: 0, total_outstanding: 0, total_paid: 0 };
		}
		return [];
	}),
}));

function mountManagement(props = {}) {
	return mount(InvoiceManagement, {
		props: { modelValue: true, posProfile: "POS-A", ...props },
		global: {
			mocks: { __: (value) => value },
			config: { globalProperties: { __: (value) => value } },
		},
	});
}

describe("InvoiceManagement Sales/Purchases toggle", () => {
	beforeEach(() => {
		setActivePinia(createPinia());
		globalThis.__ = (value) => value;
	});

	afterEach(() => {
		globalThis.__ = undefined;
		vi.clearAllMocks();
	});

	it("hides the Sales/Purchases toggle without purchase permission", async () => {
		const wrapper = mountManagement({ canManagePurchases: false });
		await flushPromises();
		expect(wrapper.find('[data-testid="invoice-mode-toggle"]').exists()).toBe(false);
	});

	it("shows the toggle and defaults to the Sales view with purchase permission", async () => {
		const wrapper = mountManagement({ canManagePurchases: true });
		await flushPromises();
		expect(wrapper.find('[data-testid="invoice-mode-toggle"]').exists()).toBe(true);
		// Sales view: the embedded purchase list is not rendered yet.
		expect(wrapper.find('[data-testid="stub-purchase-list"]').exists()).toBe(false);
	});

	it("switches to the Purchases view and renders the embedded purchase list", async () => {
		const wrapper = mountManagement({ canManagePurchases: true });
		await flushPromises();
		await wrapper.find('[data-testid="invoice-mode-purchases"]').trigger("click");
		await flushPromises();
		const list = wrapper.find('[data-testid="stub-purchase-list"]');
		expect(list.exists()).toBe(true);
		// Default purchase tab is "unpaid" → outstanding filter.
		expect(list.attributes("data-fixed-status")).toBe("unpaid");
	});

	it("changing purchase tabs re-scopes the embedded list's fixed status", async () => {
		const wrapper = mountManagement({ canManagePurchases: true });
		await flushPromises();
		await wrapper.find('[data-testid="invoice-mode-purchases"]').trigger("click");
		await flushPromises();

		await wrapper.find('[data-testid="purchase-tab-history"]').trigger("click");
		await flushPromises();
		expect(
			wrapper.find('[data-testid="stub-purchase-list"]').attributes("data-fixed-status"),
		).toBe("history");

		await wrapper.find('[data-testid="purchase-tab-drafts"]').trigger("click");
		await flushPromises();
		expect(
			wrapper.find('[data-testid="stub-purchase-list"]').attributes("data-fixed-status"),
		).toBe("drafts");
	});

	it("opens directly on the Purchases view when initialViewMode is 'purchases'", async () => {
		const wrapper = mountManagement({
			canManagePurchases: true,
			initialViewMode: "purchases",
		});
		await flushPromises();
		expect(wrapper.find('[data-testid="stub-purchase-list"]').exists()).toBe(true);
	});
});
