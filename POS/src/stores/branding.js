import { call } from "@/utils/apiWrapper"
import { defineStore } from "pinia"
import { computed, ref } from "vue"

export const DEFAULT_BRANDING = {
	enabled: 1,
	app_name: "Digit POS",
	app_short_name: "Digit",
	workspace_label: "Digit POS",
	login_title: "تسجيل الدخول إلى Digit POS",
	login_subtitle: "أدخل اسم المستخدم وكلمة المرور لفتح نقطة البيع.",
	primary_logo: "",
	header_logo: "",
	app_icon: "",
	pwa_icon_192: "",
	pwa_icon_512: "",
	primary_color: "#0a8754",
	secondary_color: "#064e3b",
	theme_color: "#0a8754",
	background_color: "#ffffff",
	install_button_label: "تثبيت",
	receipt_title: "Digit POS",
	receipt_footer: "",
	demo_banner_enabled: 0,
	demo_banner_text: "",
	custom_css_optional: "",
}

const BRANDING_STYLE_ID = "pos-branding-settings-css"
const BRANDING_CUSTOM_STYLE_ID = "pos-branding-custom-css"
const BRANDING_RAMP_STYLE_ID = "pos-branding-accent-ramp-css"

/* Derive a full accent ramp from the brand primary and remap every hardcoded
   Tailwind blue/indigo utility to it, so the branding settings screen drives
   the ENTIRE identity (buttons, links, borders, rings) — not just a few vars. */
function _rgb(h) {
	h = String(h || "").replace("#", "")
	if (h.length === 3) h = h.split("").map((c) => c + c).join("")
	const n = Number.parseInt(h || "0a8754", 16)
	return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}
function _hex(r, g, b) {
	return "#" + [r, g, b].map((x) => Math.max(0, Math.min(255, Math.round(x))).toString(16).padStart(2, "0")).join("")
}
function _mix(hex, t, a) {
	const [r, g, b] = _rgb(hex)
	return _hex(r + (t[0] - r) * a, g + (t[1] - g) * a, b + (t[2] - b) * a)
}
const _W = [255, 255, 255]
const _B = [0, 0, 0]

function buildAccentRampCss(primary) {
	const P = primary || DEFAULT_BRANDING.primary_color
	const ramp = {
		50: _mix(P, _W, 0.92),
		100: _mix(P, _W, 0.84),
		200: _mix(P, _W, 0.68),
		300: _mix(P, _W, 0.45),
		400: _mix(P, _W, 0.2),
		500: P,
		600: P,
		700: _mix(P, _B, 0.18),
		800: _mix(P, _B, 0.3),
		900: _mix(P, _B, 0.42),
	}
	const shades = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]
	const props = [
		["bg", "background-color"],
		["text", "color"],
		["border", "border-color"],
		["ring", "--tw-ring-color"],
		["fill", "fill"],
		["stroke", "stroke"],
		["decoration", "text-decoration-color"],
		["caret", "caret-color"],
		["accent", "accent-color"],
		["shadow", "--tw-shadow-color"],
	]
	// Remap all cool-range hues (blue · indigo · purple · violet · fuchsia) to the brand.
	const HUES = ["blue", "indigo", "purple", "violet", "fuchsia"]

	// Use explicit Tailwind-aware CSS selectors instead of [class*="..."] attribute
	// substring matching. [class*="hover:bg-blue-50"] would match the string even when
	// the element is not hovered — causing permanent green on every row. Instead we
	// generate the correct state-scoped selectors so hover/active variants only fire
	// in their actual pseudo-class state.
	const STATE_VARIANTS = [
		["", ""],
		["hover\\:", ":hover"],
		["active\\:", ":active"],
		["focus\\:", ":focus"],
		["focus-within\\:", ":focus-within"],
		["focus-visible\\:", ":focus-visible"],
		["disabled\\:", ":disabled"],
		["checked\\:", ":checked"],
	]

	let css = ""

	for (const s of shades) {
		const c = ramp[s]
		for (const [u, prop] of props) {
			for (const h of HUES) {
				for (const [pfx, sfx] of STATE_VARIANTS) {
					css += `.${pfx}${u}-${h}-${s}${sfx}{${prop}:${c} !important}`
				}
				// Group-hover / group-active / peer-hover
				css += `.group:hover .group-hover\\:${u}-${h}-${s}{${prop}:${c} !important}`
				css += `.group:active .group-active\\:${u}-${h}-${s}{${prop}:${c} !important}`
				css += `.peer:hover~.peer-hover\\:${u}-${h}-${s}{${prop}:${c} !important}`
			}
		}
	}

	// Gradient utilities — per-shade so from-blue-50 ≠ from-blue-600
	const pr = _rgb(P)
	const transparent = `rgba(${pr[0]},${pr[1]},${pr[2]},0)`
	for (const h of HUES) {
		for (const s of shades) {
			const c = ramp[s]
			for (const [pfx, sfx] of STATE_VARIANTS) {
				css += `.${pfx}from-${h}-${s}${sfx}{--tw-gradient-from:${c} var(--tw-gradient-from-position) !important;--tw-gradient-to:${transparent} var(--tw-gradient-to-position) !important}`
				css += `.${pfx}to-${h}-${s}${sfx}{--tw-gradient-to:${c} var(--tw-gradient-to-position) !important}`
				css += `.${pfx}via-${h}-${s}${sfx}{--tw-gradient-via:${c} !important}`
			}
		}
	}

	css += `:root{--ink-blue-1:${ramp[100]};--ink-blue-2:${P};--ink-blue-3:${P};--ink-blue-4:${P};--ink-blue-5:${P};--ink-blue-6:${ramp[700]};--ink-blue-7:${ramp[800]};--ink-blue-8:${ramp[900]};--surface-blue-1:${ramp[100]};--surface-blue-2:${ramp[200]};--surface-blue-3:${P};--surface-blue-4:${ramp[700]};--outline-blue-1:${ramp[300]};--outline-blue-2:${P};--outline-blue-3:${ramp[700]}}`
	return css
}

