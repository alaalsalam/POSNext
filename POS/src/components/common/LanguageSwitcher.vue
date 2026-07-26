<template>
	<div ref="dropdownRef" class="relative">
		<!-- Trigger button -->
		<button
			@click="toggleDropdown"
			class="group flex items-center gap-2 rounded-xl border border-slate-200 bg-white/95 px-2.5 py-2 text-sm shadow-sm backdrop-blur transition-all duration-200 hover:border-emerald-300 hover:bg-emerald-50/70 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-1 disabled:cursor-wait disabled:opacity-60"
			:class="[isRTL ? 'flex-row-reverse' : '', isOpen ? 'border-emerald-300 bg-emerald-50/70 shadow-md' : '']"
			:disabled="isChanging"
			:aria-expanded="isOpen"
			:aria-label="__('Switch Language')"
			:title="__('Switch Language')"
		>
			<template v-if="isChanging">
				<LoadingIndicator class="h-4 w-4 text-emerald-600" />
				<span class="hidden text-xs font-medium text-emerald-700 sm:inline">{{ __("Changing...") }}</span>
			</template>
			<template v-else>
				<!-- Globe icon -->
				<svg
					class="h-4 w-4 shrink-0 text-slate-500 transition-colors group-hover:text-emerald-600"
					:class="isOpen ? 'text-emerald-600' : ''"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					aria-hidden="true"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
					/>
				</svg>
				<!-- Language label -->
				<span
					class="hidden text-[13px] font-semibold leading-none text-slate-700 transition-colors group-hover:text-emerald-800 sm:inline"
					:class="isOpen ? 'text-emerald-800' : ''"
				>
					{{ localeConfig.nativeName }}
				</span>
				<!-- Code badge (mobile fallback) -->
				<span
					class="inline rounded-md bg-emerald-50 px-1.5 py-0.5 text-[11px] font-bold tracking-wide text-emerald-700 sm:hidden"
				>
					{{ locale.toUpperCase() }}
				</span>
				<!-- Chevron -->
				<FeatherIcon
					name="chevron-down"
					class="h-3 w-3 shrink-0 text-slate-400 transition-transform duration-200"
					:class="{ 'rotate-180 text-emerald-500': isOpen }"
				/>
			</template>
		</button>

		<!-- Dropdown -->
		<Transition
			enter-active-class="transition ease-out duration-150"
			enter-from-class="opacity-0 -translate-y-1 scale-95"
			enter-to-class="opacity-100 translate-y-0 scale-100"
			leave-active-class="transition ease-in duration-100"
			leave-from-class="opacity-100 translate-y-0 scale-100"
			leave-to-class="opacity-0 -translate-y-1 scale-95"
		>
			<div
				v-if="isOpen"
				class="absolute z-50 mt-2 w-52 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-2xl shadow-slate-200/60 ring-1 ring-black/[0.04]"
				:class="isRTL ? 'start-0' : 'end-0'"
				role="menu"
				:aria-label="__('Language selection')"
			>
				<!-- Header -->
				<div class="flex items-center gap-2 border-b border-slate-100 bg-slate-50/80 px-4 py-2.5">
					<svg
						class="h-3.5 w-3.5 shrink-0 text-slate-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						aria-hidden="true"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
						/>
					</svg>
					<span class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
						{{ __("Language") }}
					</span>
				</div>

				<!-- Options -->
				<div class="p-1.5">
					<button
						v-for="(config, code) in supportedLocales"
						:key="code"
						@click="selectLanguage(code)"
						class="group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 transition-all duration-150"
						:class="[
							locale === code
								? 'bg-emerald-50 text-emerald-800 ring-1 ring-emerald-100 shadow-sm'
								: 'text-slate-700 hover:bg-slate-50 hover:text-slate-900',
							config.dir === 'rtl' ? 'flex-row-reverse' : '',
						]"
						role="menuitem"
					>
						<!-- Flag -->
						<span
							class="flex h-8 w-10 shrink-0 items-center justify-center rounded-lg bg-white text-xl shadow-sm ring-1 ring-slate-100 transition-transform duration-150"
							:class="locale !== code ? 'group-hover:scale-110' : ''"
						>
							{{ getFlagEmoji(config.countryCode) }}
						</span>

						<!-- Text -->
						<span
							class="flex min-w-0 flex-1 flex-col"
							:class="config.dir === 'rtl' ? 'items-end' : 'items-start'"
						>
							<span class="text-[13px] font-semibold leading-tight">{{ config.nativeName }}</span>
							<span
								class="mt-0.5 text-[11px] leading-tight"
								:class="locale === code ? 'text-emerald-500' : 'text-slate-400'"
							>
								{{ langEnglishName(code) }}
							</span>
						</span>

						<!-- Active indicator -->
						<span
							v-if="locale === code"
							class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-100"
						>
							<FeatherIcon name="check" class="h-3 w-3 text-emerald-700" />
						</span>
					</button>
				</div>
			</div>
		</Transition>
	</div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { FeatherIcon, LoadingIndicator } from "frappe-ui";
import { useLocale } from "@/composables/useLocale";

const { locale, localeConfig, isRTL, supportedLocales, changeLocale } = useLocale();

const isOpen = ref(false);
const isChanging = ref(false);
const dropdownRef = ref(null);

const getFlagEmoji = (countryCode) => {
	const code = (countryCode || "us").toUpperCase();
	if (code === "SA") return "🇸🇦";
	if (code === "US") return "🇺🇸";
	return code
		.split("")
		.map((char) => String.fromCodePoint(127397 + char.charCodeAt(0)))
		.join("");
};

// Map locale code → English name for subtitle
const ENGLISH_NAMES = { ar: "Arabic", en: "English" };
const langEnglishName = (code) => ENGLISH_NAMES[code] || code.toUpperCase();

const toggleDropdown = () => !isChanging.value && (isOpen.value = !isOpen.value);

const selectLanguage = async (code) => {
	isOpen.value = false;
	if (code === locale.value || isChanging.value) return;

	isChanging.value = true;
	try {
		await changeLocale(code);
	} finally {
		isChanging.value = false;
	}
};

const handleClickOutside = (event) => {
	if (!dropdownRef.value?.contains(event.target)) {
		isOpen.value = false;
	}
};

onMounted(() => document.addEventListener("click", handleClickOutside));
onUnmounted(() => document.removeEventListener("click", handleClickOutside));
</script>
