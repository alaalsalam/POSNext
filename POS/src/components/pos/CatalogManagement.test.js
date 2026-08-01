// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { call } from "@/utils/apiWrapper"
import CatalogManagement from "./CatalogManagement.vue"

vi.mock("@/utils/apiWrapper", () => ({ call: vi.fn() }))

describe("CatalogManagement", () => {
	beforeEach(() => {
		globalThis.__ = (value) => value
		call.mockImplementation(async (method, args) => {
			if (method.endsWith("get_item_groups_for_select"))
				return args.include_parents
					? [{ name: "All Item Groups", is_group: 1 }]
					: ["Products"]
			if (method.endsWith("get_catalog_defaults"))
				return {
					selling_currency: "SAR",
					buying_currency: "SAR",
					uoms: ["Nos"],
				}
			return { item_name: "Test Item" }
		})
	})

	afterEach(() => {
		globalThis.__ = undefined
		vi.clearAllMocks()
	})

	it("sends the scoped catalog payload once while creation is in flight", async () => {
		const wrapper = mount(CatalogManagement, {
			props: { show: true, posProfile: "POS-A" },
			global: { mocks: { __: (value) => value } },
		})
		await flushPromises()
		await wrapper
			.get('input[placeholder="Unique item code"]')
			.setValue("ITEM-1")
		await wrapper
			.get('input[placeholder="e.g. iPhone 16 Pro Max"]')
			.setValue("Test Item")
		await wrapper.findAll("select")[0].setValue("Products")

		let release
		const pending = new Promise((resolve) => {
			release = resolve
		})
		call.mockImplementation((method) =>
			method.endsWith("create_quick_item") ? pending : Promise.resolve([]),
		)
		const create = wrapper.get('[data-testid="catalog-create-item"]')
		create.trigger("click")
		await wrapper.vm.$nextTick()
		await create.trigger("click")
		const creates = call.mock.calls.filter(([method]) =>
			method.endsWith("create_quick_item"),
		)
		expect(creates).toHaveLength(1)
		expect(creates[0][1]).toMatchObject({
			item_code: "ITEM-1",
			item_name: "Test Item",
			item_group: "Products",
			stock_uom: "Nos",
			pos_profile: "POS-A",
		})
		release({ item_name: "Test Item" })
		await flushPromises()
	})
})