function normalizeBranding(data = {}) {
	return {
		...DEFAULT_BRANDING,
		...Object.fromEntries(
			Object.entries(data || {}).filter(([, value]) => value !== null && value !== undefined),
		),
	}
}

function setStyleTag(id, cssText) {
	if (typeof document === "undefined") return
	let style = document.getElementById(id)
	if (!cssText) {
		style?.remove()
		return
	}
	if (!style) {
		style = document.createElement("style")
		style.id = id
		document.head.appendChild(style)
	}
	style.textContent = cssText
}

function updateMeta(name, value) {
	if (typeof document === "undefined" || !value) return
	let meta = document.querySelector(`meta[name="${name}"]`)
	if (!meta) {
		meta = document.createElement("meta")
		meta.setAttribute("name", name)
		document.head.appendChild(meta)
	}
	meta.setAttribute("content", value)
}

export const useBrandingStore = defineStore("branding", () => {
	const settings = ref({ ...DEFAULT_BRANDING })
	const loaded = ref(false)
	const loading = ref(false)
	const error = ref(null)

	const appName = computed(() => settings.value.app_name || DEFAULT_BRANDING.app_name)
	const appShortName = computed(() => settings.value.app_short_name || DEFAULT_BRANDING.app_short_name)
	const loginTitle = computed(() => settings.value.login_title || DEFAULT_BRANDING.login_title)
	const loginSubtitle = computed(() => settings.value.login_subtitle || DEFAULT_BRANDING.login_subtitle)
	const installButtonLabel = computed(() => settings.value.install_button_label || DEFAULT_BRANDING.install_button_label)
	const primaryLogo = computed(() => settings.value.primary_logo || "")
	const headerLogo = computed(() => settings.value.header_logo || settings.value.primary_logo || "")
	const appIcon = computed(() => settings.value.app_icon || "")
	const primaryColor = computed(() => settings.value.primary_color || DEFAULT_BRANDING.primary_color)
	const secondaryColor = computed(() => settings.value.secondary_color || DEFAULT_BRANDING.secondary_color)
	const demoBannerEnabled = computed(() => Boolean(settings.value.demo_banner_enabled))
	const demoBannerText = computed(() => settings.value.demo_banner_text || "")
	const receiptTitle = computed(() => settings.value.receipt_title || DEFAULT_BRANDING.receipt_title)
	const receiptFooter = computed(() => settings.value.receipt_footer || "")

	async function loadBranding({ force = false } = {}) {
		if (loaded.value && !force) return settings.value
		loading.value = true
		error.value = null
		try {
			const result = await call("pos_next.api.branding.get_pos_branding_settings", {})
			settings.value = normalizeBranding(result)
		} catch (err) {
			error.value = err
			settings.value = normalizeBranding(settings.value)
		} finally {
			loaded.value = true
			loading.value = false
			applyBranding()
		}
		return settings.value
	}

	function applyBranding() {
		if (typeof document === "undefined") return

		document.title = appName.value
		updateMeta("theme-color", settings.value.theme_color || primaryColor.value)
		updateMeta("apple-mobile-web-app-title", appShortName.value)

		window.pos_next_branding = { ...settings.value }

		setStyleTag(
			BRANDING_STYLE_ID,
			`:root {
				--pos-brand-primary: ${primaryColor.value};
				--pos-brand-secondary: ${secondaryColor.value};
				--pos-brand-theme: ${settings.value.theme_color || primaryColor.value};
				--pos-brand-background: ${settings.value.background_color || DEFAULT_BRANDING.background_color};
			}`,
		)
		setStyleTag(BRANDING_RAMP_STYLE_ID, buildAccentRampCss(primaryColor.value))
		setStyleTag(BRANDING_CUSTOM_STYLE_ID, settings.value.custom_css_optional || "")
	}

	return {
		settings,
		loaded,
		loading,
		error,
		appName,
		appShortName,
		loginTitle,
		loginSubtitle,
		installButtonLabel,
		primaryLogo,
		headerLogo,
		appIcon,
		primaryColor,
		secondaryColor,
		demoBannerEnabled,
		demoBannerText,
		receiptTitle,
		receiptFooter,
		loadBranding,
		applyBranding,
	}
})

export function getRuntimeBranding() {
	if (typeof window === "undefined") return DEFAULT_BRANDING
	return normalizeBranding(window.pos_next_branding || {})
}
