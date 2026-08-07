// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import SupplierPaymentDialog from "./SupplierPaymentDialog.vue"

// The dialog calls the shared wrapper (import { call } from "@/utils/apiWrapper"),
// NOT window.frappe.call. Mock the same path runtime uses; the wrapper returns the
// server message DIRECTLY (no { message } envelope).
const { call } = vi.hoisted(() => ({ call: vi.fn() }))
vi.mock("@/utils/apiWrapper", () => ({ call: (...args) => call(...args) }))

vi.mock("@/utils/managementI18n", () => ({
	managerTranslate: (value, args = []) =>
		args.reduce((s, a, i) => s.replace(`{${i}}`, a), value),
}))

describe("SupplierPaymentDialog", () => {
	beforeEach(() => {
		globalThis.frappe = { boot: { lang: "en" } }
		call.mockReset()
		call.mockImplementation(async (method) => {
			if (method.endsWith("get_supplier_payment_defaults")) {
				return {
					invoice: {
						name: "PINV-1",
						supplier: "SUP-1",
						company: "ACME",
						currency: "SAR",
						outstanding_amount: 100,
					},
					posting_date: "2026-08-01",
					accounts: [{ name: "Cash - A", account_name: "Cash", account_type: "Cash" }],
					modes_of_payment: [],
					can_submit: true,
				}
			}
			return { name: "PAY-1", docstatus: 1 }
		})
	})

	afterEach(() => {
		globalThis.frappe = undefined
		vi.clearAllMocks()
	})

	it("passes profile scope and a durable retry key to the payment API via the wrapper", async () => {
		const wrapper = mount(SupplierPaymentDialog, {
			props: { invoice: { name: "PINV-1" }, posProfile: "POS-A" },
		})
		await flushPromises()

		// Never touches window.frappe.call — only the apiWrapper.
		expect(call.mock.calls[0][0]).toBe(
			"pos_next.api.purchases.get_supplier_payment_defaults",
		)
		expect(call.mock.calls[0][1]).toMatchObject({
			invoice_name: "PINV-1",
			pos_profile: "POS-A",
		})

		const selects = wrapper.findAll("select")
		await selects[1].setValue("Cash - A")
		const submit = wrapper
			.findAll("button")
			.find((button) => button.text().includes("اعتماد الدفعة"))
		await submit.trigger("click")
		await flushPromises()

		const create = call.mock.calls.find(([method]) =>
			method.endsWith("create_supplier_payment"),
		)
		expect(create[1]).toMatchObject({
			invoice_name: "PINV-1",
			pos_profile: "POS-A",
			paid_from: "Cash - A",
			submit: 1,
		})
		expect(create[1].idempotency_key).toMatch(/^[A-Za-z0-9][A-Za-z0-9._:-]{7,139}$/)
	})
})
