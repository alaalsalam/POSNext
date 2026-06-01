<template>
  <div dir="rtl" class="min-h-screen bg-slate-100 py-8 px-4 sm:px-6 lg:px-8">
    <div class="mx-auto grid min-h-[calc(100vh-4rem)] w-full max-w-6xl items-center gap-6 lg:grid-cols-[420px_1fr]">
      <div class="space-y-6">
      <div class="text-center lg:text-right">
        <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-md">
          <FeatherIcon name="shopping-bag" class="h-7 w-7" :stroke-width="2" />
        </div>
        <h2 class="mt-5 text-3xl font-extrabold text-slate-900">
          تسجيل الدخول إلى POS YemenFrappe
        </h2>
        <p class="mt-2 text-sm leading-6 text-slate-600">
          أدخل بريد مستخدم الديمو وكلمة المرور الموحدة لفتح شاشة البيع.
        </p>
      </div>

      <div class="bg-white py-7 px-6 shadow rounded-lg border border-slate-200">
        <form class="space-y-6" @submit.prevent="submit">
          <div v-if="session.login.error" class="rounded-md bg-red-50 p-4 border border-red-100">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="mr-3">
                <h3 class="text-sm font-medium text-red-800">
                  تعذر تسجيل الدخول
                </h3>
                <div class="mt-2 text-sm text-red-700">
                  <p>{{ readableLoginError }}</p>
                </div>
              </div>
            </div>
          </div>

          <div>
            <Input
              v-model="loginForm.email"
              required
              name="email"
              type="text"
              placeholder="مثال: supermarket@gmail.com"
              label="البريد الإلكتروني أو اسم المستخدم"
              :disabled="session.login.loading"
            />
          </div>

          <div>
            <label class="block">
              <span class="mb-2 block text-sm leading-4 text-slate-700">كلمة المرور</span>
              <div class="relative">
                <input
                  v-model="loginForm.password"
                  required
                  name="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="أدخل كلمة المرور"
                  :disabled="session.login.loading"
                  class="form-input block w-full border-slate-300 placeholder-slate-400 pe-10 focus:border-blue-500 focus:ring-blue-500"
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute inset-y-0 end-0 flex items-center pe-3 text-slate-600 hover:text-slate-800 transition-colors focus:outline-none"
                  :disabled="session.login.loading"
                  tabindex="-1"
                  :aria-label="showPassword ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور'"
                >
                  <FeatherIcon
                    :name="showPassword ? 'eye-off' : 'eye'"
                    class="h-5 w-5"
                    :stroke-width="2"
                  />
                </button>
              </div>
            </label>
          </div>

          <div>
            <Button
              :loading="session.login.loading"
              variant="solid"
              class="w-full py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              type="submit"
            >
              {{ session.login.loading ? 'جاري الدخول...' : 'دخول إلى شاشة البيع' }}
            </Button>
          </div>
        </form>
      </div>

      <div class="rounded-lg border border-blue-100 bg-blue-50 p-4 text-right text-sm leading-6 text-blue-900">
        <div class="flex items-start gap-3">
          <FeatherIcon name="info" class="mt-0.5 h-5 w-5 flex-shrink-0" :stroke-width="2" />
          <div>
            <p class="font-semibold">ملاحظة لمستخدمي الديمو</p>
            <p class="mt-1 text-blue-800">
              كلمة المرور لجميع حسابات الديمو:
              <span class="rounded bg-white px-2 py-0.5 font-mono font-semibold text-blue-950">demo@2026</span>
            </p>
          </div>
        </div>
      </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white p-5 shadow">
        <div class="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 class="text-lg font-bold text-slate-900">حسابات الدخول السريعة</h3>
            <p class="mt-1 text-sm leading-6 text-slate-600">
              اختر الشركة وسيتم تعبئة البريد وكلمة المرور تلقائياً.
            </p>
          </div>
          <div class="rounded-md bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-800">
            الصلاحيات جاهزة
          </div>
        </div>

        <div class="grid max-h-[72vh] gap-3 overflow-y-auto pr-1 sm:grid-cols-2 xl:grid-cols-3">
          <button
            v-for="account in demoAccounts"
            :key="account.email"
            type="button"
            class="group rounded-lg border border-slate-200 bg-slate-50 p-3 text-right transition hover:border-blue-300 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            @click="fillDemoAccount(account)"
          >
            <div class="flex items-start gap-3">
              <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-white text-blue-700 shadow-sm ring-1 ring-slate-200 group-hover:ring-blue-200">
                <FeatherIcon :name="account.icon" class="h-5 w-5" :stroke-width="2" />
              </div>
              <div class="min-w-0">
                <p class="truncate text-sm font-bold text-slate-900">{{ account.company }}</p>
                <p class="truncate text-xs font-medium text-slate-500">{{ account.email }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ account.profile }}</p>
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Shift Opening Dialog -->
    <ShiftOpeningDialog
      v-model="showShiftDialog"
      @shift-opened="handleShiftOpened"
      @dialog-closed="handleDialogClosed"
    />
  </div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"
import { computed, onMounted, reactive, ref, watch } from "vue"
import { useRouter } from "vue-router"
import ShiftOpeningDialog from "../components/ShiftOpeningDialog.vue"
import { session } from "../data/session"
import { useSessionLock } from "../composables/useSessionLock"
import { cleanupUserSession } from "../utils/sessionCleanup"
import { ensureCSRFToken } from "../utils/csrf"
import { offlineWorker } from "../utils/offline/workerClient"
import { logger } from "@/utils/logger"

