import { call } from "@/utils/apiWrapper"
import { defineStore } from "pinia"
import { computed, ref } from "vue"

export const DEFAULT_BRANDING = {
	enabled: 1,
	app_name: "POSNext",
	app_short_name: "POS",
	workspace_label: "POS",
	login_title: "Sign in to POS",
	login_subtitle: "Enter your username and password to open the point of sale.",
	primary_logo: "",
	header_logo: "",
	app_icon: "",
	pwa_icon_192: "",
	pwa_icon_512: "",
	primary_color: "#4F46E5",
	secondary_color: "#2563EB",
	theme_color: "#4F46E5",
	background_color: "#ffffff",
	install_button_label: "Install",
	receipt_title: "POS",
	receipt_footer: "",
	demo_banner_enabled: 0,
	demo_banner_text: "",
	custom_css_optional: "",
}

const BRANDING_STYLE_ID = "pos-branding-settings-css"
const BRANDING_CUSTOM_STYLE_ID = "pos-branding-custom-css"

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
