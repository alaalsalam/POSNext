import { describe, expect, it } from "vitest"
import { buildDeskReportUrl, isRtlLocale } from "./reportUtils"

describe("report dashboard utilities", () => {
	it("uses RTL only for Arabic or an RTL document", () => {
		expect(isRtlLocale("ar", "ltr")).toBe(true)
		expect(isRtlLocale("en", "rtl")).toBe(true)
		expect(isRtlLocale("en", "ltr")).toBe(false)
	})

	it("passes the authorized profile and dates to a Desk report", () => {
		const url = buildDeskReportUrl(
			"Sales vs Shifts Report",
			"الجوالات",
			"2026-07-01",
			"2026-07-31",
		)
		expect(url).toContain("/app/query-report/Sales%20vs%20Shifts%20Report?")
		const query = new URLSearchParams(url.split("?")[1])
		expect(query.get("pos_profile")).toBe("الجوالات")
		expect(query.get("from_date")).toBe("2026-07-01")
		expect(query.get("to_date")).toBe("2026-07-31")
	})
})
