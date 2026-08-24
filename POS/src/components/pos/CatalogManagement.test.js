// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import AutocompleteSelect from "@/components/common/AutocompleteSelect.vue"
import CatalogManagement from "./CatalogManagement.vue"

// AutocompleteSelect evaluates __() in a prop default at import time — provide a global.
const { call } = vi.hoisted(() => {
	globalThis.__ = (value) => value
	return { call: vi.fn() }
})
vi.mock("frappe-ui", () => ({ FeatherIcon: { template: "<span />" } }))
vi.mock("@/utils/apiWrapper", () => ({ call: (...args) => call(...args) }))

const { showSuccess, showError } = vi.hoisted(() => ({
	showSuccess: vi.fn(),
	showError: vi.fn(),
}))
vi.mock("@/utils/errorHandler", () => ({
	parseError: (e) => ({ message: e?.message || "error" }),
}))
vi.mock("@/composables/useToast", () => ({
	useToast: () => ({ showSuccess, showError }),
}))
vi.mock("@/utils/managementI18n", () => ({
	managerTranslate: (v, args = []) =>
		args.reduce((s, a, i) => s.replace(`{${i}}`, a), v),
}))
vi.mock("@/utils/currency", () => ({
	formatCurrency: (v) => `SAR ${Number(v || 0).toFixed(2)}`,
}))

const ITEMS = [
	{ item_code: "POS-ITM-00001", item_name: "Item One", item_group: "Products", stock_uom: "Nos", description: "first", image: "", serial: "S1", barcode: "B1", qty: 5, available: 5, cost_price: 10, selling_price: 15, disabled: 0 },
	{ item_code: "POS-ITM-00002", item_name: "Item Two", item_group: "Products", stock_uom: "Nos", description: "", image: "", serial: "", barcode: "B2", qty: 2, available: 2, cost_price: 20, selling_price: 25, disabled: 1 },
]

function mockApi() {
	call.mockImplementation(async (method, args = {}) => {
		if (method.endsWith("get_catalog_defaults")) return { uoms: ["Nos", "Box"], currency: "SAR" }
		if (method.endsWith("get_item_groups_for_select")) return ["Products", "Services"]
		if (method.endsWith("get_catalog_items")) {
			const items = args.search
				? ITEMS.filter((i) => i.item_name.includes(args.search))
				: ITEMS
			return { items, warehouse: "WH", currency: "SAR" }
		}
		if (method.endsWith("get_catalog_item")) return ITEMS.find((i) => i.item_code === args.item_code)
		if (method.endsWith("create_catalog_item")) return { item_code: "POS-ITM-00003", item_name: args.item_name, item_group: args.item_group }
		if (method.endsWith("update_catalog_item")) return { ...ITEMS[0], item_name: args.item_name }
		if (method.endsWith("delete_catalog_item")) return { item_code: args.item_code, deleted: false, disabled: true }
		return {}
	})
}

function lastCall(suffix) {
	const calls = call.mock.calls.filter(([m]) => m.endsWith(suffix))
	return calls.length ? calls[calls.length - 1] : null
}

async function mountScreen(props = {}) {
	const wrapper = mount(CatalogManagement, {
		props: { show: true, posProfile: "POS-A", canManageCatalog: true, ...props },
	})
	await flushPromises()
	return wrapper
}

