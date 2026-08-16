<template>
	<div class="min-h-screen bg-emerald-50/60 px-4 py-8 sm:px-6 lg:px-8" dir="auto">
		<div class="mx-auto grid min-h-[calc(100vh-4rem)] w-full max-w-7xl items-center gap-8 lg:grid-cols-[1.35fr_0.9fr]">
			<section v-if="showDemoAccounts" class="rounded-lg border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
				<div class="mb-5 flex flex-col gap-1 text-right">
					<h2 class="text-2xl font-bold text-slate-950">{{ __("حسابات الدخول السريعة") }}</h2>
					<p class="text-sm text-slate-600">
						{{ __("اختر النشاط وسيتم تجهيز بيانات الدخول لتجربة نقاط البيع.") }}
					</p>
				</div>

				<div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
					<button
						v-for="account in demoAccounts"
						:key="`${account.profile}-${account.email}`"
						type="button"
						class="group flex min-h-[88px] items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-4 text-right transition hover:border-emerald-300 hover:bg-emerald-50/70 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:ring-offset-2"
						@click="fillDemoAccount(account)"
						:disabled="session.login.loading"
					>
						<div class="min-w-0 flex-1">
							<div class="truncate text-base font-semibold text-slate-950">
								{{ account.company }}
							</div>
							<div class="mt-1 truncate text-sm text-slate-700" dir="ltr">
								{{ account.email }}
							</div>
							<div class="mt-1 truncate text-sm font-medium text-slate-600">
								{{ account.profile }}
							</div>
						</div>
						<span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700 transition group-hover:border-emerald-300 group-hover:bg-emerald-100 group-hover:text-emerald-800">
							<FeatherIcon :name="account.icon" class="h-6 w-6" :stroke-width="2" />
						</span>
					</button>
				</div>
			</section>

			<section class="mx-auto w-full max-w-xl">
				<div class="mb-8 text-center">
					<div class="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-700 text-white shadow-lg shadow-emerald-200">
						<FeatherIcon name="shopping-bag" class="h-8 w-8" :stroke-width="2" />
					</div>
					<h1 class="mt-6 text-3xl font-bold text-slate-950">
						{{ __("Sign in to POS Digit") }}
					</h1>
					<p class="mt-3 text-sm text-slate-600">
						{{ __("Enter your username and password to open the Digit point of sale.") }}
					</p>
				</div>

				<div class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
					<form class="space-y-6" @submit.prevent="submit">
						<div v-if="session.login.error" class="rounded-lg border border-red-100 bg-red-50 p-4 text-right">
							<div class="flex items-start gap-3">
								<FeatherIcon name="x-circle" class="mt-0.5 h-5 w-5 shrink-0 text-red-500" :stroke-width="2" />
								<div>
									<h3 class="text-sm font-semibold text-red-800">
										{{ __("Login Failed") }}
									</h3>
									<p class="mt-2 whitespace-pre-line text-sm text-red-700">
										{{ session.login.error.messages.join("\n") }}
									</p>
								</div>
							</div>
						</div>

						<Input
							v-model="loginForm.email"
							required
							name="email"
							type="text"
							:placeholder="__('Enter your username or email')"
							:label="__('User ID / Email')"
							:disabled="session.login.loading"
						/>

						<label class="block">
							<span class="mb-2 block text-sm leading-4 text-slate-700">{{
								__("Password")
							}}</span>
							<div class="relative">
								<input
									v-model="loginForm.password"
									required
									name="password"
									:type="showPassword ? 'text' : 'password'"
									:placeholder="__('Enter your password')"
									:disabled="session.login.loading"
									class="form-input block w-full rounded-md border-slate-300 pe-10 placeholder-slate-400 focus:border-emerald-600 focus:ring-emerald-600"
								/>
								<button
									type="button"
									@click="showPassword = !showPassword"
									class="absolute inset-y-0 end-0 flex items-center pe-3 text-slate-500 transition hover:text-slate-800 focus:outline-none"
									:disabled="session.login.loading"
									tabindex="-1"
									:aria-label="showPassword ? __('Hide password') : __('Show password')"
								>
									<FeatherIcon
										:name="showPassword ? 'eye-off' : 'eye'"
										class="h-5 w-5"
										:stroke-width="2"
									/>
								</button>
							</div>
						</label>

						<Button
							:loading="session.login.loading"
							variant="solid"
							class="w-full rounded-md border border-transparent bg-emerald-700 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:ring-offset-2 disabled:opacity-50"
							type="submit"
						>
							{{ session.login.loading ? __("Signing in...") : __("دخول إلى شاشة البيع") }}
						</Button>
					</form>
				</div>

				<div class="mt-6 rounded-lg border border-emerald-100 bg-emerald-50 p-4 text-center text-sm text-slate-700">
					<div class="font-semibold text-slate-900">{{ __("ملاحظة لمستخدمي الديمو") }}</div>
					<div class="mt-1">{{ __("كلمة المرور موحدة لجميع حسابات الديمو.") }}</div>
				</div>
			</section>
		</div>

		<ShiftOpeningDialog
			v-model="showShiftDialog"
			@shift-opened="handleShiftOpened"
			@dialog-closed="handleDialogClosed"
		/>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import ShiftOpeningDialog from "../components/ShiftOpeningDialog.vue";
