// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import SupplierPaymentDialog from "./SupplierPaymentDialog.vue"

// The dialog calls the shared wrapper (import { call } from "@/utils/apiWrapper"),
// NOT window.frappe.call. Mock the same path runtime uses; the wrapper returns the
// server message DIRECTLY (no { message } envelope).
const { call } = vi.hoisted(() => ({ call: vi.fn() }))
vi.mock("@/utils/apiWrapper", () => ({ call: (...args) => call(...args) }))

vi.mock("@/utils/currency", () => ({
	// Simple, deterministic formatter so tests assert on the number, not locale glyphs.
	formatCurrency: (v) => Number(v || 0).toFixed(2),
}))

vi.mock("@/utils/managementI18n", () => ({
	managerTranslate: (value, args = []) =>
		args.reduce((s, a, i) => s.replace(`{${i}}`, a), value),
}))

// New backend shape: payment_methods (profile order), a default, and one whose
// settings account is missing (must render disabled, not hidden).
function defaults(overrides = {}) {
	return {
		invoice: {
			name: "PINV-1",
			supplier: "SUP-1",
			supplier_name: "Acme",
			currency: "YER",
			outstanding_amount: 100,
		},
		posting_date: "2026-08-01",
		can_submit: true,
		payment_methods: [
			{ mode_of_payment: "نقد", default: 1, account_missing: false },
			{ mode_of_payment: "جيب", default: 0, account_missing: false },
			{ mode_of_payment: "ون كاش", default: 0, account_missing: true },
		],
		...overrides,
	}
}

function mockApi(overrides = {}) {
	call.mockImplementation(async (method) => {
		if (method.endsWith("get_supplier_payment_defaults")) return defaults(overrides)
		return { name: "PAY-1", docstatus: 1 }
	})
}

function mountDialog() {
	globalThis.frappe = { boot: { lang: "en" } }
	return mount(SupplierPaymentDialog, {
		props: { invoice: { name: "PINV-1" }, posProfile: "POS-A" },
	})
}

describe("SupplierPaymentDialog", () => {
	beforeEach(() => {
		call.mockReset()
		mockApi()
	})

	afterEach(() => {
		globalThis.frappe = undefined
		vi.clearAllMocks()
	})

	it("loads defaults through the apiWrapper (not window.frappe.call)", async () => {
		mountDialog()
		await flushPromises()
		expect(call.mock.calls[0][0]).toBe(
			"pos_next.api.purchases.get_supplier_payment_defaults",
		)
		expect(call.mock.calls[0][1]).toMatchObject({ invoice_name: "PINV-1", pos_profile: "POS-A" })
	})

	it("renders payment-method tiles with the default pre-selected and no account dropdown", async () => {
		const wrapper = mountDialog()
		await flushPromises()
		// Tiles, not a dropdown: the raw account <select> is gone.
		expect(wrapper.find("select").exists()).toBe(false)
		expect(wrapper.find('[data-testid="pay-method-نقد"]').exists()).toBe(true)
		expect(wrapper.find('[data-testid="pay-method-جيب"]').exists()).toBe(true)
		// The default tile (نقد) is pre-selected (orange border class).
		expect(wrapper.find('[data-testid="pay-method-نقد"]').classes()).toContain("border-orange-500")
	})

	it("disables (not hides) a tile whose settings account is missing", async () => {
		const wrapper = mountDialog()
		await flushPromises()
		const missing = wrapper.find('[data-testid="pay-method-ون كاش"]')
		expect(missing.exists()).toBe(true) // still shown
		expect(missing.attributes("disabled")).toBeDefined()
		expect(wrapper.text()).toContain("غير مهيأ في الإعدادات")
	})

	it("sends mode_of_payment and does NOT send paid_from on save", async () => {
		const wrapper = mountDialog()
		await flushPromises()
		// Pick a non-default method.
		await wrapper.find('[data-testid="pay-method-جيب"]').trigger("click")
		const submit = wrapper.findAll("button").find((b) => b.text().includes("اعتماد الدفعة"))
		await submit.trigger("click")
		await flushPromises()

		const create = call.mock.calls.find(([m]) => m.endsWith("create_supplier_payment"))
		expect(create[1]).toMatchObject({
			invoice_name: "PINV-1",
			pos_profile: "POS-A",
			mode_of_payment: "جيب",
			submit: 1,
		})
		expect("paid_from" in create[1]).toBe(false)
		expect(create[1].idempotency_key).toMatch(/^[A-Za-z0-9][A-Za-z0-9._:-]{7,139}$/)
	})

	it("shows the remaining amount for a partial payment and 'paid in full' at outstanding", async () => {
		const wrapper = mountDialog()
		await flushPromises()
		// Defaults to the full outstanding → paid in full.
		expect(wrapper.find('[data-testid="remaining-panel"]').text()).toContain("مسدَّد بالكامل")

		// Partial payment → remaining shows.
		await wrapper.find('input[type="number"]').setValue(40)
		await flushPromises()
		const panel = wrapper.find('[data-testid="remaining-panel"]').text()
		expect(panel).toContain("المتبقي بعد الدفع")
		expect(panel).toContain("60.00")
	})

	it("prevents overpayment: caps the amount at outstanding", async () => {
		const wrapper = mountDialog()
		await flushPromises()
		const input = wrapper.find('input[type="number"]')
		await input.setValue(500) // more than the 100 outstanding
		await flushPromises()
		// Capped to outstanding; remaining reads paid-in-full, not negative.
		expect(wrapper.find('[data-testid="remaining-panel"]').text()).toContain("مسدَّد بالكامل")
		expect(Number(input.element.value)).toBeLessThanOrEqual(100)
	})

	it("keeps reference no + date behind the additional-details disclosure", async () => {
		const wrapper = mountDialog()
		await flushPromises()
		// Collapsed by default: reference inputs not rendered.
		expect(wrapper.text()).not.toContain("رقم المرجع")
		await wrapper.find('[data-testid="additional-details-toggle"]').trigger("click")
		await flushPromises()
		expect(wrapper.text()).toContain("رقم المرجع")
	})
})
