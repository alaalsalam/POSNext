import { afterEach, describe, expect, it, vi } from "vitest"

vi.mock("@/stores/branding", () => ({
	getRuntimeBranding: () => ({}),
}))

import { parseError } from "./errorHandler"

describe("parseError", () => {
	afterEach(() => {
		globalThis.__ = undefined
	})

	it("turns a missing reporting exchange rate into an actionable cashier message", () => {
		globalThis.__ = (message) => message
		const result = parseError({
			exc_type: "ReportingCurrencyExchangeNotFoundError",
			message: "Unable to find exchange rate from YER to SAR",
		})

		expect(result.type).toBe("warning")
		expect(result.title).toBe("Currency Configuration Error")
		expect(result.message).toContain("set the reporting currency to YER")
		expect(result.technicalDetails).toBeNull()
		expect(result.retryable).toBe(false)
	})
})
