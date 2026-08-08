// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import CashManagement from "./CashManagement.vue"

// Calls go through the shared wrapper (import { call } from "@/utils/apiWrapper").
const { call } = vi.hoisted(() => ({ call: vi.fn() }))
vi.mock("@/utils/apiWrapper", () => ({ call: (...args) => call(...args) }))

vi.mock("@/utils/currency", () => ({ formatCurrency: (v) => Number(v || 0).toFixed(2) }))
vi.mock("@/utils/errorHandler", () => ({ parseError: (e) => ({ message: e?.message || "error" }) }))
vi.mock("@/composables/useToast", () => ({
	useToast: () => ({ showSuccess: vi.fn(), showError: vi.fn() }),
}))
vi.mock("@/utils/managementI18n", () => ({
	managerTranslate: (v, args = []) => args.reduce((s, a, i) => s.replace(`{${i}}`, a), v),
}))

function mockApi() {
	call.mockImplementation(async (method, params) => {
		if (method.endsWith("get_cash_entry_accounts")) {
			// Different accounts per type so a refetch is observable.
			return params.entry_type === "Receipt"
				? { accounts: [{ name: "REC-1", account_name: "Sundry Debtors" }], currency: "YER" }
				: { accounts: [{ name: "EXP-1", account_name: "Office Expense" }], currency: "YER" }
		}
		if (method.endsWith("get_cash_entries")) {
			return {
				entries: [
					{
						name: "CE-1",
						posa_cash_entry_type: "Expense",
						total_debit: 50,
						user_remark: "Water",
						posting_date: "2026-08-08",
						creation: "2026-08-08 10:00:00",
					},
				],
				received_total: 200,
				paid_total: 50,
				net_total: 150,
			}
		}
		if (method.endsWith("create_cash_entry")) return { name: "CE-NEW" }
		return {}
	})
}

function mountPanel() {
	globalThis.frappe = { boot: { lang: "ar" } }
	return mount(CashManagement, { props: { posProfile: "POS-A" } })
}

async function typeAmount(wrapper, digits) {
	const keys = wrapper.findAll("button.numkey")
	const key = (label) => keys.find((b) => b.text().trim() === label)
	for (const d of digits) await key(d).trigger("click")
}

describe("CashManagement", () => {
	beforeEach(() => {
		call.mockReset()
		mockApi()
	})
	afterEach(() => {
		globalThis.frappe = undefined
		vi.clearAllMocks()
	})

	it("loads accounts + entries via the wrapper on mount", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		const methods = call.mock.calls.map(([m]) => m)
		expect(methods).toContain("pos_next.api.cash_management.get_cash_entry_accounts")
		expect(methods).toContain("pos_next.api.cash_management.get_cash_entries")
		expect(wrapper.text()).toContain("Office Expense") // Expense accounts by default
	})

	it("re-fetches accounts (and resets the selected account) when the type changes", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		call.mockClear()
		await wrapper.find('[data-testid="type-Receipt"]').trigger("click")
		await flushPromises()
		const acctCall = call.mock.calls.find(([m]) => m.endsWith("get_cash_entry_accounts"))
		expect(acctCall[1].entry_type).toBe("Receipt")
		expect(wrapper.find('[data-testid="account-select"]').element.value).toBe("") // reset
		expect(wrapper.text()).toContain("Sundry Debtors")
	})

	it("blocks submit when the amount is 0 or a required note is missing", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		const submit = wrapper.find('[data-testid="cash-submit"]')
		// amount 0 → disabled
		expect(submit.attributes("disabled")).toBeDefined()

		// Expense (note required): amount + account but no note → still disabled.
		await typeAmount(wrapper, ["5", "0"])
		await wrapper.find('[data-testid="account-select"]').setValue("EXP-1")
		await flushPromises()
		expect(submit.attributes("disabled")).toBeDefined()
		expect(call.mock.calls.some(([m]) => m.endsWith("create_cash_entry"))).toBe(false)
	})

	it("Receipt does not require a note; submit sends the exact English entry_type + payload", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		await wrapper.find('[data-testid="type-Receipt"]').trigger("click")
		await flushPromises()
		await typeAmount(wrapper, ["1", "2", "5"])
		await wrapper.find('[data-testid="account-select"]').setValue("REC-1")
		await flushPromises()

		const submit = wrapper.find('[data-testid="cash-submit"]')
		expect(submit.attributes("disabled")).toBeUndefined() // no note needed
		await submit.trigger("click")
		await flushPromises()

		const create = call.mock.calls.find(([m]) => m.endsWith("create_cash_entry"))
		expect(create[1]).toMatchObject({
			entry_type: "Receipt",
			amount: 125,
			account: "REC-1",
			pos_profile: "POS-A",
		})
	})

	it("submits an Expense with a note and the exact payload", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		await typeAmount(wrapper, ["5", "0"])
		await wrapper.find('[data-testid="account-select"]').setValue("EXP-1")
		await wrapper.find('[data-testid="remarks"]').setValue("Bottled water")
		await flushPromises()
		await wrapper.find('[data-testid="cash-submit"]').trigger("click")
		await flushPromises()
		const create = call.mock.calls.find(([m]) => m.endsWith("create_cash_entry"))
		expect(create[1]).toMatchObject({
			entry_type: "Expense",
			amount: 50,
			account: "EXP-1",
			remarks: "Bottled water",
			pos_profile: "POS-A",
		})
	})

	it("renders the recent entries list with received / paid / net totals", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		const text = wrapper.text()
		expect(text).toContain("Water") // entry remark
		expect(text).toContain("200.00") // received_total
		expect(text).toContain("50.00") // paid_total
		expect(text).toContain("150.00") // net_total
	})

	it("guards against double-submit while a create is in flight", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		await typeAmount(wrapper, ["5", "0"])
		await wrapper.find('[data-testid="account-select"]').setValue("EXP-1")
		await wrapper.find('[data-testid="remarks"]').setValue("Water")
		await flushPromises()

		let release
		const pending = new Promise((resolve) => {
			release = resolve
		})
		call.mockImplementation((method) =>
			method.endsWith("create_cash_entry") ? pending : Promise.resolve({}),
		)
		const submit = wrapper.find('[data-testid="cash-submit"]')
		submit.trigger("click")
		await wrapper.vm.$nextTick()
		await submit.trigger("click")
		expect(call.mock.calls.filter(([m]) => m.endsWith("create_cash_entry"))).toHaveLength(1)
		release({ name: "CE-NEW" })
		await flushPromises()
	})
})
