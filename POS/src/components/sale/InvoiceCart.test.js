// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { setActivePinia, createPinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Global translate shim used by compiled templates across the module graph.
globalThis.__ = (v, args) => (Array.isArray(args) ? args : []).reduce((s, a, i) => s.replace(`{${i}}`, a), v);

// Cart store: minimal surface the template reads; mode toggles per test.
const { cart } = vi.hoisted(() => ({
	cart: {
		mode: "purchase",
		supplier: null,
		purchaseDefaultSupplier: null,
		taxInclusive: false,
		targetDoctype: "Sales Invoice",
		isSubmitting: false,
		purchaseWarehouse: "Stores - A",
		appliedOffers: [],
		setSupplier: vi.fn(),
		changeItemUOM: vi.fn(),
		updateItemDetails: vi.fn(),
	},
}));
vi.mock("@/stores/posCart", () => ({ usePOSCartStore: () => cart }));
vi.mock("@/stores/posSettings", () => ({
	usePOSSettingsStore: () => ({ allowSalesOrder: false, allowUserToEditRate: false }),
}));
vi.mock("@/stores/posOffers", () => ({
	usePOSOffersStore: () => ({ ensureOffersFetched: vi.fn() }),
}));
vi.mock("@/stores/customerSearch", () => ({
	useCustomerSearchStore: () => ({
		allCustomers: [],
		loadAllCustomers: vi.fn(),
		loadCustomerHistory: vi.fn(),
		trackCustomerSelection: vi.fn(),
	}),
}));
vi.mock("@/composables/useFormatters", () => ({
	useFormatters: () => ({ formatQuantity: (v) => String(v) }),
}));
vi.mock("@/composables/useCartSort", async () => {
	const { ref, computed } = await import("vue");
	// Mirror the real signature: useCartSort(getItems) → sortedItems (a real
	// computed so Vue template auto-unwraps it) reflects props.items.
	return {
		useCartSort: (getItems) => ({
			cartSortBy: ref(null),
			cartSortOrder: ref("asc"),
			showCartSortDropdown: ref(false),
			sortedItems: computed(() =>
				typeof getItems === "function" ? getItems() || [] : [],
			),
			CART_SORT_OPTIONS: [],
			CART_SORT_ICONS: {},
			toggleCartSortDropdown: vi.fn(),
			handleCartSortToggle: vi.fn(),
			getCartSortLabel: () => "",
			getCartSortIconState: () => "none",
		}),
	};
});
vi.mock("@/utils/offline", () => ({ isOffline: () => false }));
vi.mock("@/utils/offline/workerClient", () => ({ offlineWorker: {} }));
vi.mock("@/utils/currency", () => ({
	DEFAULT_CURRENCY: "SAR",
	formatCurrency: (v) => Number(v || 0).toFixed(2),
}));
vi.mock("frappe-ui", () => ({
	FeatherIcon: { template: "<span />" },
	createResource: () => ({ reload: vi.fn(), submit: vi.fn(), data: null }),
}));

import InvoiceCart from "./InvoiceCart.vue";

const translate = (v, args) => (Array.isArray(args) ? args : []).reduce((s, a, i) => s.replace(`{${i}}`, a), v);
const stubs = {
	EditItemDialog: { template: "<div />" },
	SupplierSelector: { template: "<div />" },
};

function mountCart(items) {
	return mount(InvoiceCart, {
		props: { items, posProfile: "POS-A", currency: "SAR" },
		global: {
			stubs,
			mocks: { __: translate },
			config: { globalProperties: { __: translate } },
		},
	});
}

describe("InvoiceCart purchase-mode zero-rate chip", () => {
	beforeEach(() => {
		setActivePinia(createPinia());
		cart.mode = "purchase";
	});

	afterEach(() => {
		vi.clearAllMocks();
	});

	it("renders «أدخل السعر» chip for a zero-rate purchase line", async () => {
		const wrapper = mountCart([
			{
				item_code: "PHN-AIRPODS-4",
				item_name: "AirPods 4",
				quantity: 1,
				rate: 0,
				uom: "Nos",
				stock_uom: "Nos",
				item_uoms: [],
			},
		]);
		await flushPromises();
		const chip = wrapper.find('[data-testid="enter-price-chip"]');
		expect(chip.exists()).toBe(true);
		expect(chip.text()).toContain("أدخل السعر");
	});

	it("shows the plain rate (no chip) for a priced purchase line", async () => {
		const wrapper = mountCart([
			{
				item_code: "PHN-1",
				item_name: "iPhone",
				quantity: 1,
				rate: 1299,
				uom: "Nos",
				stock_uom: "Nos",
				item_uoms: [],
			},
		]);
		await flushPromises();
		expect(wrapper.find('[data-testid="enter-price-chip"]').exists()).toBe(false);
		expect(wrapper.text()).toContain("1299.00");
	});

	it("does not show the chip in sales mode even for a zero-rate line", async () => {
		cart.mode = "sales";
		const wrapper = mountCart([
			{
				item_code: "X",
				item_name: "Freebie",
				quantity: 1,
				rate: 0,
				uom: "Nos",
				stock_uom: "Nos",
				item_uoms: [],
			},
		]);
		await flushPromises();
		expect(wrapper.find('[data-testid="enter-price-chip"]').exists()).toBe(false);
	});
});
