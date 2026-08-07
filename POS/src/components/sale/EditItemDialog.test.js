// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import EditItemDialog from "./EditItemDialog.vue";

// Rate editing hinges on the POS Settings flag in sales mode; purchase mode must
// override it to always-editable. Toggle this per test.
const { settings } = vi.hoisted(() => ({ settings: { allowUserToEditRate: false, maxDiscountAllowed: 0, allowItemDiscount: true } }));

vi.mock("@/stores/posSettings", () => ({
	usePOSSettingsStore: () => settings,
}));

vi.mock("@/stores/serialNumber", () => ({
	useSerialNumberStore: () => ({ getSerialsForItem: vi.fn(() => []) }),
}));

vi.mock("@/composables/useToast", () => ({
	useToast: () => ({ showSuccess: vi.fn(), showError: vi.fn(), showWarning: vi.fn() }),
}));

vi.mock("@/utils/stockValidator", () => ({
	getItemStock: vi.fn(async () => ({ actual_qty: 100 })),
}));

vi.mock("frappe-ui", () => ({
	Button: { template: "<button><slot /></button>" },
	FeatherIcon: { template: "<span />" },
	createResource: () => ({ submit: vi.fn(), reload: vi.fn(), loading: false, data: null }),
}));

const ITEM = {
	item_code: "ITEM-1",
	item_name: "Widget",
	stock_uom: "Nos",
	uom: "Nos",
	quantity: 1,
	rate: 0,
	price_list_rate: 0,
	item_uoms: [],
};

function mountDialog(props = {}) {
	return mount(EditItemDialog, {
		attachTo: document.body,
		props: { modelValue: true, item: { ...ITEM }, currency: "SAR", ...props },
		global: {
			stubs: { SelectInput: true },
			mocks: { __: (value) => value },
			config: { globalProperties: { __: (value) => value } },
		},
	});
}

// The dialog teleports to <body>, so query the document (not the wrapper). The
// rate field is the first number input with step="0.01" (the discount input,
// also step="0.01", renders later).
function rateInput() {
	const inputs = [...document.querySelectorAll('input[type="number"][step="0.01"]')];
	return inputs[0] || null;
}

describe("EditItemDialog rate editing", () => {
	beforeEach(() => {
		globalThis.__ = (value) => value;
		settings.allowUserToEditRate = false;
		settings.maxDiscountAllowed = 0;
	});

	afterEach(() => {
		globalThis.__ = undefined;
		document.body.innerHTML = "";
		vi.clearAllMocks();
	});

	it("purchase mode: rate is editable even when the POS Settings flag is off", async () => {
		const wrapper = mountDialog({ mode: "purchase" });
		await flushPromises();
		const input = rateInput();
		expect(input).toBeTruthy();
		expect(input.hasAttribute("readonly")).toBe(false);
	});

	it("sales mode: rate is read-only when the POS Settings flag is off", async () => {
		const wrapper = mountDialog({ mode: "sales" });
		await flushPromises();
		const input = rateInput();
		expect(input).toBeTruthy();
		expect(input.hasAttribute("readonly")).toBe(true);
	});

	it("sales mode: rate is editable when the POS Settings flag is on", async () => {
		settings.allowUserToEditRate = true;
		const wrapper = mountDialog({ mode: "sales" });
		await flushPromises();
		const input = rateInput();
		expect(input.hasAttribute("readonly")).toBe(false);
	});
});
