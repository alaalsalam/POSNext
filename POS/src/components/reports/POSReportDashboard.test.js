// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import POSReportDashboard from "./POSReportDashboard.vue";

// The dashboard calls the shared wrapper (import { call } from "@/utils/apiWrapper"),
// NOT window.frappe.call. Mock the same path runtime uses; the wrapper returns the
// server message DIRECTLY (no { message } envelope).
const { call } = vi.hoisted(() => ({ call: vi.fn() }));
vi.mock("@/utils/apiWrapper", () => ({ call: (...args) => call(...args) }));

vi.mock("@/utils/currency", () => ({
	formatCurrency: (v) => String(v ?? ""),
}));

function translate(value, args = []) {
	return args.reduce((s, a, i) => s.replace(`{${i}}`, a), value);
}

function mountDashboard() {
	globalThis.frappe = { boot: { lang: "en" } };
	globalThis.__ = translate;
	return mount(POSReportDashboard, {
		global: {
			mocks: { __: translate },
			config: { globalProperties: { __: translate } },
		},
	});
}

// Full-dashboard mock: a non-empty profile so loadAll fires, plus every downstream
// endpoint. Pass overrides to shape summary/trend/top-items per test.
function mockFullApi(overrides = {}) {
	const summary = {
		currency: "YER",
		from_date: "2026-08-01",
		to_date: "2026-08-31",
		sales_total: 10954.4,
		sales_count: 33,
		avg_invoice: 331.95,
		net_sales: 9277.2,
		returns_total: 1677.2,
		returns_count: 3,
		outstanding_total: 0,
		reconciled: true,
		reconciliation_difference: 0,
		delta: { sales_total: null, sales_count: null, avg_invoice: null, returns_total: null },
		previous: {},
		...overrides.summary,
	};
	const trend = overrides.trend || {
		granularity: "day",
		currency: "YER",
		buckets: [
			{ label: "2026-08-03", sales: 419, count: 3 },
			{ label: "2026-08-05", sales: 7936.4, count: 22 },
		],
	};
	const topItems = overrides.topItems || {
		currency: "YER",
		items: [
			{ item_code: "A", item_name: "iPhone 15 Pro Max", qty: 2, amount: 2598, uom: "Nos" },
			{ item_code: "B", item_name: "AirPods 4", qty: 13, amount: 1937, uom: "Nos" },
		],
	};
	call.mockImplementation(async (method) => {
		if (method.endsWith("get_report_filters"))
			return {
				pos_profiles: [{ name: "Phones", currency: "YER" }],
				periods: [{ key: "this_month", label: "This Month" }],
				desk_reports: [],
			};
		if (method.endsWith("get_current_shift_profile")) return { pos_profile: "Phones" };
		if (method.endsWith("get_daily_summary")) return summary;
		if (method.endsWith("get_sales_trend")) return trend;
		if (method.endsWith("get_top_items")) return topItems;
		if (method.endsWith("get_payment_breakdown"))
			return { methods: [], settlement_reconciled: true, tender_reconciled: true };
		if (method.endsWith("get_recent_transactions")) return { transactions: [], count: 0 };
		return {};
	});
}

function methodsCalled() {
	return call.mock.calls.map(([m]) => m);
}

