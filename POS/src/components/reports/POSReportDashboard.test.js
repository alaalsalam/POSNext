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
});