const log = logger.create("Login")
const demoPassword = "demo@2026"
const demoAccounts = [
	{ company: "الكافيه", email: "cafe@gmail.com", profile: "Cafe", icon: "coffee" },
	{ company: "الشوكولاتة", email: "chocolates@gmail.com", profile: "Chocolates", icon: "gift" },
	{ company: "الأجهزة الكهربائية", email: "Electrical@gmail.com", profile: "Electrical Appliances", icon: "zap" },
	{ company: "الزهور", email: "flower@gmail.com", profile: "Flowers", icon: "heart" },
	{ company: "النظارات", email: "glasses@gmail.com", profile: "Glasses", icon: "eye" },
	{ company: "الذهب والمجوهرات", email: "gold@gmail.com", profile: "Gold and Jewelry", icon: "award" },
	{ company: "الحلاقة والتجميل", email: "hairdressing@gmail.com", profile: "Hairdressing", icon: "scissors" },
	{ company: "الآيس كريم", email: "icecream@gmail.com", profile: "Ice Cream", icon: "smile" },
	{ company: "العطور", email: "perfumes@gmail.com.sa", profile: "Perfumes", icon: "star" },
	{ company: "الصيدلية", email: "pharmacy@gmail.com", profile: "Pharmacy", icon: "plus-circle" },
	{ company: "الجوالات", email: "phones@gmail.com", profile: "Phones", icon: "smartphone" },
	{ company: "البيتزا", email: "pizza@gmail.com", profile: "Pizza", icon: "disc" },
	{ company: "المطعم", email: "restaurant@gmail.com", profile: "Restaurant", icon: "shopping-cart" },
	{ company: "السوبر ماركت", email: "supermarket@gmail.com", profile: "Super Market", icon: "shopping-bag" },
	{ company: "الألعاب", email: "toys@gmail.com", profile: "Toys", icon: "box" },
]

const router = useRouter()
const { cachePasswordHashFromLogin } = useSessionLock()

const loginForm = reactive({
	email: "",
	password: "",
})

const showShiftDialog = ref(false)
const showPassword = ref(false)

function fillDemoAccount(account) {
	loginForm.email = account.email
	loginForm.password = demoPassword
	showPassword.value = true
}

const readableLoginError = computed(() => {
	const messages = session.login.error?.messages || []
	const rawMessage = messages.join(" ").trim()

	if (!rawMessage) {
		return "يرجى التأكد من البريد الإلكتروني وكلمة المرور ثم المحاولة مرة أخرى."
	}

	if (/invalid|incorrect|password|user|login/i.test(rawMessage)) {
		return "بيانات الدخول غير صحيحة. تأكد من البريد وكلمة المرور الموحدة."
	}

	if (/disabled/i.test(rawMessage)) {
		return "هذا المستخدم غير مفعل. يرجى مراجعة مدير النظام."
	}

	if (/permission|not permitted/i.test(rawMessage)) {
		return "المستخدم لا يملك صلاحية الدخول إلى شاشة البيع."
	}

	return rawMessage
})

// Reset state when login page mounts
onMounted(async () => {
	// Clear login form
	loginForm.email = ""
	loginForm.password = ""
	showPassword.value = false

	// Clear any login errors
	if (session.login.error) {
		session.login.reset()
	}

	// Only clear state if user is NOT logged in
	// If user is already logged in (e.g., after successful login), don't clear their session
	if (!session.isLoggedIn) {
		showShiftDialog.value = false
		await cleanupUserSession()
	}
})

function submit() {
	if (!loginForm.email || !loginForm.password) {
		return
	}

	session.login.submit({
		email: loginForm.email.trim(),
		password: loginForm.password,
	})
}

// Watch for successful login
watch(
	() => session.isLoggedIn,
	async (isLoggedIn) => {
		if (isLoggedIn) {
			// Initialize CSRF token after successful login
			try {
				log.info("User logged in, initializing CSRF token...")
				await ensureCSRFToken()

				// Sync CSRF token to worker for background API calls
				if (window.csrf_token) {
					await offlineWorker.setCSRFToken(window.csrf_token)
				}
			} catch (error) {
				log.error("Failed to initialize CSRF token after login:", error)
			}

			// Cache password hash for offline session unlock
			await cachePasswordHashFromLogin(loginForm.password)

			// Show shift opening dialog after successful login
			showShiftDialog.value = true
		}
	},
)

// Watch for dialog being closed via X button (v-model update)
// When user closes dialog without action, navigate to POSSale
watch(showShiftDialog, (isOpen, wasOpen) => {
	// Only navigate if dialog was open and is now closed, and user is logged in
	if (wasOpen === true && isOpen === false && session.isLoggedIn) {
		router.push({ name: "POSSale" })
	}
})

function handleShiftOpened() {
	// Navigate to POS sale after shift is opened
	router.push({ name: "POSSale" })
}

function handleDialogClosed({ reason }) {
	// Navigate to /pos when dialog is cancelled or resumed
	// "cancelled" means user closed dialog without action
	// "resumed" means user chose to resume existing shift
	// In both cases, navigate to POSSale (existing shift will be active)
	if (reason === "cancelled" || reason === "resumed") {
		router.push({ name: "POSSale" })
	}
}

// Clear error when user starts typing
watch([() => loginForm.email, () => loginForm.password], () => {
	if (session.login.error) {
		session.login.reset()
	}
})
</script>