import { session } from "../data/session";
import { useSessionLock } from "../composables/useSessionLock";
import { cleanupUserSession } from "../utils/sessionCleanup";
import { ensureCSRFToken } from "../utils/csrf";
import { offlineWorker } from "../utils/offline/workerClient";
import { logger } from "@/utils/logger";
import { useBrandingStore } from "@/stores/branding";

const log = logger.create("Login");

const router = useRouter();
const branding = useBrandingStore();
const { cachePasswordHashFromLogin } = useSessionLock();
const showDemoAccounts = computed(() => Boolean(branding.settings?.show_demo_accounts));

const demoPassword = "demo@2026";
const demoAccounts = [
	{ company: "الكافيه", email: "cafe@gmail.com", profile: "الكافيه", icon: "coffee" },
	{ company: "الشوكولاتة", email: "chocolates@gmail.com", profile: "الشوكولاتة", icon: "gift" },
	{ company: "الأجهزة الكهربائية", email: "Electrical@gmail.com", profile: "الأجهزة الكهربائية", icon: "zap" },
	{ company: "الزهور", email: "flower@gmail.com", profile: "الزهور", icon: "heart" },
	{ company: "النظارات", email: "glasses@gmail.com", profile: "النظارات", icon: "eye" },
	{ company: "الذهب والمجوهرات", email: "gold@gmail.com", profile: "الذهب والمجوهرات", icon: "award" },
	{ company: "صالون الحلاقة", email: "hairdressing@gmail.com", profile: "صالون الحلاقة", icon: "scissors" },
	{ company: "الآيس كريم", email: "icecream@gmail.com", profile: "الآيس كريم", icon: "smile" },
	{ company: "العطور", email: "perfumes@gmail.com.sa", profile: "العطور", icon: "star" },
	{ company: "الصيدلية", email: "pharmacy@gmail.com", profile: "الصيدلية", icon: "plus-circle" },
	{ company: "الجوالات", email: "phones@gmail.com", profile: "الجوالات", icon: "smartphone" },
	{ company: "البيتزا", email: "pizza@gmail.com", profile: "البيتزا", icon: "target" },
	{ company: "المطعم", email: "restaurant@gmail.com", profile: "المطعم", icon: "shopping-cart" },
	{ company: "السوبر ماركت", email: "supermarket@gmail.com", profile: "السوبر ماركت", icon: "shopping-bag" },
	{ company: "الألعاب", email: "toys@gmail.com", profile: "الألعاب", icon: "box" },
];

const loginForm = reactive({
	email: "",
	password: "",
});

const showShiftDialog = ref(false);
const showPassword = ref(false);

onMounted(async () => {
	await branding.loadBranding();
	loginForm.email = "";
	loginForm.password = "";
	showPassword.value = false;

	if (session.login.error) {
		session.login.reset();
	}

	if (!session.isLoggedIn) {
		showShiftDialog.value = false;
		await cleanupUserSession();
	}
});

function fillDemoAccount(account) {
	loginForm.email = account.email;
	loginForm.password = demoPassword;
	showPassword.value = true;
}

function submit() {
	if (!loginForm.email || !loginForm.password) {
		return;
	}

	session.login.submit({
		email: loginForm.email.trim(),
		password: loginForm.password,
	});
}

watch(
	() => session.isLoggedIn,
	async (isLoggedIn) => {
		if (isLoggedIn) {
			try {
				log.info("User logged in, initializing CSRF token...");
				await ensureCSRFToken();

				if (window.csrf_token) {
					await offlineWorker.setCSRFToken(window.csrf_token);
				}
			} catch (error) {
				log.error("Failed to initialize CSRF token after login:", error);
			}

			await cachePasswordHashFromLogin(loginForm.password);
			showShiftDialog.value = true;
		}
	}
);

watch(showShiftDialog, (isOpen, wasOpen) => {
	if (wasOpen === true && isOpen === false && session.isLoggedIn) {
		router.push({ name: "POSSale" });
	}
});

function handleShiftOpened() {
	router.push({ name: "POSSale" });
}

function handleDialogClosed({ reason }) {
	if (reason === "cancelled" || reason === "resumed") {
		router.push({ name: "POSSale" });
	}
}

watch([() => loginForm.email, () => loginForm.password], () => {
	if (session.login.error) {
		session.login.reset();
	}
});
</script>
