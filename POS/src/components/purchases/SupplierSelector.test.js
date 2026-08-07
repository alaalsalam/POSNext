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

function mountSelector(props = {}) {
	return mount(SupplierSelector, {
		props: { posProfile: "POS-A", ...props },
	});
}

describe("SupplierSelector", () => {
	beforeEach(() => {
		call.mockReset();
		// get_supplier_groups on mount
		call.mockResolvedValue([{ name: "All Supplier Groups" }]);
	});

	afterEach(() => {
		vi.clearAllMocks();
	});

	it("renders the supplier card (not an empty picker) when a supplier is selected", async () => {
		const wrapper = mountSelector({
			modelValue: { name: "SUP-1", supplier_name: "Acme" },
		});
		await flushPromises();
		expect(wrapper.text()).toContain("Acme");
		// Card actions present; no search input while showing the card.
		expect(wrapper.find('[data-testid="supplier-change"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="supplier-clear"]').exists()).toBe(true);
		expect(wrapper.find("#cart-supplier-search").exists()).toBe(false);
		// No "edit details" action (no update_supplier backend).
		expect(wrapper.find('[data-testid="supplier-edit"]').exists()).toBe(false);
	});

	it("Clear reverts to the configured default supplier when one exists", async () => {
		const wrapper = mountSelector({
			modelValue: { name: "SUP-1", supplier_name: "Acme" },
			defaultSupplier: { name: "SUP-DEF", supplier_name: "Default Co" },
		});
		await flushPromises();
		await wrapper.find('[data-testid="supplier-clear"]').trigger("click");
		const emitted = wrapper.emitted("update:modelValue");
		expect(emitted).toBeTruthy();
		expect(emitted.at(-1)[0]).toEqual({ name: "SUP-DEF", supplier_name: "Default Co" });
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

	it("Change reveals the search input over the selected supplier card", async () => {
		const wrapper = mountSelector({
			modelValue: { name: "SUP-1", supplier_name: "Acme" },
		});
		await flushPromises();
		await wrapper.find('[data-testid="supplier-change"]').trigger("click");
		await flushPromises();
		expect(wrapper.find("#cart-supplier-search").exists()).toBe(true);
	});
});
