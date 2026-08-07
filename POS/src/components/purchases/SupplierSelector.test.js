// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import SupplierSelector from "./SupplierSelector.vue";

const { call } = vi.hoisted(() => ({ call: vi.fn() }));
vi.mock("@/utils/apiWrapper", () => ({ call: (...args) => call(...args) }));

vi.mock("@/composables/useToast", () => ({
	useToast: () => ({ showError: vi.fn(), showSuccess: vi.fn(), showWarning: vi.fn() }),
}));

vi.mock("@/utils/managementI18n", () => ({
	managerTranslate: (value, args = []) =>
		args.reduce((s, a, i) => s.replace(`{${i}}`, a), value),
}));

const SUPPLIERS = [
	{ name: "SUP-1", supplier_name: "Acme Supplies", supplier_group: "Local" },
	{ name: "SUP-2", supplier_name: "Globex Trading", supplier_group: "Import" },
	{ name: "SUP-3", supplier_name: "Initech", supplier_group: "Local" },
];

// Mount fires get_suppliers(limit:100) + get_supplier_groups in parallel.
function mockApi(suppliers = SUPPLIERS) {
	call.mockImplementation(async (method) => {
		if (method.endsWith("get_suppliers")) return suppliers;
		if (method.endsWith("get_supplier_groups")) return [{ name: "All Supplier Groups" }];
		if (method.endsWith("create_supplier"))
			return { name: "SUP-NEW", supplier_name: "New Co" };
		return [];
	});
}

function mountSelector(props = {}) {
	return mount(SupplierSelector, {
		props: { posProfile: "POS-A", ...props },
	});
}

describe("SupplierSelector", () => {
	beforeEach(() => {
		call.mockReset();
		mockApi();
	});

	afterEach(() => {
		vi.clearAllMocks();
	});

	it("preloads suppliers on mount so the list is ready before typing", async () => {
		mountSelector();
		await flushPromises();
		const methods = call.mock.calls.map(([m]) => m);
		expect(methods).toContain("pos_next.api.purchases.get_suppliers");
		// Preload requests a full page, not a 2-char search.
		const preload = call.mock.calls.find(([m]) => m.endsWith("get_suppliers"));
		expect(preload[1].limit).toBe(100);
		expect(preload[1].search).toBeUndefined();
	});

	it("focus with empty search shows the preloaded supplier list", async () => {
		const wrapper = mountSelector();
		await flushPromises();
		await wrapper.find("#cart-supplier-search").trigger("focus");
		await flushPromises();
		const text = wrapper.text();
		expect(text).toContain("Acme Supplies");
		expect(text).toContain("Globex Trading");
		expect(text).toContain("Initech");
	});

	it("typing filters the preloaded list in-memory (no per-keystroke API call)", async () => {
		const wrapper = mountSelector();
		await flushPromises();
		const input = wrapper.find("#cart-supplier-search");
		await input.trigger("focus");
		await input.setValue("glob");
		await flushPromises();
		const text = wrapper.text();
		expect(text).toContain("Globex Trading");
		expect(text).not.toContain("Acme Supplies");
		// The only get_suppliers call was the mount preload — filtering stayed local.
		const supplierCalls = call.mock.calls.filter(([m]) => m.endsWith("get_suppliers"));
		expect(supplierCalls).toHaveLength(1);
	});

	it("selecting a supplier from the list emits it and closes the picker", async () => {
		const wrapper = mountSelector();
		await flushPromises();
		await wrapper.find("#cart-supplier-search").trigger("focus");
		await flushPromises();
		const row = wrapper
			.findAll("button")
			.find((b) => b.text().includes("Globex Trading"));
		await row.trigger("mousedown");
		expect(wrapper.emitted("update:modelValue").at(-1)[0]).toMatchObject({
			name: "SUP-2",
			supplier_name: "Globex Trading",
		});
	});

	it("renders the supplier card (not an empty picker) when a supplier is selected", async () => {
		const wrapper = mountSelector({
			modelValue: { name: "SUP-1", supplier_name: "Acme" },
		});
		await flushPromises();
		expect(wrapper.text()).toContain("Acme");
		expect(wrapper.find('[data-testid="supplier-change"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="supplier-clear"]').exists()).toBe(true);
		expect(wrapper.find("#cart-supplier-search").exists()).toBe(false);
		// No "edit details" action (no update_supplier backend).
		expect(wrapper.find('[data-testid="supplier-edit"]').exists()).toBe(false);
	});

	it("Change reveals the search input with the list shown", async () => {
		const wrapper = mountSelector({
			modelValue: { name: "SUP-1", supplier_name: "Acme" },
		});
		await flushPromises();
		await wrapper.find('[data-testid="supplier-change"]').trigger("click");
		await flushPromises();
		expect(wrapper.find("#cart-supplier-search").exists()).toBe(true);
		// The preloaded list is visible immediately on Change.
		expect(wrapper.text()).toContain("Acme Supplies");
	});

	it("Create opens the quick-create block", async () => {
		const wrapper = mountSelector({
			modelValue: { name: "SUP-1", supplier_name: "Acme" },
		});
		await flushPromises();
		await wrapper.find('[data-testid="supplier-create"]').trigger("click");
		await flushPromises();
		expect(wrapper.find("select").exists()).toBe(true); // the group <select> in quick-create
	});

	it("Clear reverts to the configured default supplier when one exists", async () => {
		const wrapper = mountSelector({
			modelValue: { name: "SUP-1", supplier_name: "Acme" },
			defaultSupplier: { name: "SUP-DEF", supplier_name: "Default Co" },
		});
		await flushPromises();
		await wrapper.find('[data-testid="supplier-clear"]').trigger("click");
		expect(wrapper.emitted("update:modelValue").at(-1)[0]).toEqual({
			name: "SUP-DEF",
			supplier_name: "Default Co",
		});
	});

	it("Clear deselects (null → picker) when no default supplier is configured", async () => {
		const wrapper = mountSelector({
			modelValue: { name: "SUP-1", supplier_name: "Acme" },
			defaultSupplier: null,
		});
		await flushPromises();
		await wrapper.find('[data-testid="supplier-clear"]').trigger("click");
		expect(wrapper.emitted("update:modelValue").at(-1)[0]).toBeNull();
	});
});
