// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import PurchaseInvoiceForm from "./PurchaseInvoiceForm.vue"

// The form calls the shared wrapper (import { call } from "@/utils/apiWrapper"),
// NOT window.frappe.call. Mock the same path runtime uses; the wrapper returns the
// server message DIRECTLY (no { message } envelope) — call(method, params).
const { call } = vi.hoisted(() => ({ call: vi.fn() }))
vi.mock("@/utils/apiWrapper", () => ({ call: (...args) => call(...args) }))

vi.mock("@/composables/useToast", () => ({
	useToast: () => ({ showSuccess: vi.fn(), showError: vi.fn(), showWarning: vi.fn() }),
}))

vi.mock("@/utils/managementI18n", () => ({
	managerTranslate: (value, args = []) =>
		args.reduce((s, a, i) => s.replace(`{${i}}`, a), value),
}))

const invoice = {
	name: "PINV-1",
	docstatus: 0,
	supplier: "SUP-1",
	supplier_name: "Supplier",
	posting_date: "2026-08-01",
	due_date: "2026-08-31",
	bill_date: "2026-08-01",
	company: "ACME",
	currency: "SAR",
	company_currency: "SAR",
	conversion_rate: 1,
	buying_price_list: "Buying",
	price_list_currency: "SAR",
	plc_conversion_rate: 1,
	modified: "2026-08-01 10:00:00",
	items: [
		{ item_code: "ITEM-1", item_name: "Item", qty: 1, uom: "Nos", rate: 10, amount: 10 },
	],
}

// The wrapper returns the message unwrapped; mirror that here.
function responseFor(method) {
	if (method.endsWith("get_new_purchase_invoice_defaults"))
		return {
			company: "ACME",
			currency: "SAR",
			company_currency: "SAR",
			buying_price_list: "Buying",
			price_list_currency: "SAR",
		}
	if (method.endsWith("get_purchase_invoice")) return invoice
	if (method.endsWith("get_supplier_groups")) return [{ name: "All Supplier Groups" }]
	if (method.endsWith("get_purchase_currencies")) return [{ name: "SAR" }]
	if (
		method.endsWith("get_warehouses") ||
		method.endsWith("get_expense_accounts") ||
		method.endsWith("get_purchase_tax_templates")
	)
		return []
	if (method.endsWith("save_purchase_invoice"))
		return { name: "PINV-1", modified: "2026-08-01 11:00:00" }
	if (method.endsWith("submit_purchase_invoice")) return { name: "PINV-1", docstatus: 1 }
	return []
}

async function mountForm(props = {}) {
	const wrapper = mount(PurchaseInvoiceForm, {
		props: { invoiceName: "PINV-1", posProfile: "POS-A", canWrite: true, canSubmit: true, ...props },
	})
	await flushPromises()
	return wrapper
}

// call.mock.calls entries are [method, params].
function callsTo(suffix) {
	return call.mock.calls.filter(([method]) => method.endsWith(suffix))
}

describe("PurchaseInvoiceForm", () => {
	beforeEach(() => {
		globalThis.frappe = { boot: { lang: "en" } }
		globalThis.confirm = vi.fn(() => true)
		call.mockReset()
		call.mockImplementation(async (method) => responseFor(method))
	})

	afterEach(() => {
		globalThis.frappe = undefined
		globalThis.confirm = undefined
		vi.clearAllMocks()
	})

	it("uses the apiWrapper (not window.frappe.call) for its API calls", async () => {
		await mountForm()
		// Defaults + option lists all went through the wrapper as (method, params).
		expect(call).toHaveBeenCalled()
		expect(call.mock.calls[0][0]).toBe(
			"pos_next.api.purchases.get_new_purchase_invoice_defaults",
		)
		expect(typeof call.mock.calls[0][1]).toBe("object")
	})

	it("reuses its action key and carries expected_modified through save and submit", async () => {
		const wrapper = await mountForm()
		await wrapper.get('[data-testid="purchase-save"]').trigger("click")
		await flushPromises()
		await wrapper.get('[data-testid="purchase-save"]').trigger("click")
		await flushPromises()

		const saves = callsTo("save_purchase_invoice")
		expect(saves).toHaveLength(2)
		expect(saves[0][1].idempotency_key).toBe(saves[1][1].idempotency_key)
		expect(saves[0][1].expected_modified).toBe("2026-08-01 10:00:00")
		expect(saves[1][1].expected_modified).toBe("2026-08-01 11:00:00")

		await wrapper.get('[data-testid="purchase-submit"]').trigger("click")
		await wrapper.get('[data-testid="purchase-confirm-submit"]').trigger("click")
		await flushPromises()
		const submit = callsTo("submit_purchase_invoice")[0]
		expect(submit[1]).toMatchObject({
			name: "PINV-1",
			expected_modified: "2026-08-01 11:00:00",
			pos_profile: "POS-A",
		})
	})

	it("blocks a second save while the first request is in flight", async () => {
		const wrapper = await mountForm()
		let release
		const pending = new Promise((resolve) => {
			release = resolve
		})
		call.mockImplementation((method) =>
			method.endsWith("save_purchase_invoice")
				? pending
				: Promise.resolve(responseFor(method)),
		)
		const save = wrapper.get('[data-testid="purchase-save"]')
		save.trigger("click")
		await wrapper.vm.$nextTick()
		await save.trigger("click")
		expect(callsTo("save_purchase_invoice")).toHaveLength(1)
		release({ name: "PINV-1", modified: "2026-08-01 11:00:00" })
		await flushPromises()
	})

	it("shows a safe reload action for stale drafts", async () => {
		const wrapper = await mountForm()
		call.mockImplementation((method) => {
			if (method.endsWith("save_purchase_invoice"))
				return Promise.reject({
					message: "Draft changed; reload",
					exc_type: "TimestampMismatchError",
				})
			return Promise.resolve(responseFor(method))
		})
		await wrapper.get('[data-testid="purchase-save"]').trigger("click")
		await flushPromises()
		expect(wrapper.get('[data-testid="purchase-error"]').text()).toContain("Draft changed")
		expect(wrapper.find('[data-testid="purchase-reload"]').exists()).toBe(true)
	})

	it("renders cancel only when the submitted document permission allows it", async () => {
		const submitted = { ...invoice, docstatus: 1 }
		call.mockImplementation(async (method) =>
			method.endsWith("get_purchase_invoice") ? submitted : responseFor(method),
		)
		const wrapper = await mountForm({ canWrite: false, canSubmit: false, canCancel: false })
		expect(wrapper.find('[data-testid="purchase-cancel"]').exists()).toBe(false)
		await wrapper.setProps({ canCancel: true })
		expect(wrapper.find('[data-testid="purchase-cancel"]').exists()).toBe(true)
	})
})
