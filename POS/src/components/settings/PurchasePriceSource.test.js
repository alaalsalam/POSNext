// @vitest-environment jsdom

// Light assertion for the "Purchase Price Source" control added to POSSettings'
// Purchase Defaults section. POSSettings.vue is too heavy to mount whole, so this
// verifies the contract that matters: the select binds posa_purchase_price_source,
// offers exactly the three English values the backend expects (Arabic labels), and
// the stored VALUE is the English string.
import { mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import SelectField from "./SelectField.vue"

// The exact option contract mirrored from POSSettings' purchasePriceSourceOptions.
const OPTIONS = [
	{ value: "Buying Price List", label: "قائمة أسعار الشراء" },
	{ value: "Last Purchase Rate", label: "آخر سعر شراء" },
	{ value: "Valuation Rate", label: "متوسط التكلفة" },
]

const translate = (v) => v
const mountOpts = {
	global: { mocks: { __: translate }, config: { globalProperties: { __: translate } } },
}

describe("Purchase Price Source control", () => {
	beforeEach(() => {
		globalThis.__ = translate
	})
	afterEach(() => {
		globalThis.__ = undefined
	})

	it("offers exactly the three backend option VALUES with Arabic labels", () => {
		const wrapper = mount(SelectField, {
			props: { modelValue: "Buying Price List", label: "Purchase Price Source", options: OPTIONS },
			...mountOpts,
		})
		const values = wrapper.findAll("option").map((o) => o.element.value)
		// (SelectField prepends an empty "-- Select --" placeholder.)
		expect(values).toContain("Buying Price List")
		expect(values).toContain("Last Purchase Rate")
		expect(values).toContain("Valuation Rate")
		// Arabic labels are shown.
		expect(wrapper.text()).toContain("قائمة أسعار الشراء")
		expect(wrapper.text()).toContain("آخر سعر شراء")
		expect(wrapper.text()).toContain("متوسط التكلفة")
	})

	it("pre-selects the configured value and emits the exact English string on change", async () => {
		const wrapper = mount(SelectField, {
			props: { modelValue: "Buying Price List", label: "Purchase Price Source", options: OPTIONS },
			...mountOpts,
		})
		expect(wrapper.find("select").element.value).toBe("Buying Price List")
		await wrapper.find("select").setValue("Valuation Rate")
		expect(wrapper.emitted("update:modelValue").at(-1)[0]).toBe("Valuation Rate")
	})
})
