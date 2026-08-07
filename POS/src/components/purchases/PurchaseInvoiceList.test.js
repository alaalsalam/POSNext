// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import PurchaseInvoiceList from "./PurchaseInvoiceList.vue";

// The component calls the shared wrapper (import { call } from "@/utils/apiWrapper"),
// NOT window.frappe.call. Mock the same path runtime uses; the wrapper returns the
// server message DIRECTLY (no { message } envelope).
const { call } = vi.hoisted(() => ({ call: vi.fn() }));
vi.mock("@/utils/apiWrapper", () => ({ call: (...args) => call(...args) }));

vi.mock("@/utils/managementI18n", () => ({
	managerTranslate: (value, args = []) =>
		args.reduce((s, a, i) => s.replace(`{${i}}`, a), value),
}));

function inv(name, docstatus, outstanding, status) {
	return {
		name,
		supplier: "SUP-1",
		supplier_name: "Acme",
		posting_date: "2026-08-01",
		grand_total: 100,
		outstanding_amount: outstanding,
		status,
		docstatus,
		currency: "SAR",
	};
}

function mountList(props = {}) {
	globalThis.frappe = { boot: { lang: "en" } };
	return mount(PurchaseInvoiceList, {
		props: { posProfile: "POS-A", canCreatePayment: true, ...props },
	});
}

describe("PurchaseInvoiceList (embedded)", () => {
	beforeEach(() => {
		call.mockReset();
	});

	afterEach(() => {
		globalThis.frappe = undefined;
		vi.clearAllMocks();
	});

	it("uses the apiWrapper call (not window.frappe.call) with the right method", async () => {
		call.mockResolvedValue({ invoices: [], total: 0 });
		mountList({ fixedStatus: "history" });
		await flushPromises();
		expect(call).toHaveBeenCalled();
		expect(call.mock.calls[0][0]).toBe("pos_next.api.purchases.get_purchase_invoices");
	});

	it("Unpaid tab surfaces an unpaid invoice even when newer paid invoices exist", async () => {
		// Newest-first: 2 paid, then 1 outstanding — the outstanding one must show.
		call.mockImplementation(async (method) => {
			if (method.endsWith("get_purchase_invoices")) {
				return {
					invoices: [
						inv("PINV-3", 1, 0, "Paid"),
						inv("PINV-2", 1, 0, "Paid"),
						inv("PINV-1", 1, 50, "Partly Paid"),
					],
					total: 3,
				};
			}
			if (method.endsWith("get_purchase_outstanding_summary")) {
				return { total_outstanding: 50, unpaid_count: 0, partial_count: 1 };
			}
			return {};
		});

		const wrapper = mountList({ fixedStatus: "unpaid" });
		await flushPromises();

		const text = wrapper.text();
		expect(text).toContain("PINV-1"); // outstanding invoice is visible
		expect(text).not.toContain("PINV-3"); // paid invoices are filtered out
		expect(text).not.toContain("PINV-2");
		expect(wrapper.text()).toContain("تسجيل دفعة"); // pay action available
	});

	it("Unpaid tab requests a full first page so outstanding invoices are not paged away", async () => {
		call.mockResolvedValue({ invoices: [], total: 0 });
		mountList({ fixedStatus: "unpaid" });
		await flushPromises();
		const listCall = call.mock.calls.find(([method]) =>
			method.endsWith("get_purchase_invoices"),
		);
		expect(listCall[1].limit).toBe(100);
	});

	it("History tab shows all invoices (no outstanding filter) and skips the summary fetch", async () => {
		call.mockImplementation(async (method) => {
			if (method.endsWith("get_purchase_invoices")) {
				return {
					invoices: [inv("PINV-9", 1, 0, "Paid"), inv("PINV-8", 0, 0, "Draft")],
					total: 2,
				};
			}
			return {};
		});

		const wrapper = mountList({ fixedStatus: "history" });
		await flushPromises();
		expect(wrapper.text()).toContain("PINV-9");
		expect(wrapper.text()).toContain("PINV-8");
		const summaryCall = call.mock.calls.find(([method]) =>
			method.endsWith("get_purchase_outstanding_summary"),
		);
		expect(summaryCall).toBeUndefined();
	});

	it("Drafts tab filters to docstatus 0 server-side", async () => {
		call.mockResolvedValue({ invoices: [], total: 0 });
		mountList({ fixedStatus: "drafts" });
		await flushPromises();
		const listCall = call.mock.calls.find(([method]) =>
			method.endsWith("get_purchase_invoices"),
		);
		expect(listCall[1].status).toBe("Draft");
	});
});
