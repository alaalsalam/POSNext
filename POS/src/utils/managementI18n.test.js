import { afterEach, describe, expect, it, vi } from "vitest"
import { managerTranslate } from "./managementI18n"

describe("managerTranslate", () => {
	afterEach(() => {
		globalThis.frappe = undefined
		globalThis.__ = undefined
	})

	it("shows English only for an English locale", () => {
		globalThis.frappe = { boot: { lang: "en" } }
		expect(managerTranslate("دفعات الموردين")).toBe("Supplier Payments")
		expect(managerTranslate("متبقي: {0}", [25])).toBe("Outstanding: 25")
	})

	it("shows Arabic only for an Arabic locale", () => {
		globalThis.frappe = { boot: { lang: "ar" } }
		expect(managerTranslate("دفعات الموردين")).toBe("دفعات الموردين")
	})

	it("delegates English source keys to Frappe translation", () => {
		globalThis.frappe = { boot: { lang: "ar" } }
		globalThis.__ = vi.fn(() => "العملة")
		expect(managerTranslate("Currency")).toBe("العملة")
	})
})
