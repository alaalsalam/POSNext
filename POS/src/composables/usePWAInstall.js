import { computed, onMounted, onUnmounted, ref } from "vue"

const DISMISS_KEY = "pwa-install-dismissed"
const INSTALLED_KEY = "pwa-install-installed"
const DISMISS_WINDOW_DAYS = 7
const DISMISS_WINDOW_MS = DISMISS_WINDOW_DAYS * 24 * 60 * 60 * 1000
const IOS_HINT_DISMISS_KEY = "pwa-install-ios-hint-dismissed"

const deferredPrompt = ref(null)
const isInstallable = ref(false)
const isInstalled = ref(false)
const showInstallBadge = ref(false)
const isIOSInstallHintAvailable = ref(false)
const showIOSInstallHint = ref(false)
let listenersRegistered = false

const isClient = () => typeof window !== "undefined"

const isStandaloneDisplay = () => {
	if (!isClient()) return false
	return (
		window.matchMedia("(display-mode: standalone)").matches ||
		window.navigator.standalone === true
	)
}

const isIOSSafari = () => {
	if (!isClient()) return false
	const userAgent = window.navigator.userAgent || ""
	const vendor = window.navigator.vendor || ""
	const isIOS = /iphone|ipad|ipod/i.test(userAgent)
	const isSafari = /safari/i.test(userAgent) && !/crios|fxios|edgios/i.test(userAgent)
	return isIOS && isSafari && /apple/i.test(vendor || "Apple")
}

const hasActiveDismissal = () => {
	if (!isClient()) return false
	try {
		const stored = localStorage.getItem(DISMISS_KEY)
		if (!stored) return false
		const dismissedAt = new Date(stored).getTime()
		if (Number.isNaN(dismissedAt)) {
			localStorage.removeItem(DISMISS_KEY)
			return false
		}

		if (Date.now() - dismissedAt < DISMISS_WINDOW_MS) {
			return true
		}

		localStorage.removeItem(DISMISS_KEY)
		return false
	} catch (error) {
		console.warn("[PWA] Failed to read dismissal state", error)
		return false
	}
}

const hasInstalledFlag = () => {
	if (!isClient()) return false
	return localStorage.getItem(INSTALLED_KEY) === "1"
}

const hasDismissedIOSHint = () => {
	if (!isClient()) return false
	return localStorage.getItem(IOS_HINT_DISMISS_KEY) === "1"
}

const updateInstalledState = () => {
	const installed = isStandaloneDisplay() || hasInstalledFlag()
	isInstalled.value = installed
	if (installed) {
		isInstallable.value = false
		showInstallBadge.value = false
		showIOSInstallHint.value = false
		if (isClient()) {
			try {
				localStorage.removeItem(DISMISS_KEY)
			} catch (error) {
				console.warn("[PWA] Failed to clear dismissal state", error)
			}
		}
	}
	return installed
}

const updateIOSHintState = () => {
	if (!isClient() || updateInstalledState()) {
		return
	}
	const shouldShowHint = isIOSSafari()
	isIOSInstallHintAvailable.value = shouldShowHint
	showIOSInstallHint.value = shouldShowHint && !hasDismissedIOSHint()
}

const handleBeforeInstallPrompt = (event) => {
	event.preventDefault()
	deferredPrompt.value = event
	isInstallable.value = true
	showIOSInstallHint.value = false
	if (!isInstalled.value && !hasActiveDismissal()) {
		showInstallBadge.value = true
	}
}

const handleAppInstalled = () => {
	deferredPrompt.value = null
	isInstallable.value = false
	showInstallBadge.value = false
	showIOSInstallHint.value = false
	if (isClient()) {
		try {
			localStorage.setItem(INSTALLED_KEY, "1")
		} catch (error) {
			console.warn("[PWA] Failed to persist installed state", error)
		}
	}
	updateInstalledState()
}

const handleVisibilityChange = () => {
	if (document.visibilityState === "visible") {
		updateInstalledState()
		updateIOSHintState()
	}
}

const registerListeners = () => {
	if (!isClient() || listenersRegistered) return
	listenersRegistered = true
	if (!updateInstalledState()) {
		window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt)
		window.addEventListener("appinstalled", handleAppInstalled)
		if (typeof document !== "undefined") {
			document.addEventListener("visibilitychange", handleVisibilityChange)
		}
		updateIOSHintState()
	}
}

export function usePWAInstall() {
	onMounted(() => {
		registerListeners()
	})

	onUnmounted(() => {
		// Keep global PWA listeners alive so the prompt is not lost when route
		// components remount during the cashier flow.
	})

	const canInstall = computed(() => {
		return isInstallable.value && !isInstalled.value && Boolean(deferredPrompt.value)
	})

	const promptInstall = async () => {
		if (!deferredPrompt.value) {
			return false
		}

		deferredPrompt.value.prompt()
		const { outcome } = await deferredPrompt.value.userChoice
		deferredPrompt.value = null
		isInstallable.value = false
		if (outcome === "accepted") {
			showInstallBadge.value = false
			handleAppInstalled()
			return true
		}

		showInstallBadge.value = false
		return false
	}

	const dismissBadge = () => {
		showInstallBadge.value = false
	}

	const dismissIOSHint = () => {
		showIOSInstallHint.value = false
		if (!isClient()) return
		try {
			localStorage.setItem(IOS_HINT_DISMISS_KEY, "1")
		} catch (error) {
			console.warn("[PWA] Failed to dismiss iOS install hint", error)
		}
	}

	const snoozeBadge = () => {
		showInstallBadge.value = false
		if (!isClient()) return
		try {
			localStorage.setItem(DISMISS_KEY, new Date().toISOString())
		} catch (error) {
			console.warn("[PWA] Failed to snooze install badge", error)
		}
	}

	return {
		canInstall,
		isInstallable,
		isInstalled,
		isIOSInstallHintAvailable,
		showInstallBadge,
		showIOSInstallHint,
		promptInstall,
		dismissBadge,
		dismissIOSHint,
		snoozeBadge,
	}
}