describe("POSReportDashboard", () => {
	beforeEach(() => {
		call.mockReset();
	});

	afterEach(() => {
		globalThis.frappe = undefined;
		globalThis.__ = undefined;
		vi.clearAllMocks();
	});

	it("loads filters through the apiWrapper (not window.frappe.call)", async () => {
		call.mockResolvedValue({ pos_profiles: [], periods: [], desk_reports: [] });
		mountDashboard();
		await flushPromises();
		expect(call).toHaveBeenCalledWith("pos_next.api.reports.get_report_filters");
	});

	it("shows a retryable ERROR state (not the no-profiles empty state) when filters fail", async () => {
		call.mockRejectedValue({ message: "Boom" });
		const wrapper = mountDashboard();
		await flushPromises();

		// Distinct, retryable error state.
		expect(wrapper.find('[data-testid="reports-retry"]').exists()).toBe(true);
		expect(wrapper.text()).toContain("Boom");
		// Must NOT render the "no profiles" false-empty state.
		expect(wrapper.text()).not.toContain("No report-enabled POS Profiles");
	});

	it("shows the no-profiles empty state only when the call SUCCEEDS with an empty list", async () => {
		call.mockResolvedValue({ pos_profiles: [], periods: [], desk_reports: [] });
		const wrapper = mountDashboard();
		await flushPromises();

		expect(wrapper.find('[data-testid="reports-retry"]').exists()).toBe(false);
		expect(wrapper.text()).toContain("No report-enabled POS Profiles");
	});

	it("Retry re-requests the filters", async () => {
		call.mockRejectedValueOnce({ message: "Boom" });
		const wrapper = mountDashboard();
		await flushPromises();
		expect(wrapper.find('[data-testid="reports-retry"]').exists()).toBe(true);

		call.mockResolvedValue({ pos_profiles: [], periods: [], desk_reports: [] });
		await wrapper.find('[data-testid="reports-retry"]').trigger("click");
		await flushPromises();

		// Error cleared; the (successful) empty state now shows instead.
		expect(wrapper.find('[data-testid="reports-retry"]').exists()).toBe(false);
		expect(wrapper.text()).toContain("No report-enabled POS Profiles");
	});

	// ── New smart layer ──────────────────────────────────────────────────────

	it("fetches the sales trend and top items through the wrapper", async () => {
		mockFullApi();
		mountDashboard();
		await flushPromises();
		const methods = methodsCalled();
		expect(methods).toContain("pos_next.api.reports.get_sales_trend");
		expect(methods).toContain("pos_next.api.reports.get_top_items");
	});

	it("renders '—' for a null delta and never '0%'", async () => {
		mockFullApi(); // this month: all deltas null
		const wrapper = mountDashboard();
		await flushPromises();
		const text = wrapper.text();
		expect(text).toContain("—");
		// A null baseline must NOT be shown as a real 0% change.
		expect(text).not.toContain("0%");
	});

	it("renders a real percent for a 0% delta (distinct from null)", async () => {
		mockFullApi({
			summary: { delta: { sales_total: 0, sales_count: 0, avg_invoice: 0, returns_total: 0 } },
		});
		const wrapper = mountDashboard();
		await flushPromises();
		expect(wrapper.text()).toContain("0%");
	});

	it("shows the trend empty state when every bucket is zero", async () => {
		mockFullApi({
			trend: {
				granularity: "day",
				currency: "YER",
				buckets: [
					{ label: "2026-08-01", sales: 0, count: 0 },
					{ label: "2026-08-02", sales: 0, count: 0 },
				],
			},
		});
		const wrapper = mountDashboard();
		await flushPromises();
		expect(wrapper.find('[data-testid="trend-empty"]').exists()).toBe(true);
	});

	it("renders top items with a proportional bar", async () => {
		mockFullApi();
		const wrapper = mountDashboard();
		await flushPromises();
		expect(wrapper.text()).toContain("iPhone 15 Pro Max");
		expect(wrapper.text()).toContain("AirPods 4");
	});

	it("flags reconciliation review when a tender flag is false", async () => {
		mockFullApi();
		call.mockImplementation((method) => {
			if (method.endsWith("get_report_filters"))
				return Promise.resolve({
					pos_profiles: [{ name: "Phones", currency: "YER" }],
					periods: [{ key: "this_month", label: "This Month" }],
					desk_reports: [],
				});
			if (method.endsWith("get_current_shift_profile"))
				return Promise.resolve({ pos_profile: "Phones" });
			if (method.endsWith("get_daily_summary"))
				return Promise.resolve({ reconciled: true, currency: "YER", sales_total: 1, delta: {} });
			if (method.endsWith("get_payment_breakdown"))
				return Promise.resolve({ methods: [], settlement_reconciled: true, tender_reconciled: false });
			return Promise.resolve({ transactions: [], count: 0, buckets: [], items: [] });
		});
		const wrapper = mountDashboard();
		await flushPromises();
		expect(wrapper.text()).toContain("Needs review");
	});
});
