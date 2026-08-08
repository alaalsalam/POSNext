// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import ExpenseTypeManagement from "./ExpenseTypeManagement.vue"

const { call } = vi.hoisted(() => ({ call: vi.fn() }))
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

const TYPES = {
	expense_types: [
		{
			name: "EXP-ELEC",
			expense_type_name: "Electricity",
			expense_account: "ACC-1",
			account_name: "Utilities",
			enabled: 1,
		},
	],
	company: "ACME",
}
const ACCOUNTS = {
	accounts: [
		{ name: "ACC-1", account_name: "Utilities" },
		{ name: "ACC-2", account_name: "Maintenance" },
	],
	company: "ACME",
}

function mockApi() {
	call.mockImplementation(async (method) => {
		if (method.endsWith("get_expense_types")) return TYPES
		if (method.endsWith("get_expense_accounts")) return ACCOUNTS
		if (method.endsWith("save_expense_type")) return { name: "EXP-NEW" }
		if (method.endsWith("delete_expense_type"))
			return { name: "EXP-ELEC", deleted: true }
		return {}
	})
}

function mountScreen() {
	globalThis.frappe = { boot: { lang: "ar" } }
	mockApi()
	return mount(ExpenseTypeManagement, { props: { posProfile: "POS-A" } })
}

function savePayload() {
	return call.mock.calls.find(([m]) => m.endsWith("save_expense_type"))?.[1]
}

describe("ExpenseTypeManagement", () => {
	beforeEach(() => {
		call.mockReset()
		showSuccess.mockClear()
		showError.mockClear()
	})
	afterEach(() => {
		globalThis.frappe = undefined
		vi.clearAllMocks()
	})

	it("loads types + scoped expense accounts on mount and lists them", async () => {
		const wrapper = mountScreen()
		await flushPromises()
		const methods = call.mock.calls.map(([m]) => m)
		expect(methods).toContain("pos_next.api.cash_management.get_expense_types")
		expect(methods).toContain(
			"pos_next.api.cash_management.get_expense_accounts",
		)
		expect(wrapper.text()).toContain("Electricity")
		expect(wrapper.text()).toContain("Utilities")
		// The account select is populated from the scoped list.
		const options = wrapper
			.find('[data-testid="expense-account-select"]')
			.findAll("option")
		expect(options.map((o) => o.text())).toEqual(
			expect.arrayContaining(["Utilities", "Maintenance"]),
		)
	})

	it("creates a new type (no name) with the exact payload", async () => {
		const wrapper = mountScreen()
		await flushPromises()
		await wrapper.find('[data-testid="expense-type-name"]').setValue("Water")
		await wrapper
			.find('[data-testid="expense-account-select"]')
			.setValue("ACC-2")
		await flushPromises()
		await wrapper.find('[data-testid="save-expense-type"]').trigger("click")
		await flushPromises()
		expect(savePayload()).toMatchObject({
			name: null,
			expense_type_name: "Water",
			expense_account: "ACC-2",
			enabled: 1,
			pos_profile: "POS-A",
		})
	})

	it("edit pre-fills the form and saves with the existing name", async () => {
		const wrapper = mountScreen()
		await flushPromises()
		await wrapper.find('[data-testid="edit-EXP-ELEC"]').trigger("click")
		await flushPromises()
		expect(
			wrapper.find('[data-testid="expense-type-name"]').element.value,
		).toBe("Electricity")
		expect(
			wrapper.find('[data-testid="expense-account-select"]').element.value,
		).toBe("ACC-1")
		await wrapper
			.find('[data-testid="expense-type-name"]')
			.setValue("Electricity & Power")
		await wrapper.find('[data-testid="save-expense-type"]').trigger("click")
		await flushPromises()
		expect(savePayload()).toMatchObject({
			name: "EXP-ELEC",
			expense_type_name: "Electricity & Power",
			expense_account: "ACC-1",
		})
	})

	it("delete confirms then calls delete_expense_type", async () => {
		const confirmSpy = vi.spyOn(globalThis, "confirm").mockReturnValue(true)
		const wrapper = mountScreen()
		await flushPromises()
		await wrapper.find('[data-testid="delete-EXP-ELEC"]').trigger("click")
		await flushPromises()
		expect(confirmSpy).toHaveBeenCalled()
		const del = call.mock.calls.find(([m]) => m.endsWith("delete_expense_type"))
		expect(del[1]).toMatchObject({ name: "EXP-ELEC", pos_profile: "POS-A" })
		confirmSpy.mockRestore()
	})

	it("delete is a no-op when the confirm is cancelled", async () => {
		const confirmSpy = vi.spyOn(globalThis, "confirm").mockReturnValue(false)
		const wrapper = mountScreen()
		await flushPromises()
		await wrapper.find('[data-testid="delete-EXP-ELEC"]').trigger("click")
		await flushPromises()
		expect(
			call.mock.calls.some(([m]) => m.endsWith("delete_expense_type")),
		).toBe(false)
		confirmSpy.mockRestore()
	})
})