describe("CatalogManagement (classic items screen)", () => {
	beforeEach(() => mockApi())
	afterEach(() => vi.clearAllMocks())

	it("loads the item list on open", async () => {
		const wrapper = await mountScreen()
		expect(lastCall("get_catalog_items")).toBeTruthy()
		expect(wrapper.get('[data-testid="cat-row-0"]').text()).toContain("Item One")
		expect(wrapper.get('[data-testid="cat-row-1"]').text()).toContain("Item Two")
		// First row is selected into the form.
		expect(wrapper.get('[data-testid="cat-item-code"]').element.value).toBe("POS-ITM-00001")
	})

	it("Add creates an item with no item_code and with qty + cost", async () => {
		const wrapper = await mountScreen()
		await wrapper.get('[data-testid="cat-add"]').trigger("click")
		await wrapper.get('[data-testid="cat-item-name"]').setValue("New Item")
		wrapper.findComponent(AutocompleteSelect).vm.$emit("update:modelValue", "Products")
		await wrapper.get('[data-testid="cat-qty"]').setValue("3")
		await wrapper.get('[data-testid="cat-cost"]').setValue("10")
		await wrapper.get('[data-testid="cat-save"]').trigger("click")
		await flushPromises()

		const payload = lastCall("create_catalog_item")[1]
		expect(payload).not.toHaveProperty("item_code")
		expect(payload).toMatchObject({
			item_name: "New Item",
			item_group: "Products",
			qty: 3,
			cost_price: 10,
			pos_profile: "POS-A",
		})
		expect(showSuccess).toHaveBeenCalled()
	})

	it("blocks a positive quantity without a cost price", async () => {
		const wrapper = await mountScreen()
		await wrapper.get('[data-testid="cat-add"]').trigger("click")
		await wrapper.get('[data-testid="cat-item-name"]').setValue("No Cost")
		wrapper.findComponent(AutocompleteSelect).vm.$emit("update:modelValue", "Products")
		await wrapper.get('[data-testid="cat-qty"]').setValue("5")
		await wrapper.get('[data-testid="cat-save"]').trigger("click")
		await flushPromises()

		expect(lastCall("create_catalog_item")).toBeNull()
		expect(showError).toHaveBeenCalled()
	})

	it("Edit loads the selected row through get_catalog_item, then Save updates it", async () => {
		const wrapper = await mountScreen()
		await wrapper.get('[data-testid="cat-row-1"]').trigger("click")
		await wrapper.get('[data-testid="cat-edit"]').trigger("click")
		await flushPromises()

		expect(lastCall("get_catalog_item")[1]).toMatchObject({ item_code: "POS-ITM-00002" })

		await wrapper.get('[data-testid="cat-item-name"]').setValue("Item Two Renamed")
		await wrapper.get('[data-testid="cat-save"]').trigger("click")
		await flushPromises()

		const payload = lastCall("update_catalog_item")[1]
		expect(payload).toMatchObject({
			item_code: "POS-ITM-00002",
			item_name: "Item Two Renamed",
			pos_profile: "POS-A",
		})
	})

	it("Delete confirms before calling delete_catalog_item", async () => {
		const confirmSpy = vi.fn(() => true)
		vi.stubGlobal("confirm", confirmSpy)
		const wrapper = await mountScreen()
		await wrapper.get('[data-testid="cat-row-0"]').trigger("click")
		await wrapper.get('[data-testid="cat-delete"]').trigger("click")
		await flushPromises()

		expect(confirmSpy).toHaveBeenCalled()
		expect(lastCall("delete_catalog_item")[1]).toMatchObject({ item_code: "POS-ITM-00001" })
		vi.unstubAllGlobals()
	})

	it("does not delete when the confirmation is cancelled", async () => {
		vi.stubGlobal("confirm", vi.fn(() => false))
		const wrapper = await mountScreen()
		await wrapper.get('[data-testid="cat-row-0"]').trigger("click")
		await wrapper.get('[data-testid="cat-delete"]').trigger("click")
		await flushPromises()

		expect(lastCall("delete_catalog_item")).toBeNull()
		vi.unstubAllGlobals()
	})

	it("Search queries get_catalog_items with the search term", async () => {
		const wrapper = await mountScreen()
		await wrapper.get('[data-testid="cat-search-input"]').setValue("Two")
		await wrapper.get('[data-testid="cat-search-btn"]').trigger("click")
		await flushPromises()

		expect(lastCall("get_catalog_items")[1]).toMatchObject({ search: "Two" })
		expect(wrapper.get('[data-testid="cat-row-0"]').text()).toContain("Item Two")
		expect(wrapper.find('[data-testid="cat-row-1"]').exists()).toBe(false)
	})

	it("navigation cursor loads rows into the form without an API call", async () => {
		const wrapper = await mountScreen()
		call.mockClear()

		await wrapper.get('[data-testid="cat-nav-last"]').trigger("click")
		expect(wrapper.get('[data-testid="cat-item-code"]').element.value).toBe("POS-ITM-00002")

		await wrapper.get('[data-testid="cat-nav-first"]').trigger("click")
		expect(wrapper.get('[data-testid="cat-item-code"]').element.value).toBe("POS-ITM-00001")

		// Client-side cursor: no server round trips for navigation.
		expect(call).not.toHaveBeenCalled()
	})

	it("hides Edit and Delete when catalog management is not allowed", async () => {
		const wrapper = await mountScreen({ canManageCatalog: false })
		expect(wrapper.find('[data-testid="cat-edit"]').exists()).toBe(false)
		expect(wrapper.find('[data-testid="cat-delete"]').exists()).toBe(false)
		// Add and Search remain available.
		expect(wrapper.find('[data-testid="cat-add"]').exists()).toBe(true)
		expect(wrapper.find('[data-testid="cat-search-btn"]').exists()).toBe(true)
	})
})
