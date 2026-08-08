// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import PurchaseInvoiceDetailDialog from "./PurchaseInvoiceDetailDialog.vue"

// The dialog calls the shared wrapper (import { call } from "@/utils/apiWrapper").
// The wrapper returns the server message DIRECTLY (no { message } envelope).
const { call } = vi.hoisted(() => ({ call: vi.fn() }))
vi.mock("@/utils/apiWrapper", () => ({ call: (...args) => call(...args) }))

vi.mock("@/utils/currency", () => ({
	formatCurrency: (v) => Number(v || 0).toFixed(2),
}))

vi.mock("@/utils/managementI18n", () => ({
	managerTranslate: (value, args = []) =>
		args.reduce((s, a, i) => s.replace(`{${i}}`, a), value),
}))

function makeInvoice(overrides = {}) {
	return {
		name: "PINV-1",
		supplier: "SUP-1",
		supplier_name: "Acme Trading",
		posting_date: "2026-08-01",
		due_date: "2026-08-31",
		bill_no: "BILL-9",
		docstatus: 1,
		status: "Partly Paid",
		currency: "YER",
		total: 900,
		total_taxes_and_charges: 100,
		grand_total: 1000,
		outstanding_amount: 400,
		items: [
			{ item_code: "PHN-1", item_name: "iPhone 15", qty: 2, uom: "Nos", rate: 400, amount: 800 },
			{ item_code: "PHN-2", item_name: "AirPods", qty: 1, uom: "Nos", rate: 100, amount: 100 },
		],
		// Internal fields that must NOT surface in the review view.
		expense_account: "Stock In Hand - A",
		cost_center: "Main - A",
		buying_price_list: "Standard Buying",
		taxes_and_charges: "Purchase VAT 15%",
		...overrides,
	}
}

function mountDialog(props = {}, invoice = makeInvoice()) {
	globalThis.frappe = { boot: { lang: "en" } }
	call.mockImplementation(async (method) => {
		if (method.endsWith("get_purchase_invoice")) return invoice
		return {}
	})
	return mount(PurchaseInvoiceDetailDialog, {
		props: { invoiceName: "PINV-1", posProfile: "POS-A", ...props },
	})
}

describe("PurchaseInvoiceDetailDialog", () => {
	beforeEach(() => {
		call.mockReset()
	})

	afterEach(() => {
		globalThis.frappe = undefined
		vi.clearAllMocks()
	})

	it("loads via the apiWrapper and renders supplier / status / items / totals / payment", async () => {
		const wrapper = mountDialog({ canPay: true })
		await flushPromises()

		expect(call.mock.calls[0][0]).toBe("pos_next.api.purchases.get_purchase_invoice")
		expect(call.mock.calls[0][1]).toMatchObject({ name: "PINV-1", pos_profile: "POS-A" })

		const text = wrapper.text()
		expect(text).toContain("Acme Trading") // supplier
		expect(text).toContain("مدفوعة جزئيًا") // derived status (outstanding < grand total)
		expect(text).toContain("iPhone 15") // item
		expect(text).toContain("AirPods")
		// Payment status panel: total / paid (1000-400=600) / remaining (400).
		expect(text).toContain("1000.00")
		expect(text).toContain("600.00")
		expect(text).toContain("400.00")
	})

	it("does NOT render raw expense / cost-center / price-list / tax-template internals", async () => {
		const wrapper = mountDialog()
		await flushPromises()
		const text = wrapper.text()
		expect(text).not.toContain("Stock In Hand")
		expect(text).not.toContain("Main - A")
		expect(text).not.toContain("Standard Buying")
		expect(text).not.toContain("Purchase VAT 15%")
	})

	it("shows «تسجيل دفعة» only when submitted + outstanding + can-pay", async () => {
		// submitted + outstanding + canPay → shown
		const paid = mountDialog({ canPay: true })
		await flushPromises()
		expect(paid.find('[data-testid="detail-pay"]').exists()).toBe(true)

		// canPay false → hidden
		const noPerm = mountDialog({ canPay: false })
		await flushPromises()
		expect(noPerm.find('[data-testid="detail-pay"]').exists()).toBe(false)

		// fully paid (outstanding 0) → hidden even with canPay
		const settled = mountDialog({ canPay: true }, makeInvoice({ outstanding_amount: 0 }))
		await flushPromises()
		expect(settled.find('[data-testid="detail-pay"]').exists()).toBe(false)

		// draft → hidden
		const draft = mountDialog({ canPay: true }, makeInvoice({ docstatus: 0 }))
		await flushPromises()
		expect(draft.find('[data-testid="detail-pay"]').exists()).toBe(false)
	})

	it("shows «تعديل» only for a draft with write permission", async () => {
		const draft = mountDialog({ canWrite: true }, makeInvoice({ docstatus: 0 }))
		await flushPromises()
		expect(draft.find('[data-testid="detail-edit"]').exists()).toBe(true)

		// submitted → no edit
		const submitted = mountDialog({ canWrite: true })
		await flushPromises()
		expect(submitted.find('[data-testid="detail-edit"]').exists()).toBe(false)

		// draft but no write permission → no edit
		const noWrite = mountDialog({ canWrite: false }, makeInvoice({ docstatus: 0 }))
		await flushPromises()
		expect(noWrite.find('[data-testid="detail-edit"]').exists()).toBe(false)
	})

	it("emits pay-invoice / edit-invoice from the actions", async () => {
		const wrapper = mountDialog({ canPay: true })
		await flushPromises()
		await wrapper.find('[data-testid="detail-pay"]').trigger("click")
		expect(wrapper.emitted("pay-invoice")[0][0]).toMatchObject({ name: "PINV-1" })
	})

	it("keeps cancel as a subtle secondary action (only submitted + can-cancel)", async () => {
		const wrapper = mountDialog({ canCancel: true })
		await flushPromises()
		const cancel = wrapper.find('[data-testid="detail-cancel"]')
		expect(cancel.exists()).toBe(true)
		// Not a prominent filled button — a subtle text button (no bg-*-600 fill).
		expect(cancel.classes().some((c) => /^bg-(red|orange)-600$/.test(c))).toBe(false)
	})
})
