// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import SupplierPaymentDialog from "./SupplierPaymentDialog.vue"

describe("SupplierPaymentDialog", () => {
	beforeEach(() => {
		globalThis.__ = (value) => value
		globalThis.frappe = {
			boot: { lang: "en" },
			call: vi.fn(async ({ method }) => {
				if (method.endsWith("get_supplier_payment_defaults")) {
					return {
						message: {
							invoice: {
								name: "PINV-1",
								supplier: "SUP-1",
								company: "ACME",
								currency: "SAR",
								outstanding_amount: 100,
							},
							posting_date: "2026-08-01",
							accounts: [
								{
									name: "Cash - A",
									account_name: "Cash",
									account_type: "Cash",
								},
							],
							modes_of_payment: [],
							can_submit: true,
						},
					}
				}
				return { message: { name: "PAY-1", docstatus: 1 } }
			}),
		}
	})

	afterEach(() => {
		globalThis.frappe = undefined
		globalThis.__ = undefined
	})

	it("passes profile scope and a durable retry key to the payment API", async () => {
		const wrapper = mount(SupplierPaymentDialog, {
			props: { invoice: { name: "PINV-1" }, posProfile: "POS-A" },
		})
		await flushPromises()
		const selects = wrapper.findAll("select")
		await selects[1].setValue("Cash - A")
		const submit = wrapper
			.findAll("button")
			.find((button) => button.text().includes("Submit Payment"))
		await submit.trigger("click")
		await flushPromises()

		const calls = globalThis.frappe.call.mock.calls.map(([request]) => request)
		expect(calls[0].args).toMatchObject({
			invoice_name: "PINV-1",
			pos_profile: "POS-A",
		})
		const create = calls.find((request) =>
			request.method.endsWith("create_supplier_payment"),
		)
		expect(create.args).toMatchObject({
			invoice_name: "PINV-1",
			pos_profile: "POS-A",
			paid_from: "Cash - A",
			submit: 1,
		})
		expect(create.args.idempotency_key).toMatch(
			/^[A-Za-z0-9][A-Za-z0-9._:-]{7,139}$/,
		)
	})
})
