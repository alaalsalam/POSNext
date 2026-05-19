#!/usr/bin/env node
/**
 * Browser-level PWA control verification for POSNext Phase 7B.
 *
 * Runs against the deployed site using the repo's Playwright dependency and
 * the system Chrome binary. It does not submit invoices or mutate business data.
 */

const fs = require("node:fs")
const path = require("node:path")
const { chromium } = require("playwright")

const BASE_URL = process.env.POSNEXT_PWA_URL || "https://pos.yemenfrappe.com/pos"
const OUTPUT_PATH =
	process.env.POSNEXT_PWA_VERIFY_OUTPUT ||
	"/home/frappe/frappe-bench/sites/pos.yemenfrappe.com/private/files/posnext_phase7b_browser_control_result.json"
const CHROME_PATH = process.env.CHROME_PATH || "/usr/bin/google-chrome"

async function snapshot(page) {
	return await page.evaluate(async () => {
		const result = {
			href: window.location.href,
			title: document.title,
			manifest_href: document.querySelector('link[rel="manifest"]')?.href || null,
			sw_available: "serviceWorker" in navigator,
			controlled_by_sw: false,
			controller_script_url: null,
			registrations: [],
			cache_names: [],
			errors: [],
		}

		if (!("serviceWorker" in navigator)) {
			result.errors.push("navigator.serviceWorker is not available")
			return result
		}

		try {
			await Promise.race([
				navigator.serviceWorker.ready,
				new Promise((resolve) => setTimeout(resolve, 8000)),
			])
		} catch (error) {
			result.errors.push(`serviceWorker.ready failed: ${error?.message || error}`)
		}

		try {
			result.controlled_by_sw = Boolean(navigator.serviceWorker.controller)
			result.controller_script_url = navigator.serviceWorker.controller?.scriptURL || null
		} catch (error) {
			result.errors.push(`controller check failed: ${error?.message || error}`)
		}

		try {
			const registrations = await navigator.serviceWorker.getRegistrations()
			result.registrations = registrations.map((registration) => ({
				scope: registration.scope,
				active_script_url: registration.active?.scriptURL || null,
				active_state: registration.active?.state || null,
				waiting_script_url: registration.waiting?.scriptURL || null,
				installing_script_url: registration.installing?.scriptURL || null,
			}))
		} catch (error) {
			result.errors.push(`getRegistrations failed: ${error?.message || error}`)
		}

		try {
			if ("caches" in window) {
				result.cache_names = await caches.keys()
			}
		} catch (error) {
			result.errors.push(`caches.keys failed: ${error?.message || error}`)
		}

		return result
	})
}

async function main() {
	const consoleMessages = []
	const pageErrors = []
	const browser = await chromium.launch({
		headless: true,
		executablePath: CHROME_PATH,
		args: ["--no-sandbox", "--disable-dev-shm-usage"],
	})

	try {
		const context = await browser.newContext({
			ignoreHTTPSErrors: true,
			serviceWorkers: "allow",
		})
		const page = await context.newPage()
		page.on("console", (message) => {
			consoleMessages.push({
				type: message.type(),
				text: message.text().slice(0, 500),
			})
		})
		page.on("pageerror", (error) => pageErrors.push(error.message))

		await page.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 60000 })
		await page.waitForTimeout(6000)
		const first = await snapshot(page)

		await page.reload({ waitUntil: "domcontentloaded", timeout: 60000 })
		await page.waitForTimeout(6000)
		const second = await snapshot(page)

		const registrationPath = (scope) => {
			try {
				return new URL(scope).pathname
			} catch {
				return ""
			}
		}
		const activeRegistration = second.registrations.find(
			(registration) => registrationPath(registration.scope) === "/pos/",
		)
		const result = {
			generated_at: new Date().toISOString(),
			url: BASE_URL,
			browser: "chromium",
			chrome_path: CHROME_PATH,
			first_load: first,
			second_load: second,
			summary: {
				sw_available: second.sw_available,
				controlled_by_sw: second.controlled_by_sw,
				active_sw_url: second.controller_script_url || activeRegistration?.active_script_url || null,
				active_scope: activeRegistration?.scope || null,
				has_pos_scope: second.registrations.some(
					(registration) => registrationPath(registration.scope) === "/pos/",
				),
				registration_count: second.registrations.length,
				cache_count: second.cache_names.length,
				critical_console_errors: consoleMessages.filter((message) => message.type === "error"),
				page_errors: pageErrors,
			},
			console_messages: consoleMessages.slice(-80),
		}

		fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true })
		fs.writeFileSync(OUTPUT_PATH, JSON.stringify(result, null, 2))
		console.log(JSON.stringify(result, null, 2))
	} finally {
		await browser.close()
	}
}

main().catch((error) => {
	const result = {
		generated_at: new Date().toISOString(),
		url: BASE_URL,
		error: error?.stack || error?.message || String(error),
		summary: {
			controlled_by_sw: false,
			has_pos_scope: false,
		},
	}
	fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true })
	fs.writeFileSync(OUTPUT_PATH, JSON.stringify(result, null, 2))
	console.error(JSON.stringify(result, null, 2))
	process.exit(1)
})
