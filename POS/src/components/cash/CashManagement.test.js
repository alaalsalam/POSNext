// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import CashManagement from "./CashManagement.vue"

// Calls go through the shared wrapper (import { call } from "@/utils/apiWrapper").
const { call } = vi.hoisted(() => ({ call: vi.fn() }))
vi.mock("@/utils/apiWrapper", () => ({ call: (...args) => call(...args) }))

// Stable toast spies so the posting-mode success text can be asserted.
const { showSuccess, showError } = vi.hoisted(() => ({
	showSuccess: vi.fn(),
	showError: vi.fn(),
}))

vi.mock("@/utils/currency", () => ({
	formatCurrency: (v) => Number(v || 0).toFixed(2),
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
// Screen 2 is out of scope for these tests — stub it.
vi.mock("./ExpenseTypeManagement.vue", () => ({
	default: {
		name: "ExpenseTypeManagement",
		template: "<div data-testid='expense-manager-stub' />",
	},
}))

const SETUP = {
	posting_mode: "Immediate",
	is_manager: false,
	default_cash_account: "CASH-1",
	cash_boxes: [
		{ name: "CASH-1", account_name: "Main Drawer", account_type: "Cash" },
		{ name: "BANK-1", account_name: "Bank", account_type: "Bank" },
	],
	expense_types: [{ name: "EXP-ELEC", expense_type_name: "Electricity" }],
	currency: "YER",
}

const ENTRIES = {
	entries: [
		{
			name: "CE-1",
			posa_cash_entry_type: "Expense",
			total_debit: 50,
			user_remark: "Water",
			posting_date: "2026-08-08",
			creation: "2026-08-08 10:00:00",
			docstatus: 1,
			status: "Approved",
		},
	],
	received_total: 200,
	paid_total: 50,
	net_total: 150,
	pending_count: 0,
	is_manager: false,
}

function mockApi(overrides = {}) {
	const setup = { ...SETUP, ...(overrides.setup || {}) }
	const entries = { ...ENTRIES, ...(overrides.entries || {}) }
	const createResult = overrides.createResult || {
		name: "CE-NEW",
		status: "Approved",
	}
	call.mockImplementation(async (method) => {
		if (method.endsWith("get_cash_management_setup")) return setup
		if (method.endsWith("get_cash_entries")) return entries
		if (method.endsWith("get_parties"))
			return { parties: [{ name: "CUST-1", party_name: "Ali" }] }
		if (method.endsWith("get_cash_entry_accounts"))
			return { accounts: [{ name: "GEN-1", account_name: "Misc Income" }] }
		if (method.endsWith("create_cash_entry")) return createResult
		if (method.endsWith("approve_cash_entry"))
			return { name: "CE-1", status: "Approved" }
		if (method.endsWith("reject_cash_entry"))
			return { name: "CE-1", status: "Rejected" }
		return {}
	})
}

function mountPanel(overrides) {
	globalThis.frappe = { boot: { lang: "ar" } }
	mockApi(overrides)
	return mount(CashManagement, { props: { posProfile: "POS-A" } })
}

async function typeAmount(wrapper, digits) {
	const keys = wrapper.findAll("button.numkey")
	const key = (label) => keys.find((b) => b.text().trim() === label)
	for (const d of digits) await key(d).trigger("click")
}

function createPayload() {
	return call.mock.calls.find(([m]) => m.endsWith("create_cash_entry"))?.[1]
}

describe("CashManagement", () => {
	beforeEach(() => {
		call.mockReset()
		showSuccess.mockClear()
		showError.mockClear()
	})
	afterEach(() => {
		globalThis.frappe = undefined
		vi.clearAllMocks()
	})

	it("loads setup + entries via the wrapper on mount (not accounts)", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		const methods = call.mock.calls.map(([m]) => m)
		expect(methods).toContain(
			"pos_next.api.cash_management.get_cash_management_setup",
		)
		expect(methods).toContain("pos_next.api.cash_management.get_cash_entries")
		expect(methods).not.toContain(
			"pos_next.api.cash_management.get_cash_entry_accounts",
		)
		// Default cash box selected from setup.
		expect(wrapper.find('[data-testid="from-box-select"]').element.value).toBe(
			"CASH-1",
		)
	})

	it("renders all four entry types", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		for (const t of ["Expense", "Receipt", "Payment", "Transfer"]) {
			expect(wrapper.find(`[data-testid="type-${t}"]`).exists()).toBe(true)
		}
	})

	it("submits an Expense with expense_type + cash_account + note", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		await typeAmount(wrapper, ["5", "0"])
		await wrapper
			.find('[data-testid="expense-type-select"]')
			.setValue("EXP-ELEC")
		await wrapper.find('[data-testid="remarks"]').setValue("Bottled water")
		await flushPromises()
		await wrapper.find('[data-testid="cash-submit"]').trigger("click")
		await flushPromises()
		expect(createPayload()).toMatchObject({
			entry_type: "Expense",
			amount: 50,
			expense_type: "EXP-ELEC",
			cash_account: "CASH-1",
			remarks: "Bottled water",
			pos_profile: "POS-A",
		})
	})

	it("shows the expense empty-state (no submit) when there are no expense types", async () => {
		const wrapper = mountPanel({ setup: { expense_types: [] } })
		await flushPromises()
		expect(wrapper.find('[data-testid="expense-empty"]').exists()).toBe(true)
		expect(wrapper.find('[data-testid="cash-submit"]').exists()).toBe(false)
	})

	it("Receipt submits a party payload (Customer) into the chosen box; note optional", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		await wrapper.find('[data-testid="type-Receipt"]').trigger("click")
		await flushPromises()
		await typeAmount(wrapper, ["1", "2", "5"])
		await wrapper.find('[data-testid="party-select"]').setValue("CUST-1")
		await wrapper.find('[data-testid="cash-box-select"]').setValue("BANK-1")
		await flushPromises()
		const submit = wrapper.find('[data-testid="cash-submit"]')
		expect(submit.attributes("disabled")).toBeUndefined() // no note needed
		await submit.trigger("click")
		await flushPromises()
		expect(createPayload()).toMatchObject({
			entry_type: "Receipt",
			amount: 125,
			party_type: "Customer",
			party: "CUST-1",
			cash_account: "BANK-1",
			pos_profile: "POS-A",
		})
	})

	it("Payment (Employee) requires a note and sends party_type=Employee", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		await wrapper.find('[data-testid="type-Payment"]').trigger("click")
		await flushPromises()
		await typeAmount(wrapper, ["9", "0"])
		await wrapper.find('[data-testid="party-select"]').setValue("CUST-1")
		await flushPromises()
		// Note is required for Payment → still disabled.
		expect(
			wrapper.find('[data-testid="cash-submit"]').attributes("disabled"),
		).toBeDefined()
		await wrapper.find('[data-testid="remarks"]').setValue("Advance")
		await flushPromises()
		await wrapper.find('[data-testid="cash-submit"]').trigger("click")
		await flushPromises()
		expect(createPayload()).toMatchObject({
			entry_type: "Payment",
			amount: 90,
			party_type: "Employee",
			party: "CUST-1",
			remarks: "Advance",
			pos_profile: "POS-A",
		})
	})

	it("Transfer sends cash_account (from) + to_account (to) and blocks equal boxes", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		await wrapper.find('[data-testid="type-Transfer"]').trigger("click")
		await flushPromises()
		await typeAmount(wrapper, ["3", "0"])
		// Same box → cannot submit.
		await wrapper.find('[data-testid="to-box-select"]').setValue("CASH-1")
		await flushPromises()
		expect(
			wrapper.find('[data-testid="cash-submit"]').attributes("disabled"),
		).toBeDefined()
		// Different box → allowed.
		await wrapper.find('[data-testid="to-box-select"]').setValue("BANK-1")
		await flushPromises()
		await wrapper.find('[data-testid="cash-submit"]').trigger("click")
		await flushPromises()
		expect(createPayload()).toMatchObject({
			entry_type: "Transfer",
			amount: 30,
			cash_account: "CASH-1",
			to_account: "BANK-1",
			pos_profile: "POS-A",
		})
	})

	it("Receipt via a general account sends account instead of a party", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		await wrapper.find('[data-testid="type-Receipt"]').trigger("click")
		await flushPromises()
		await wrapper.find('[data-testid="counter-account"]').trigger("click")
		await flushPromises()
		await typeAmount(wrapper, ["4", "0"])
		await wrapper.find('[data-testid="account-select"]').setValue("GEN-1")
		await flushPromises()
		await wrapper.find('[data-testid="cash-submit"]').trigger("click")
		await flushPromises()
		const payload = createPayload()
		expect(payload).toMatchObject({
			entry_type: "Receipt",
			account: "GEN-1",
			cash_account: "CASH-1",
		})
		expect(payload.party).toBeUndefined()
	})

	it("blocks submit when amount is 0", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		expect(
			wrapper.find('[data-testid="cash-submit"]').attributes("disabled"),
		).toBeDefined()
	})

	it("posting mode After Approval shows the pending-approval success text", async () => {
		const wrapper = mountPanel({
			setup: { posting_mode: "After Approval" },
			createResult: { name: "CE-NEW", status: "Pending Approval" },
		})
		await flushPromises()
		// Hint is visible.
		expect(wrapper.text()).toContain("تُعتمد من المدير قبل الترحيل")
		await typeAmount(wrapper, ["5", "0"])
		await wrapper
			.find('[data-testid="expense-type-select"]')
			.setValue("EXP-ELEC")
		await wrapper.find('[data-testid="remarks"]').setValue("Water")
		await flushPromises()
		await wrapper.find('[data-testid="cash-submit"]').trigger("click")
		await flushPromises()
		expect(showSuccess).toHaveBeenCalledWith("تم الحفظ — بانتظار الاعتماد")
	})

	it("posting mode Immediate shows the recorded success text", async () => {
		const wrapper = mountPanel({
			createResult: { name: "CE-NEW", status: "Approved" },
		})
		await flushPromises()
		await typeAmount(wrapper, ["5", "0"])
		await wrapper
			.find('[data-testid="expense-type-select"]')
			.setValue("EXP-ELEC")
		await wrapper.find('[data-testid="remarks"]').setValue("Water")
		await flushPromises()
		await wrapper.find('[data-testid="cash-submit"]').trigger("click")
		await flushPromises()
		expect(showSuccess).toHaveBeenCalledWith("تم تسجيل الحركة")
	})

	it("hides approve/reject and the manage link for a non-manager", async () => {
		const wrapper = mountPanel({
			entries: {
				entries: [
					{
						name: "CE-P",
						posa_cash_entry_type: "Expense",
						total_debit: 20,
						user_remark: "x",
						creation: "2026-08-08 09:00:00",
						docstatus: 0,
						status: "Pending Approval",
					},
				],
				pending_count: 1,
				is_manager: false,
			},
		})
		await flushPromises()
		expect(wrapper.find('[data-testid="approve-CE-P"]').exists()).toBe(false)
		expect(wrapper.find('[data-testid="manage-expense-types"]').exists()).toBe(
			false,
		)
	})

	it("shows approve/reject on pending entries for a manager and calls the endpoints", async () => {
		const wrapper = mountPanel({
			setup: { is_manager: true },
			entries: {
				entries: [
					{
						name: "CE-P",
						posa_cash_entry_type: "Expense",
						total_debit: 20,
						user_remark: "x",
						creation: "2026-08-08 09:00:00",
						docstatus: 0,
						status: "Pending Approval",
					},
				],
				pending_count: 1,
				is_manager: true,
			},
		})
		await flushPromises()
		expect(wrapper.find('[data-testid="manage-expense-types"]').exists()).toBe(
			true,
		)
		expect(wrapper.find('[data-testid="approve-CE-P"]').exists()).toBe(true)
		await wrapper.find('[data-testid="approve-CE-P"]').trigger("click")
		await flushPromises()
		const approve = call.mock.calls.find(([m]) =>
			m.endsWith("approve_cash_entry"),
		)
		expect(approve[1]).toMatchObject({ name: "CE-P", pos_profile: "POS-A" })
	})

	it("guards against double-submit while a create is in flight", async () => {
		const wrapper = mountPanel()
		await flushPromises()
		await typeAmount(wrapper, ["5", "0"])
		await wrapper
			.find('[data-testid="expense-type-select"]')
			.setValue("EXP-ELEC")
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
		expect(
			call.mock.calls.filter(([m]) => m.endsWith("create_cash_entry")),
		).toHaveLength(1)
		release({ name: "CE-NEW", status: "Approved" })
		await flushPromises()
	})
})
