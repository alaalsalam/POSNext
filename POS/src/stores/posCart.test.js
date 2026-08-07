// @vitest-environment jsdom

import { setActivePinia, createPinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// --- Mocks -----------------------------------------------------------------

// Minimal fake useInvoice: plain refs + no-op actions so posCart can wire up
// without pulling in frappe-ui resources / real pricing logic.
const { fakeInvoice } = vi.hoisted(() => {
	const { ref } = require("vue");
	const invoice = {
		invoiceItems: ref([]),
		customer: ref(null),
		subtotal: ref(0),
		totalTax: ref(0),
		totalDiscount: ref(0),
		grandTotal: ref(0),
		posProfile: ref("POS-A"),
		posOpeningShift: ref(null),
		payments: ref([]),
		salesTeam: ref([]),
		additionalDiscount: ref(0),
		taxInclusive: ref(false),
		isSubmitting: ref(false),
		addItem: vi.fn((item, qty = 1) => {
			invoice.invoiceItems.value.push({
				item_code: item.item_code,
				item_name: item.item_name,
				rate: item.rate || 0,
				price_list_rate: item.price_list_rate || item.rate || 0,
				quantity: qty,
				uom: item.uom || item.stock_uom,
				stock_uom: item.stock_uom,
				conversion_factor: 1,
			});
		}),
		removeItem: vi.fn(),
		updateItemQuantity: vi.fn(),
		submitInvoice: vi.fn(async () => ({ name: "SINV-1" })),
		clearCart: vi.fn(() => {
			invoice.invoiceItems.value = [];
		}),
		loadTaxRules: vi.fn(),
		setTaxInclusive: vi.fn(),
		setDefaultCustomer: vi.fn(),
		applyDiscount: vi.fn(),
		removeDiscount: vi.fn(),
		applyOffersResource: { submit: vi.fn() },
		getItemDetailsResource: {},
		resolveUomPricing: vi.fn(),
		recalculateItem: vi.fn(),
		rebuildIncrementalCache: vi.fn(),
		formatItemsForSubmission: vi.fn(),
	};
	return { fakeInvoice: invoice };
});

vi.mock("@/composables/useInvoice", () => ({
	useInvoice: () => fakeInvoice,
}));

vi.mock("@/stores/posOffers", () => ({
	usePOSOffersStore: () => ({
		hasFetched: false,
		clearOneTimeContext: vi.fn(),
		loadOneTimeContextForCustomer: vi.fn(async () => {}),
		ensureOffersFetched: vi.fn(async () => {}),
		updateCartSnapshot: vi.fn(),
		checkOfferEligibility: () => ({ eligible: true }),
		allEligibleOffers: [],
		autoEligibleOffers: [],
	}),
}));

const { enforceStock } = vi.hoisted(() => ({ enforceStock: { value: false } }));
vi.mock("@/stores/posSettings", () => ({
	usePOSSettingsStore: () => ({
		shouldEnforceStockValidation: () => enforceStock.value,
	}),
}));

vi.mock("@/stores/posShift", () => ({
	usePOSShiftStore: () => ({ currentProfile: { customer: "Walk In" } }),
}));

const { offlineState } = vi.hoisted(() => ({
	offlineState: { isOffline: false },
}));
vi.mock("@/utils/offline/offlineState", () => ({
	offlineState,
}));

vi.mock("@/composables/useToast", () => ({
	useToast: () => ({
		showSuccess: vi.fn(),
		showError: vi.fn(),
		showWarning: vi.fn(),
	}),
}));

const { call } = vi.hoisted(() => ({ call: vi.fn() }));
vi.mock("@/utils/apiWrapper", () => ({ call: (...args) => call(...args) }));

vi.mock("@/utils/stockValidator", () => ({
	// Report items as stock-tracked and always short, so any un-guarded validation
	// site would block. Purchase mode must bypass all of them.
	shouldValidateItemStock: () => true,
	checkStockAvailability: () => ({ available: false, error: "Out of stock" }),
}));

vi.mock("@/utils/errorHandler", () => ({
	parseError: (e) => e?.message || "error",
}));

import { usePOSCartStore } from "./posCart";

// --- Tests -----------------------------------------------------------------

describe("posCart purchase mode", () => {
	beforeEach(() => {
		setActivePinia(createPinia());
		globalThis.__ = (value, args) => value;
		offlineState.isOffline = false;
		enforceStock.value = false;
		fakeInvoice.invoiceItems.value = [];
		fakeInvoice.customer.value = null;
		call.mockReset();
	});

	afterEach(() => {
		globalThis.__ = undefined;
		vi.clearAllMocks();
	});

	it("defaults to sales mode", () => {
		const cart = usePOSCartStore();
		expect(cart.mode).toBe("sales");
		expect(cart.isPurchaseMode).toBe(false);
	});

	it("setMode resets cart and party when switching modes", () => {
		const cart = usePOSCartStore();
		// Simulate a sales cart with a customer.
		cart.setCustomer({ name: "CUST-1", customer_name: "Alice" });
		fakeInvoice.customer.value = { name: "CUST-1" };
		cart.addItem({ item_code: "ITEM-1", item_name: "A", stock_uom: "Nos" });
		expect(cart.invoiceItems.length).toBe(1);

		cart.setMode("purchase");

		expect(cart.mode).toBe("purchase");
		expect(cart.invoiceItems.length).toBe(0); // cart cleared
		expect(cart.customer).toBeNull(); // customer cleared
		expect(cart.supplier).toBeNull();
	});

	it("setMode is a no-op when the mode is unchanged", () => {
		const cart = usePOSCartStore();
		cart.setMode("purchase");
		cart.setSupplier({ name: "SUP-1", supplier_name: "Acme" });
		cart.setMode("purchase"); // same mode → must not clear the supplier
		expect(cart.supplier).toEqual({ name: "SUP-1", supplier_name: "Acme" });
	});

	it("switching purchase → sales clears the supplier", () => {
		const cart = usePOSCartStore();
		cart.setMode("purchase");
		cart.setSupplier({ name: "SUP-1", supplier_name: "Acme" });
		cart.setMode("sales");
		expect(cart.mode).toBe("sales");
		expect(cart.supplier).toBeNull();
	});

	it("setMode('purchase') empties the purchase-default fields the pre-fill relies on", () => {
		const cart = usePOSCartStore();
		// Simulate a prior purchase session that left fields set.
		cart.setMode("purchase");
		cart.setSupplier({ name: "SUP-1", supplier_name: "Acme" });
		cart.setPurchaseWarehouse("Stores - A");
		cart.setPurchaseTaxTemplate("Std Purchase Tax");
		cart.setPurchaseExpenseAccount("Cost of Goods Sold - A");

		// Leaving and re-entering purchase mode must reset every purchase-default field
		// so POSSale.applyPurchaseDefaults()'s "only fill when empty" guards are satisfied.
		cart.setMode("sales");
		cart.setMode("purchase");

		expect(cart.supplier).toBeNull();
		expect(cart.purchaseWarehouse).toBe("");
		expect(cart.purchaseTaxTemplate).toBeNull();
		expect(cart.purchaseExpenseAccount).toBe("");
	});

	it("purchase-default setters accept the values applyPurchaseDefaults writes on entry", () => {
		const cart = usePOSCartStore();
		cart.setMode("purchase");
		// Mirrors POSSale.applyPurchaseDefaults(): supplier is an object, the rest are names.
		cart.setSupplier({ name: "SUP-9", supplier_name: "SUP-9" });
		cart.setPurchaseWarehouse("Main - A");
		cart.setPurchaseTaxTemplate("Purchase VAT 15%");
		cart.setPurchaseExpenseAccount("Expenses - A");

		expect(cart.supplier).toEqual({ name: "SUP-9", supplier_name: "SUP-9" });
		expect(cart.purchaseWarehouse).toBe("Main - A");
		expect(cart.purchaseTaxTemplate).toBe("Purchase VAT 15%");
		expect(cart.purchaseExpenseAccount).toBe("Expenses - A");
	});

	it("submitPurchaseInvoice saves + submits a Purchase Invoice with qty payload", async () => {
		const cart = usePOSCartStore();
		cart.setMode("purchase");
		cart.setSupplier({ name: "SUP-1", supplier_name: "Acme" });
		cart.setPurchaseWarehouse("Stores - A");
		cart.addItem({
			item_code: "ITEM-1",
			item_name: "A",
			stock_uom: "Nos",
			uom: "Nos",
			rate: 5,
		});

		call
			.mockResolvedValueOnce({ name: "PINV-1", modified: "2026-08-07 10:00:00" })
			.mockResolvedValueOnce({
				name: "PINV-1",
				grand_total: 5,
				outstanding_amount: 5,
			});

		const defaults = {
			company: "ACME",
			currency: "SAR",
			posting_date: "2026-08-07",
			due_date: "2026-09-06",
			buying_price_list: "Standard Buying",
		};
		const result = await cart.submitPurchaseInvoice(defaults);

		expect(result?.name).toBe("PINV-1");
		expect(call).toHaveBeenCalledTimes(2);

		const [saveMethod, saveArgs] = call.mock.calls[0];
		expect(saveMethod).toBe("pos_next.api.purchases.save_purchase_invoice");
		const payload = JSON.parse(saveArgs.data);
		expect(payload.supplier).toBe("SUP-1");
		expect(payload.update_stock).toBe(1);
		expect(payload.set_warehouse).toBe("Stores - A");
		expect(payload.items).toHaveLength(1);
		// Cart uses `quantity`; the purchase API expects `qty`.
		expect(payload.items[0]).toMatchObject({ item_code: "ITEM-1", qty: 1, rate: 5 });
		expect(payload.items[0].quantity).toBeUndefined();

		const [submitMethod] = call.mock.calls[1];
		expect(submitMethod).toBe("pos_next.api.purchases.submit_purchase_invoice");
	});

	it("carries the Settings-sourced defaults (warehouse + tax + expense) into the payload", async () => {
		// The main screen no longer shows warehouse/tax/expense pickers; those come
		// silently from Settings → Purchase Defaults. POSSale.applyPurchaseDefaults()
		// writes them into the store on entry — mirrored here via the setters — and the
		// payload must carry them without any on-screen picker interaction.
		const cart = usePOSCartStore();
		cart.setMode("purchase");
		cart.setSupplier({ name: "SUP-1", supplier_name: "Acme" });
		cart.setPurchaseWarehouse("Stores - A");
		cart.setPurchaseTaxTemplate("Purchase VAT 15%");
		cart.setPurchaseExpenseAccount("Cost of Goods Sold - A");
		cart.addItem({
			item_code: "ITEM-1",
			item_name: "A",
			stock_uom: "Nos",
			uom: "Nos",
			rate: 5,
		});

		call
			.mockResolvedValueOnce({ name: "PINV-2", modified: "2026-08-07 10:00:00" })
			.mockResolvedValueOnce({
				name: "PINV-2",
				grand_total: 5,
				outstanding_amount: 5,
			});

		const defaults = {
			company: "ACME",
			currency: "SAR",
			posting_date: "2026-08-07",
			due_date: "2026-09-06",
			buying_price_list: "Standard Buying",
		};
		const result = await cart.submitPurchaseInvoice(defaults);

		expect(result?.name).toBe("PINV-2");
		const [, saveArgs] = call.mock.calls[0];
		const payload = JSON.parse(saveArgs.data);
		expect(payload.set_warehouse).toBe("Stores - A");
		expect(payload.taxes_and_charges).toBe("Purchase VAT 15%");
		expect(payload.items[0].warehouse).toBe("Stores - A");
		expect(payload.items[0].expense_account).toBe("Cost of Goods Sold - A");
	});

	it("submitPurchaseInvoice refuses without a supplier", async () => {
		const cart = usePOSCartStore();
		cart.setMode("purchase");
		cart.setPurchaseWarehouse("Stores - A");
		cart.addItem({ item_code: "ITEM-1", item_name: "A", stock_uom: "Nos" });

		const result = await cart.submitPurchaseInvoice({});
		expect(result).toBeNull();
		expect(call).not.toHaveBeenCalled();
	});

	it("does not stock-block quantity increases in purchase mode", () => {
		enforceStock.value = true; // stock enforcement ON + validator reports short
		const cart = usePOSCartStore();
		cart.setMode("purchase");
		cart.addItem({
			item_code: "ITEM-1",
			item_name: "A",
			stock_uom: "Nos",
			uom: "Nos",
			rate: 5,
		});
		fakeInvoice.updateItemQuantity.mockClear();

		// Raise qty from 1 → 50 (buying more than stock is the normal purchase case).
		cart.updateItemQuantity("ITEM-1", 50, "Nos");

		// The base updater must be called (not short-circuited by stock validation).
		expect(fakeInvoice.updateItemQuantity).toHaveBeenCalledWith("ITEM-1", 50, "Nos");
	});

	it("submitPurchaseInvoice is blocked while offline", async () => {
		const cart = usePOSCartStore();
		cart.setMode("purchase");
		cart.setSupplier({ name: "SUP-1" });
		cart.setPurchaseWarehouse("Stores - A");
		cart.addItem({ item_code: "ITEM-1", item_name: "A", stock_uom: "Nos" });
		offlineState.isOffline = true;

		const result = await cart.submitPurchaseInvoice({});
		expect(result).toBeNull();
		expect(call).not.toHaveBeenCalled();
	});
});
