const fs = require("node:fs")
const path = require("node:path")
const { chromium } = require("playwright")

const POS_URL = process.env.POSNEXT_PWA_URL || "https://pos.yemenfrappe.com/pos"
const OUTPUT =
	process.env.POSNEXT_PWA_FIX2_OUTPUT ||
	"/home/frappe/frappe-bench/sites/pos.yemenfrappe.com/private/files/posnext_phase7b_fix2_browser_result.json"

async function collect(page, label) {
	return await page.evaluate(async (label) => {
		const result = {
			label,
			href: location.href,
			sw_available: "serviceWorker" in navigator,
			controlled_by_sw: false,
			controller_script_url: null,
			registrations: [],
			cache_names: [],
			errors: [],
		}
		if (!("serviceWorker" in navigator)) return result
		try {
			result.registrations = (await navigator.serviceWorker.getRegistrations()).map((reg) => ({
				scope: reg.scope,
				active_script_url: reg.active?.scriptURL || null,
				active_state: reg.active?.state || null,
				update_via_cache: reg.updateViaCache || null,
			}))
		} catch (error) {
			result.errors.push(`getRegistrations: ${error?.message || error}`)
		}
		try {
			result.controlled_by_sw = Boolean(navigator.serviceWorker.controller)
			result.controller_script_url = navigator.serviceWorker.controller?.scriptURL || null
		} catch (error) {
			result.errors.push(`controller: ${error?.message || error}`)
		}
		try {
			if ("caches" in window) result.cache_names = await caches.keys()
		} catch (error) {
			result.errors.push(`caches: ${error?.message || error}`)
		}
		return result
	}, label)
}

async function clearOrigin(page) {
	return await page.evaluate(async () => {
		const result = { unregistered: [], deleted_caches: [], errors: [] }
		if ("serviceWorker" in navigator) {
			try {
				for (const reg of await navigator.serviceWorker.getRegistrations()) {
					result.unregistered.push({
						scope: reg.scope,
						script: reg.active?.scriptURL || null,
						ok: await reg.unregister(),
					})
				}
			} catch (error) {
				result.errors.push(`unregister: ${error?.message || error}`)
			}
		}
		if ("caches" in window) {
			try {
				for (const key of await caches.keys()) {
					result.deleted_caches.push({ key, ok: await caches.delete(key) })
				}
			} catch (error) {
				result.errors.push(`delete caches: ${error?.message || error}`)
			}
		}
		return result
	})
}

async function waitForReady(page) {
	return await page.evaluate(async () => {
		if (!("serviceWorker" in navigator)) return { ok: false, reason: "serviceWorker unavailable" }
		try {
			const reg = await Promise.race([
				navigator.serviceWorker.ready,
				new Promise((_, reject) => setTimeout(() => reject(new Error("ready timeout")), 15000)),
			])
			return {
				ok: true,
				scope: reg.scope,
				active_script_url: reg.active?.scriptURL || null,
			}
		} catch (error) {
			return { ok: false, reason: error?.message || String(error) }
		}
	})
}

async function main() {
	const consoleMessages = []
	const pageErrors = []
	const browser = await chromium.launch({
		headless: true,
		executablePath: process.env.CHROME_PATH || "/usr/bin/google-chrome",
		args: ["--no-sandbox", "--disable-dev-shm-usage"],
	})
	try {
		const context = await browser.newContext({ ignoreHTTPSErrors: true, serviceWorkers: "allow" })
		const page = await context.newPage()
		page.on("console", (message) =>
			consoleMessages.push({ type: message.type(), text: message.text().slice(0, 500) }),
		)
		page.on("pageerror", (error) => pageErrors.push(error.message))

		await page.goto(POS_URL, { waitUntil: "domcontentloaded", timeout: 60000 })
		await page.waitForTimeout(3000)
		const before = await collect(page, "before_clear")
		const clear = await clearOrigin(page)
		await page.goto(`${POS_URL}?sw_fix2=${Date.now()}`, {
			waitUntil: "domcontentloaded",
			timeout: 60000,
		})
		await page.waitForTimeout(5000)
		const ready = await waitForReady(page)
		const afterRegister = await collect(page, "after_register")
		await page.reload({ waitUntil: "domcontentloaded", timeout: 60000 })
		await page.waitForTimeout(5000)
		const final = await collect(page, "after_reload")
		const activeRegistration = final.registrations[0] || null
		const result = {
			generated_at: new Date().toISOString(),
			pos_url: POS_URL,
			before,
			clear,
			ready,
			afterRegister,
			final,
			summary: {
				controlled_by_sw: final.controlled_by_sw,
				active_sw_url: final.controller_script_url || activeRegistration?.active_script_url || null,
				active_scope: activeRegistration?.scope || null,
				registrations_count: final.registrations.length,
				cache_names: final.cache_names,
				unregister_clear_cache_done: true,
				console_sw_errors: consoleMessages.filter((message) =>
					/serviceworker|service worker|scope|sw\.js/i.test(message.text),
				),
				page_errors: pageErrors,
			},
		}
		fs.mkdirSync(path.dirname(OUTPUT), { recursive: true })
		fs.writeFileSync(OUTPUT, JSON.stringify(result, null, 2))
		console.log(JSON.stringify(result.summary, null, 2))
	} finally {
		await browser.close()
	}
}

main().catch((error) => {
	const result = {
		generated_at: new Date().toISOString(),
		error: error?.stack || error?.message || String(error),
		summary: { controlled_by_sw: false },
	}
	fs.mkdirSync(path.dirname(OUTPUT), { recursive: true })
	fs.writeFileSync(OUTPUT, JSON.stringify(result, null, 2))
	console.error(JSON.stringify(result, null, 2))
	process.exit(1)
})
